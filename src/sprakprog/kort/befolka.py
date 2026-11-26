"""Härled kortbeståndet ur språkdatabasen och stamanalysen.

Vilka kort som ska finnas avgörs av GENERATOR.md, "Hur fint ska ett formkort
skäras?": en form får eget kort först när den inte går att härleda ur det
användaren redan har kort för. Den här modulen omsätter det till rader.

Källorna är tre, och ingen av dem är id:n:

    sprak.db            koncept, lexem, mönster — via NATURLIGA nycklar
    ordbok/stammar.tsv  stammar och rester, ur ordbok/verktyg/stammar.py
    ordbok/ändelser.tsv klassernas ändelsetabeller, samma verktyg

Befolkningen är idempotent och ADDITIV: kort som redan finns rörs inte, så
att repetitionshistoriken överlever att beståndet räknas om. Kort som inte
längre har täckning i språkdatabasen tas inte bort automatiskt — det vore
att kasta historik på en ombyggnad — utan rapporteras.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

PROJEKTROT = Path(__file__).resolve().parents[3]
STAMFIL = PROJEKTROT / "ordbok" / "stammar.tsv"
ÄNDELSEFIL = PROJEKTROT / "ordbok" / "ändelser.tsv"

#: Ordföljdsregler som renderarna faktiskt implementerar, en rad per kort.
#: Listan hör hemma i kod och inte i data, av skälet i GENERATOR.md: reglerna
#: ÄR koden, och en kortlista i databasen skulle kunna glida isär från den.
#: Franskans adjektivplacering står medvetet INTE här — den är `prenominal`
#: på lexemet, alltså en lexikal egenskap och inte en regel att lära sig.
ORDFÖLJD = {
    "sv": [("svo", "subjekt före verb före objekt"),
           ("adverbial_sist", "adverbial sist i satsen"),
           ("v2_fråga", "finita verbet först i ja/nej-fråga"),
           ("biff", "satsadverbial före finita verbet i bisats")],
    "en": [("svo", "subjekt före verb före objekt"),
           ("do_omskrivning", "do i fråga och negation utan hjälpverb"),
           ("dativväxling", "indirekt objekt före direkt, utan preposition")],
    "de": [("v2", "finita verbet på plats två i huvudsats"),
           ("v1_fråga", "finita verbet först i ja/nej-fråga och imperativ"),
           ("satsklammer", "infinita verbdelar sist i satsen"),
           ("verb_sist", "finita verbet sist i bisats"),
           ("dativ_före_ackusativ", "dativobjekt före ackusativobjekt"),
           ("nachfeld", "bisatser utanför satsklammern")],
    "fr": [("svo", "subjekt före verb före objekt"),
           ("klitika_före", "objektspronomen före verbet"),
           ("est_ce_que", "frågeinledning i stället för inversion")],
    "es": [("svo", "subjekt före verb före objekt"),
           ("klitika_före", "objektspronomen före verbet"),
           ("klitikadubblering", "indirekt objekt dubbleras med klitikum"),
           ("inversion_wh", "subjekt efter verbet i wh-fråga")],
    "it": [("svo", "subjekt före verb före objekt"),
           ("klitika_före", "objektspronomen före verbet"),
           ("inversion_wh", "subjekt efter verbet i wh-fråga")],
    "ja": [("sov", "verbet sist"),
           ("postpositioner", "partikeln efter frasen, inte före"),
           ("bisats_före", "bisatsen före huvudverbet"),
           ("frågeord_kvar", "frågeordet står kvar på ledets plats")],
}

#: Lexikala egenskaper som syns på ANDRA ord än det de tillhör, och därför
#: inte fångas av vare sig stam eller ändelse. GENERATOR.md korttyp 5.
EGENSKAPER = {
    "genus": "Substantiv",
    "hjälpverb": "Verb",
    "prenominal": "Adjektiv",
    "ja_adjektiv_typ": "Adjektiv",
}


def _nyckel(*delar) -> str:
    """Naturlig nyckel som läsbar sträng. Aldrig id:n — se kort.sql."""
    return ":".join("" if d is None else str(d) for d in delar)


def _lägg_till(kort: list, typ, språk, facit, *, koncept=None, variant=None,
               ordklass=None, klass=None, cell=None, stamgrupp=None,
               egenskap=None, räckvidd=1) -> None:
    nyckel = _nyckel(typ, språk, koncept, variant, ordklass, klass, cell,
                     stamgrupp, egenskap)
    kort.append((nyckel, typ, språk, koncept, variant, ordklass, klass, cell,
                 stamgrupp, egenskap, facit, räckvidd))


def _stamrader(språk: set[str]):
    if not STAMFIL.exists():
        raise FileNotFoundError(
            f"{STAMFIL} saknas — kör ordbok/verktyg/stammar.py --skriv först")
    with STAMFIL.open(encoding="utf-8") as f:
        for rad in csv.DictReader(f, delimiter="\t"):
            if rad["språk"] in språk:
                yield rad


def _ändelserader(språk: set[str]):
    with ÄNDELSEFIL.open(encoding="utf-8") as f:
        for rad in csv.DictReader(f, delimiter="\t"):
            if rad["språk"] in språk:
                yield rad


def härled(språk_db: sqlite3.Connection, språk: set[str],
           nåbart: dict[str, set[tuple]] | None = None) -> list[tuple]:
    """Alla kort som ska finnas, som rader redo att sättas in.

    `nåbart` är språk → {(koncept, variant, cell)} som går att möta på
    kursens nivå. Utelämnad betyder hela beståndet.

    Filtret måste ligga HÄR och inte efteråt, därför att varje korttyp har
    sin egen koppling till celler: en stam täcker många, en rest exakt en,
    ett systemkort hör till en klass och inte till ett ord. Att filtrera på
    raderna efteråt skulle kräva den kopplingen en gång till.
    """
    kort: list[tuple] = []

    def nås(s_: str, koncept: str, variant: str | None, celler) -> bool:
        if nåbart is None:
            return True
        mängd = nåbart.get(s_, set())
        return any((koncept, variant, c) in mängd for c in celler)

    # Egenskaps- och rektionskort hänger på ORDET och inte på en cell, men
    # de ska ändå följa med det: att veta att Buch är neutrum är meningslöst
    # innan Buch finns i kursen.
    nådda_ord: dict[str, set] = {}
    if nåbart is not None:
        for s_, mängd in nåbart.items():
            nådda_ord[s_] = {k for k, _, _ in mängd}

    def ordet_finns(s_: str, koncept: str) -> bool:
        return nåbart is None or koncept in nådda_ord.get(s_, set())

    # ── ordkort: att ordet finns och betyder något ────────────────────
    for r in språk_db.execute(
            """SELECT k.nyckel, k.ordklass, l.språk, l.lemma, l.variant
               FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id
               WHERE EXISTS (SELECT 1 FROM Former f WHERE f.lexem_id = l.id)"""):
        if r["språk"] in språk and (
                nåbart is None
                or any(k == r["nyckel"] and v == r["variant"]
                       for k, v, _ in nåbart.get(r["språk"], ()))):
            _lägg_till(kort, "ord", r["språk"], r["lemma"],
                       koncept=r["nyckel"], variant=r["variant"],
                       ordklass=r["ordklass"])

    # ── stam- och formkort ur stamanalysen ────────────────────────────
    # stamgrupp >= 0 är en stam; -1 är en rest, alltså en form som inte gick
    # att härleda och därför får ett eget formkort. Att skillnaden är EN
    # kolumn i samma fil är hela poängen med analysen.
    for rad in _stamrader(språk):
        grupp = int(rad["stamgrupp"])
        celler = rad["celler"].split(",")
        if not nås(rad["språk"], rad["koncept"], rad["variant"] or None, celler):
            continue
        if grupp >= 0:
            _lägg_till(kort, "stam", rad["språk"], rad["form"],
                       koncept=rad["koncept"], variant=rad["variant"] or None,
                       ordklass=rad["ordklass"], klass=rad["klass"],
                       stamgrupp=grupp, räckvidd=len(celler))
        else:
            # Resten identifieras på CELLEN och inte på formsträngen. Två
            # celler kan ha samma sträng, och gjorde det: 788 kort kollapsade
            # i nyckeln första gången befolkningen kördes.
            _lägg_till(kort, "form", rad["språk"], rad["form"],
                       koncept=rad["koncept"], variant=rad["variant"] or None,
                       ordklass=rad["ordklass"], klass=rad["klass"],
                       cell=celler[0], räckvidd=1)

    # ── golvet: ordklasser utan stamanalys får ett kort per cell ──────
    # Artiklar, pronomen och andra små slutna klasser har för få medlemmar
    # för att en ändelsetabell ska vara en REGEL — `das`/`dem`/`ein` delar
    # inget system att utnyttja. Då gäller GENERATOR.md:s golv: varje form
    # är sitt eget kort. Det är inte en reservlösning utan modellens
    # nedre gräns, och den syns här därför att den faktiskt inträffar.
    analyserade = {(rad["språk"], rad["ordklass"]) for rad in _stamrader(språk)}
    from ..rendering import RenderingsFel, Uppslag
    for s_ in sorted(språk):
        u = Uppslag(språk_db, s_)
        for r in språk_db.execute(
                """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
                   JOIN Koncept k ON k.id = l.koncept_id WHERE l.språk = ?""", (s_,)):
            if (s_, r["ordklass"]) in analyserade:
                continue
            # Smal fångst: ett lexem utan läsbart paradigm hoppas över, men
            # ett programfel ska synas. Mätt kastar `_celler` aldrig över hela
            # lexikonet, så grenen är en spärr och ingen normalväg.
            try:
                celler = {c: f for c, f in u._celler(r).items() if f}
            except (RenderingsFel, KeyError):
                continue
            for cell, form in celler.items():
                if not nås(s_, r["nyckel"], r["variant"], [cell]):
                    continue
                _lägg_till(kort, "form", s_, form, koncept=r["nyckel"],
                           variant=r["variant"], ordklass=r["ordklass"],
                           cell=cell, räckvidd=1)

    # ── systemkort: ändelsetabellernas celler ─────────────────────────
    # Räckvidden är antalet ord i klassen — kortet delas av dem alla, och
    # det är den siffran som avgör om det ska schemaläggas eller bara mätas.
    klasstorlek: dict[tuple, int] = {}
    for rad in _stamrader(språk):
        if int(rad["stamgrupp"]) == 0:
            nyckel = (rad["språk"], rad["ordklass"], rad["klass"])
            klasstorlek[nyckel] = klasstorlek.get(nyckel, 0) + 1
    nådda_celler: dict[str, set] = {}
    if nåbart is not None:
        for s_, mängd in nåbart.items():
            nådda_celler[s_] = {c for _, _, c in mängd}
    for rad in _ändelserader(språk):
        if nåbart is not None and rad["cell"] not in nådda_celler.get(rad["språk"], set()):
            continue
        n = klasstorlek.get((rad["språk"], rad["ordklass"], rad["klass"]), 1)
        _lägg_till(kort, "system", rad["språk"], rad["ändelse"] or "∅",
                   ordklass=rad["ordklass"], klass=rad["klass"],
                   cell=rad["cell"], räckvidd=n)

    # ── rektionskort: att ett styrande ord kräver en viss form ────────
    for r in språk_db.execute(
            """SELECT m.språk, k.nyckel, k.ordklass, mk.slot, mk.kasus,
                      mk.tempus, p.nyckel AS prep
               FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               LEFT JOIN Koncept p ON p.id = mk.preposition_koncept_id
               WHERE m.språk IS NOT NULL
                 AND (mk.kasus IS NOT NULL OR mk.tempus IS NOT NULL
                      OR mk.preposition_koncept_id IS NOT NULL)"""):
        if r["språk"] not in språk or not ordet_finns(r["språk"], r["nyckel"]):
            continue
        for egenskap, värde in (("kasus", r["kasus"]), ("modus", r["tempus"]),
                                ("preposition", r["prep"])):
            if värde is not None:
                _lägg_till(kort, "rektion", r["språk"], str(värde),
                           koncept=r["nyckel"], ordklass=r["ordklass"],
                           cell=r["slot"], egenskap=egenskap)

    # ── egenskapskort: det som syns på ANDRA ord ──────────────────────
    for egenskap, ordklass in EGENSKAPER.items():
        for r in språk_db.execute(
                f"""SELECT k.nyckel, l.språk, l.variant, l.{egenskap} AS värde
                    FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id
                    WHERE k.ordklass = ? AND l.{egenskap} IS NOT NULL""",
                (ordklass,)):
            if r["språk"] in språk and ordet_finns(r["språk"], r["nyckel"]):
                _lägg_till(kort, "egenskap", r["språk"], str(r["värde"]),
                           koncept=r["nyckel"], variant=r["variant"],
                           ordklass=ordklass, egenskap=egenskap)

    # Böjningsklass är också en egenskap hos ordet, men bara när klassen är
    # ett VAL — har ordklassen en enda klass finns inget att kunna.
    klasser: dict[tuple, set] = {}
    for rad in _stamrader(språk):
        klasser.setdefault((rad["språk"], rad["ordklass"]), set()).add(rad["klass"])
    sedda = set()
    for rad in _stamrader(språk):
        if len(klasser[(rad["språk"], rad["ordklass"])]) < 2:
            continue
        id_ = (rad["språk"], rad["koncept"], rad["variant"])
        if id_ in sedda or not ordet_finns(rad["språk"], rad["koncept"]):
            continue
        sedda.add(id_)
        _lägg_till(kort, "egenskap", rad["språk"], rad["klass"],
                   koncept=rad["koncept"], variant=rad["variant"] or None,
                   ordklass=rad["ordklass"], egenskap="böjningsklass")

    # ── ordföljdskort ─────────────────────────────────────────────────
    for s in sorted(språk):
        for regel, beskrivning in ORDFÖLJD.get(s, []):
            _lägg_till(kort, "ordföljd", s, beskrivning, egenskap=regel)

    return kort


def _golvkort(språk_db: sqlite3.Connection, språk: set[str]) -> list[tuple]:
    """Beroendekartan för de ordklasser som inte har någon stamanalys."""
    from ..rendering import RenderingsFel, Uppslag
    analyserade = {(rad["språk"], rad["ordklass"]) for rad in _stamrader(språk)}
    ut = []
    for s_ in sorted(språk):
        u = Uppslag(språk_db, s_)
        for r in språk_db.execute(
                """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
                   JOIN Koncept k ON k.id = l.koncept_id WHERE l.språk = ?""", (s_,)):
            if (s_, r["ordklass"]) in analyserade:
                continue
            try:
                celler = {c: f for c, f in u._celler(r).items() if f}
            except (RenderingsFel, KeyError):
                continue
            for cell in celler:
                ut.append((s_, r["nyckel"], r["variant"], cell,
                           _nyckel("form", s_, r["nyckel"], r["variant"],
                                   r["ordklass"], None, cell, None, None)))
    return ut


def _cellkort(språk: set[str]) -> list[tuple]:
    """(språk, koncept, variant, cell) → kortets naturliga nyckel.

    Renderarens beroendekarta i tabellform: från det `Uppslag.form` redan
    känner till, till de kort som prövas när formen används.
    """
    ut = []
    for rad in _stamrader(språk):
        grupp = int(rad["stamgrupp"])
        celler = rad["celler"].split(",")
        typ = "stam" if grupp >= 0 else "form"
        nyckel = _nyckel(typ, rad["språk"], rad["koncept"],
                         rad["variant"] or None, rad["ordklass"], rad["klass"],
                         None if grupp >= 0 else celler[0],
                         grupp if grupp >= 0 else None, None)
        for cell in celler:
            ut.append((rad["språk"], rad["koncept"], rad["variant"] or None,
                       cell, nyckel))
        # ändelsen som gäller samma cell
        for cell in celler:
            ut.append((rad["språk"], rad["koncept"], rad["variant"] or None, cell,
                       _nyckel("system", rad["språk"], None, None,
                               rad["ordklass"], rad["klass"], cell, None, None)))
    return ut


def nåbara(språk_db: sqlite3.Connection, språk: str, nivå: int, cefr: str,
           kandidater: int = 4000) -> set[tuple]:
    """(koncept, variant, cell) som GÅR att möta på den här nivån.

    Mätt och inte härledd: samplaren bygger meningar på nivån, renderaren
    renderar dem, och instrumenteringen säger vilka former som slogs upp.
    Den bakvägen — från cell till de specparametrar som ger den — finns inte
    och behöver inte finnas.

    Skälet att alls mäta: en tysk nybörjare har 2 119 kort på A1, men på
    nivå 4 går bara 643 av dem att möta. De övriga 1 476 skulle ligga i kön,
    väljas som mål, och aldrig kunna nås av någon mening.
    """
    import random

    from ..generator.urval import Ordförråd, Samplare
    from ..rendering import RenderingsFel, Uppslag, Validator
    from ..rendering import (
        EngelskRenderare, FranskRenderare, ItalienskRenderare,
        JapanskRenderare, SpanskRenderare, SvenskRenderare, TyskRenderare,
    )
    renderare = {"sv": SvenskRenderare, "en": EngelskRenderare,
                 "de": TyskRenderare, "fr": FranskRenderare,
                 "es": SpanskRenderare, "it": ItalienskRenderare,
                 "ja": JapanskRenderare}[språk](språk_db)
    validator = Validator(språk_db)
    samplare = Samplare(Ordförråd(språk_db, språk, cefr), nivå, random.Random(0))

    rörda: list = []
    original = Uppslag.form

    def logga(själv, lexem, cell):
        rörda.append((lexem["nyckel"], lexem["variant"], cell))
        return original(själv, lexem, cell)

    Uppslag.form = logga
    sedda: set[tuple] = set()
    try:
        for _ in range(kandidater):
            m = samplare.kandidat()
            if m is None or validator.validera(m):
                continue
            rörda.clear()
            try:
                renderare.rendera(m)
            except (RenderingsFel, KeyError, ValueError):
                continue
            sedda.update(rörda)
    finally:
        Uppslag.form = original
    return sedda


def befolka(kort_db: sqlite3.Connection, språk_db: sqlite3.Connection,
            språk: set[str], *, nivå: int | None = None,
            cefr: str = "C2", mät: bool = True) -> dict[str, int]:
    """Sätt in de kort som saknas. Rör aldrig ett kort som redan finns.

    Additivt av ett skäl: ett befintligt kort bär repetitionshistorik, och
    att skriva över det för att beståndet räknats om vore att kasta det enda
    som inte går att återskapa. Därför går funktionen att köra om vid varje
    upplåsning — det är så en nivå ÖPPNAS: nya kort skapas.

    Med `nivå` satt skapas bara kort som går att möta på den nivån. Ett kort
    som inte går att nå hör inte hemma i kön; principen är densamma som för
    former specen inte når, bara med en gräns som flyttar sig.
    """
    nåbart = None
    if nivå is not None:
        nåbart = {s_: nåbara(språk_db, s_, nivå, cefr) for s_ in sorted(språk)}
    rader = härled(språk_db, språk, nåbart)
    före = kort_db.execute("SELECT COUNT(*) FROM Kort").fetchone()[0]
    kort_db.executemany(
        """INSERT OR IGNORE INTO Kort
           (nyckel, typ, språk, koncept, variant, ordklass, klass, cell,
            stamgrupp, egenskap, facit, räckvidd)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", rader)
    kort_db.commit()
    efter = kort_db.execute("SELECT COUNT(*) FROM Kort").fetchone()[0]

    # Beroendekartan byggs om varje gång — den bär ingen historik, bara
    # kopplingen, och den ska följa språkdatabasen.
    #
    # BARA FÖR DE SPRÅK SOM BEFOLKAS. Raderingen gällde hela tabellen medan
    # återuppbyggnaden bara gällde `språk`, så varje befolkning av ETT språk
    # tömde kartan för ALLA ANDRA. Att skapa kursen sv→en 2026-08-15 raderade
    # därmed tyskans 3 000 kopplingar, och tyskan hade sedan dess bara sina
    # ORDKORT: rättningen kunde inte skylla ett böjningsfel på vare sig stam
    # eller ändelse, och svarade "inget kort hör till ordet" på varje
    # formfel. Beståndet såg oskadat ut hela tiden — Kort-tabellen var hel,
    # och raden som rapporterades ("1 290 kopplingar") räknade det språk som
    # just byggts, aldrig det som tappats.
    idn = {r["nyckel"]: r["id"] for r in kort_db.execute("SELECT id, nyckel FROM Kort")}
    kort_db.executemany("DELETE FROM Cellkort WHERE språk = ?",
                        [(s_,) for s_ in sorted(språk)])
    kort_db.executemany(
        "INSERT INTO Cellkort (språk, koncept, variant, cell, kort_id) VALUES (?,?,?,?,?)",
        [(s, k, v, c, idn[n])
         for s, k, v, c, n in _cellkort(språk) + _golvkort(språk_db, språk)
         if n in idn])
    kort_db.commit()
    kopplingar = kort_db.execute("SELECT COUNT(*) FROM Cellkort").fetchone()[0]

    # Kort utan täckning i den härledda mängden — rapporteras, tas inte bort.
    #
    # Bara när HELA beståndet härletts. Med en nivåspärr är mängden SAMPLAD,
    # och två svep når inte exakt samma kort — då är "föräldralös" bara
    # brus. Att ändå behålla korten är rätt: de bär historik.
    föräldralösa: list[str] = []
    if nåbart is None:
        härledda = {r[0] for r in rader}
        föräldralösa = [r["nyckel"] for r in kort_db.execute("SELECT nyckel FROM Kort")
                        if r["nyckel"] not in härledda]
    # Införandeordningen skrivs om varje gång, precis som beroendekartan:
    # den bär ingen historik utan följer språkdatabasen.
    for s_ in sorted(språk):
        rang = _rang(språk_db, s_, cefr)
        if rang:
            kort_db.executemany(
                "UPDATE Kort SET rang = ? WHERE språk = ? AND koncept = ?",
                [(v, s_, k) for k, v in rang.items()])
    kort_db.commit()

    # EXPONERINGEN MÅSTE MÄTAS OM NÄR BESTÅNDET ÄNDRAS, och det är precis här
    # det gör det. Mätningen fanns, tröskeln fanns, kolumnen fanns — men
    # ingenting anropade dem, så `exponering` var NULL på varje kort och
    # `schemalagt` 1 på alla. Följden var att de allestädes närvarande korten
    # låg i kön och betygsattes om och om igen: `∅` möts 0,93 gånger per
    # mening, `a` 0,41, och de fick var sitt Good i nästan varje mening.
    #
    # Kostar 1,7 s för tyskan och 0,4 för engelskan — försumbart mot att köra
    # befolkningen, som ändå bara sker när en nivå öppnas.
    #
    # `kostnad()` ställer en HYPOTETISK fråga i en kopia och stänger av det
    # här: den vill veta hur många kort en nivå skulle lägga till, inte hur
    # ofta de skulle mötas.
    if mät:
        # SPRÅKVIS, PARVIS. Mätningen och skrivningen hör ihop: bara det
        # språk vars exponering just mätts får sin flagga omskriven. Att
        # skriva alla på slutet lät en språkmätning ändra ett annat språks
        # kö — se `sätt_schemalagt`.
        for s_ in sorted(språk):
            mät_exponering(kort_db, språk_db, s_)
            sätt_schemalagt(kort_db, språk=s_)

    return {"härledda": len(rader), "nya": efter - före, "totalt": efter,
            "kopplingar": kopplingar, "föräldralösa": len(föräldralösa),
            "omätta": kort_db.execute(
                "SELECT COUNT(*) FROM Kort WHERE exponering IS NULL").fetchone()[0],
            "ej_schemalagda": kort_db.execute(
                "SELECT COUNT(*) FROM Kort WHERE schemalagt = 0").fetchone()[0]}


