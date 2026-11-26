"""Kaikki-data-accessor — index + JSONL + byte-offset-cache.

Hanterar uppslag av kaikki-poster för en given (lemma, pos).
- Index (.pkl) används där det räcker — verb / noun / adj.
- JSONL-scan används som fallback för pron / frågepronomen / fall där
  indexet missar (kaikki-indexet är ofullständigt).
- En byte-offset-cache byggs lazily vid första JSONL-användning och sparas
  som .pkl bredvid kaikki-dumpen. Sätter ner uppslag från linjär scan
  (~10 sek) till O(antal poster för (lemma, pos)) — typiskt ~1 ms.

VIKTIGT — saknade språk:
    Kaikki-dumparna i `gammal/datafiler/kaikki/` täcker bara sv, de, es,
    fr, it. ENGELSKA OCH JAPANSKA SAKNAS HELT. För dessa språk behövs en
    separat datakälla:
      - en: Wiktionary-API direkt eller en kaikki-extraktion på engelska
        (kaikki.org tillhandahåller olika dumpar — se kaikki.org).
      - ja: liknande, plus eventuellt NINJAL-databaser eller JMdict för
        verbböjning. I den nuvarande mappningen kan dessa språk inte
        hanteras — försök ger `SpråkSaknas`-fel.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

PROJEKTROT = Path(__file__).resolve().parents[3]
KAIKKI_DIR = PROJEKTROT / "gammal" / "datafiler" / "kaikki"

SPRÅK_MED_KAIKKI: frozenset[str] = frozenset({"sv", "de", "es", "fr", "it"})
SPRÅK_UTAN_KAIKKI: frozenset[str] = frozenset({"en", "ja"})


class SpråkSaknas(RuntimeError):
    """Höjs när kaikki-data inte finns för ett språk."""


@dataclass(frozen=True, slots=True)
class KaikkiPost:
    """En kaikki-post för en (lemma, pos)-kombination — det vi bryr oss om."""
    lemma: str
    pos: str
    forms: list[tuple[str, list[str]]]   # [(form, tags), ...]
    head_exp: str = ""


class KaikkiAccess:
    """Lazy uppslagslager för en språkdump.

    Användning:
        ka = KaikkiAccess("sv")
        for post in ka.poster_för("tala", "verb"):
            for form, tags in post.forms:
                ...
    """

    def __init__(self, språk: str):
        if språk in SPRÅK_UTAN_KAIKKI:
            raise SpråkSaknas(
                f"Kaikki-dump saknas för '{språk}'. Engelska och japanska "
                f"behöver separat dataladdning (Wiktionary-API eller dedikerad "
                f"resurs) — den här modulen kan inte mappa {språk}."
            )
        if språk not in SPRÅK_MED_KAIKKI:
            raise ValueError(f"Okänt språk: {språk!r}")
        self.språk = språk
        self._index: dict | None = None
        self._offsets: dict[tuple[str, str], list[int]] | None = None

    # ── Filsökvägar ──────────────────────────────────────────────────

    def _index_fil(self) -> Path:
        return KAIKKI_DIR / f"kaikki_{self.språk}_index.pkl"

    def _jsonl_fil(self) -> Path:
        return KAIKKI_DIR / f"kaikki_{self.språk}.jsonl"

    def _offset_cache_fil(self) -> Path:
        return KAIKKI_DIR / f"kaikki_{self.språk}_offsets.pkl"

    # ── Lazy-loading ─────────────────────────────────────────────────

    def _ladda_index(self) -> dict:
        if self._index is None:
            with self._index_fil().open("rb") as f:
                self._index = pickle.load(f)
        return self._index

    def _ladda_offsets(self) -> dict[tuple[str, str], list[int]]:
        if self._offsets is not None:
            return self._offsets
        cache = self._offset_cache_fil()
        if cache.exists():
            with cache.open("rb") as f:
                self._offsets = pickle.load(f)
            return self._offsets
        self._offsets = self._bygg_offsets()
        with cache.open("wb") as f:
            pickle.dump(self._offsets, f, protocol=pickle.HIGHEST_PROTOCOL)
        return self._offsets

    def _bygg_offsets(self) -> dict[tuple[str, str], list[int]]:
        """Linjär scan av JSONL för att bygga byte-offset-index per (word, pos).

        Engångsoperation — tar ~10 sek för 348 MB sv-dump. Sparas som .pkl.
        """
        offsets: dict[tuple[str, str], list[int]] = {}
        path = self._jsonl_fil()
        with path.open("rb") as f:
            byte_pos = 0
            for line in f:
                try:
                    d = json.loads(line)
                    w = d.get("word")
                    p = d.get("pos")
                    if w and p:
                        offsets.setdefault((w, p), []).append(byte_pos)
                except json.JSONDecodeError:
                    pass
                byte_pos += len(line)
        return offsets

    # ── Publika uppslag ──────────────────────────────────────────────

    def poster_för(self, lemma: str, pos: str) -> list[KaikkiPost]:
        """Hämta alla kaikki-poster för (lemma, pos).

        Försöker indexet först (snabbt). Faller tillbaka till JSONL via
        offset-cache om indexet inte har posten.
        """
        # Steg 1: indexet
        idx = self._ladda_index()
        träff = idx.get(lemma, {}).get(pos)
        if träff is not None and träff.get("forms"):
            forms = [
                (f[0], list(f[1])) if isinstance(f, (list, tuple))
                else (f.get("form", ""), f.get("tags", []) or [])
                for f in träff["forms"]
            ]
            return [
                KaikkiPost(
                    lemma=lemma,
                    pos=pos,
                    forms=forms,
                    head_exp=träff.get("head_exp", ""),
                )
            ]

        # Steg 2: JSONL via offset
        offsets = self._ladda_offsets()
        nycklar = offsets.get((lemma, pos), [])
        if not nycklar:
            return []
        path = self._jsonl_fil()
        poster: list[KaikkiPost] = []
        with path.open("rb") as f:
            for off in nycklar:
                f.seek(off)
                line = f.readline()
                d = json.loads(line)
                forms_raw = d.get("forms", []) or []
                forms = [
                    (fm.get("form", ""), list(fm.get("tags", []) or []))
                    for fm in forms_raw
                    if "table-tags" not in (fm.get("tags") or [])
                    and "inflection-template" not in (fm.get("tags") or [])
                ]
                head_exp = ""
                if d.get("head_templates"):
                    head_exp = d["head_templates"][0].get("expansion", "")
                poster.append(
                    KaikkiPost(lemma=lemma, pos=pos, forms=forms, head_exp=head_exp)
                )
        return poster
