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


def _lemman(språk_db: sqlite3.Connection) -> dict[tuple, str]:
    """(språk, koncept, variant) → lemma. Läses en gång, används på två
    ställen: `härled` för att avgöra om stamkortet ska finnas, `_cellkort`
    för att avgöra vart cellen ska peka när det inte gör det."""
    return {(r["språk"], r["nyckel"], r["variant"]): r["lemma"]
            for r in språk_db.execute(
                """SELECT k.nyckel, l.språk, l.lemma, l.variant
                   FROM Lexem l JOIN Koncept k ON k.id = l.koncept_id""")}


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
           nåbart: dict[str, set[tuple]] | None = None,
           böjningsceller: dict[str, set[str]] | None = None) -> list[tuple]:
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
    #
    # EN STAM SOM ÄR HELA ORDET LÄR INTE UT NÅGOT. Julius: *"Vi gjorde il i
    # ordglosdelen redan. Är det problematiskt att il är identisk som ord och
    # som stem?"* — och det är det. Kortet frågar samma sak som ordkortet,
    # med samma facit, och den som klarat det ena kan det andra utan att veta
    # om det.
    #
    # Mätt på franskan innan villkoret sattes in:
    #
    #     Substantiv   133 av 136 stamkort identiska med sitt ordkort
    #     Pronomen       8 av  10
    #     Verb           0 av  70
    #
    # Verben är undantaget, och det är just där stammen bär betydelse:
    # `exist` mot `exister`. För ett oböjt substantiv eller pronomen finns
    # ingen stam att skilja från ordet.
    #
    # Samma tomma läromoment som ändelserna hade före hopslagningen (F5b,
    # 52 %), i en annan korttyp och med samma svar: kortet ska bara finnas
    # när det säger något ordkortet inte redan säger.
    lemman = _lemman(språk_db)
    for rad in _stamrader(språk):
        grupp = int(rad["stamgrupp"])
        celler = rad["celler"].split(",")
        if not nås(rad["språk"], rad["koncept"], rad["variant"] or None, celler):
            continue
        if grupp >= 0:
            if rad["form"] == lemman.get(
                    (rad["språk"], rad["koncept"], rad["variant"] or None)):
                continue          # stammen ÄR ordet — se kommentaren ovan
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
        # BÖJNINGSSTEGEN GRINDAR ÄNDELSEKORTEN. Utan den här raden skapades
        # franskans sex personändelser allihop på nivå 1 — sex läromoment
        # samma dag, varav två tomma (`pres_1sg` och `pres_3sg` är båda `e`
        # i K0). Se F5b och `dimensioner.stege`.
        #
        # NYCKELN ÄR (SPRÅK, ORDKLASS) och inte bara språket. Första
        # versionen grindade på språk, och eftersom stegen bara känner
        # VERBcellerna föll substantivens och adjektivens ändelser bort helt:
        # tyskans 241 ändelsekort blev 16. En ordklass utan stege ska passera
        # ogrindad, inte försvinna — och `None` betyder fortfarande ingen
        # grind alls, vilket verktyg som sveper hela beståndet behöver.
        nyckel = (rad["språk"], rad["ordklass"])
        if (böjningsceller is not None and nyckel in böjningsceller
                and rad["cell"] not in böjningsceller[nyckel]):
            continue
        n = klasstorlek.get((rad["språk"], rad["ordklass"], rad["klass"]), 1)
        # KORTET HÖR TILL ÄNDELSEN, INTE TILL CELLEN — och det är skillnaden
        # mellan att lära sig något och att bli tillfrågad om det.
        #
        # Franskans K0 hade `pres_1sg = e` och `pres_3sg = e` som TVÅ kort med
        # olika namn och samma svar. Det andra kunde aldrig lära ut något: har
        # man klarat det första finns ingenting kvar. Sex frågor för fem
        # kunskaper.
        #
        # Nyckeln är därför (typ, språk, ordklass, klass, ÄNDELSE) och cellen
        # står tom. `INSERT OR IGNORE` gör hopslagningen av sig själv: två
        # celler med samma ändelse ger samma naturliga nyckel och därmed ett
        # kort. Båda cellernas uppslag pekar sedan på det via `Cellkort`, så
        # `Elle parle.` och `Je parle.` prövar samma kunskap — vilket de gör.
        #
        # Alternativet var att grinda bort den andra cellen på nivåstegen,
        # men då försvann attributionen med den: meningen slog upp en cell
        # utan kort. Att slå ihop är att ta bort det tomma momentet UTAN att
        # lämna ett hål. Se F5b.
        _lägg_till(kort, "system", rad["språk"], rad["ändelse"] or "∅",
                   ordklass=rad["ordklass"], klass=rad["klass"],
                   egenskap=rad["ändelse"] or "∅", räckvidd=n)

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