#: CEFR som rangordning. A1 före A2 före B1 — samma ordning som `CEFR` i
#: urval.py, men som tal.
_NIVÅRANG = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}

#: Ordklasser en minimal sats inte kan vara utan: verbet, frashuvudet och
#: artikeln det kräver. Allt annat är bestämningar som dessutom är låsta
#: bakom en nivå på komplexitetsstegen, så de behövs inte först.
_OUMBÄRLIGA = {"Verb", "Pronomen", "Substantiv", "Artikel"}


def _rang(språk_db: sqlite3.Connection, språk: str, cefr: str) -> dict[str, int]:
    """Konceptnyckel → införandeordning. Lägre = tidigare.

    Tre signaler, alla redan i språkdatabasen:

        källa        bas_kärna före grundord. De slutna ordklasserna ÄR
                     kärnan, och uppdelningen är redan gjord i nivålistorna.
        nivå         A1 före A2.
        centralitet  hur många meningar ordet gör möjliga — för ett
                     substantiv antalet verb det kan stå med, för ett verb
                     antalet ord som kan vara dess subjekt.

    CENTRALITETEN NORMALISERAS INOM ORDKLASS. Ett verb med 169 möjliga
    subjekt och ett pronomen med 65 möjliga verb mäter inte samma sak, och
    att jämföra talen rakt av satte modalverben före pronomenen — man kan
    inte böja ett verb innan man har någon att böja det efter.

    Rangen är per KONCEPT, så alla kort som hör till ett ord delar den.
    """
    from ..generator.urval import Ordförråd

    o = Ordförråd(språk_db, språk, cefr)
    meta = {r["nyckel"]: r for r in språk_db.execute(
        "SELECT nyckel, källa, nivå, ordklass, person, numerus FROM Koncept")}

    def råcentralitet(k: str) -> int:
        ordklass = o.ordklass.get(k)
        if ordklass in ("Substantiv", "Pronomen"):
            return len(o.verb_för(k))
        if ordklass == "Verb":
            krav = o.verb.get(k)
            return len(o.uppfyller(krav.get("subjekt", []))) if krav else 0
        return 0

    tak: dict[str, int] = {}
    rå: dict[str, int] = {}
    for k in o.ordklass:
        if k not in meta:
            continue
        rå[k] = råcentralitet(k)
        ordklass = o.ordklass[k]
        tak[ordklass] = max(tak.get(ordklass, 0), rå[k])

    def nyckel(k: str):
        m = meta[k]
        t = tak.get(o.ordklass.get(k), 0)
        andel = rå[k] / t if t else 0.0
        return (0 if m["källa"] == "bas_kärna" else 1,
                _NIVÅRANG.get(m["nivå"], 9),
                0 if m["ordklass"] in _OUMBÄRLIGA else 1,
                -andel,
                # PARADIGMETS EGEN ORDNING NÄR CENTRALITETEN ÄR LIKA.
                #
                # Sista brytpunkten var konceptNYCKELN, alltså alfabetet, och
                # det avgjorde i tysthet i vilken ordning man möter språkets
                # mest grundläggande ord. Mätt på franskan: alla sex
                # personliga pronomen har centralitet 65 — de kan stå med
                # samma 65 verb — så ordningen föll på strängjämförelsen, och
                # `pronomen_1pl` kom före `pronomen_1sg` därför att "p" < "s".
                #
                # Följden var att man lärde sig `nous` före `je`, och `vous`
                # före `tu`. Julius märkte det: "Nu t.ex lär vi oss ni och vi
                # innan vi lär oss du."
                #
                # `person` och `numerus` ligger redan på Koncept och ger
                # paradigmets ordning: je, tu, il/elle, nous, vous, ils. Det
                # är ordningen varje läromedel i varje av de sju språken
                # använder, och den är läst ur datan snarare än vald.
                #
                # Koncept UTAN de fälten (substantiv, verb, adjektiv) får 9
                # och påverkas inte av varandra — brytpunkten gäller bara där
                # ett paradigm faktiskt finns.
                m["numerus"] or 9, m["person"] or 9,
                k)

    return {k: i for i, k in enumerate(sorted(rå, key=nyckel))}


