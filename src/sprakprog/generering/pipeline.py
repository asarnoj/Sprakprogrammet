"""Genererings-pipeline: slot-fil + LLM → Former-tabellen.

Flöde per anrop:
  1. Läs slot-filen för (språk, ordklass).
  2. Hämta Lexem-rader från databasen.
  3. Dela upp i batchar.
  4. För varje batch: bygg prompt → anropa Claude → parsa JSON → skriv Former.
  5. Returnera statistik.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

from ..kaikki_mappning.paradigm import (
    ALLA_AXLAR, PARADIGM_DIR, Cell, Slot, ladda_legend, ladda_slot,
)

STANDARD_MODELL = "claude-haiku-4-5"
STANDARD_BATCH = 10

# Riktvärde för hur många formsträngar ett svar bör innehålla. Modellen
# tappar precision och kapar svar när det blir för mycket: de/Adjektiv har
# 144 celler, så tio ord i en batch ger 1 440 former i ett svep — det var så
# es/Verb "abrir" tyst gav noll rader vid batch 10 men alla 53 vid batch 1.
FORMER_PER_SVAR = 300


def _lämplig_batch(antal_celler: int) -> int:
    """Batch-storlek som håller svaret runt FORMER_PER_SVAR former.

    de/Adjektiv (144 celler) → 2, romanska verb (45–53) → 5–6,
    substantiv (2–8) → 10. Motsvarar de storlekar som togs fram för hand
    i smoke-testet 2026-08-01.
    """
    if antal_celler <= 0:
        return STANDARD_BATCH
    return max(1, min(STANDARD_BATCH, FORMER_PER_SVAR // antal_celler))


# ── LLM-transport ────────────────────────────────────────────────────
#
# Anropar claude-CLI:t direkt via subprocess — INTE claude-agent-sdk.
#
# Bakgrund (2026-07-09): claude-agent-sdk-python är enligt Anthropics egen
# dokumentation (code.claude.com/docs/en/agent-sdk/overview) designat för
# ANTHROPIC_API_KEY-fakturering, och dokumentationen ber uttryckligen
# tredjepartsverktyg byggda på Agent SDK:t att INTE erbjuda claude.ai-inloggning
# (dvs. prenumerationsfakturering) utan förhandsgodkännande. En stängd
# GitHub-issue (anthropics/claude-agent-sdk-python#559) bekräftar att SDK:t
# inte stödjer Max/Pro-fakturering.
#
# CLI:t (`claude -p "prompt"`) är däremot den officiellt avsedda vägen för
# att köra Claude Code icke-interaktivt mot en Pro/Max-prenumeration — det
# är samma faktureringsväg som interaktiv användning. Därför används den
# här, utan SDK-beroende.
#
# Kör `claude` en gång och logga in innan skarp körning. Sätt INTE
# ANTHROPIC_API_KEY i miljön — då faktureras API-credits i stället
# (API-nyckeln vinner tyst över prenumerations-inloggningen).

def _anropa_llm(prompt: str, modell: str) -> str:
    """Skicka prompten till Claude via claude-CLI:t, returnera svarstexten."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    result = subprocess.run(
        ["claude", "--model", modell, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"exit {result.returncode}")
    return result.stdout


def _ladda_instruktioner(språk: str, ordklass: str) -> str:
    """Läs paradigm/{språk}/INSTRUKTIONER.md: sektionen 'Allmänt' + ordklassens.

    Returnerar tom sträng om filen eller sektionerna saknas — prompten
    fungerar utan, men blir bättre med.
    """
    fil = PARADIGM_DIR / språk / "INSTRUKTIONER.md"
    if not fil.exists():
        return ""

    sektioner: dict[str, list[str]] = {}
    aktuell: list[str] | None = None
    for rad in fil.read_text(encoding="utf-8").splitlines():
        if rad.startswith("## "):
            aktuell = sektioner.setdefault(rad[3:].strip(), [])
        elif aktuell is not None and not rad.startswith("> "):
            aktuell.append(rad)

    delar = []
    for namn in ("Allmänt", ordklass):
        if namn in sektioner:
            text = "\n".join(sektioner[namn]).strip()
            if text:
                delar.append(f"[{namn}]\n{text}")
    return "\n\n".join(delar)