def _cellkort(språk_db: sqlite3.Connection, språk: set[str]) -> list[tuple]:
    """(språk, koncept, variant, cell) → kortets naturliga nyckel.

    Renderarens beroendekarta i tabellform: från det `Uppslag.form` redan
    känner till, till de kort som prövas när formen används.

    NÄR STAMMEN ÄR ORDET PEKAR CELLEN PÅ ORDKORTET. `härled` slutade skapa
    stamkortet i det läget, och utan omdirigeringen föll raden bort tyst
    (`if n in idn` vid insättningen) — cellen hade då bara ÄNDELSEN kvar att
    skylla på. Mätt på beroendekartan innan omdirigeringen fanns:

        fr    811 av  8 874 celler utan annat kort än ändelsen
        de 13 177 av 23 109
        sv  2 366 av  4 791
        en  1 593 av  2 054

    Ett fel `mère` hade alltså bokförts på ändelsen `s`. Stamkortet stod och
    höll ordkortets plats i kartan: ordkort hade före det här NOLL rader i
    `Cellkort` i samtliga språk, så ett felstavat ord kunde aldrig bokföras
    på ordet självt. Det är samma kort som förr, med sitt riktiga namn.
    """
    ut = []
    lemman = _lemman(språk_db)
    # (språk, ordklass, klass, cell) → ändelse. Läses en gång; uppslaget görs
    # per cell och per stam nedan.
    ändelser = {(r["språk"], r["ordklass"], r["klass"], r["cell"]):
                r["ändelse"] or "∅" for r in _ändelserader(språk)}
    for rad in _stamrader(språk):
        grupp = int(rad["stamgrupp"])
        celler = rad["celler"].split(",")
        stammen_är_ordet = grupp >= 0 and rad["form"] == lemman.get(
            (rad["språk"], rad["koncept"], rad["variant"] or None))
        if stammen_är_ordet:
            nyckel = _nyckel("ord", rad["språk"], rad["koncept"],
                             rad["variant"] or None, rad["ordklass"],
                             None, None, None, None)
        else:
            typ = "stam" if grupp >= 0 else "form"
            nyckel = _nyckel(typ, rad["språk"], rad["koncept"],
                             rad["variant"] or None, rad["ordklass"],
                             rad["klass"], None if grupp >= 0 else celler[0],
                             grupp if grupp >= 0 else None, None)
        for cell in celler:
            ut.append((rad["språk"], rad["koncept"], rad["variant"] or None,
                       cell, nyckel))
        # ändelsen som gäller samma cell — BARA FÖR STAMMAR.
        #
        # EN REST UPPVISAR INTE KLASSENS ÄNDELSE; det är definitionen av en
        # rest. `dela_upp` lägger cellen bland resterna just för att formen
        # inte slutar på ändelsen, och att sedan koppla cellen till
        # ändelsekortet är att påstå motsatsen. Julius om `J'ai.`: *"vad är
        # ens s för ändelsekort? Prövades det verkligen?"* — nej.
        #
        #     was     → ändelsekort 'ed'
        #     です     → ändelsekort 'ます'
        #     mannen  → ändelsekort 'et'
        #     être    → ändelsekort 'er'
        #
        # Mätt på kopplingarna innan villkoret: ja 8,9 %, fr 6,2 %, en 5,8 %,
        # it 5,4 %, es 3,5 %, sv 1,7 %. Kortet steg i stabilitet på bevis som
        # aldrig fanns — den enda feltypen som FÖRDÄRVAR data i stället för
        # att sakna den. Formkortet äger hela strängen; där finns ingen
        # ändelse att pröva separat.
        for cell in celler if grupp >= 0 else ():
            # ÄNDELSEN, inte cellen — samma nyckel som kortet fick ovan.
            ändelse = ändelser.get(
                (rad["språk"], rad["ordklass"], rad["klass"], cell))
            if ändelse is None:
                # Klassen har ingen ändelse för cellen. Det är inte ett fel:
                # paradigmet kan sakna cellen helt, och då finns inget kort
                # att peka på heller.
                continue
            ut.append((rad["språk"], rad["koncept"], rad["variant"] or None, cell,
                       _nyckel("system", rad["språk"], None, None,
                               rad["ordklass"], rad["klass"], None, None,
                               ändelse)))
    return ut