def exponeringsgräns(meningar_per_dag: int) -> float:
    """Över så många möten per mening slutar schemaläggning ha en spak.

    RÄKNAS, står inte i koden. Ett kort möts `exponering × meningar_per_dag`
    gånger om dagen, och FSRS kortaste meningsfulla intervall ÄR en dag — ett
    kort som möts oftare än så kan aldrig spacas, hur kön än ser ut. Alltså
    är gränsen 1/meningar_per_dag.

    Talet stod tidigare som 0,05 med härledningen i en kommentar, vilket var
    rätt uträknat för 20 meningar om dagen och tyst fel för alla andra. Nu när
    takten är användarens val måste gränsen följa den. Se GENERATOR.md,
    "Schemalagda kort mot mätta kort".
    """
    return 1.0 / meningar_per_dag


def sätt_schemalagt(kort_db: sqlite3.Connection,
                    meningar_per_dag: int | None = None, *,
                    språk: str | None = None) -> int:
    """Kort som möts oftare än gränsen mäts men schemaläggs inte.

    Kräver att `exponering` är mätt. Omätta kort lämnas schemalagda — att
    gissa vore att bygga in en tumregel där beslutet säger mätning.

    SKRIVNINGEN ÄR SPRÅKVIS, och det var den inte. `UPDATE Kort SET
    schemalagt = …` utan `WHERE språk` skrev om ALLA språks flagga vid varje
    anrop, också de vars exponering aldrig mättes i den körningen — och
    gränsen kom dessutom ur `MIN(meningar_per_dag)` över samtliga kurser, så
    en kurs inställning avgjorde en annan kurss kö.

    Det är exakt samma felklass som I3: `befolka` körde en gång
    `DELETE FROM Cellkort` utan språkfilter, och att skapa en engelsk kurs
    raderade därmed tyskans hela beroendekarta — i en månad, utan att något
    syntes. Skrivningar i det här lagret ska aldrig sträcka sig utanför det
    språk anroparen bad om.

    `meningar_per_dag` hämtas nu ur KURSEN för språket i fråga. Talet är i
    övrigt en kvarleva efter B4 — användarens ratt är minuter — och E6 säger
    att gränsen egentligen ska följa den uppmätta takten. Att räkna om den
    är ett beslut och inte en rättelse, så den står kvar som den är; det som
    ändrats är bara att den inte längre är någon annans.
    """
    from .schemalaggning import STANDARD_MENINGAR_PER_DAG
    if meningar_per_dag is None:
        rad = kort_db.execute(
            "SELECT MIN(meningar_per_dag) AS m FROM Kurs"
            + (" WHERE målspråk = ?" if språk else ""),
            (språk,) if språk else ()).fetchone()
        meningar_per_dag = (rad["m"] if rad and rad["m"] else STANDARD_MENINGAR_PER_DAG)
    kort_db.execute(
        "UPDATE Kort SET schemalagt = (exponering IS NULL OR exponering <= ?)"
        + (" WHERE språk = ?" if språk else ""),
        (exponeringsgräns(meningar_per_dag),) + ((språk,) if språk else ()))
    kort_db.commit()
    return kort_db.execute(
        "SELECT COUNT(*) FROM Kort WHERE schemalagt = 0"
        + (" AND språk = ?" if språk else ""),
        (språk,) if språk else ()).fetchone()[0]


