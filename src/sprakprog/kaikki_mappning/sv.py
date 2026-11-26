"""Svenska-specifik kaikki-mappning.

Översätter kaikki-tags till våra Former-axlar enligt sv-konventioner och
matchar resulterande axel-tupel mot slot-filens celler.

Specialfall som hanteras explicit:
  • `error-unrecognized-form` är inte ett fel — kaikki misslyckas bara
    klassificera default-formen. Behåll och flagga som not.
  • Pronomen-lemmaformen finns inte i kaikki-forms (lemmat är förstås
    inte en "form" av sig självt). Injicera lemmat i nom-cellen för
    Pronomen och Frågepronomen.
  • Genus=Alla (3) i en cell matchar form utan genus-tag. Andra IntEnum-
    axlar har ingen sådan neutralizer.
  • Kasus "nominative" i sv täcker [Nom, Ack, Dat] (kasus=7) eftersom
    sv inte morfologiskt skiljer dem; matchningen sker via subset-regeln.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .data_access import KaikkiAccess, KaikkiPost
from .paradigm import ALLA_AXLAR, INTFLAG_AXLAR, Cell, Slot, ladda_legend, ladda_slot


# ── Tag-mappningstabell ─────────────────────────────────────────────────

# kaikki-tag → (axel, lista_av_konstantnamn)
# Vid generering OR:as bitmask-värdena; för IntEnum måste listan ha 1 element.
SV_TAG_MAP: dict[str, tuple[str, list[str]]] = {
    # Tempus (verb)
    "infinitive":  ("tempus", ["Inf"]),
    "present":     ("tempus", ["Pres"]),
    "preterite":   ("tempus", ["Pret"]),
    "past":        ("tempus", ["Pret"]),
    "supine":      ("tempus", ["Sup"]),
    "imperative":  ("tempus", ["Imp"]),

    # Diates (verb)
    "active":  ("diates", ["Aktiv"]),
    "passive": ("diates", ["Passiv"]),

    # Species (substantiv, adjektiv)
    "indefinite": ("species", ["Obest"]),
    "definite":   ("species", ["Best"]),

    # Kasus (substantiv, pronomen)
    # OBS sv: "nominative" på substantiv täcker faktiskt nom+ack+dat (sv
    # särskiljer bara genitiv morfologiskt). Vi mappar till bara Nom-biten;
    # subset-matchning gör att det matchar mot kasus=[Nom,Ack,Dat]-celler.
    "nominative": ("kasus",  ["Nom"]),
    "genitive":   ("kasus",  ["Gen"]),
    "oblique":    ("kasus",  ["Ack", "Dat"]),  # för pronomen

    # Numerus
    "singular": ("numerus", ["Sg"]),
    "plural":   ("numerus", ["Pl"]),

    # Genus (sv: utrum/neutrum mappas till UtrMask/NeuFem-axelvärden)
    "common": ("genus", ["UtrMask"]),
    "uter":   ("genus", ["UtrMask"]),
    "neuter": ("genus", ["NeuFem"]),

    # Grad (adjektiv)
    "positive":    ("grad", ["Pos"]),
    "comparative": ("grad", ["Komp"]),
    "superlative": ("grad", ["Superl"]),

    # Possessivformer (pronomen) — kombinerade tags
    "possessed-common": ("genus_numerus", ["UtrMask", "Sg"]),  # specialfall, hanteras separat
    "possessed-neuter": ("genus_numerus", ["NeuFem",  "Sg"]),
    "possessed-plural": ("genus_numerus", ["Alla",    "Pl"]),
}

# Tags som bara är information vi inte använder — ignoreras tyst
SV_TAGS_IGNORE: frozenset[str] = frozenset({
    "indicative",        # vi spårar inte modus
    "first-person",      # person på Lexem, ej Former
    "second-person",
    "third-person",
    "possessive",        # markerar bara att det är possessivt
})

# Tags som markerar former vi skippar
SV_TAGS_SKIP: frozenset[str] = frozenset({
    "archaic", "dated", "obsolete",
    "alternative", "colloquial", "pronunciation-spelling",
    "subjunctive", "participle",
    "masculine", "feminine",  # sv adjektiv: arkaiska genusformer, inte nuvarande system
    "Kalix", "Luleå", "Piteå", "Norrbotten", "Småland", "Skåne",
})

# Tags som inte är fel men markerar kaikki-osäkerhet — behåll, notera
SV_TAGS_NOTE: frozenset[str] = frozenset({"error-unrecognized-form"})

# Default-värden när tag är frånvarande (sv-specifika)
SV_DEFAULT_DIATES = "Aktiv"  # form utan active/passive-tag är aktiv

# Genus-värdet som matchar form-utan-genus i en cell
SV_NEUTRALIZER: dict[str, str] = {"genus": "Alla"}

# Mappar Koncept.ordklass → kaikki-pos
ORDKLASS_TILL_POS: dict[str, str] = {
    "Verb":          "verb",
    "Substantiv":    "noun",
    "Adjektiv":      "adj",
    "Adverb":        "adv",
    "Pronomen":      "pron",
    "Frågepronomen": "pron",
    "Räkneord":      "num",
    "Preposition":   "prep",
    "Konjunktion":   "conj",
}

# Ordklasser där indexet är opålitligt — gå direkt till JSONL
ORDKLASSER_FÖRBI_INDEX: frozenset[str] = frozenset({"Pronomen", "Frågepronomen"})


# ── Output-typer ────────────────────────────────────────────────────────

@dataclass
class FylldCell:
    cell_id: str
    form: str
    axlar: dict[str, int | None]
    kaikki_tags: list[str]


@dataclass
class SaknadCell:
    cell_id: str
    förväntade_axlar: dict[str, int | None]


@dataclass
class SkippadForm:
    form: str
    kaikki_tags: list[str]
    skäl: str


@dataclass
class Mappningsrapport:
    lemma: str
    språk: str
    ordklass: str
    celler_fyllda: list[FylldCell] = field(default_factory=list)
    celler_saknade: list[SaknadCell] = field(default_factory=list)
    former_skippade: list[SkippadForm] = field(default_factory=list)
    varningar: list[str] = field(default_factory=list)
    # Internt: person+numerus-ankare för pronomen-filtrering (ej i som_dict)
    _pn_ankare: tuple[str | None, str | None] | None = field(default=None, repr=False)

    def som_dict(self) -> dict[str, Any]:
        """JSON-serialiserbar representation."""
        return {
            "lemma": self.lemma,
            "språk": self.språk,
            "ordklass": self.ordklass,
            "celler_fyllda": [
                {
                    "cell_id": c.cell_id,
                    "form": c.form,
                    "axlar": c.axlar,
                    "kaikki_tags": c.kaikki_tags,
                }
                for c in self.celler_fyllda
            ],
            "celler_saknade": [
                {"cell_id": c.cell_id, "förväntade_axlar": c.förväntade_axlar}
                for c in self.celler_saknade
            ],
            "former_skippade": [
                {"form": f.form, "kaikki_tags": f.kaikki_tags, "skäl": f.skäl}
                for f in self.former_skippade
            ],
            "varningar": list(self.varningar),
        }


# ── Huvudfunktion ───────────────────────────────────────────────────────

def mappa_lemma_sv(
    lemma: str,
    ordklass: str,
    *,
    access: KaikkiAccess | None = None,
) -> Mappningsrapport:
    """Mappa ett svenskt lemma till slot-fil-celler via kaikki + sv-regler."""
    if access is None:
        access = KaikkiAccess("sv")

    legend = ladda_legend()
    slot = ladda_slot("sv", ordklass, legend=legend)

    rapport = Mappningsrapport(lemma=lemma, språk="sv", ordklass=ordklass)

    # Hämta kaikki-poster
    pos = ORDKLASS_TILL_POS.get(ordklass)
    if pos is None:
        rapport.varningar.append(
            f"Okänd ordklass {ordklass!r} — saknar kaikki-pos-mappning."
        )
        _markera_alla_celler_saknade(slot.celler, rapport)
        return rapport

    # Pronomen-/frågepronomen-fall: hoppa över indexet, alltid JSONL
    if ordklass in ORDKLASSER_FÖRBI_INDEX:
        # Twiddle: använd JSONL direkt genom att inte gå via indexet
        # (poster_för försöker först indexet — vi får workaround genom
        # att förstöra indexcachen tillfälligt, men det är hackigt; istället
        # kallar vi en privat metod)
        offsets = access._ladda_offsets()
        nycklar = offsets.get((lemma, pos), [])
        path = access._jsonl_fil()
        poster: list[KaikkiPost] = []
        if nycklar:
            import json as _json
            with path.open("rb") as f:
                for off in nycklar:
                    f.seek(off)
                    line = f.readline()
                    d = _json.loads(line)
                    forms_raw = d.get("forms", []) or []
                    forms = [
                        (fm.get("form", ""), list(fm.get("tags", []) or []))
                        for fm in forms_raw
                        if "table-tags" not in (fm.get("tags") or [])
                        and "inflection-template" not in (fm.get("tags") or [])
                    ]
                    poster.append(KaikkiPost(lemma=lemma, pos=pos, forms=forms))
    else:
        poster = access.poster_för(lemma, pos)

    if not poster:
        rapport.varningar.append(f"Inga kaikki-poster funna för ({lemma!r}, pos={pos!r}).")
        _markera_alla_celler_saknade(slot.celler, rapport)
        # Pronomen-injiceringen kan ändå ge oss nom-cellen
        if ordklass in ORDKLASSER_FÖRBI_INDEX:
            _injicera_pronomen_lemma(lemma, slot, rapport, legend)
        return rapport

    # Slå ihop alla forms från alla matchande poster (kan finnas multipla
    # senses/etymologier); deduplicera på (form, tags-tupel)
    seen: set[tuple[str, tuple[str, ...]]] = set()
    alla_former: list[tuple[str, list[str]]] = []
    for post in poster:
        for form, tags in post.forms:
            nyckel = (form, tuple(sorted(tags)))
            if nyckel in seen:
                continue
            seen.add(nyckel)
            alla_former.append((form, tags))

    # Pronomen-injicering: lemmat som nom-cell
    if ordklass in ORDKLASSER_FÖRBI_INDEX:
        _injicera_pronomen_lemma(lemma, slot, rapport, legend)

    # Frågepronomen-injicering: lemmat som ack_dat-cell (vem = nom = ack i sv)
    if ordklass == "Frågepronomen":
        _injicera_frågepronomen_ack_dat(lemma, slot, rapport, legend)

    # Adjektiv-injicering: lemmaformen som obest_m_sg_pos (kaikki saknar genus-tag)
    if ordklass == "Adjektiv":
        _injicera_adjektiv_lemma(lemma, slot, rapport, legend)

    # Bygg person+numerus-ankare från lemmats nominativform (för pronomen-filtrering)
    if ordklass in ORDKLASSER_FÖRBI_INDEX:
        _ankare_p: str | None = None
        _ankare_n: str | None = None
        for _f, _t in alla_former:
            if _f == lemma:
                for _tag in _t:
                    if _tag in {"first-person", "second-person", "third-person"}:
                        _ankare_p = _tag
                    if _tag in {"singular", "plural"}:
                        _ankare_n = _tag
                break
        rapport._pn_ankare = (_ankare_p, _ankare_n)

    # För varje form, översätt tags → axlar och matcha mot celler
    matchade_cell_ider: set[tuple[str, tuple[tuple[str, int | None], ...]]] = set()
    # håll koll på vilka celler som blivit fyllda (id + axel-tupel-key) för
    # att markera "saknad" korrekt
    fyllda_cell_axel_tuplar: set[tuple[str, ...]] = set()
    for c in rapport.celler_fyllda:
        fyllda_cell_axel_tuplar.add(_axel_nyckel(c.axlar))

    for form, tags in alla_former:
        if form == "-" or not form:
            rapport.former_skippade.append(SkippadForm(form, list(tags), "tomt formvärde"))
            continue

        skip_skäl = _ska_skippas(tags)
        if skip_skäl:
            rapport.former_skippade.append(SkippadForm(form, list(tags), skip_skäl))
            continue

        try:
            axlar = _tags_till_axlar(tags, legend)
        except ValueError as e:
            rapport.varningar.append(f"Form {form!r}: {e}")
            continue

        # Filtrera till lemma-paradigmet med person+numerus-ankare
        if ordklass in ORDKLASSER_FÖRBI_INDEX:
            ankare = rapport._pn_ankare
            if ankare and (ankare[0] is not None or ankare[1] is not None):
                _fp = next(
                    (t for t in tags if t in {"first-person", "second-person", "third-person"}),
                    None,
                )
                _fn = next((t for t in tags if t in {"singular", "plural"}), None)
                _skippa = False
                if _fp is not None and _fp != ankare[0]:
                    _skippa = True
                elif (
                    _fn is not None
                    and "possessive" not in tags
                    and _fn != ankare[1]
                ):
                    _skippa = True
                if _skippa:
                    rapport.former_skippade.append(
                        SkippadForm(form, list(tags), f"hör till annat paradigm än {lemma!r}")
                    )
                    continue

        träffar = [c for c in slot.celler if _matchar(c, axlar, legend)]
        if not träffar:
            rapport.varningar.append(
                f"Form {form!r} (tags={tags}) → axlar={axlar} matchar ingen cell."
            )
            continue
        if len(träffar) > 1:
            # Välj den mest specifika (minst antal NULL-axlar)
            träffar.sort(key=lambda c: sum(1 for v in c.axlar.values() if v is None))
        cell = träffar[0]

        nyckel = _axel_nyckel(cell.axlar)
        if nyckel in fyllda_cell_axel_tuplar:
            # Redan fylld — kaikki-dubblett, hoppa
            continue
        fyllda_cell_axel_tuplar.add(nyckel)

        rapport.celler_fyllda.append(
            FylldCell(
                cell_id=cell.id,
                form=form,
                axlar=dict(cell.axlar),
                kaikki_tags=list(tags),
            )
        )

    # Markera ofyllda celler som saknade
    for cell in slot.celler:
        if _axel_nyckel(cell.axlar) not in fyllda_cell_axel_tuplar:
            rapport.celler_saknade.append(
                SaknadCell(cell_id=cell.id, förväntade_axlar=dict(cell.axlar))
            )

    return rapport


# ── Hjälpfunktioner ─────────────────────────────────────────────────────

def _ska_skippas(tags: list[str]) -> str | None:
    """Returnera skäl-sträng om formen ska skippas, annars None."""
    for t in tags:
        if t in SV_TAGS_SKIP:
            return t
    return None


def _tags_till_axlar(
    tags: list[str], legend: dict[str, dict[str, int]]
) -> dict[str, int | None]:
    """Översätt en kaikki-tag-lista till axel→int-dict (None för okända axlar)."""
    axlar: dict[str, int | None] = {a: None for a in ALLA_AXLAR}
    pres_tags = set(tags)
    for tag in tags:
        if tag in SV_TAGS_IGNORE or tag in SV_TAGS_NOTE:
            continue
        if tag not in SV_TAG_MAP:
            # Okänd tag — varna senare via uppringaren
            continue
        axel, namn_lista = SV_TAG_MAP[tag]
        # Specialfall: possessed-* sätter både genus och numerus
        if axel == "genus_numerus":
            g_namn, n_namn = namn_lista
            axlar["genus"] = legend["genus"][g_namn]
            axlar["numerus"] = legend["numerus"][n_namn]
            continue
        if axel in INTFLAG_AXLAR:
            bits = 0
            for n in namn_lista:
                bits |= legend[axel][n]
            if axlar[axel] is None:
                axlar[axel] = bits
            else:
                axlar[axel] |= bits
        else:
            if len(namn_lista) != 1:
                raise ValueError(f"IntEnum-tag {tag!r} mappar till flera värden")
            v = legend[axel][namn_lista[0]]
            if axlar[axel] is not None and axlar[axel] != v:
                raise ValueError(
                    f"Konflikt: {axel} satt till både {axlar[axel]} och {v}"
                )
            axlar[axel] = v

    # Default: diates=Aktiv om inte explicit satt och form är ett verb
    # (Vi avgör verb-status via förekomst av tempus-bit)
    if axlar.get("tempus") is not None and axlar.get("diates") is None:
        axlar["diates"] = legend["diates"][SV_DEFAULT_DIATES]

    # Default: numerus=Sg för best adj-former utan numerus-tag.
    # Kaikki utelämnar ibland "singular" för best-former (t.ex. "stora" tagged
    # som bara [definite, positive]). Utan detta default matchar formen inga celler.
    _best = legend.get("species", {}).get("Best")
    _pos  = legend.get("grad", {}).get("Pos")
    _spl  = legend.get("grad", {}).get("Superl")
    if (
        _best is not None
        and axlar.get("species") == _best
        and axlar.get("grad") in {_pos, _spl}
        and axlar.get("numerus") is None
    ):
        axlar["numerus"] = legend["numerus"]["Sg"]

    return axlar


def _matchar(cell: Cell, form_axlar: dict[str, int | None], legend: dict) -> bool:
    """Cell matchar form om alla axlar stämmer enligt subset/equals-regeln."""
    for axel in ALLA_AXLAR:
        c = cell.axlar.get(axel)
        f = form_axlar.get(axel)
        if c is None and f is None:
            continue
        if c is None and f is not None:
            return False
        if c is not None and f is None:
            # Cell-värdet kan vara en "neutralizer" som accepterar form-utan-tag
            namn = SV_NEUTRALIZER.get(axel)
            if namn is not None and legend[axel].get(namn) == c:
                continue
            return False
        # Båda satta
        if axel in INTFLAG_AXLAR:
            if (f & c) != f:
                return False
        else:
            if f != c:
                return False
    return True


def _axel_nyckel(axlar: dict[str, int | None]) -> tuple[str, ...]:
    """Hashbar nyckel för en axeltupel (för dedupering)."""
    return tuple(f"{a}={axlar.get(a)}" for a in ALLA_AXLAR)


def _injicera_adjektiv_lemma(
    lemma: str,
    slot: Slot,
    rapport: Mappningsrapport,
    legend: dict[str, dict[str, int]],
) -> None:
    """Injicera lemmaformen direkt som obest_m_sg_pos.

    Kaikki taggar default-adjektivformen med 'error-unrecognized-form' och
    saknar genus-tag. Istället för att förlita oss på tag-matchning fyller
    vi cellen direkt med lemmat.
    """
    mål = "obest_m_sg_pos"
    for cell in slot.celler:
        if cell.id == mål:
            redan_fylld = any(c.cell_id == mål for c in rapport.celler_fyllda)
            if not redan_fylld:
                rapport.celler_fyllda.append(
                    FylldCell(
                        cell_id=mål,
                        form=lemma,
                        axlar=dict(cell.axlar),
                        kaikki_tags=["[INJICERAD lemma → obest_m_sg_pos]"],
                    )
                )
            return


def _injicera_frågepronomen_ack_dat(
    lemma: str,
    slot: Slot,
    rapport: Mappningsrapport,
    legend: dict[str, dict[str, int]],
) -> None:
    """Injicera lemmat som ack_dat-cellen för frågepronomen.

    I modern svenska är 'vem' homograft för nominativ och ackusativ/dativ.
    Kaikki har ingen separat oblique-form — vi injicerar lemmat direkt.
    """
    ack_val = legend["kasus"]["Ack"]
    dat_val = legend["kasus"]["Dat"]
    mål_kasus = ack_val | dat_val
    for cell in slot.celler:
        c_kasus = cell.axlar.get("kasus")
        if c_kasus is not None and c_kasus == mål_kasus:
            redan_fylld = any(c.cell_id == cell.id for c in rapport.celler_fyllda)
            if not redan_fylld:
                rapport.celler_fyllda.append(
                    FylldCell(
                        cell_id=cell.id,
                        form=lemma,
                        axlar=dict(cell.axlar),
                        kaikki_tags=["[INJICERAD lemma → ack_dat]"],
                    )
                )
            return


def _form_hör_till_lemma(form: str, lemma: str) -> bool:
    """Heuristik: form hör till lemma-paradigmet om de delar inledande bokstav.

    Hanterar kaikki-fallet där pronomen-poster bundlar flera paradigm
    (t.ex. "vem"-posten innehåller även "vilken"-former). För svenska
    pronomen är initialbokstaven en pålitlig diskriminator (jag/mig vs
    min/mitt vs vem/vilken — ALLA delar dock 'v', så för vem behöver vi
    starkare regel: form ska börja med samma 1–3 bokstäver som lemmat).
    """
    if not form or not lemma:
        return False
    # Personligt vs possessivt: jag/mig delar j/m. Använd första bokstaven.
    # vem/vilken: båda börjar med v men skiljer sig på andra bokstaven.
    # Heuristik: form delar minst en bokstav-prefix med lemmat, ELLER är
    # genitiv-form (lemma+s).
    if form == lemma + "s":
        return True
    # Acceptera form vars första två bokstäver matchar lemmats första två.
    n = min(2, len(lemma))
    return form[:n].lower() == lemma[:n].lower()


def _injicera_pronomen_lemma(
    lemma: str,
    slot: Slot,
    rapport: Mappningsrapport,
    legend: dict[str, dict[str, int]],
) -> None:
    """Lägg in lemmat som nom-cellen för pronomen/frågepronomen."""
    nom_värde = legend["kasus"]["Nom"]
    for cell in slot.celler:
        c_kasus = cell.axlar.get("kasus")
        if c_kasus is not None and (c_kasus & nom_värde) == nom_värde:
            # Är "nom"-eller-"nom-inkluderande" cell — fyll om ej redan fylld
            redan_fylld = any(c.cell_id == cell.id for c in rapport.celler_fyllda)
            if not redan_fylld:
                rapport.celler_fyllda.append(
                    FylldCell(
                        cell_id=cell.id,
                        form=lemma,
                        axlar=dict(cell.axlar),
                        kaikki_tags=["[INJICERAD lemma → nom]"],
                    )
                )
            return


def _markera_alla_celler_saknade(celler: list[Cell], rapport: Mappningsrapport) -> None:
    for cell in celler:
        rapport.celler_saknade.append(
            SaknadCell(cell_id=cell.id, förväntade_axlar=dict(cell.axlar))
        )