def nåbara(språk_db: sqlite3.Connection, språk: str, nivå: int, cefr: str,
           kandidater: int = 4000,
           tillåtet: set[str] | None = None) -> set[tuple]:
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
    samplare = Samplare(Ordförråd(språk_db, språk, cefr), nivå,
                        random.Random(0), tillåtet=tillåtet)

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


def _slå_ihop_gamla_ändelsekort(kort_db: sqlite3.Connection,
                                språk: set[str]) -> int:
    """Flytta historiken från cell-nycklade ändelsekort till de ändelse-nycklade.

    ENGÅNGSMIGRATION, och den behövs därför att kortets IDENTITET ändrades.
    Förut fanns ett kort per (klass, cell); nu ett per (klass, ändelse). Utan
    den här funktionen blir de gamla korten kvar med sin historik men UTAN
    rad i `Cellkort` — alltså schemalagda, förfallna, och omöjliga för någon
    mening att nå. Mätt på Julius franska: 15 föräldralösa kort efter en
    nivåupplåsning, varav 7 med historik. Det är exakt A3:s spökkort.

    DEN SVAGASTE EVIDENSEN VINNER. Två gamla kort — `pres_1sg` och
    `pres_3sg`, båda `e` — blir ett. Vilken stabilitet ska det ärva? Det
    lägsta, och skälet är att den sammanslagna kunskapen inte kan vara
    säkrare än den osäkraste mätningen av den. Att ta den högsta vore att
    påstå att man kan något bättre än man visat.

    Repetitionsraderna följer med allihop: de är mätningar av samma kunskap,
    gjorda under olika namn, och FSRS optimerare läser dem som en historik.
    """
    flyttade = 0
    for s_ in sorted(språk):
        gamla = kort_db.execute(
            """SELECT id, ordklass, klass, facit, stabilitet, svårighet,
                      tillstånd, steg, sedd, förfaller, antal, fall
               FROM Kort WHERE språk = ? AND typ = 'system'
                 AND cell IS NOT NULL""", (s_,)).fetchall()
        if not gamla:
            continue
        nya = {(r["ordklass"], r["klass"], r["facit"]): r["id"]
               for r in kort_db.execute(
                   """SELECT id, ordklass, klass, facit FROM Kort
                      WHERE språk = ? AND typ = 'system' AND cell IS NULL""",
                   (s_,))}
        for g in gamla:
            ny_id = nya.get((g["ordklass"], g["klass"], g["facit"]))
            if ny_id is None:
                continue          # ingen efterföljare — lämna kortet i fred
            kort_db.execute("UPDATE Repetition SET kort_id = ? WHERE kort_id = ?",
                            (ny_id, g["id"]))
            if g["sedd"] is not None:
                mål = kort_db.execute(
                    "SELECT stabilitet, sedd FROM Kort WHERE id = ?",
                    (ny_id,)).fetchone()
                svagare = (mål["sedd"] is None
                           or (g["stabilitet"] or 0) < (mål["stabilitet"] or 0))
                if svagare:
                    kort_db.execute(
                        """UPDATE Kort SET stabilitet = ?, svårighet = ?,
                               tillstånd = ?, steg = ?, sedd = ?, förfaller = ?
                           WHERE id = ?""",
                        (g["stabilitet"], g["svårighet"], g["tillstånd"],
                         g["steg"], g["sedd"], g["förfaller"], ny_id))
                kort_db.execute(
                    "UPDATE Kort SET antal = antal + ?, fall = fall + ? WHERE id = ?",
                    (g["antal"] or 0, g["fall"] or 0, ny_id))
            kort_db.execute("DELETE FROM Kort WHERE id = ?", (g["id"],))
            flyttade += 1
    if flyttade:
        kort_db.commit()
    return flyttade