def sammanfattning(kort_db: sqlite3.Connection) -> list[sqlite3.Row]:
    return kort_db.execute(
        """SELECT språk, typ, COUNT(*) AS antal,
                  SUM(schemalagt) AS schemalagda,
                  ROUND(AVG(räckvidd), 1) AS snitträckvidd
           FROM Kort GROUP BY språk, typ ORDER BY språk, antal DESC""").fetchall()


def mät_exponering(kort_db, språk_db, språk: str, meningar: int = 2000) -> int:
    """Mät hur ofta varje kort möts, genom att sampla meningar och logga.

    Fördelningen är den SLUMPMÄSSIGA, inte generatorns — generatorn kommer
    att vikta mot förfallna kort. Den här mätningen är alltså ett förval som
    ska räknas om mot verklig användning när loggen finns.
    """
    import collections
    import random

    from ..rendering import (
        Attribut, Bestämdhet, Grad, Mening, Nominalfras, Numerus,
        RenderingsFel, Tidsreferens, Uppslag, Validator,
    )
    from ..rendering import (
        EngelskRenderare, FranskRenderare, ItalienskRenderare,
        JapanskRenderare, SpanskRenderare, SvenskRenderare, TyskRenderare,
    )
    renderare = {"sv": SvenskRenderare, "en": EngelskRenderare,
                 "de": TyskRenderare, "fr": FranskRenderare,
                 "es": SpanskRenderare, "it": ItalienskRenderare,
                 "ja": JapanskRenderare}[språk](språk_db)
    validator = Validator(språk_db)
    rörda: list = []
    original = Uppslag.form

    def logga(self, lexem, cell):
        rörda.append((self.språk, lexem["nyckel"], lexem["variant"], cell))
        return original(self, lexem, cell)

    original_egenskap = Uppslag.egenskap
    egenskaper: list = []

    def logga_egenskap(self, lexem, namn):
        egenskaper.append((lexem["nyckel"], namn))
        return original_egenskap(self, lexem, namn)

    # ORDFÖLJDEN MÄTS HÄR, och det är den mätningen som gör E6:s uppdelning
    # automatisk. En regel som gäller i varje mening får exponering nära 1
    # och lyfts ur schemat av `sätt_schemalagt`; en som bara gäller när en
    # konstruktion är i spel får en exponering som går att schemalägga.
    # A7 punkt 2 behöver alltså ingen egen lista över vilka regler som är
    # högfrekventa — den följer ur samma mätning som allt annat.
    #
    # KÄND GRÄNS: svepet nedan bygger bara enkla påståendesatser, så regler
    # som kräver fråga, bisats eller två objekt får exponering 0,0. Det är
    # "inte mätt" och inte "mätt som sällsynt" — men utfallet blir rätt ändå,
    # eftersom just de reglerna är de som SKA vara schemalagda.
    original_ordföljd = Uppslag.ordföljd
    ordföljder: list = []

    def logga_ordföljd(self, regel):
        ordföljder.append(regel)
        return original_ordföljd(self, regel)

    karta: dict = collections.defaultdict(list)
    for rad in kort_db.execute(
            "SELECT språk, koncept, variant, cell, kort_id FROM Cellkort WHERE språk = ?",
            (språk,)):
        karta[(rad["språk"], rad["koncept"], rad["variant"], rad["cell"])].append(
            rad["kort_id"])

    # ORDKORT OCH EGENSKAPSKORT HÄNGER PÅ KONCEPTET, inte på en cell, och står
    # därför inte i Cellkort. Utan de här två uppslagen mättes de aldrig: alla
    # 223 tyska ordkort och alla 428 genuskort fick exponering 0, vilket är
    # samma lucka som en gång gjorde att varje mening attribuerade noll
    # ordkort. Det är dessutom just de korten som ska sorteras på exponering
    # när nya ord ska införas — ett ord man kommer att möta ofta hör hemma
    # tidigt.
    ordkort: dict = collections.defaultdict(list)
    for rad in kort_db.execute(
            """SELECT koncept, variant, id FROM Kort
               WHERE språk = ? AND typ = 'ord' AND koncept IS NOT NULL""",
            (språk,)):
        ordkort[(rad["koncept"], rad["variant"])].append(rad["id"])
    ordföljdskort: dict = {}
    for rad in kort_db.execute(
            """SELECT egenskap, id FROM Kort
               WHERE språk = ? AND typ = 'ordföljd'""", (språk,)):
        ordföljdskort[rad["egenskap"]] = rad["id"]
    egenskapskort: dict = collections.defaultdict(list)
    for rad in kort_db.execute(
            """SELECT koncept, egenskap, id FROM Kort
               WHERE språk = ? AND typ = 'egenskap' AND koncept IS NOT NULL""",
            (språk,)):
        egenskapskort[(rad["koncept"], rad["egenskap"])].append(rad["id"])

    subst = [r[0] for r in språk_db.execute(
        """SELECT k.nyckel FROM Koncept k JOIN Lexem l ON l.koncept_id = k.id
           AND l.språk = ? WHERE k.ordklass = 'Substantiv' AND k.räknebar = 1""",
        (språk,))]
    adj = [r[0] for r in språk_db.execute(
        """SELECT k.nyckel FROM Koncept k JOIN Lexem l ON l.koncept_id = k.id
           AND l.språk = ? WHERE k.ordklass = 'Adjektiv'""", (språk,))]
    verb = [r[0] for r in språk_db.execute(
        """SELECT DISTINCT k.nyckel FROM Mönster m JOIN Koncept k ON k.id = m.koncept_id
           JOIN MönsterKrav mk ON mk.mönster_id = m.id
           WHERE mk.slot = 'objekt' AND m.språk IS NULL""")]
    if not (subst and adj and verb):
        return 0

    random.seed(3)
    Uppslag.form = logga
    Uppslag.egenskap = logga_egenskap
    Uppslag.ordföljd = logga_ordföljd
    try:
        träffar: collections.Counter = collections.Counter()
        byggda = försök = 0
        while byggda < meningar and försök < meningar * 50:
            försök += 1
            m = Mening(
                random.choice(verb),
                Nominalfras(random.choice(subst),
                            random.choice(list(Bestämdhet)[:2]),
                            random.choice(list(Numerus))),
                objekt=Nominalfras(random.choice(subst),
                                   random.choice(list(Bestämdhet)[:2]),
                                   random.choice(list(Numerus)),
                                   attribut=(Attribut(random.choice(adj),
                                                      random.choice(list(Grad))),)),
                tid=random.choice(list(Tidsreferens)))
            if validator.validera(m):
                continue
            rörda.clear()
            egenskaper.clear()
            ordföljder.clear()
            try:
                renderare.rendera(m)
            except RenderingsFel:
                continue
            byggda += 1
            for nyckel in set(rörda):
                for kid in karta.get(nyckel, []):
                    träffar[kid] += 1
            for _, koncept, variant, _ in set(rörda):
                for kid in ordkort.get((koncept, variant), []):
                    träffar[kid] += 1
            for nyckel in set(egenskaper):
                for kid in egenskapskort.get(nyckel, []):
                    träffar[kid] += 1
            for regel in set(ordföljder):
                kid = ordföljdskort.get(regel)
                if kid is not None:
                    träffar[kid] += 1
    finally:
        Uppslag.form = original
        Uppslag.egenskap = original_egenskap
        Uppslag.ordföljd = original_ordföljd
    if not byggda:
        return 0
    kort_db.executemany("UPDATE Kort SET exponering = ? WHERE id = ?",
                        [(n / byggda, kid) for kid, n in träffar.items()])
    kort_db.execute(
        "UPDATE Kort SET exponering = 0 WHERE språk = ? AND exponering IS NULL",
        (språk,))
    kort_db.commit()
    return byggda
