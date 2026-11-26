"""Granskning av genererade former — en starkare modell läser igenom Former.

Bakgrund: genereringen körs med en liten snabb modell (claude-haiku-4-5) för
att 65 000 former ska vara möjliga att producera. Smoke-testet 2026-08-01
visade ~1 % avvikelser, koncentrerade till oregelbunden morfologi (tyskt
Abend → "Äbende", spanskt abrir 2pl → "abríais").

Att i stället generera allt med en stark modell är dyrt: utdata är 65 000
formsträngar. Granskning vänder på ekonomin — formerna går IN i prompten och
bara avvikelserna kommer ut, ungefär 30 gånger mindre utdata. Därför är det
billigare att generera billigt och granska dyrt än att generera dyrt.

Granskningen ÄNDRAR ingenting. Den skriver en TSV-rapport med förslag.
Att tillämpa dem är ett separat, mänskligt beslut (KONVENTIONER.md §9).
"""

from __future__ import annotations

import csv
import json
import os
import math
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from ..kaikki_mappning.paradigm import (
    ALLA_AXLAR, INTFLAG_AXLAR, Cell, Slot, ladda_legend, ladda_slot,
)
from .pipeline import (
    _anropa_llm, _beskriv_cell, _bygg_invers_legend, _ladda_instruktioner,
    _lämplig_batch, _språknamn,
)

def _vägra_i_claude_code() -> str | None:
    """Samma spärr som generera_former har.

    Anropen går via `claude -p` som subprocess. Körs det inifrån Claude Code
    hänger subprocessen i stället för att svara.
    """
    if os.environ.get("CLAUDECODE"):
        return ("Kör inte det här kommandot inifrån Claude Code — öppna ett "
                "vanligt terminalfönster och kör det därifrån.")
    return None


# Poängen med granskningen är att fånga det generatorn missade — därför en
# klart starkare modell än genereringens standard. --modell för att sänka.
STANDARD_GRANSKNINGSMODELL = "claude-opus-5"

# När prenumerationens kvot tar slut misslyckas VARJE följande anrop. Utan
# en spärr fortsätter körningen genom alla återstående batchar och gör
# hundratals meningslösa anrop, vilket dränker loggen och döljer var det
# faktiskt stannade. Nattkörningen 2026-08-10 slutade så.
MAX_FEL_I_RAD = 5

RAPPORT_KOLUMNER = (
    "språk", "ordklass", "koncept", "lemma", "cell",
    "nuvarande", "förslag", "allvar", "motivering",
)


@dataclass(frozen=True, slots=True)
class Avvikelse:
    språk: str
    ordklass: str
    koncept: str
    lemma: str
    cell: str
    nuvarande: str
    förslag: str
    allvar: str        # "fel" | "osäker"
    motivering: str


@dataclass
class Granskningsstatistik:
    avbruten: bool = False      # spärren slog till — sluta, kör om senare
    granskade_lexem: int = 0
    granskade_former: int = 0
    avvikelser_fel: int = 0
    avvikelser_osäkra: int = 0
    fel: list[str] = field(default_factory=list)

    def skriv_ut(self) -> None:
        print(f"Lexem granskade  : {self.granskade_lexem}")
        print(f"Former granskade : {self.granskade_former}")
        print(f"Avvikelser (fel) : {self.avvikelser_fel}")
        print(f"Avvikelser (osäk): {self.avvikelser_osäkra}")
        if self.fel:
            print(f"Körningsfel ({len(self.fel)}):")
            for f in self.fel[:10]:
                print(f"  {f}")
            if len(self.fel) > 10:
                print(f"  ... och {len(self.fel) - 10} till")


def _matchar(rad_värde: int | None, cell_värde: int | None, axel: str) -> bool:
    """Täcker en Former-rad den här cellen på den här axeln?

    IntEnum-axlar måste vara exakt lika. IntFlag-axlar kan ha kollapsats
    (SCHEMA.md §5) — raden täcker cellen om alla cellens bitar är satta.
    """
    if cell_värde is None:
        return rad_värde is None
    if rad_värde is None:
        return False
    if axel in INTFLAG_AXLAR:
        return rad_värde & cell_värde == cell_värde
    return rad_värde == cell_värde


