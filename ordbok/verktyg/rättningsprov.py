"""Prov för rättningens positioner: bär rätt kort rätt ord?

VARFÖR DET HÄR PROVET FINNS. Rättningen räknar i SKRIVNA ORD — den delar
facit på blanksteg — men spåret räknar UPPSLAG, och det är inte samma sak.
Ett uppslag är ett ord för spåret och kan vara flera på pappret: "how many",
"hur många", "inte längre", "den här". Läses det ena indexet som det andra
glider allt efter det första flerordiga uppslaget ett steg.

FELET SOM FAKTISKT HÄNDE. Med facit "How many books does the girl read?" gav

    "How many book does the girl read?"     fel numerus på substantivet
        → substantivet godkändes, och do, kongruens och inversion
          underkändes: sex kort som inte hade gjort något

    "How many books does the girl reads?"   fel form på verbet
        → INGET kort underkändes alls. Svaret var fel och rättningen
          hittade ingenting.

Det slog mot `interr_det_hur_många` och `interr_det_hur_mycket`, som båda är
prövbara nivåkort och alltså kommer att läras ut.

VARFÖR DET ÄR VÄRT ETT EGET NÄT. Rättningen är den enda delen som kan skriva
FALSKA rader i inlärarloggen, och en falsk rad larmar inte — den ser riktig
ut. Samma skäl som `attributionsprov` finns av, en våning ner: det provet
frågar vilken KORTTYP som fick skulden, det här frågar vilket ORD kortet står
på.

VAD PROVET GÖR. Bygger meningar med flerordiga uppslag, ändrar ETT ord i
svaret, och kräver att kortet som bär just det ordet faller — och att kort
som inte rör ordet inte faller. Fallen är valda så att det ändrade ordet
ligger EFTER det flerordiga uppslaget, för det är där glidningen syns.

Kör:  python ordbok/verktyg/rättningsprov.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kortmodell import Formtabell                      # noqa: E402
from sprakprog.rattning import Rättningsfel, rätta               # noqa: E402
from sprakprog.rendering import spåra                            # noqa: E402
from sprakprog.rendering import spec as S                        # noqa: E402
from sprakprog.rendering.en import EngelskRenderare              # noqa: E402
from sprakprog.rendering.sv import SvenskRenderare               # noqa: E402

RENDERARE = {"en": EngelskRenderare, "sv": SvenskRenderare}

#: En fråga med "how many" / "hur många": ett uppslag, två skrivna ord, och
#: fyra ord efter sig att glida på.
HUR_MÅNGA = S.Mening(
    verb="kom_läsa",
    subjekt=S.Nominalfras("pers_flicka", S.Bestämdhet.BESTÄMD),
    objekt=S.Nominalfras("skol_bok", numerus=S.Numerus.PL,
                         frågedeterminant="interr_det_hur_många"),
    fråga_om="objekt")

#: Svenskan smälter inte ihop frågedeterminanten — "hur många" saknar sin
#: pluralcell — men den har flerordiga VERB: "litar på" är ett uppslag och
#: två ord, med objektet efter sig att glida på.
LITAR_PÅ = S.Mening(
    verb="gen_lita",
    subjekt=S.Nominalfras("pers_flicka", S.Bestämdhet.BESTÄMD),
    objekt=S.Nominalfras("pers_pojke", S.Bestämdhet.BESTÄMD))

#: (språk, mening, svar, kort som MÅSTE falla, kort som INTE får falla)
FALL = [
    ("en", HUR_MÅNGA, "How many book does the girl read?",
     ["ändelse:Substantiv/regelbunden/pl"],
     ["regel:val/kongruens/3sg", "ord:artikel_bestamd", "ord:pers_flicka"]),
    # «reads» är en FORM av läsa, så lexemet kan användaren (3.3). Skulden
    # ligger på cellvalet — prerekvisitstegen i 7.3.
    #
    # VILKET cellval ändrades 2026-11-26. Satsen krävde förut att
    # `tempusform/presens` föll, eftersom kortet stod på det ändrade ordet. Men
    # presens VAR rätt — användaren skrev presens. Det som brast är att
    # huvudverbet böjdes trots do-omskrivning, och det är do-omskrivningens
    # innehåll. Det syns på att dess andra utfall `utan_do` skriver just
    # «reads»: «how many books reads the girl». Punkt 3 i 7.3 avgör vilket av
    # två cellbeslut som bär felet; se `rattning._förklarar`.
    ("en", HUR_MÅNGA, "How many books does the girl reads?",
     ["regel:val/do_omskrivning/med_do"],
     ["regel:val/tempusform/presens",
      "ord:kom_läsa", "ord:skol_bok", "ord:artikel_bestamd", "ord:pers_flicka"]),
    # RENT ORDFEL. «write» är ingen form av `read`, så varken tempusvalet eller
    # do-omskrivningen prövades — inget av deras utfall skriver «write» — och
    # de hålls. Mätt 2026-11-26: förut föll tre kort och bara ett hade gjort
    # fel. Skulden landar ändå, på ordkortet.
    ("en", HUR_MÅNGA, "How many books does the girl write?",
     ["ord:kom_läsa"],
     ["regel:val/tempusform/presens", "regel:val/do_omskrivning/med_do",
      "regel:val/kongruens/3sg", "ord:skol_bok", "ord:pers_flicka"]),
    ("en", HUR_MÅNGA, "How many books does the boy read?",
     ["ord:pers_flicka"],
     ["ord:skol_bok", "ord:kom_läsa", "regel:val/kongruens/3sg"]),
    ("en", HUR_MÅNGA, "How many books does a girl read?",
     ["ord:artikel_bestamd", "regel:val/bestämning/bestämd_artikel"],
     ["ord:pers_flicka", "ord:kom_läsa", "ord:skol_bok"]),
    ("en", HUR_MÅNGA, None, [], []),          # facit mot sig självt
    # «pojke» är obestämd singular av samma lexem: bestämdheten brast, inte
    # ordet (7.3 steg 1).
    ("sv", LITAR_PÅ, "Flickan litar på pojke.",
     ["regel:val/bestämning/bestämd_suffix"],
     ["ord:pers_pojke", "ord:pers_flicka", "ord:gen_lita"]),
    ("sv", LITAR_PÅ, "Flickan litar på flickan.",
     ["ord:pers_pojke"],
     ["ord:gen_lita"]),
    ("sv", LITAR_PÅ, None, [], []),
]


def _fall(språk: str, mening, svar, måste_falla, får_inte_falla) -> list[str]:
    renderare = RENDERARE[språk](sqlite3.connect(ROT / "sprak.db"))
    ut = spåra(renderare, mening)
    tabell = Formtabell(renderare.u)
    brister: list[str] = []

    if svar is None:                      # bara: facit rättar sig mot sig självt
        svar, måste_falla = ut.text, []
    res = rätta(tabell, ut, svar)
    fallna = {str(k) for k, b in res.betyg.items() if b != "good"}

    for kort in måste_falla:
        if kort not in fallna:
            brister.append(f"{kort} bar ordet som ändrades men gick fri")
    for kort in får_inte_falla:
        if kort in fallna:
            brister.append(f"{kort} föll fast dess ord stod kvar")
    if svar == ut.text and fallna:
        brister.append(f"perfekt svar underkände {sorted(fallna)}")
    # SKULDEN MÅSTE LANDA. Prerekvisitstegen (7.3) ograderar formkort när ett
    # beslut bär felet i stället — men ibland finns inget beslut: «How many
    # books» blir plural av frågedeterminantens krav, inte av något `val`-kort.
    # Ograderades ändelsen ändå föll ingenting, och ett fel svar blev perfekt.
    if svar != ut.text and not fallna:
        brister.append(f"ingenting föll på «{svar}» — rättningen tiger")
    return brister


def _spannet_räknar_rätt() -> list[str]:
    """Varje uppslags ordantal måste summera till meningens."""
    brister = []
    for språk in RENDERARE:
        renderare = RENDERARE[språk](sqlite3.connect(ROT / "sprak.db"))
        ut = spåra(renderare, HUR_MÅNGA if språk == "en" else LITAR_PÅ)
        skrivna = sum(len(str(o).split()) for o in ut.ord)
        if skrivna != len(ut.text.split()):
            brister.append(f"{språk}: {skrivna} uppslagsord mot "
                           f"{len(ut.text.split())} i {ut.text!r}")
        if not any(len(str(o).split()) > 1 for o in ut.ord):
            brister.append(f"{språk}: provet träffar inget flerordigt uppslag "
                           f"i {ut.text!r} — fallet har tappat sin poäng")
    return brister


def _vägrar_vid_uppslagsfel() -> list[str]:
    """Ett trasigt uppslag ska VÄGRAS, inte bli «annat ord».

    Förut låg uppslaget i `_läget` i ett `try` som fångade allt och svarade
    ANNAT_ORD. Då blev ett databasfel utsagan «användaren kan inte ordet», och
    ordkortet fick ett underkänt för ett programfel. Går den här kontrollen
    stumt har någon satt tillbaka det breda `except`.
    """
    import sqlite3 as _s

    renderare = RENDERARE["en"](sqlite3.connect(ROT / "sprak.db"))
    ut = spåra(renderare, HUR_MÅNGA)
    tabell = Formtabell(renderare.u)
    # Värm tabellen, så att `meningens_kort` klarar sig på cachen och det bara
    # är `_läget` som når det trasiga uppslaget.
    rätta(tabell, ut, ut.text)

    def trasig(lexem):
        raise _s.OperationalError("databasen svarar inte (provets påhitt)")

    riktig, renderare.u._celler = renderare.u._celler, trasig
    try:
        rätta(tabell, ut, "How many books does the girl write?")
    except Rättningsfel:
        return []
    except Exception as e:                       # noqa: BLE001
        return [f"uppslagsfelet kom ut som {type(e).__name__}, inte Rättningsfel"]
    else:
        return ["ett trasigt uppslag gav ett betyg i stället för att vägras"]
    finally:
        renderare.u._celler = riktig


def _falsifiera() -> list[str]:
    """Varje gammalt läge ska fälla sitt prov.

    Ett prov som inte går att fälla är ingen invariant utan en förhoppning —
    samma uppställning som `passprovet` och `övervakningsprov`.
    """
    import sprakprog.rattning as R

    def utan_villkor(betyg, formkort, korten):
        """Det läge jag byggde först: ogradera formkorten oavsett om någon
        annan bär felet. Då tiger rättningen på «How many book …»."""
        for formens in formkort.values():
            for kort in formens:
                betyg.pop(kort, None)

    def utan_punkt3(betyg, avvikelser, beslut_för, korten):
        """Läget som gällde till 2026-11-26: cellbesluten faller med sin
        position, och ingen frågar om något annat utfall förklarar avvikelsen.
        Då skriver ett rent ordfel falska «again» på grammatiken."""
        return

    fall = [("stegen ograderade formkortet utan att någon annan bar felet",
             "_stegen", utan_villkor),
            ("cellbesluten föll med sin position, utan punkt 3",
             "_punkt3", utan_punkt3)]
    brister = []
    print("\nfalsifiering — varje gammalt läge ska fälla sitt prov:")
    for namn, attr, ersättning in fall:
        gammalt = getattr(R, attr)
        setattr(R, attr, ersättning)
        try:
            fel = [b for f in FALL for b in _fall(*f)]
        finally:
            setattr(R, attr, gammalt)
        if fel:
            print(f"  ✓ föll  {namn}  ({len(fel)} fynd)")
        else:
            print(f"  ✗ STUMT  {namn}")
            brister.append(f"{namn} gav inga fynd — provet vaktar inte regeln")
    return brister


def main() -> int:
    brister: list[str] = []
    print("── uppslag mot skrivna ord ──")
    for b in (fel := _spannet_räknar_rätt()):
        print(f"  ✗ {b}")
    brister += fel
    if not fel:
        print("  ✓ spannen summerar till meningens ordantal")

    print("\n── vilket kort bär vilket ord ──")
    for språk, mening, svar, måste, får_inte in FALL:
        try:
            fel = _fall(språk, mening, svar, måste, får_inte)
        except Rättningsfel as e:
            fel = [f"rättningen vägrade: {e}"]
        etikett = svar if svar else "facit mot sig självt"
        print(f"  {'✓' if not fel else '✗'} {språk}  {etikett}")
        for b in fel:
            print(f"      {b}")
        brister += fel

    print("\n── vägrar hellre än gissar ──")
    for b in (fel := _vägrar_vid_uppslagsfel()):
        print(f"  ✗ {b}")
    brister += fel
    if not fel:
        print("  ✓ ett trasigt uppslag vägras i stället för att bli «annat ord»")

    brister += _falsifiera()
    # spannen + varje fall + vägransprovet; falsifieringen räknas inte, den
    # vaktar proven i stället för programmet.
    antal = len(FALL) + 2
    print(f"\n{antal} kontroller, {len(brister)} brister."
          if brister else f"\n{antal} kontroller, allt håller.")
    return 1 if brister else 0


if __name__ == "__main__":
    raise SystemExit(main())
