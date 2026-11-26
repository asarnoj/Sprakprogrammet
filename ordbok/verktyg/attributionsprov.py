"""Prov för rättningens attribution: VILKET kort fick skulden?

VARFÖR DET HÄR PROVET FINNS. Rättningen är den enda delen av systemet som kan
skriva FALSKA rader i inlärarloggen. Skyller den på fel kort får det kortet en
repetition det inte förtjänade, och det som faktiskt brast får ingen — och
inget larmar, för båda raderna ser riktiga ut.

FELET SOM FAKTISKT HÄNDE. `existerer` för `existez` bokfördes som att
användaren inte kunde ordet `exister`. Ordkortet fick Again, och eftersom ett
fallerat ordkort SKYDDAR sina form- och stamkort (A4) blev böjningsfelet
varken bedömt eller registrerat. Användaren hade skrivit stammen `exist-` och
missat ändelsen — alltså visat ordkunskapen och brustit i böjningen — och fick
motsatt besked.

A4:s regel är riktig: kan man inte hämta fram ordet ALLS prövades böjningen
aldrig. Villkoret i koden var något annat — "är det här exakt en känd cellform"
— och varje felböjning är per definition ingen känd cellform. Skyddet gällde
alltså precis de fall det inte var till för.

VAD PROVET INTE ÄR. Det prövar inte om ATTRIBUTIONEN ÄR RÄTT i någon djupare
mening; det prövar att ett antal fall med känd skada landar på rätt korttyp.
Fallen är valda för att spänna över de tre utfallen: ändelsen, ordet, och den
korta stammen som lockar till fel svar.

VILAR PÅ LEXIKONET, INTE PÅ HISTORIKEN. `_skyll` läser `typ`, `koncept` och
`facit`, som är statiska; inlärartillståndet rör den bara i sista grenen, som
inget fall här träffar. Provet åldras därför inte med Julius övande.

Kör:  python ordbok/verktyg/attributionsprov.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut                       # noqa: E402
from sprakprog.kort.befolka import befolka             # noqa: E402
from sprakprog.kort.db import anslut_kort              # noqa: E402
from sprakprog.generator.rattning import (               # noqa: E402
    KASUSTOKEN, Rättare,
)

#: (språk, skrev, väntat, koncept, cell, väntad korttyp, varför)
FALL = [
    ("fr", "existerer", "existez", "verb_finnas", "pres_2pl", "system",
     "stammen finns i försöket — ändelsen brast, inte ordet"),
    ("fr", "existons", "existez", "verb_finnas", "pres_2pl", "system",
     "en äkta annan cell: rätt stam, fel ändelse"),
    ("fr", "mange", "existez", "verb_finnas", "pres_2pl", "ord",
     "ingen del av ordet — då är det ordet som brast"),
    ("fr", "apprend", "as", "verb_ha", "pres_2sg", "ord",
     "kort stam `a`: `apprend` är apprendre, och `appr-` förklarar mer"),
    ("fr", "attend", "as", "verb_ha", "pres_2sg", "ord",
     "samma fälla, annat ord — `attend-` slår `a-`"),
    ("fr", "avons", "avez", "verb_ha", "pres_2pl", "system",
     "rätt stam `av`, fel ändelse"),
    ("fr", "coûtez", "coûte", "eko_v_kosta", "pres_3sg", "system",
     "rätt stam, fel person"),

    # ── rektion: rätt form, fel kasus (A7 punkt 3) ────────────────────
    #
    # `den Mann` för `dem Mann` är ingen påhittad form — den är korrekt för
    # ackusativ. Vad som avgör kasusen är VERBET, och `helfen` styr dativ.
    # Utan rektionssteget skylldes det på artikelns FORMKORT, alltså på det
    # kort som möts i nästan varje mening, medan rektionen för just `helfen`
    # gick fri.
    ("de", "den", "dem", "artikel_bestamd", "m_dat", "rektion",
     "helfen styr dativ — kasusen brast, inte artikelformen",
     [("arb_hjälpa", "objekt", "kasus")]),
    ("de", "den", "dem", "artikel_bestamd", "m_dat", "form",
     "utan ett styrande verb finns ingen rektion att skylla på — då är det "
     "artikelparadigmet som brast",
     []),
    ("de", "den", "dem", "artikel_bestamd", "m_dat", "form",
     "TVÅ verb styr dativ i samma mening: vilket användaren tänkte på går "
     "inte att veta, och då säger vi ingenting (D1)",
     [("arb_hjälpa", "objekt", "kasus"), ("soc_tacka", "objekt", "kasus")]),
    ("de", "dem", "den", "artikel_bestamd", "m_akk", "rektion",
     "åt andra hållet: fragen styr ackusativ, användaren skrev dativ",
     [("kom_fråga", "io", "kasus")]),

    # ── genus: rätt artikelparadigm, fel genus på substantivet ────────
    #
    # `un mère` för `une mère` är ingen påhittad form — `un` är korrekt för
    # maskulinum. Vad som avgör är SUBSTANTIVETS genus, och det är ett eget
    # kort. Regeln fanns men kunde aldrig gripa: renderaren läser samma
    # substantivs genus FLERA gånger per mening (artikeln, adjektivet), så
    # `egenskaper` bär dubbletter, och `len(träffande) == 1` såg två uppslag
    # av samma ord som två kandidater och teg.
    #
    # Priset stod i Julius kortlek: `form:une` hade fallerat fyra gånger av
    # sex och stod på D = 9,85 — men alla fyra felen var `un` framför ett
    # feminint substantiv. Ett kort bar straffet för fyra andra korts
    # kunskap, och INGET genuskort hade ett enda fall.
    ("fr", "un", "une", "artikel_obestamd", "f_sg", "egenskap",
     "genuset styr artikelformen — och DUBBLETTEN i uppslaget får inte "
     "räknas som två kandidater",
     [], [("fam_mamma", "genus"), ("fam_mamma", "genus")]),
    ("fr", "un", "une", "artikel_obestamd", "f_sg", "form",
     "TVÅ olika substantiv kan förklara felet: vilket användaren tänkte på "
     "går inte att veta, och då säger vi ingenting (D1)",
     [], [("fam_mamma", "genus"), ("fam_storasyster", "genus")]),
]


def kör(r_per_språk) -> list[str]:
    fel = []
    for fall in FALL:
        språk, skrev, väntat, koncept, cell, vill, varför = fall[:7]
        rektioner = fall[7] if len(fall) > 7 else []
        egenskaper = fall[8] if len(fall) > 8 else []
        r = r_per_språk(språk)
        # `_skyll` lämnar sedan 2026-08-26 också slutsatsen som NYCKEL, för
        # att gränssnittet ska kunna sätta text på den själv i stället för
        # att visa svensk prosa i en engelsk rättning. Provet läser
        # fortfarande `förklaring` — den svenska texten är kvar just för att
        # provutskrifter ska gå att läsa.
        kid, förklaring, _osäker, _nyckel, _arg = r._skyll(
            skrev, väntat, koncept, None, cell, egenskaper=egenskaper,
            rektioner=rektioner)
        rad = (r.kort_db.execute("SELECT typ FROM Kort WHERE id = ?",
                                 (kid,)).fetchone() if kid else None)
        typ = rad["typ"] if rad else "—"
        if typ != vill:
            fel.append(f"{skrev!r} för {väntat!r}: skyllde på {typ}, "
                       f"väntat {vill} ({varför}) — {förklaring}")
    return fel


def prov_inget_falskt_godkännande(r_per_språk) -> list[str]:
    """ETT FEL SVAR FÅR ALDRIG GE GOOD ÅT ETT KORT SOM INTE PRÖVADES.

    Det här är modulens hårdaste regel och den enda vars brott är osynligt:
    ett kort med falsk historik ser ut precis som ett med äkta, och FSRS
    skjuter det längre bort just när användaren visat att det inte sitter.

    TVÅ FALL MED KÄND SKADA, båda funna i drift:

        `nous coüter` för `Vous coûtez.`   ordkortet föll som det skulle —
                                           och ÄNDELSEN `ez` fick Good, i
                                           ett svar som var en infinitiv
                                           utan `ez` i sig.

        `Je apprends` för `J'apprends.`    sandhi slog ihop `je` + `apprends`
                                           till en token, så inget uppslag
                                           matchade det felskrivna ordet.
                                           Sju kort av sju fick Good.

    Provet arbetar på RÄTTNINGEN och inte på `_skyll`, eftersom felet inte
    satt i attributionen utan i vad som hände med de ÖVRIGA korten efteråt.
    """
    from sprakprog.generator import Förslag, Generator
    from sprakprog.db import anslut
    fel = []
    # SANDHIFALLET HÖR INTE HIT. Där visades varje kort och Good är rätt —
    # se `prov_sandhi_spåras`, som prövar just den skillnaden.
    for språk, sök, svar in (("fr", "coûtez", "nous coüter"),):
        r = r_per_språk(språk)
        g = Generator(anslut(), r.kort_db, språk, källspråk="sv", nivå=1,
                      cefr="A1", frö=3)
        g._läs_kort()
        for _ in range(4000):
            m = g.samplare.kandidat()
            if m is None or g.validator.validera(m):
                continue
            res = g._rendera(m)
            if res is None or sök not in res[0]:
                continue
            text, kl, upp, eg, rk, of, osm = res
            mitt_svar = svar or text.replace("'", "e ").rstrip(".")
            rätt = g.rätta(Förslag(m, text, None, kl, None, upp, eg, rk, of, False, osm),
                           mitt_svar)
            if rätt.korrekt:
                continue
            # ORDFÖLJDSKORT UNDANTAS, och det är ingen uppmjukning.
            # Ordföljd handlar om POSITIONER och inte om att orden är rätta:
            # `nous coüter` har subjekt före verb, hur fel båda orden än är.
            # Det är samma ortogonalitet som gör omkastningsdetektionen
            # riktig åt andra hållet — ett FLYTTAT ord fäller inget ordkort
            # (A7). Att kräva att ordföljden faller med orden vore att
            # dubbelräkna samma fel.
            # ORDFÖLJDSKORT UNDANTAS, och det är ingen uppmjukning.
            # Ordföljd handlar om POSITIONER och inte om att orden är rätta:
            # `nous coüter` har subjekt före verb, hur fel båda orden än är.
            # Det är samma ortogonalitet som gör omkastningsdetektionen
            # riktig åt andra hållet — ett FLYTTAT ord fäller inget ordkort
            # (A7). Att kräva att ordföljden faller med orden vore att
            # dubbelräkna samma fel.
            godkända = [k for k, v in rätt.utfall.items() if v
                        and r.kort_db.execute(
                            "SELECT typ FROM Kort WHERE id = ?",
                            (k,)).fetchone()["typ"] != "ordföljd"]
            if godkända:
                namn = [r.kort_db.execute(
                    "SELECT typ, facit FROM Kort WHERE id = ?", (k,)).fetchone()
                    for k in godkända]
                fel.append(
                    f"{text!r} besvarat {mitt_svar!r} gav GOOD åt "
                    + ", ".join(f"{x['typ']}:{x['facit']!r}" for x in namn[:4]))
            break
    return fel


def prov_sandhi_spåras(r_per_språk) -> list[str]:
    """En SAMMANSMÄLT token ska gå att spåra till sina uppslag.

    Uppslaget är per FORM men diffen per TOKEN, och sandhi slår ihop två
    former till en: `je` + `apprends` blir `j'apprends`. Ingen form i
    uppslaget matchar då den strängen — varken som lika eller som delsträng,
    för elisionen tar bort en bokstav — och kopplingen token→kort brast.

    Följden var värre än en missad koppling: eftersom INGET kort gick att
    knyta till felet hölls hela meningen utanför betygsättningen. Mätt: 19 av
    60 franska felsvar gav noll mätning, och före det gav samma fall GOOD åt
    alla sju korten.

    RÄTT SVAR ÄR ATT INGENTING HÅLLS INNE. Provet krävde först motsatsen,
    och det var fel: skriver användaren `Je apprends` har hen visat pronomenet,
    stammen, ändelsen och ordföljden — alla korten prövades och klarades. Det
    enda som brast är elisionen, och den har inget kort. D3 säger då: säg vad
    som var fel, mät ingenting på det, och straffa inte det som visades.

    Provet kräver alltså tre saker: att svaret räknas som FEL, att korten
    ändå bedöms, och att anmärkningen NAMNGER sammansmältningen i stället för
    att skylla på ett ord.

    Ett äkta stavfel i samma mening (`je xpprends`) ska däremot fortfarande
    hålla inne korten bakom den sammansmälta token — det är den andra halvan
    och den som `_sammansmälta` finns för.
    """
    from sprakprog.db import anslut
    from sprakprog.generator import Förslag, Generator
    fel = []
    for språk in ("fr",):
        r = r_per_språk(språk)
        g = Generator(anslut(), r.kort_db, språk, källspråk="sv", nivå=1,
                      cefr="A1", frö=3)
        g._läs_kort()
        for _ in range(4000):
            m = g.samplare.kandidat()
            if m is None or g.validator.validera(m):
                continue
            res = g._rendera(m)
            if res is None or "'" not in res[0]:
                continue
            text, kl, upp, eg, rk, of, osm = res
            f = Förslag(m, text, None, kl, None, upp, eg, rk, of, False, osm)
            # HALVA ETT: bara elisionen missad.
            svar = text.replace("'", "e ").rstrip(".")
            rätt = g.rätta(f, svar)
            if rätt.korrekt:
                fel.append(f"{text!r} besvarat {svar!r} räknades som RÄTT — "
                           f"elisionen är obligatorisk")
            if len(rätt.utfall) != len(kl):
                fel.append(f"{text!r} besvarat {svar!r}: "
                           f"{len(kl) - len(rätt.utfall)} kort hölls inne fast "
                           f"alla former visades")
            if any(a.kort_id for a in rätt.anmärkningar):
                fel.append(f"{text!r} besvarat {svar!r}: ett kort fick skulden "
                           f"för en elision som inte har något kort")
            # HALVA TVÅ: ett äkta stavfel inne i den sammansmälta token.
            trasigt = "je x" + text.split("'", 1)[1].rstrip(".")[1:]
            r2 = g.rätta(f, trasigt)
            if len(r2.utfall) == len(kl):
                fel.append(f"{text!r} besvarat {trasigt!r}: inget kort hölls "
                           f"inne — sammansmältningen spårades inte")
            if not r2.utfall:
                fel.append(f"{text!r} besvarat {trasigt!r}: HELA meningen "
                           f"hölls inne")
            break
    return fel


def _sabotage_utan_stamprov():
    """Före rättelsen: bara exakt cellform räknades som "ordet fanns"."""
    orig = Rättare._bär_stammen
    Rättare._bär_stammen = lambda själv, skrev, koncept: False
    return lambda: setattr(Rättare, "_bär_stammen", orig)


def _sabotage_naken_prefix():
    """Naken prefixregel i stället för längsta matchande stam.

    Den vägen prövades och mättes: 21 % av de franska formerna är prefixade
    av NÅGON främmande stam, mot 3 % när den längsta får förklara. `aime` mot
    `a` är fallet i listan ovan.
    """
    orig = Rättare._bär_stammen

    def naken(själv, skrev, koncept):
        return any(skrev.startswith(st)
                   for st, k in själv._stamindex().items() if koncept in k)

    Rättare._bär_stammen = naken
    return lambda: setattr(Rättare, "_bär_stammen", orig)


def _sabotage_genus_räknar_uppslag():
    """Före rättelsen: kandidaterna räknades per UPPSLAG, inte per koncept.

    Renderaren läser samma substantivs genus flera gånger per mening, så
    varje entydigt fall såg tvetydigt ut och regeln teg.
    """
    from sprakprog.generator.rattning import Rättare
    äkta = Rättare._genusgivaren

    def per_uppslag(själv, cell, träffar, egenskaper):
        träffande = []
        for koncept, namn in egenskaper:          # utan dict.fromkeys
            if namn != "genus":
                continue
            rad = själv._genuskort(koncept)
            if rad is None or rad["facit"] is None:
                continue
            try:
                genus = int(rad["facit"])
            except (TypeError, ValueError):
                continue
            if själv._genusbytet(cell, träffar, genus):
                träffande.append(koncept)
        return träffande[0] if len(träffande) == 1 else None

    Rättare._genusgivaren = per_uppslag
    return lambda: setattr(Rättare, "_genusgivaren", äkta)


def _sabotage_utan_rektion():
    """Före A7 punkt 3: rektionen fanns inte i skuldstegen.

    Då föll ett kasusfel igenom till artikelns formkort — och rektionskorten
    var dessutom onåbara (A3), så det kort som faktiskt brast kunde varken
    fällas eller mötas.
    """
    orig = Rättare._rektionsgivaren
    Rättare._rektionsgivaren = lambda själv, cell, träffar, rektioner: None
    return lambda: setattr(Rättare, "_rektionsgivaren", orig)


def _sabotage_rektion_utan_entydighet():
    """Ta första träffen i stället för att kräva exakt en.

    Det är samma fel som pinne 7 i D1: att gissa när datan inte räcker. Med
    två dativstyrande verb i meningen skulle det peka ut ett av dem på måfå.
    """
    orig = Rättare._rektionsgivaren

    def första(själv, cell, träffar, rektioner):
        tokens = KASUSTOKEN.get(själv.språk, {})
        for koncept, slot, namn in rektioner:
            if namn != "kasus":
                continue
            rad = själv._rektionskort(koncept, slot)
            if rad is None or rad["facit"] is None:
                continue
            if själv._koordinatbytet(cell, träffar, tokens, int(rad["facit"])):
                return (koncept, slot)
        return None

    Rättare._rektionsgivaren = första
    return lambda: setattr(Rättare, "_rektionsgivaren", orig)


SABOTAGE = [("genusgivaren räknar uppslag i stället för koncept",
             _sabotage_genus_räknar_uppslag),
            ("utan stamprovet — allt blir 'fel ord'", _sabotage_utan_stamprov),
            ("naken prefixregel — kort stam kapar ordet", _sabotage_naken_prefix),
            ("utan rektionssteget — kasusfel blir formfel", _sabotage_utan_rektion),
            ("rektion utan entydighetskrav — gissar bland flera",
             _sabotage_rektion_utan_entydighet)]


def _kör_extra(r_per_språk) -> list[str]:
    return prov_inget_falskt_godkännande(r_per_språk)


#: Nivån provets kortbestånd byggs på. FALLEN KRÄVER KORT SOM BARA FINNS
#: HÖGRE UPP — tyskans dativformer `dem`/`den` hör till en nivå långt över
#: grundsatsen — och beståndet ärvdes tidigare ur `kort.db` som den råkade se
#: ut. Julius nollställde sv→de till nivå 1 den 2026-09-04, och då fanns
#: korten inte: provet rapporterade "inget kort hör till ordet" för två fall.
#:
#: Det är fjärde gången ett prov visar sig bero på vilket tillstånd databasen
#: råkar ha, och svaret är detsamma varje gång: låt provet ställa upp sin egen
#: förutsättning. `befolka` är additiv och rör aldrig ett befintligt kort, så
#: den lägger bara till det som saknas.
NIVÅ_PROVAS = 24
CEFR_PROVAS = "C2"


def _eget_bestånd(katalog: Path) -> sqlite3.Connection:
    """Kopia av kortleken, påfylld till `NIVÅ_PROVAS` för fallens språk."""
    mål = katalog / "attribution.db"
    käll = sqlite3.connect(ROT / "kort.db")
    dst = sqlite3.connect(mål)
    try:
        käll.backup(dst)
    finally:
        dst.close()
        käll.close()
    kort = anslut_kort(mål)
    with anslut() as sp:
        sp.row_factory = sqlite3.Row
        # `mät=False`: exponeringen kostar sekunder och styr ingenting här.
        befolka(kort, sp, {"de", "fr", "sv"},
                nivå=NIVÅ_PROVAS, cefr=CEFR_PROVAS, mät=False)
    return kort


def main() -> int:
    katalog = tempfile.TemporaryDirectory()
    kort = _eget_bestånd(Path(katalog.name))
    språk_db = anslut()
    rättare: dict[str, Rättare] = {}

    def r_per_språk(språk):
        if språk not in rättare:
            rättare[språk] = Rättare(språk_db, kort, språk)
        return rättare[språk]

    fel = kör(r_per_språk)
    print(f"{len(FALL)} fall med känd skada")
    print(f"  {'✗' if fel else '✓'} rätt korttyp får skulden")
    for f in fel:
        print(f"      {f}")

    # RÄTTNINGENS HÅRDASTE REGEL, prövad för sig. Den handlar inte om VILKET
    # kort som får skulden utan om vad som händer med de övriga.
    with tempfile.TemporaryDirectory() as tmp:
        # SAMMA BESTÅND SOM OVAN, inte `kort.db` igen: annars prövar den
        # här halvan en annan kortlek än den förra.
        kopia = Path(tmp) / "a.db"
        käll = kort
        dst = sqlite3.connect(kopia)
        try:
            käll.backup(dst)
        finally:
            dst.close()
        prov_db = sqlite3.connect(kopia)
        prov_db.row_factory = sqlite3.Row
        prov_db.execute(
            "UPDATE Kort SET sedd = '2026-01-01T00:00:00+00:00' WHERE språk = 'fr'")
        prov_db.commit()
        egna: dict[str, Rättare] = {}

        def r2(språk):
            if språk not in egna:
                egna[språk] = Rättare(språk_db, prov_db, språk)
            return egna[språk]

        falska = prov_inget_falskt_godkännande(r2)
        sandhi = prov_sandhi_spåras(r2)
        prov_db.close()
    fel += falska + sandhi
    print(f"  {'✗' if falska else '✓'} inget falskt godkännande på ett fel svar")
    for f in falska:
        print(f"      {f}")
    print(f"  {'✗' if sandhi else '✓'} sammansmälta token spåras till sina uppslag")
    for f in sandhi:
        print(f"      {f}")

    print("\nfalsifiering — varje gammal regel ska fälla provet:")
    stumma = 0
    for namn, sab in SABOTAGE:
        ångra = sab()
        try:
            rättare.clear()
            brister = kör(r_per_språk)
        finally:
            ångra()
            rättare.clear()
        if not brister:
            stumma += 1
        print(f"  {'✓ föll' if brister else '✗ STUMT'}  {namn}"
              + (f"  ({len(brister)} fall)" if brister else ""))
    if stumma:
        print(f"\n{stumma} sabotage fällde inte provet.")
    return 1 if (fel or stumma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