def _former_per_cell(rader: list[sqlite3.Row], slot: Slot) -> dict[str, str]:
    """Mappa Former-rader tillbaka till cell-ID:n.

    Former lagrar axelvärden, inte cell-ID. En kollapsad rad täcker flera
    celler. Celler utan träff får "" — de saknas i databasen.
    """
    ut: dict[str, str] = {}
    for cell in slot.celler:
        # Flera rader kan matcha: en kollapsad rad har fler bitar satta än
        # cellen kräver, och en rad för en ANNAN cell kan därför också vara
        # en supermängd. es subj_imperf_1sg (Vol|Imperf = 5120) matchar
        # subj_1sg (Vol = 1024) på det viset, och gav 595 falska träffar i
        # granskningen 2026-08-10. Välj därför den närmaste matchningen:
        # exakt träff först, annars den med minst överskjutande bitar.
        kandidater = [
            r for r in rader
            if all(_matchar(r[a], cell.axlar.get(a), a) for a in ALLA_AXLAR)
        ]
        if not kandidater:
            ut[cell.id] = ""
            continue

        # Avståndet räcker inte. it subj_2pl (Vol) har två kandidater två
        # bitar bort: "assaggiate" (Pres|Imp|Vol = 1042, rätt svar) och
        # "assaggiaste" (Pret|Vol|Imperf = 5124, congiuntivo imperfetto).
        #
        # Det som skiljer dem är att 5124 innehåller en ANNAN, mer specifik
        # cells hela avtryck: subj_imperf_2pl är Vol|Imperf = 5120, och
        # 5124 ⊇ 5120. Raden tillhör alltså den cellen, inte den här.
        # 1042 innehåller ingen sådan mer specifik cell.
        mer_specifika = [
            tuple(c.axlar.get(a) for a in ALLA_AXLAR)
            for c in slot.celler
            if c.id != cell.id
            and all(
                # samma IntEnum-axlar …
                c.axlar.get(a) == cell.axlar.get(a) for a in ALLA_AXLAR
                if a not in INTFLAG_AXLAR
            )
            and all(
                # … men strikt fler IntFlag-bitar
                (c.axlar.get(a) or 0) & (cell.axlar.get(a) or 0) == (cell.axlar.get(a) or 0)
                for a in INTFLAG_AXLAR
            )
            and any(
                (c.axlar.get(a) or 0) != (cell.axlar.get(a) or 0) for a in INTFLAG_AXLAR
            )
        ]

        def tillhör_annan(r: sqlite3.Row) -> bool:
            return any(
                all((r[a] or 0) & (v or 0) == (v or 0)
                    for a, v in zip(ALLA_AXLAR, spec) if a in INTFLAG_AXLAR)
                for spec in mer_specifika
            )

        def poäng(r: sqlite3.Row) -> tuple[int, int]:
            avstånd = sum(
                bin((r[a] or 0) ^ (cell.axlar.get(a) or 0)).count("1")
                for a in INTFLAG_AXLAR
            )
            return (int(tillhör_annan(r)), avstånd)

        ut[cell.id] = min(kandidater, key=poäng)["form"]
    return ut


# ── Strukturgranskning — samma rapport, ingen modell ──────────────────
#
# Vissa fel går att se utan att kunna språket, bara genom att jämföra två
# fält som måste stämma överens. De behöver varken LLM, kvot eller ett
# fönster utanför Claude Code, och de kan därför köras vid varje ändring.

# Modalverben lagrar sitt lemma i PRESENS — kan, bör, vill, får, brukar,
# måste, ska. Infinitiven finns bara i inf-cellen, och lemmajämförelsen
# nedan säger därför ingenting om dem. De känns igen på konceptnyckeln,
# som redan är load-bearing i renderaren (`form_för("modal_ska", "pres")`).
MODALPREFIX = "modal_"