# ── Statistik ────────────────────────────────────────────────────────

@dataclass
class Statistik:
    behandlade_lemman: int = 0
    behandlade_lexem: int = 0   # ≥ lemman: flera lexem kan dela lemmasträng
    skrivna_celler: int = 0
    tomma_celler: int = 0       # LLM returnerade "" — OK för defektiva
    saknade_celler: int = 0     # LLM returnerade inte cell-ID alls
    fel: list[str] = field(default_factory=list)

    def skriv_ut(self) -> None:
        print(f"Lemman behandlade : {self.behandlade_lemman}")
        print(f"Lexem skrivna     : {self.behandlade_lexem}")
        print(f"Celler skrivna    : {self.skrivna_celler}")
        print(f"Tomma (defektiva) : {self.tomma_celler}")
        print(f"Saknade (LLM-miss): {self.saknade_celler}")
        if self.fel:
            print(f"Fel ({len(self.fel)}):")
            for f in self.fel[:10]:
                print(f"  {f}")
            if len(self.fel) > 10:
                print(f"  ... och {len(self.fel) - 10} till")


# ── Hjälpfunktioner ──────────────────────────────────────────────────

def _bygg_invers_legend(legend: dict[str, dict[str, int]]) -> dict[str, dict[int, str]]:
    """Vänd legend: {axel: {namn: int}} → {axel: {int: namn}}."""
    return {
        axel: {v: k for k, v in mappning.items()}
        for axel, mappning in legend.items()
    }


def _beskriv_cell(cell: Cell, inv_legend: dict[str, dict[int, str]]) -> str:
    """Gör en mänskligt läsbar beskrivning av en cell, t.ex. 'tempus=Pres+Imp, diates=Aktiv'."""
    delar: list[str] = []
    for axel in ALLA_AXLAR:
        v = cell.axlar.get(axel)
        if v is None:
            continue
        axel_inv = inv_legend.get(axel, {})
        if axel in ("tempus", "kasus"):  # IntFlag — kan vara OR av flera
            namn_delar = [axel_inv.get(bit, str(bit))
                          for bit in sorted(axel_inv)
                          if (v & bit) == bit and bit != 0]
            delar.append(f"{axel}={'+'.join(namn_delar) or str(v)}")
        else:
            namn = axel_inv.get(v, str(v))
            delar.append(f"{axel}={namn}")
    return ", ".join(delar) if delar else "invariant"


def _bygg_prompt(
    lemman: list[str],
    slot: Slot,
    inv_legend: dict[str, dict[int, str]],
    instruktioner: str = "",
) -> str:
    """Bygg LLM-prompt för en batch av lemman."""
    # Axelnamnen ensamma räcker inte när en axel bär en konvention snarare än
    # sin bokstavliga betydelse — "kasus=Gen" på fr/es/it tonisk form fick
    # modellen att svara "de ella" och "di Lei". not-kommentaren förklarar
    # cellen och skickas därför med.
    cell_rader = "\n".join(
        f"  - {cell.id}: {_beskriv_cell(cell, inv_legend)}"
        + (f"  — {cell.not_kommentar}" if cell.not_kommentar else "")
        for cell in slot.celler
    )
    lemma_lista = ", ".join(lemman)

    # Bygg exempelstruktur för ett ord
    exempel_cell = slot.celler[0].id if slot.celler else "form"
    tomt_ex = ", ".join(f'"{c.id}": ""' for c in slot.celler[:3])

    instruktions_block = (
        f"\nSpråkspecifika instruktioner:\n{instruktioner}\n" if instruktioner else ""
    )

    return f"""Du är morfologiexpert. Böj följande {slot.ordklass.lower()}-ord på {_språknamn(slot.språk)}.
Svara ENBART med giltig JSON — ingen annan text.
{instruktions_block}

Celler att fylla i (cell-id: beskrivning):
{cell_rader}

Ord att böja: {lemma_lista}

Regler:
- Lämna tom sträng "" för former som inte existerar (t.ex. imperativ för modalverb).
- Varje ord ska ha ALLA cell-ID:n som nycklar, även om värdet är "".
- Skriv formerna precis som de används i text (med alla diakritiska tecken).
- Flerordslemman (t.ex. "laga mat", "se marier", "sich erinnern"): böj det
  första ordet som inte är reflexivmarkör (se/s'/sich); övriga ord följer
  med oförändrade i varje form ("lagar mat", inte bara "lagar").

Returnera JSON med exakt detta format:
{{
  "{lemman[0]}": {{{tomt_ex}, ...}},
  ...
}}"""