def _slå_ihop_stam_med_ord(kort_db: sqlite3.Connection,
                           språk: set[str]) -> int:
    """Flytta historiken från stamkort som ÄR sitt ord till ordkortet.

    ENGÅNGSMIGRATION, samma form som `_slå_ihop_gamla_ändelsekort` och av
    samma skäl. Stamkortet slutade skapas när stammen är identisk med ordet
    (se `härled`), och utan den här funktionen blir de gamla kvar med sin
    historik men utan rad i `Cellkort` — schemalagda, förfallna och omöjliga
    för någon mening att nå. A3:s spökkort, självförvållade.

    HISTORIKEN HÖR HEMMA PÅ ORDKORTET, inte i papperskorgen. De två korten
    ställde samma fråga med samma facit — `il` mot `il` — så deras
    repetitioner är mätningar av samma kunskap under två namn.

    DEN SVAGASTE EVIDENSEN VINNER, som vid ändelsehopslagningen: det
    sammanslagna kortet ärver den lägsta stabiliteten, eftersom kunskapen
    inte kan vara säkrare än den osäkraste mätningen av den.
    """
    flyttade = 0
    for s_ in sorted(språk):
        for g in kort_db.execute(
                """SELECT s.id, s.stabilitet, s.svårighet, s.tillstånd, s.steg,
                          s.sedd, s.förfaller, s.antal, s.fall, o.id AS ord_id
                   FROM Kort s JOIN Kort o
                     ON o.språk = s.språk AND o.koncept = s.koncept
                        AND o.variant IS s.variant
                        AND o.typ = 'ord' AND o.facit = s.facit
                   WHERE s.språk = ? AND s.typ = 'stam'""", (s_,)).fetchall():
            kort_db.execute("UPDATE Repetition SET kort_id = ? WHERE kort_id = ?",
                            (g["ord_id"], g["id"]))
            if g["sedd"] is not None:
                mål = kort_db.execute(
                    "SELECT stabilitet, sedd FROM Kort WHERE id = ?",
                    (g["ord_id"],)).fetchone()
                if (mål["sedd"] is None
                        or (g["stabilitet"] or 0) < (mål["stabilitet"] or 0)):
                    kort_db.execute(
                        """UPDATE Kort SET stabilitet = ?, svårighet = ?,
                               tillstånd = ?, steg = ?, sedd = ?, förfaller = ?
                           WHERE id = ?""",
                        (g["stabilitet"], g["svårighet"], g["tillstånd"],
                         g["steg"], g["sedd"], g["förfaller"], g["ord_id"]))
                kort_db.execute(
                    "UPDATE Kort SET antal = antal + ?, fall = fall + ? WHERE id = ?",
                    (g["antal"] or 0, g["fall"] or 0, g["ord_id"]))
            kort_db.execute("DELETE FROM Kort WHERE id = ?", (g["id"],))
            flyttade += 1
    if flyttade:
        kort_db.commit()
    return flyttade


