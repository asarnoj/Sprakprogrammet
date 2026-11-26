"""Granskning av RENDERADE MENINGAR — hitta felen renderarna gör.

PROBLEMET. Renderarna producerar meningar och några är fel. Två är kända
(franskans reflexiva verb tappar sitt pronomen, tyskans fraslexem får fel
deklination) och det finns med säkerhet fler. Regressionsnätet fångar dem
inte: det fryser vad systemet GÖR, så ett fel som redan fanns när korpusen
frystes passerar varje gång (G4). Och ingen läser 900 meningar för hand.

VARFÖR ETT FORMULÄR OCH INTE FRITEXT. "Den här ser konstig ut" går inte att
sammanställa. Ska femhundra anmärkningar bli en arbetslista måste varje
anmärkning säga VAD som är fel och VAR rättelsen hör hemma — och de två är
olika frågor. En felaktig form kan bero på att renderaren valde fel cell
(renderarfel) eller på att cellen innehåller fel sträng (datafel), och de
lagas på skilda ställen.

Därför två kolumner som gör arbetet sorterbart:

    feltyp    böjning · ordföljd · kongruens · saknat_led · överflödigt_led
              · lexikalt · semantiskt
    åtgärd    renderare · former · restriktioner · ordbok

`åtgärd` är den som gör anmärkningen till arbete. Utan den är rapporten en
lista över missnöje.

TVÅ KORPUSAR, OCH DE SVARAR PÅ OLIKA FRÅGOR.

    ur loggen   de meningar som FAKTISKT ställts (`Mening`-tabellen bär spec
                och text för var och en). Speglar verklig användning, och
                växer av sig själv medan någon övar — det är den parallella
                granskningen.
    ur svepet   den designade korpusen i `ordbok/verktyg/renderarbild.py`,
                57 namngivna konstruktioner × 7 språk. Täcker systematiskt
                och kräver ingen användning alls.

GRANSKNINGEN ÄNDRAR ALDRIG NÅGOT. Den skriver en TSV med anmärkningar. Att
tillämpa dem är ett separat beslut — samma regel som `granska-former`.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..generator.rattning import ORDMELLANRUM

#: Formuläret. Varje rad är EN anmärkning om EN mening.
RAPPORT_KOLUMNER = (
    "källa",        # logg:<mening_id>  eller  svep:<konstruktion>
    "språk",
    "text",         # vad renderaren producerade
    "spec",         # specifikationen, så fallet går att återskapa
    "dom",          # rätt | fel | meningslös
    "feltyp",       # se modulens huvud; tomt när dom = rätt
    "ord",          # ordet det gäller, tomt när felet är hela meningen
    "förslag",      # vad det borde vara
    "åtgärd",       # renderare | former | restriktioner | ordbok
    "motivering",   # en rad
)

#: Ordgräns för ordräkningen: mellanslag, eller en apostrof mellan två
#: bokstäver — elisionen i `J'existe`, som är två led skrivna ihop.
#:
#: Regeln träffar också engelskans `don't` och genitivens `John's`, som
#: delas i två. Det är medvetet överseende: kontrollen frågar bara om
#: meningen har FÄRRE än två led, så en delning för mycket kan på sin höjd
#: dölja ett enordsfall som redan är osannolikt. Att i stället lista
#: apostrofens giltiga bruk per språk vore en regeltabell för att svara på
#: en räkning.
import re as _re
_ORDGRÄNS = _re.compile(r"\s+|(?<=[^\W\d_])['\u2019](?=[^\W\d_])")

DOMAR = ("rätt", "fel", "meningslös")
FELTYPER = ("böjning", "ordföljd", "kongruens", "saknat_led",
            "överflödigt_led", "lexikalt", "semantiskt")
ÅTGÄRDER = ("renderare", "former", "restriktioner", "ordbok")

#: Granskningen ska fånga det generatorn och renderaren missade, så en klart
#: starkare modell än genereringens standard. Samma val som granska-former.
STANDARD_MODELL = "claude-opus-5"


@dataclass(frozen=True, slots=True)
class Post:
    """En mening att granska."""
    källa: str
    språk: str
    text: str
    spec: str


def _vägra_i_claude_code() -> str | None:
    """Anropen går via `claude -p` som subprocess och hänger inifrån Claude
    Code. Samma spärr som `granska_former` och `generera_former`."""
    if os.environ.get("CLAUDECODE"):
        return ("Kör inte det här kommandot inifrån Claude Code — öppna ett "
                "vanligt terminalfönster och kör det därifrån.")
    return None


# ── korpusarna ───────────────────────────────────────────────────────

def korpus_ur_loggen(kort_db: sqlite3.Connection, språk: str | None = None,
                     gräns: int | None = None) -> list[Post]:
    """Meningar som faktiskt ställts. Den parallella granskningens korpus.

    Ingen ny insamling behövs: `Mening` bär spec och text för varje mening
    som någonsin serverats. Korpusen växer alltså medan någon övar, vilket är
    precis vad "parallellt med användningen" betyder.
    """
    villkor = "WHERE språk = ?" if språk else ""
    p: tuple = (språk,) if språk else ()
    rader = kort_db.execute(
        f"""SELECT id, språk, text, spec FROM Mening {villkor}
            ORDER BY id DESC {'LIMIT ?' if gräns else ''}""",
        p + ((gräns,) if gräns else ())).fetchall()
    return [Post(f"logg:{r['id']}", r["språk"], r["text"], r["spec"])
            for r in rader]


def korpus_ur_svep(språk_db: sqlite3.Connection,
                   språk: str | None = None) -> list[Post]:
    """Den designade korpusen, renderad. Täcker utan att någon övat.

    Korpusen är namngiven per konstruktion (`renderarbild.KORPUS`), vilket är
    hela poängen: en anmärkning går att läsa som "bisats med negation är fel i
    tyskan" i stället för "kandidat 417".
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                           / "ordbok" / "verktyg"))
    from renderarbild import KORPUS, RENDERARE  # noqa: PLC0415

    from ..kort.schemalaggning import spec_json
    from ..rendering import RenderingsFel

    ut: list[Post] = []
    for kod, klass in RENDERARE.items():
        if språk and kod != språk:
            continue
        r = klass(språk_db)
        for namn, m in KORPUS:
            try:
                text = r.rendera(m)
            except RenderingsFel:
                continue          # vägran är inte ett renderarfel att granska
            except Exception as e:                        # noqa: BLE001
                text = f"KRASCH {type(e).__name__}: {e}"
            ut.append(Post(f"svep:{namn}", kod, text, spec_json(m)))
    return ut


