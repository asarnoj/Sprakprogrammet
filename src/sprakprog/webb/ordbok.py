"""Ordboksvyn — hela paradigmet med kunskapen inlagd i det.

VARFÖR VYN FINNS. Julius, om kortövning: "när det är flera liknande kort
fastnar jag på de i evigheter … sedan tar jag en stund att kolla på de utanför
och faktiskt lära mig och få en överblick." Kön ger en cell i taget; det här
ger hela tabellen på en gång, med det man kan färglagt.

LAYOUTEN HÄRLEDS UR AXLARNA, INTE UR ORDKLASSEN. Varje cell i slot-filen bär
sina koordinater — kasus, numerus, genus, species, grad, person, tempus,
diates. Vilka som VARIERAR för ett givet lexem säger hur tabellen ska se ut:
de två med flest värden blir rader och kolumner, resten delar upp i flera
tabeller. Tyska adjektivets 147 celler blir nio fyra-gånger-fyra-tabeller,
substantivets sex blir en enda, och ingen rad kod känner till skillnaden.
Samma sak gäller de sju språken.

STYRKAN PER CELL ÄR DET SVAGASTE KORTET SOM TÄCKER DEN. En cell bärs normalt
av två kort — ordets stam och klassens ändelse — och man kan formen först när
man kan båda. Att visa vilketdera som brister är hela poängen: "du kan stammen
men inte den här ändelsen" är en annan sak att öva än "du kan inte ordet".
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict

from ..kaikki_mappning.paradigm import ladda_legend, ladda_slot
from ..kort import Schemaläggare

#: Axlarnas namn i gränssnittet, och i vilken ordning de föredras som
#: tabellaxlar. Kasus och numerus först därför att de är de två som oftast
#: varierar tillsammans och som läsaren väntar sig som rader och kolumner.
AXELNAMN = {
    "kasus": "Case", "numerus": "Number", "genus": "Gender",
    "species": "Declension", "grad": "Degree", "person": "Person",
    "tempus": "Tense", "diates": "Voice",
}
#: KONGRUENSAXLAR blir tabellens rader och kolumner, KATEGORIALA blir dess
#: uppdelning i flera tabeller. Skillnaden är grammatisk och inte estetisk:
#: kongruens är vad ordet rättar sig EFTER något annat i satsen, medan tempus,
#: grad och deklinationsklass är egenskaper hos formen själv. Varje grammatikbok
#: gör samma uppdelning — tyska adjektiv som kasus × m/f/n/pl, en tabell per
#: grad och deklination; verb som person × numerus, en tabell per tempus.
#:
#: Uppdelningen gäller alla sju språken och alla ordklasser. Ingen rad kod
#: nedan känner till vilket språk den ritar.
#: Legendens namn är SPRÅKOBEROENDE bitar med SPRÅKBEROENDE betydelse, och
#: att visa dem råa vore vilseledande: genus=3 heter "Alla" och är tyskans
#: NEUTRUM. Betydelserna nedan är avlästa ur datan (adjektivets nominativ
#: singular, 2026-08-15): de 1/2/3 = netter/nette/nettes, sv 1/2/3 =
#: snäll/snällt/snälla, fr 1/2 = gentil/gentille. Tyskans species 1/2/3 =
#: netter/nette/netter, alltså stark/svag/blandad.
GENUSNAMN = {
    "de": {1: "Masc.", 2: "Fem.", 3: "Neut."},
    "sv": {1: "Utrum", 2: "Neutrum", 3: "All genders"},
    "fr": {1: "Masc.", 2: "Fem."}, "es": {1: "Masc.", 2: "Fem."},
    "it": {1: "Masc.", 2: "Fem."},
}
SPECIESNAMN = {
    "de": {1: "Strong", 2: "Weak", 3: "Mixed"},
    "sv": {1: "Indefinite", 2: "Definite", 3: "Definite pl."},
}

KONGRUENS = ("kasus", "person", "numerus", "genus")
KATEGORIALA = ("grad", "species", "tempus", "diates")
FÖREDRAGNA = KONGRUENS + KATEGORIALA


def _etiketter(legend: dict) -> dict[str, dict[int, str]]:
    """Axel → {bitvärde: namn}. Kombinerade värden får ett hopfogat namn.

    En cell kan täcka flera värden på en axel — tyskans `nom_akk_gen_pl` har
    kasus=11, alltså Nom|Ack|Gen, därför att de tre formerna sammanfaller.
    Det är en riktig egenskap hos språket och ska synas som en kolumn, inte
    delas upp i tre.
    """
    ut: dict[str, dict[int, str]] = {}
    for axel, värden in legend.items():
        if axel not in AXELNAMN:
            continue
        vänd = {v: k for k, v in värden.items()}
        ut[axel] = dict(vänd)
        for cell_värde in range(1, 1 << max(4, len(värden))):
            if cell_värde in vänd:
                continue
            delar = [n for v, n in sorted(vänd.items()) if v and cell_värde & v == v]
            if delar and sum({v for v, n in vänd.items() if n in delar}) == cell_värde:
                ut[axel][cell_värde] = "/".join(delar)
    return ut


def _nyckel(cell, axel: tuple[str, ...]) -> tuple:
    return tuple(cell.axlar.get(a) for a in axel)


def _slå_ihop(varierar: list[str], celler) -> list[tuple[str, ...]]:
    """Slå ihop axlar som inte är KORSADE, till en visningsaxel var.

    Tyskans adjektiv har genus i singular och inget genus i plural: cellerna
    är m·sg, f·sg, n·sg och pl, alltså fyra kombinationer där produkten vore
    sex. Axlarna är komplementära, inte korsade, och de fyra kolumnerna
    m/f/n/pl är hur varje grammatikbok skriver tabellen.

    Regeln: slå ihop a och b när b:s DEFINIERADHET är en FUNKTION av a:s
    värde — för varje värde av a är b antingen alltid satt eller aldrig satt,
    och båda fallen förekommer. Genus är satt när numerus är singular och
    osatt när det är plural: en funktion, alltså beroende.

    Att bara fråga "varierar b:s definieradhet bland a:s celler" räcker inte.
    Bland kasus-cellerna varierar genus också — men orsaken är numerus, inte
    kasus, och för ett givet kasus är genus ibland satt och ibland inte. Det
    är just det funktionskravet fångar.

    Prövas bara mellan KONGRUENSAXLAR. Utan den avgränsningen slår regeln
    ihop person med tempus — infinitiv och particip saknar person — och
    verbtabellen faller isär. Det är ingen slump: en kategorial axel som
    saknas i vissa former säger inget om kongruensen.

    Utan hopslagningen blev tyska adjektiv 39 tabeller. Med den blir de nio,
    och nio är hur boken gör det.
    """
    def beroende(a: tuple, b: tuple) -> bool:
        per_värde: dict[tuple, set[bool]] = defaultdict(set)
        for c in celler:
            nyckel_a = _nyckel(c, a)
            if all(v is None for v in nyckel_a):
                continue
            per_värde[nyckel_a].add(any(v is not None for v in _nyckel(c, b)))
        if any(len(v) > 1 for v in per_värde.values()):
            return False                      # inte en funktion
        utfall = {next(iter(v)) for v in per_värde.values()}
        return utfall == {True, False}        # och båda fallen förekommer

    axlar = [(a,) for a in varierar]
    ändrat = True
    while ändrat and len(axlar) > 1:
        ändrat = False
        for i in range(len(axlar)):
            for j in range(i + 1, len(axlar)):
                a, b = axlar[i], axlar[j]
                if not (set(a) <= set(KONGRUENS) and set(b) <= set(KONGRUENS)):
                    continue
                if beroende(a, b) or beroende(b, a):
                    axlar[i] = a + b
                    del axlar[j]
                    ändrat = True
                    break
            if ändrat:
                break
    return axlar


class Ordbok:
    def __init__(self, språk_db: sqlite3.Connection,
                 kort_db: sqlite3.Connection) -> None:
        self.s = språk_db
        self.k = kort_db
        self.schemaläggare = Schemaläggare(kort_db)
        self.legend = ladda_legend()
        self._grund = _etiketter(self.legend)
        self._slot: dict[tuple, object] = {}

    def etiketter_för(self, språk: str) -> dict[str, dict[int, str]]:
        """Axeletiketter med språkets egna namn på genus och deklination."""
        ut = {a: dict(v) for a, v in self._grund.items()}
        for axel, karta in (("genus", GENUSNAMN), ("species", SPECIESNAMN)):
            ut[axel].update(karta.get(språk, {}))
        return ut

    def slot(self, språk: str, ordklass: str):
        if (språk, ordklass) not in self._slot:
            try:
                self._slot[(språk, ordklass)] = ladda_slot(
                    språk, ordklass, legend=self.legend)
            except FileNotFoundError:
                self._slot[(språk, ordklass)] = None
        return self._slot[(språk, ordklass)]

    # ── listan ───────────────────────────────────────────────────────

    def lista(self, språk: str) -> list[dict]:
        """Alla ord i kursen, med hur mycket av dem som sitter.

        Bara koncept som har KORT — alltså de som nivån och CEFR släppt in.
        Ett ord utan kort går inte att möta och hör inte hemma i ordboken
        förrän det gör det (samma regel som styr befolkningen).
        """
        rader = self.k.execute(
            """SELECT koncept, ordklass,
                      COUNT(*) AS kort,
                      SUM(sedd IS NOT NULL) AS sedda,
                      MIN(COALESCE(stabilitet, 0)) AS svagast
               FROM Kort WHERE språk = ? AND koncept IS NOT NULL
               GROUP BY koncept ORDER BY koncept""", (språk,)).fetchall()
        lemman = {r["nyckel"]: r["lemma"] for r in self.s.execute(
            """SELECT k.nyckel, l.lemma FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id WHERE l.språk = ?""",
            (språk,))}
        ordklasser = {r["nyckel"]: r["ordklass"] for r in self.s.execute(
            "SELECT nyckel, ordklass FROM Koncept")}
        ut = []
        for r in rader:
            if r["koncept"] not in lemman:
                continue
            ut.append({
                "koncept": r["koncept"], "lemma": lemman[r["koncept"]],
                "ordklass": ordklasser.get(r["koncept"], r["ordklass"] or "—"),
                "kort": r["kort"], "sedda": r["sedda"] or 0,
                "andel": (r["sedda"] or 0) / r["kort"],
            })
        return ut

    # ── ett ord ──────────────────────────────────────────────────────

    def _kort_per_cell(self, språk: str, koncept: str) -> dict[str, list]:
        per = defaultdict(list)
        for r in self.k.execute(
                """SELECT c.cell, k.* FROM Cellkort c JOIN Kort k ON k.id = c.kort_id
                   WHERE c.språk = ? AND c.koncept = ?""", (språk, koncept)):
            per[r["cell"]].append(r)
        return per

    def ord(self, språk: str, koncept: str) -> dict | None:
        """Ett ords hela paradigm, uppdelat i tabeller, med styrka per cell."""
        rad = self.s.execute(
            """SELECT l.id, l.lemma, k.ordklass, k.nyckel FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id
               WHERE l.språk = ? AND k.nyckel = ?""", (språk, koncept)).fetchone()
        if rad is None:
            return None
        slot = self.slot(språk, rad["ordklass"])
        if slot is None:
            return {"lemma": rad["lemma"], "ordklass": rad["ordklass"],
                    "tabeller": [], "fritt": []}

        self.etiketter = self.etiketter_för(språk)
        former = self._former(rad["id"], slot)
        kort = self._kort_per_cell(språk, koncept)
        celler = [c for c in slot.celler if former.get(c.id)]
        if not celler:
            return {"lemma": rad["lemma"], "ordklass": rad["ordklass"],
                    "tabeller": [], "fritt": []}

        # Vilka axlar varierar? Bara de säger något om ordets böjning.
        värden = {a: {c.axlar.get(a) for c in celler} - {None} for a in AXELNAMN}
        varierar = [a for a in FÖREDRAGNA if len(värden[a]) > 1]
        axlar = _slå_ihop(varierar, celler)
        rad_axel = axlar[0] if axlar else None
        kol_axel = axlar[1] if len(axlar) > 1 else None
        övriga = axlar[2:]

        if rad_axel is None:
            # Ingen axel varierar — ordet har en enda form. Japanska
            # substantiv böjs inte alls, och det är ett riktigt svar och
            # ingen lucka: tabellen har en ruta.
            rad_axel, kol_axel, övriga = (), None, []

        grupper: dict[tuple, list] = defaultdict(list)
        for c in celler:
            grupper[tuple(_nyckel(c, a) for a in övriga)].append(c)

        tabeller = []
        for nyckel, gruppceller in grupper.items():
            tabeller.append(self._tabell(
                gruppceller, rad_axel, kol_axel, övriga, nyckel, former, kort))
        tabeller.sort(key=lambda t: t["ordning"])
        return {"lemma": rad["lemma"], "ordklass": rad["ordklass"],
                "koncept": koncept, "tabeller": tabeller}

    def _etikett(self, axel: tuple[str, ...], värde: tuple) -> str:
        """Etikett för ett axelvärde, sammanslagna axlar medräknade."""
        delar = [self.etiketter.get(a, {}).get(v, "")
                 for a, v in zip(axel, värde) if v is not None]
        return " ".join(d for d in delar if d)

    def _tabell(self, celler, rad_axel, kol_axel, övriga, nyckel, former, kort):
        rubrik = " · ".join(
            e for a, v in zip(övriga, nyckel) if (e := self._etikett(a, v)))
        ordna = lambda v: tuple((x is None, x or 0) for x in v)
        rader = sorted({_nyckel(c, rad_axel) for c in celler}, key=ordna)
        kolumner = (sorted({_nyckel(c, kol_axel) for c in celler}, key=ordna)
                    if kol_axel else [()])
        rutnät = {(_nyckel(c, rad_axel),
                   _nyckel(c, kol_axel) if kol_axel else ()): c for c in celler}
        return {
            "rubrik": rubrik,
            "ordning": ordna(tuple(v for n in nyckel for v in n)),
            "radaxel": " ".join(AXELNAMN.get(a, "") for a in rad_axel),
            "kolaxel": " ".join(AXELNAMN.get(a, "") for a in kol_axel)
                       if kol_axel else "",
            "kolumner": [self._etikett(kol_axel, v) for v in kolumner]
                        if kol_axel else [""],
            "rader": [{
                "etikett": self._etikett(rad_axel, rv),
                "rutor": [self._ruta(rutnät.get((rv, kv)), former, kort)
                          for kv in kolumner],
            } for rv in rader],
        }

    def _ruta(self, cell, former, kort) -> dict | None:
        if cell is None:
            return None
        rader = kort.get(cell.id, [])
        delar = [{"typ": r["typ"], "facit": r["facit"],
                  "r": round(self.schemaläggare.retention(r), 2),
                  "sedd": r["sedd"] is not None} for r in rader]
        # Styrkan är det SVAGASTE kortet, och ett OMÖTT kort är det svagaste
        # som finns. Att bara ta minimum över de mötta vore att låta en cell
        # se stark ut fastän en av dess delar aldrig prövats: "spreche" bärs
        # av stammen sprech och ändelsen -e, och kan inte sitta förrän båda
        # gör det. Det är samma regel som budgeten använder — ett osett kort
        # har ingen retention att mäta — men här ska det synas som en lucka
        # och inte döljas.
        omött = any(not d["sedd"] for d in delar)
        styrka = (0.0 if omött else min(d["r"] for d in delar)) if delar else None
        # DELVIS är ett eget läge och inte en nyans av outforskad: "du kan
        # stammen men inte ändelsen" är något annat att göra än "du kan
        # ingenting här", och det är precis den skillnaden kortmodellen
        # finns för att kunna se.
        return {"cell": cell.id, "form": former.get(cell.id),
                "styrka": styrka,
                "outforskad": omött if delar else False,
                "delvis": bool(delar) and omött and any(d["sedd"] for d in delar),
                "delar": delar, "not": cell.not_kommentar}

    def _former(self, lexem_id: int, slot) -> dict[str, str]:
        from ..generering.granskning import _former_per_cell
        rader = self.s.execute(
            "SELECT * FROM Former WHERE lexem_id = ?", (lexem_id,)).fetchall()
        return _former_per_cell(rader, slot)