def befolka(kort_db: sqlite3.Connection, språk_db: sqlite3.Connection,
            språk: set[str], *, nivå: int | None = None,
            cefr: str = "C2", mät: bool = True,
            böjningsceller: dict[str, set[str]] | None = None) -> dict[str, int]:
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
        # BÖJNINGSGRINDEN FÖLJER NIVÅN, och behöver inte anges av anroparen.
        # Anges den ändå gäller den — det är vägen mätverktygen tar när de
        # vill se en annan nivå än kursens.
        if böjningsceller is None:
            from .dimensioner import upplåst_vid
            böjningsceller = {(s_, "Verb"): upplåst_vid(s_, nivå)[1]
                              for s_ in sorted(språk)}
    rader = härled(språk_db, språk, nåbart, böjningsceller)
    före = kort_db.execute("SELECT COUNT(*) FROM Kort").fetchone()[0]
    kort_db.executemany(
        """INSERT OR IGNORE INTO Kort
           (nyckel, typ, språk, koncept, variant, ordklass, klass, cell,
            stamgrupp, egenskap, facit, räckvidd)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", rader)
    kort_db.commit()
    # MIGRATIONEN KÖRS EFTER INSÄTTNINGEN, så efterföljarkorten finns att
    # flytta till. Den är idempotent: har inga cell-nycklade kort kvar gör
    # den ingenting.
    _slå_ihop_gamla_ändelsekort(kort_db, språk)
    _slå_ihop_stam_med_ord(kort_db, språk)
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
         for s, k, v, c, n in _cellkort(språk_db, språk) + _golvkort(språk_db, språk)
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


def exponeringsgräns(meningar_per_dag: float) -> float:
    """Över så många möten per mening slutar schemaläggning ha en spak.

    RÄKNAS, står inte i koden. Ett kort möts `exponering × meningar_per_dag`
    gånger om dagen, och FSRS kortaste meningsfulla intervall ÄR en dag — ett
    kort som möts oftare än så kan aldrig spacas, hur kön än ser ut. Alltså
    är gränsen 1/meningar_per_dag.

    Talet stod tidigare som 0,05 med härledningen i en kommentar, vilket var
    rätt uträknat för 20 meningar om dagen och tyst fel för alla andra.

    OCH SEDAN VAR DET FEL PÅ ETT ANDRA SÄTT: talet hämtades ur
    `Kurs.meningar_per_dag`, en kolumn från tiden FÖRE B4. Julius avskaffade
    den ratten själv, med skälet att den motsäger FSRS — man styr inte NÄR
    aktiva kort ska repeteras, bara hur mycket NYTT som förs in — och bytte
    till minuter. Kolumnen stod kvar på 20 i alla fyra kurserna, satt av
    ingen, medan hans verkliga franska dagar var 5, 10, 11, 13, 18, 21.

    ARGUMENTET ÄR NU MÄTT (`meningstakt`) och inte satt, och det är rätt sort
    av tal här: gränsen ställer en FAKTAFRÅGA — möts kortet mer än en gång om
    dagen? — och inte en styrfråga. Efter B5 finns inget målantal meningar
    alls; antalet är ett utfall, och det utfallet står i `Mening`.

    Att i stället gå via minuterna (`måltakt / kort_per_mening`) mättes och
    förkastades: engelskan fick 170,8 meningar om dagen på 20 minuter,
    eftersom sekunder-per-repetition kommer ur en historik som nästan bara är
    drill. Vägen minuter → meningar går genom ett mått en snedvriden historik
    förstör tyst. Meningsräkningen är rå och har inget sådant led.

    Se GENERATOR.md, "Schemalagda kort mot mätta kort".
    """
    return 1.0 / meningar_per_dag


def sätt_schemalagt(kort_db: sqlite3.Connection,
                    takt: float | None = None, *,
                    språk: str | None = None) -> int:
    """Kort som möts oftare än gränsen mäts men schemaläggs inte.

    Kräver att `exponering` är mätt. Omätta kort lämnas schemalagda — att
    gissa vore att bygga in en tumregel där beslutet säger mätning.

    OCH NU GÄLLER SAMMA REGEL FÖR TAKTEN. `takt` är meningar per övad dag,
    mätt ur `Mening` av `meningstakt`. Saknas den — kursen är aldrig övad —
    lyfts INGENTING ur schemat. Förut kom talet ur `Kurs.meningar_per_dag`,
    som alltid svarade 20 oavsett om användaren gjort en enda mening, så en
    orörd kurs fick kort utlyfta ur schemat på ett antagande om en dag som
    aldrig inträffat.

    ATT LÄMNA KORTET SCHEMALAGT ÄR DEN OFARLIGA SIDAN, och det är därför den
    här vägen får vara trubbig. Ett allestädes närvarande kort som ändå
    schemaläggs betygsätts vid varje möte, växer i stabilitet och förfaller
    aldrig — det löser sig självt. Ett sällsynt kort som felaktigt lyfts UR
    schemat förlorar däremot spacing det behöver, och märks bara om E6:s larm
    hinner fånga det.

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

    Utan `språk` görs nu ETT VARV PER SPRÅK i stället för en skrivning över
    allt: takten är olika i olika kurser, och en gemensam siffra vore samma
    sammanblandning som `MIN(meningar_per_dag)` en gång var.
    """
    from .schemalaggning import meningstakt
    if språk is None:
        return sum(sätt_schemalagt(kort_db, takt, språk=r[0])
                   for r in kort_db.execute(
                       "SELECT DISTINCT språk FROM Kort ORDER BY språk"))
    if takt is None:
        takt = meningstakt(kort_db, språk)
    if takt:
        kort_db.execute(
            "UPDATE Kort SET schemalagt = "
            "(exponering IS NULL OR exponering <= ?) WHERE språk = ?",
            (exponeringsgräns(takt), språk))
    else:
        kort_db.execute("UPDATE Kort SET schemalagt = 1 WHERE språk = ?",
                        (språk,))
    kort_db.commit()
    return kort_db.execute(
        "SELECT COUNT(*) FROM Kort WHERE schemalagt = 0 AND språk = ?",
        (språk,)).fetchone()[0]


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
            # ETT KORT RÄKNAS EN GÅNG PER MENING, inte en gång per uppslag.
            #
            # `exponering` är andelen meningar kortet möts i, alltså ett tal
            # mellan 0 och 1 — och tyskans `system:∅` stod på 1,891. Talet är
            # omöjligt, och orsaken är att flera KÄLLOR pekar på samma kort:
            # `∅` är ändelsen i många celler, och en mening som rör två av dem
            # räknade kortet två gånger. Samma sak för ordkorten, där
            # `set(rörda)` deduplicerar på hela cellnyckeln medan uppslaget
            # bara använder koncept och variant — ett substantiv i två kasus
            # räknades alltså dubbelt.
            #
            # Felet lutar systematiskt åt ETT håll och drabbar just de kort
            # som delas mest, alltså precis dem `exponeringsgräns` ska skilja
            # ut. Det påverkar också införselordningen (B3), som sorterar på
            # samma tal.
            #
            # Mätt: bara ett kort i hela beståndet passerade 1,0, men
            # dubbelräkningen finns i varje delat kort under gränsen också —
            # den syns bara inte lika tydligt.
            träffade: set[int] = set()
            for nyckel in set(rörda):
                träffade.update(karta.get(nyckel, []))
            for _, koncept, variant, _ in set(rörda):
                träffade.update(ordkort.get((koncept, variant), []))
            for nyckel in set(egenskaper):
                träffade.update(egenskapskort.get(nyckel, []))
            for regel in set(ordföljder):
                kid = ordföljdskort.get(regel)
                if kid is not None:
                    träffade.add(kid)
            for kid in träffade:
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