# ── kontroller som inte behöver någon modell ─────────────────────────

#: Ord som FÅR stå två gånger i rad, per språk. Sluten och lexikal, som
#: `ELIDERAR` i franskans renderare.
#:
#: Bara franskan har fallet, och skälet är exakt: `nous` och `vous` är de enda
#: pronomen vars SUBJEKTSFORM är identisk med deras klitikum. "Nous nous
#: dépêchons" är därför korrekt franska — första `nous` är subjektet, andra är
#: reflexivpronomenet. De andra språken skiljer formerna åt (vi/oss, wir/uns,
#: noi/ci, nosotros/nos) och kan inte producera dubbleringen.
#:
#: Kontrollen rapporterade tre fynd när reflexiva verb byggdes 2026-08-26, och
#: alla tre var det här. Att lista undantaget är att göra kontrollen skarpare;
#: att ta bort kontrollen vore att förlora den.
ÄKTA_DUBBLERING = {"fr": frozenset({"nous", "vous"})}


def strukturkontroller(poster: list[Post]) -> list[dict]:
    """Fel som går att se utan att kunna språket.

    De är värda att köra först och separat: de kostar ingenting, de kan köras
    som ett regressionstest, och de fångar en klass av fel en språkgranskare
    lätt läser förbi — en läckt intern nyckel ser ut som ett ord.

    TVÅ SPECAR SOM RENDERAR LIKADANT är den starkaste av dem. Skiljer sig
    specarna men inte texten har renderaren tappat en distinktion — singular
    och plural som blir samma sträng betyder att numerus inte realiseras. Det
    är precis den sortens fel som inte syns när man läser en mening i taget.
    """
    ut: list[dict] = []

    def anmärk(p: Post, feltyp: str, ord_: str, motiv: str,
               åtgärd: str = "renderare") -> None:
        ut.append({"källa": p.källa, "språk": p.språk, "text": p.text,
                   "spec": p.spec, "dom": "fel", "feltyp": feltyp,
                   "ord": ord_, "förslag": "", "åtgärd": åtgärd,
                   "motivering": motiv})

    per_text: dict[tuple[str, str], list[Post]] = {}
    for p in poster:
        if p.text.startswith("KRASCH"):
            anmärk(p, "saknat_led", "", p.text)
            continue
        # ELISIONEN ÄR ETT ORDMELLANRUM. `J'existe.` är två led, inte ett:
        # franskan och italienskan skriver ihop pronomen och verb med apostrof.
        # Räknat på mellanslag blev varje sådan mening ett "saknat led", och
        # det var tretton av tretton fynd — alltså en kontroll som bara
        # rapporterade sin egen tokenisering.
        ord_ = _ORDGRÄNS.split(p.text)
        ord_ = [o for o in ord_ if o]
        # JAPANSKAN SKRIVS UTAN MELLANSLAG, så ordräkning säger ingenting där.
        # Samma gräns som rättningen redan drar (`ORDMELLANRUM`), och av samma
        # skäl — se D7.
        if p.språk in ORDMELLANRUM and len(ord_) < 2:
            anmärk(p, "saknat_led", "", f"bara {len(ord_)} ord i utfallet")
        elif p.språk not in ORDMELLANRUM and len(p.text.strip()) < 3:
            anmärk(p, "saknat_led", "", f"bara {len(p.text.strip())} tecken")
        for a, b in zip(ord_, ord_[1:]):
            if (a.lower() == b.lower() and a.isalpha()
                    and a.lower() not in ÄKTA_DUBBLERING.get(p.språk, ())):
                anmärk(p, "överflödigt_led", a, f"{a!r} står två gånger i rad")
                break
        for o in ord_:
            if "_" in o:
                anmärk(p, "lexikalt", o,
                       "ser ut som en intern nyckel, inte ett ord", "ordbok")
        per_text.setdefault((p.språk, p.text), []).append(p)

    for (_språk, _text), grupp in per_text.items():
        specar = {p.spec for p in grupp}
        if len(specar) < 2:
            continue
        namn = ", ".join(sorted(p.källa for p in grupp)[:4])
        # TVÅ SORTERS SAMMANFALL, och de lagas på olika ställen. Skiljer sig
        # specarna BARA i vilka koncept de nämner är det två koncept som delar
        # lemma — `gen_spela` och `arb_leka` blir båda `play` — och det är en
        # ordboksfråga (D5 från andra hållet). Skiljer sig något GRAMMATISKT
        # har renderaren tappat en distinktion, och det är dess fel.
        if _utan_koncept(grupp) == 1:
            anmärk(grupp[0], "lexikalt", "",
                   f"olika koncept renderar identiskt ({namn}) — de delar "
                   f"lemma, så uppgiften går inte att skilja åt", "ordbok")
        else:
            anmärk(grupp[0], "kongruens", "",
                   f"{len(specar)} olika specar renderar identiskt ({namn}) — "
                   f"en grammatisk distinktion realiseras inte")
    return ut