def granska_inf_mot_lemma(conn: sqlite3.Connection) -> list[Avvikelse]:
    """Svenska verbs inf-cell måste vara lemmat.

    Bakgrund: nio verb hade sin IMPERATIV i inf-cellen (tänk, försök, gråt,
    tyck, äg, rör, lyft, lär sig, gift sig). Futurum renderas ur inf-cellen
    och gav "han ska försök att erbjuda". Felet var osynligt i formen på
    raden — inf och imp hade kollapsat till EN rad med tempus=17 (SCHEMA.md
    §5), vilket är rätt för alla -ar-verb, där imperativen ÄR infinitiven.
    Först jämförelsen mot lemmat skiljer den riktiga kollapsen från den
    felaktiga.

    Kontrollen gäller sv/Verb. Att lemmat är infinitiven stämmer även i
    en/de/fr/es/it, men där avviker 21 reflexiva verb (fr "se marier" mot
    inf-cellens "marier", de "sich erinnern" mot "erinnern") därför att
    reflexivmarkören inte lagras i cellen som i svenskan. Det är ett eget
    fel med en egen fråga — var markören hör hemma — och tas inte in här
    förrän den frågan är avgjord.
    """
    slot = ladda_slot("sv", "Verb")
    rader = conn.execute(
        f"""SELECT l.id AS lexem_id, l.lemma, k.nyckel AS koncept, f.form,
                   {', '.join('f.' + a for a in ALLA_AXLAR)}
            FROM Former f
            JOIN Lexem l   ON l.id = f.lexem_id
            JOIN Koncept k ON k.id = l.koncept_id
            WHERE l.språk = 'sv' AND k.ordklass = 'Verb'
            ORDER BY l.lemma, l.id"""
    ).fetchall()

    per_lexem: dict[int, list[sqlite3.Row]] = {}
    for r in rader:
        per_lexem.setdefault(r["lexem_id"], []).append(r)

    avvikelser: list[Avvikelse] = []
    for rader_för_lexem in per_lexem.values():
        första = rader_för_lexem[0]
        if första["koncept"].startswith(MODALPREFIX):
            continue
        # Tom inf-cell är inte det här felet. Deponensverben (hoppas,
        # minnas, andas …) har inga aktiva celler alls — bara passiva.
        inf = _former_per_cell(rader_för_lexem, slot).get("inf")
        if not inf or inf == första["lemma"]:
            continue
        avvikelser.append(Avvikelse(
            språk="sv", ordklass="Verb", koncept=första["koncept"],
            lemma=första["lemma"], cell="inf", nuvarande=inf,
            förslag=första["lemma"], allvar="fel",
            motivering="inf-cellen ska vara lemmat; svenska verb lemmatiseras "
                       "på infinitiven",
        ))
    return avvikelser


def _bygg_granskningsprompt(
    poster: list[tuple[str, dict[str, str]]],
    slot: Slot,
    inv_legend: dict[str, dict[int, str]],
    instruktioner: str,
) -> str:
    cell_rader = "\n".join(
        f"  - {cell.id}: {_beskriv_cell(cell, inv_legend)}"
        + (f"  — {cell.not_kommentar}" if cell.not_kommentar else "")
        for cell in slot.celler
    )
    former_block = "\n\n".join(
        f"{lemma}:\n" + "\n".join(f'    {cid} = "{form}"' for cid, form in former.items())
        for lemma, former in poster
    )
    instruktions_block = (
        f"\nSpråkspecifika konventioner:\n{instruktioner}\n" if instruktioner else ""
    )

    return f"""Du är morfologiexpert på {_språknamn(slot.språk)}. Nedan står böjda \
{slot.ordklass.lower()}-former som en mindre modell har genererat. Din uppgift är att \
hitta FEL — inte att förbättra stil.
Svara ENBART med giltig JSON — ingen annan text.
{instruktions_block}

Cellerna och vad de ska innehålla:
{cell_rader}

Former att granska:
{former_block}

Vad som ska flaggas:
- Faktiska fel: fel böjningsform, fel stam, felstavning, fel diakritiska
  tecken, eller en form som hör hemma i en annan cell än den står i.
- En tom sträng "" som borde ha en form (ordet böjs faktiskt i den cellen).
- Att två celler har fått samma sträng trots att språket skiljer dem åt.

Vad som ALDRIG ska flaggas:
- Att en form är formell, ovanlig, stel, litterär eller "inte vad en
  modersmålstalare skulle säga". Systemet täcker grammatik, inte register.
- En tom sträng där formen genuint inte existerar (defektiva paradigm,
  analytisk komparation, verb utan passiv).
- Att två celler har samma sträng när språket faktiskt sammanfaller där.

Är du osäker på om något är fel: sätt "allvar": "osäker" i stället för att gissa.

Returnera exakt detta format, med tom lista om allt är korrekt:
{{"avvikelser": [
  {{"lemma": "...", "cell": "cell_id", "förslag": "rätt form", "allvar": "fel", "motivering": "kort skäl"}}
]}}"""