def _språknamn(kod: str) -> str:
    return {
        "sv": "svenska", "en": "engelska", "fr": "franska",
        "de": "tyska", "es": "spanska", "it": "italienska", "ja": "japanska",
    }.get(kod, kod)


def _parsa_svar(text: str, lemman: list[str], slot: Slot) -> dict[str, dict[str, str]]:
    """Parsa LLM-svar. Returnerar {lemma: {cell_id: form}}."""
    # Extrahera JSON-blocket om det är inlindat i text
    start = text.find("{")
    slut = text.rfind("}") + 1
    if start == -1 or slut == 0:
        raise ValueError(f"Inget JSON-block hittat i svaret")
    rå = json.loads(text[start:slut])

    resultat: dict[str, dict[str, str]] = {}
    cell_ids = {c.id for c in slot.celler}

    for lemma in lemman:
        # Sök efter lemmat (LLM kan ibland ändra stor/liten bokstav)
        post = rå.get(lemma) or rå.get(lemma.lower()) or rå.get(lemma.capitalize())
        if not post or not isinstance(post, dict):
            continue
        # Behåll bara kända cell-IDs
        resultat[lemma] = {k: str(v) for k, v in post.items() if k in cell_ids}

    return resultat


def _kollaps_och_skriv(
    lexem_id: int,
    former: dict[str, str],       # {cell_id: form}
    slot: Slot,
    conn: sqlite3.Connection,
    stat: Statistik,
    torkörning: bool,
) -> None:
    """Applicera bitmask-OR-kollaps och skriv Former-rader för ett lexem."""
    # Indexera celler efter id
    cell_index = {c.id: c for c in slot.celler}

    # Bygg en lista av (axlar-dict, form) för alla icke-tomma former
    rader: list[tuple[dict[str, int | None], str]] = []
    for cell_id, form in former.items():
        if cell_id not in cell_index:
            continue
        if not form:
            stat.tomma_celler += 1
            continue
        rader.append((dict(cell_index[cell_id].axlar), form))
        stat.skrivna_celler += 1

    # Bitmask-OR-kollaps: gruppen rader med identisk form och icke-IntFlag-axlar
    # — slå ihop tempus/kasus via OR
    from ..kaikki_mappning.paradigm import INTFLAG_AXLAR

    def intflag_nyckel(axlar: dict[str, int | None]) -> tuple:
        return tuple(
            (a, axlar.get(a))
            for a in ALLA_AXLAR
            if a not in INTFLAG_AXLAR
        )

    kollapsade: dict[tuple[tuple, str], dict[str, int | None]] = {}
    for axlar, form in rader:
        nyckel = (intflag_nyckel(axlar), form)
        if nyckel not in kollapsade:
            kollapsade[nyckel] = dict(axlar)
        else:
            # OR:a IntFlag-axlarna
            for fa in INTFLAG_AXLAR:
                gamla = kollapsade[nyckel].get(fa)
                nya = axlar.get(fa)
                if gamla is not None and nya is not None:
                    kollapsade[nyckel][fa] = gamla | nya
                elif nya is not None:
                    kollapsade[nyckel][fa] = nya

    if torkörning:
        for (_, form), axlar in kollapsade.items():
            print(f"    [torr] {form!r:20s} {axlar}")
        return

    # Radera befintliga Former-rader för lexemet (idempotent)
    conn.execute("DELETE FROM Former WHERE lexem_id = ?", (lexem_id,))

    # Skriv nya rader
    for (_, form), axlar in kollapsade.items():
        conn.execute(
            """INSERT INTO Former
               (lexem_id, form, tempus, kasus, numerus, species, genus, grad, person, diates)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lexem_id,
                form,
                axlar.get("tempus"),
                axlar.get("kasus"),
                axlar.get("numerus"),
                axlar.get("species"),
                axlar.get("genus"),
                axlar.get("grad"),
                axlar.get("person"),
                axlar.get("diates"),
            ),
        )


# ── Huvud-pipeline ───────────────────────────────────────────────────

def generera_former(
    lemman: list[str],
    språk: str,
    ordklass: str,
    conn: sqlite3.Connection,
    *,
    batch_storlek: int | None = None,
    modell: str = STANDARD_MODELL,
    torkörning: bool = False,
    verbose: bool = False,
    fortsätt: bool = False,
) -> Statistik:
    """Generera böjda former via Claude och skriv till Former-tabellen.

    Args:
        lemman:       Lista av lemman att generera för. Tom lista = alla
                      lexem för (språk, ordklass) i databasen.
        språk:        Språkkod (sv, en, fr, de, es, it, ja).
        ordklass:     Ordklass-sträng (Verb, Substantiv, ...).
        conn:         Öppen databasanslutning.
        batch_storlek: Antal lemman per LLM-anrop. None = räkna ut från
                      antalet celler i slot-filen (_lämplig_batch).
        modell:       Claude-modell att använda.
        torkörning:   Om True — anropa LLM men skriv inte till DB.
        verbose:      Skriv ut per-batch-progress.
        fortsätt:     Hoppa över lexem som redan har Former-rader —
                      gör avbrutna körningar återupptagbara.
    """
    stat = Statistik()
    legend = ladda_legend()
    inv_legend = _bygg_invers_legend(legend)

    # Ladda slot-fil
    try:
        slot = ladda_slot(språk, ordklass, legend=legend)
    except FileNotFoundError as e:
        stat.fel.append(str(e))
        return stat

    if batch_storlek is None:
        batch_storlek = _lämplig_batch(len(slot.celler))
        if verbose:
            print(f"  {len(slot.celler)} celler → batch-storlek {batch_storlek}")

    instruktioner = _ladda_instruktioner(språk, ordklass)

    # Hämta (lexem_id, lemma)-par att behandla.
    #
    # Ett lemma kan höra till FLERA lexem inom samma (språk, ordklass) —
    # homonymer under olika koncept (sv "fisk" = mat_fisk + djur_fisk,
    # fr "temps" = väd_väder + tid_tid) och possessiver som delar form
    # (es "su" ligger under fem koncept). Alla ska ha egna Former-rader,
    # därför nycklas allt på lexem_id och inte på lemmasträngen.
    #
    # ja-adjektiv av typ 'no' (substantiviska) och 'verbfras' böjs inte i
    # adjektivparadigmet — de hoppas över (se setup.sql / KONVENTIONER.md).
    villkor = ""
    if språk == "ja" and ordklass == "Adjektiv":
        villkor = ("  AND (l.ja_adjektiv_typ IS NULL"
                   "       OR l.ja_adjektiv_typ IN ('i', 'na'))\n")

    par: list[tuple[int, str]] = []
    if lemman:
        for lemma in lemman:
            rader = conn.execute(
                f"""SELECT l.id, l.lemma FROM Lexem l
                   JOIN Koncept k ON k.id = l.koncept_id
                   WHERE l.lemma = ? AND l.språk = ? AND k.ordklass = ?
                   {villkor}""",
                (lemma, språk, ordklass),
            ).fetchall()
            if not rader:
                stat.fel.append(f"Lexem ej funnet i DB: {lemma!r} ({språk}/{ordklass})")
            par.extend((r["id"], r["lemma"]) for r in rader)
    else:
        par = [
            (r["id"], r["lemma"])
            for r in conn.execute(
                f"""SELECT l.id, l.lemma FROM Lexem l
                   JOIN Koncept k ON k.id = l.koncept_id
                   WHERE l.språk = ? AND k.ordklass = ?
                   {villkor}ORDER BY l.lemma""",
                (språk, ordklass),
            )
        ]

    if not par:
        print(f"  Inga lexem funna för {språk}/{ordklass}.")
        return stat

    if fortsätt:
        före = len(par)
        par = [
            (lexem_id, lemma) for lexem_id, lemma in par
            if conn.execute(
                "SELECT 1 FROM Former WHERE lexem_id = ? LIMIT 1",
                (lexem_id,),
            ).fetchone() is None
        ]
        hoppade = före - len(par)
        if hoppade and verbose:
            print(f"  --fortsätt: hoppar över {hoppade} redan genererade lexem")

    # Gruppera på lemma: LLM:en behöver bara böja varje sträng en gång, även
    # när flera lexem delar den. Resultatet fördelas sedan till alla lexem.
    lexem_per_lemma: dict[str, list[int]] = {}
    for lexem_id, lemma in par:
        lexem_per_lemma.setdefault(lemma, []).append(lexem_id)
    lemman_att_bearbeta = list(lexem_per_lemma)

    if not shutil.which("claude"):
        stat.fel.append("'claude' CLI hittades inte — installera Claude Code och logga in.")
        return stat

    if os.environ.get("CLAUDECODE"):
        stat.fel.append(
            "Kör inte 'ordbok generera' inifrån Claude Code — öppna ett vanligt "
            "terminalfönster och kör kommandot därifrån."
        )
        return stat

    # Dela upp i batchar. Varje batch är en egen transaktion (with conn:
    # nedan), så Ctrl-C mellan batchar är ofarligt — bara den pågående
    # batchen tappas, och --fortsätt tar upp den vid nästa körning.
    antal_batchar = math.ceil(len(lemman_att_bearbeta) / batch_storlek)
    for i in range(antal_batchar):
        batch = lemman_att_bearbeta[i * batch_storlek:(i + 1) * batch_storlek]
        if verbose:
            print(f"  Batch {i + 1}/{antal_batchar}: {', '.join(batch)}")

        prompt = _bygg_prompt(batch, slot, inv_legend, instruktioner)

        try:
            svar_text = _anropa_llm(prompt, modell)
        except Exception as e:
            stat.fel.append(f"LLM-fel för batch {batch}: {e}")
            continue

        try:
            former_per_lemma = _parsa_svar(svar_text, batch, slot)
        except (ValueError, json.JSONDecodeError) as e:
            stat.fel.append(f"Parse-fel för batch {batch}: {e}")
            if verbose:
                print(f"  Råsvar:\n{svar_text[:500]}")
            continue

        with conn:
            for lemma in batch:
                stat.behandlade_lemman += 1
                if lemma not in former_per_lemma:
                    stat.fel.append(f"LLM returnerade inte '{lemma}'")
                    continue

                former = former_per_lemma[lemma]
                # Räkna saknade celler
                for cell in slot.celler:
                    if cell.id not in former:
                        stat.saknade_celler += 1

                # Samma former skrivs till varje lexem som delar lemmat —
                # egna rader per lexem_id, så att båda konceptbetydelserna
                # (mat_fisk och djur_fisk) går att rendera.
                for lexem_id in lexem_per_lemma[lemma]:
                    stat.behandlade_lexem += 1
                    _kollaps_och_skriv(
                        lexem_id=lexem_id,
                        former=former,
                        slot=slot,
                        conn=conn,
                        stat=stat,
                        torkörning=torkörning,
                    )

    return stat