def _utan_koncept(grupp: list[Post]) -> int:
    """Hur många OLIKA specar gruppen har när konceptnamnen maskas bort.

    Ett betyder att skillnaden bara satt i vilka ord som valdes; fler betyder
    att något grammatiskt skiljer dem åt.
    """
    def maska(nod):
        if isinstance(nod, dict):
            return {k: ("*" if k in ("koncept", "verb") else maska(v))
                    for k, v in nod.items()}
        if isinstance(nod, list):
            return [maska(x) for x in nod]
        return nod

    former = set()
    for p in grupp:
        try:
            former.add(json.dumps(maska(json.loads(p.spec)), sort_keys=True))
        except (ValueError, TypeError):
            former.add(p.spec)
    return len(former)


# ── prompten ─────────────────────────────────────────────────────────

SPRÅKNAMN = {"sv": "svenska", "en": "engelska", "de": "tyska",
             "fr": "franska", "es": "spanska", "it": "italienska",
             "ja": "japanska"}


def bygg_prompt(poster: list[Post], språk: str) -> str:
    """Granskningsprompten för en batch.

    SPECEN FÖLJER MED, och det är avgörande. Utan den kan granskaren bara
    säga att en mening låter konstig; med den kan hen säga att renderaren
    realiserade fel numerus — alltså skilja ett fel från ett medvetet val.
    """
    rader = "\n".join(
        f"{i + 1}. {p.text}\n   spec: {p.spec}" for i, p in enumerate(poster))
    return f"""Du granskar maskinellt genererade meningar på \
{SPRÅKNAMN.get(språk, språk)}.

Varje mening är renderad ur en SPECIFIKATION som säger vad meningen ska
uttrycka. Din uppgift är att avgöra om renderingen är korrekt — inte om
meningen är vacker eller vanlig.

Bedöm varje mening som:
  rätt        korrekt språk OCH uttrycker specifikationen
  fel         grammatiskt felaktigt, eller uttrycker inte specifikationen
  meningslös  grammatiskt korrekt men semantiskt orimligt ("maten sätter sig")

För varje mening som INTE är rätt, ange:
  feltyp   {" | ".join(FELTYPER)}
  ord      ordet det gäller, eller tom sträng om felet är hela meningen
  förslag  vad det borde vara
  åtgärd   var rättelsen hör hemma:
             renderare      renderaren valde fel form, ordning eller led
             former         formen finns men strängen i tabellen är fel
             restriktioner  meningen borde aldrig ha byggts (semantik)
             ordbok         fel ord för konceptet
  motivering  en rad, konkret

Svara med enbart JSON, en lista med ett objekt per mening, i ordning:
[{{"nr": 1, "dom": "rätt"}},
 {{"nr": 2, "dom": "fel", "feltyp": "saknat_led", "ord": "lave",
   "förslag": "se lave", "åtgärd": "renderare",
   "motivering": "reflexivt verb utan sitt pronomen"}}]

MENINGARNA:
{rader}
"""