def _parsa_granskningssvar(
    text: str,
    poster: dict[str, dict[str, str]],
    koncept_per_lemma: dict[str, str],
    slot: Slot,
) -> list[Avvikelse]:
    start, slut = text.find("{"), text.rfind("}") + 1
    if start == -1 or slut == 0:
        raise ValueError("Inget JSON-block hittat i svaret")
    rå = json.loads(text[start:slut])

    giltiga_celler = {c.id for c in slot.celler}
    ut: list[Avvikelse] = []
    for a in rå.get("avvikelser", []):
        lemma, cell = a.get("lemma"), a.get("cell")
        if lemma not in poster or cell not in giltiga_celler:
            continue        # modellen hittade på ett lemma eller ett cell-ID
        allvar = a.get("allvar", "osäker")
        ut.append(Avvikelse(
            språk=slot.språk,
            ordklass=slot.ordklass,
            koncept=koncept_per_lemma.get(lemma, ""),
            lemma=lemma,
            cell=cell,
            nuvarande=poster[lemma].get(cell, ""),
            förslag=str(a.get("förslag", "")),
            allvar=allvar if allvar in ("fel", "osäker") else "osäker",
            motivering=str(a.get("motivering", "")).replace("\t", " "),
        ))
    return ut


def granska_former(
    språk: str,
    ordklass: str,
    conn: sqlite3.Connection,
    rapport: Path,
    *,
    lemman: list[str] | None = None,
    batch_storlek: int | None = None,
    modell: str = STANDARD_GRANSKNINGSMODELL,
    fortsätt: bool = False,
    verbose: bool = False,
) -> Granskningsstatistik:
    """Granska Former för (språk, ordklass) och skriv avvikelser till rapport."""
    stat = Granskningsstatistik()
    if (v := _vägra_i_claude_code()):
        stat.fel.append(v); stat.avbruten = True; return stat
    legend = ladda_legend()
    inv_legend = _bygg_invers_legend(legend)

    try:
        slot = ladda_slot(språk, ordklass, legend=legend)
    except FileNotFoundError as e:
        stat.fel.append(str(e))
        return stat

    # Samma uträkning som genereringen: en granskningsprompt med 720 tyska
    # adjektivformer (5 lexem × 144 celler) är för mycket att kontrollera
    # noggrant. Adaptiv batch ger dessutom färre anrop totalt, eftersom de
    # lätta jobben höjs till 10.
    if batch_storlek is None:
        batch_storlek = _lämplig_batch(len(slot.celler))

    instruktioner = _ladda_instruktioner(språk, ordklass)

    villkor = "AND l.lemma IN ({})".format(",".join("?" * len(lemman))) if lemman else ""
    rader = conn.execute(
        f"""SELECT l.id AS lexem_id, l.lemma, k.nyckel AS koncept, f.form,
                   {', '.join('f.' + a for a in ALLA_AXLAR)}
            FROM Former f
            JOIN Lexem l   ON l.id = f.lexem_id
            JOIN Koncept k ON k.id = l.koncept_id
            WHERE l.språk = ? AND k.ordklass = ? {villkor}
            ORDER BY l.lemma, l.id""",
        (språk, ordklass, *(lemman or [])),
    ).fetchall()

    if not rader:
        print(f"  Inga Former att granska för {språk}/{ordklass}.")
        return stat

    per_lexem: dict[int, list[sqlite3.Row]] = {}
    for r in rader:
        per_lexem.setdefault(r["lexem_id"], []).append(r)

    # Redan granskade lexem hoppas över.
    #
    # Rapporten duger INTE som facit för vad som är gjort — den innehåller
    # bara avvikelser. Ett lexem som granskades utan anmärkning saknas där
    # och skulle granskas om vid varje --fortsätt. I nattkörningen
    # 2026-08-10 gällde det 233 av 259 tyska substantiv, alltså ~90 % av
    # arbetet. Därför en separat kvittofil med ett lexem per rad.
    klarfil = rapport.with_suffix(rapport.suffix + ".klara")
    redan: set[tuple[str, str]] = set()
    if fortsätt and klarfil.exists():
        for rad in klarfil.read_text(encoding="utf-8").splitlines():
            språk_, _, lemma_ = rad.partition("\t")
            if lemma_:
                redan.add((språk_, lemma_))

    poster: list[tuple[str, dict[str, str]]] = []
    koncept_per_lemma: dict[str, str] = {}
    for rader_för_lexem in per_lexem.values():
        lemma = rader_för_lexem[0]["lemma"]
        if fortsätt and (språk, lemma) in redan:
            continue
        poster.append((lemma, _former_per_cell(rader_för_lexem, slot)))
        koncept_per_lemma[lemma] = rader_för_lexem[0]["koncept"]

    if not poster:
        if verbose:
            print(f"  --fortsätt: allt redan granskat för {språk}/{ordklass}")
        return stat

    ny_fil = not rapport.exists()
    with rapport.open("a", encoding="utf-8", newline="") as fh, \
            klarfil.open("a", encoding="utf-8") as kf:
        skrivare = csv.writer(fh, delimiter="\t", lineterminator="\n")
        if ny_fil:
            skrivare.writerow(RAPPORT_KOLUMNER)

        fel_i_rad = 0
        antal_batchar = math.ceil(len(poster) / batch_storlek)
        for i in range(antal_batchar):
            batch = poster[i * batch_storlek:(i + 1) * batch_storlek]
            if verbose:
                print(f"  Batch {i + 1}/{antal_batchar}: "
                      f"{', '.join(l for l, _ in batch)}")

            prompt = _bygg_granskningsprompt(batch, slot, inv_legend, instruktioner)
            try:
                svar = _anropa_llm(prompt, modell)
                fel_i_rad = 0
            except Exception as e:
                fel_i_rad += 1
                stat.fel.append(f"LLM-fel för batch {[l for l, _ in batch]}: {e}")
                if fel_i_rad >= MAX_FEL_I_RAD:
                    stat.fel.append(
                        f"{MAX_FEL_I_RAD} fel i rad — avbryter. Trolig orsak: "
                        f"kvoten är slut. Kör om med --fortsätt när den återställts."
                    )
                    stat.avbruten = True
                    return stat
                continue

            batch_dict = dict(batch)
            try:
                avvikelser = _parsa_granskningssvar(
                    svar, batch_dict, koncept_per_lemma, slot
                )
            except (ValueError, json.JSONDecodeError) as e:
                stat.fel.append(f"Parse-fel för batch {[l for l, _ in batch]}: {e}")
                continue

            stat.granskade_lexem += len(batch)
            stat.granskade_former += sum(
                1 for _, f in batch for v in f.values() if v
            )
            for a in avvikelser:
                if a.allvar == "fel":
                    stat.avvikelser_fel += 1
                else:
                    stat.avvikelser_osäkra += 1
                skrivare.writerow([getattr(a, k) for k in RAPPORT_KOLUMNER])

            # Kvittera batchen som granskad, oavsett om något hittades.
            for lemma, _ in batch:
                kf.write(f"{slot.språk}\t{lemma}\n")
            fh.flush(); kf.flush()   # läsbart även om körningen avbryts

    return stat