def parsa_svar(text: str, poster: list[Post]) -> list[dict]:
    """LLM-svar → rapportrader. Okända värden avvisas hellre än gissas."""
    start, slut = text.find("["), text.rfind("]")
    if start < 0 or slut < 0:
        raise ValueError("inget JSON-svar")
    ut = []
    for post in json.loads(text[start:slut + 1]):
        nr = int(post.get("nr", 0)) - 1
        if not 0 <= nr < len(poster):
            continue
        p = poster[nr]
        dom = post.get("dom", "")
        if dom not in DOMAR:
            continue
        if dom == "rätt":
            continue                       # rapporten bär bara anmärkningar
        feltyp = post.get("feltyp", "")
        åtgärd = post.get("åtgärd", "")
        ut.append({
            "källa": p.källa, "språk": p.språk, "text": p.text, "spec": p.spec,
            "dom": dom,
            "feltyp": feltyp if feltyp in FELTYPER else "",
            "ord": post.get("ord", ""),
            "förslag": post.get("förslag", ""),
            "åtgärd": åtgärd if åtgärd in ÅTGÄRDER else "",
            "motivering": post.get("motivering", "")})
    return ut


# ── sammanställningen ────────────────────────────────────────────────

def sammanställ(rapport: Path) -> str:
    """Rapporten som en ARBETSLISTA, inte som en lista över missnöje.

    Grupperingen är (språk, åtgärd, feltyp) därför att det är den enda
    indelning som svarar mot ett arbetspass: "tyska renderaren, saknat_led,
    14 fall" är något man kan sätta sig med. En lista sorterad på allvar är
    det inte.
    """
    if not rapport.exists():
        return "ingen rapport ännu"
    rader = [r.split("\t") for r in
             rapport.read_text(encoding="utf-8").splitlines()[1:] if r]
    if not rader:
        return "rapporten är tom — inga anmärkningar"
    i = {k: n for n, k in enumerate(RAPPORT_KOLUMNER)}
    räkning = Counter((r[i["språk"]], r[i["åtgärd"]] or "?",
                       r[i["feltyp"]] or "?") for r in rader)
    ut = [f"{len(rader)} anmärkningar över "
          f"{len({r[i['källa']] for r in rader})} meningar\n"]
    for (språk, åtgärd, feltyp), n in räkning.most_common():
        ut.append(f"  {n:4d}  {språk}  {åtgärd:14s} {feltyp}")
    return "\n".join(ut)
