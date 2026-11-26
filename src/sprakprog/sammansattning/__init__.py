"""Sammansättningen — steg 2 i kärnans byggordning (KÄRNAN 6.7 och punkt 9).

Kartan har gått igenom varje del av renderaren för sig och sparat varje väg:
vad den läste, vad den redovisade och vilka delar den anropade. Här fogas
vägarna ihop till hela meningar, i tre steg.

1. VÄGARNA FOGAS IHOP uppifrån. En väg genom `rendera`, och för varje anrop
   den gör en väg genom den anropade delen med samma argument. Delens egna namn
   döps om till meningens: nominalfrasens `nf.bestämdhet` blir
   `m.subjekt.bestämdhet`. Två vägar passar ihop bara om de läste samma fält,
   eller samma egenskap hos samma ord, med samma svar, och om anroparen fick
   den sorts utdata — ingenting, ett ord, en lista av en viss längd — som
   delen gav.

2. ORDEN BINDS. Varje symboliskt koncept får ett lexem vars egenskaper är de
   vägarna läste: ett substantiv i utrum som har bestämd singular. Innehållet
   prövas mot konceptens krav (6.1 punkt 6).

3. MENINGEN RENDERAS PÅ RIKTIGT, och korten räknas ur spåret med
   kortmodellen. Kartan är en övermängd — samband mellan ett ords egenskaper
   följer inte med — så det är renderingen som avgör, också vilka beslut som
   syns.

`meningar` ger meningarna i ordning efter antal ord. `finns` svarar uttömmande
på om det går att bygga en mening som prövar ett kort av bara vissa kort, vilket
nivåerna (steg 4) behöver. Uttömmande går, eftersom ingen del behöver upprepas
mer än en gång längs en gren: satsen i bisatsen i bisatsen kan kortas till
satsen i bisatsen utan att något kort tillkommer. Värdet, budgeten och
entydighetsfiltret hör till sökningen (steg 5) och finns inte här.
"""

from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Iterator

from ..kortmodell import Formtabell, Kort, meningens_kort
from ..rendering import RENDERARE, RenderingsFel, spåra
from ..rendering import spec as S
from ..rendering.karta import FÄLTKLASSER
from ..rendering.restriktioner import TIDSBIT, Validator

#: Händelser som kan bli kort. "del" är ett anrop och "ordföljd" den gamla
#: kärnans logg.
KORTHÄNDELSER = frozenset({"form", "egenskap", "rektion", "regel", "ordning"})

ROT = (("m", "lat:Mening"),)

#: Säger om ett kort får ingå i meningen; None betyder att alla får det.
Tillåten = Callable[[Kort], bool] | None

#: Egenskaper hos ett ord som renderaren kan läsa när ett beslut tvingas fram,
#: och som därför kan göra att samma mening prövar olika kort med olika ord.
EGENSKAPER = ("genus", "reflexiv", "komparation")
KONCEPTEGENSKAPER = ("person", "numerus")


@dataclass(frozen=True, slots=True)
class Träff:
    """En mening som gick att bygga, och korten den prövar."""
    mening: S.Mening
    text: str
    ord: int
    kort: frozenset


def _döp(text: str, bindning: dict) -> str:
    rot, sep, rest = text.partition(".")
    return bindning[rot] + sep + rest


def _döp_nyckel(nyckel, bindning: dict):
    if isinstance(nyckel, str):
        return _döp(nyckel, bindning)
    return (nyckel[0], _döp(nyckel[1], bindning), *nyckel[2:])


def _döp_koncept(koncept, bindning: dict):
    if isinstance(koncept, tuple):
        return ("sym", _döp(koncept[1], bindning))
    return koncept


def _döp_händelse(h: tuple, bindning: dict) -> tuple:
    """Händelsen med meningens namn, utan led och ordnummer."""
    if h[0] == "form":
        return ("form", _döp_koncept(h[2], bindning), h[3])
    if h[0] == "egenskap":
        return ("egenskap", _döp_koncept(h[2], bindning), h[3], h[4])
    if h[0] == "rektion":
        return ("rektion", _döp_koncept(h[2], bindning), h[3], h[4], h[5])
    if h[0] == "regel":
        return ("regel", h[2], h[3])
    return ("ordning", h[2])


def _slå_ihop(villkor: dict, nya: list) -> dict | None:
    """Villkoren tillsammans, eller None om två svar på samma läsning skiljer sig."""
    ut = None
    for nyckel, svar in nya:
        if nyckel in villkor or (ut is not None and nyckel in ut):
            if (ut if ut is not None else villkor)[nyckel] != svar:
                return None
            continue
        if ut is None:
            ut = dict(villkor)
        ut[nyckel] = svar
    return villkor if ut is None else ut


def _sort(utdata) -> set:
    return {"lista" if isinstance(u, tuple) else u for u in utdata}


class Sammansättare:
    """Bygger meningar ur en sparad karta.

    `par` är kursens andra språk. En mening som det språket inte kan uttrycka
    ställs inte (6.1 punkt 4).
    """

    def __init__(self, conn: sqlite3.Connection, karta: dict, par: str | None = None) -> None:
        self.språk = karta["språk"]
        self.renderare = RENDERARE[self.språk](conn)
        self.par = RENDERARE[par](conn) if par else None
        self.u = self.renderare.u
        self.tabell = Formtabell(self.u)
        self.validator = Validator(conn)
        self.conn = conn
        self._rader: dict[str, list] = {}
        self._kandidatcache: dict = {}
        self._signaturer: dict = {}
        self._nåcache: dict = {}
        self._ljudcache: dict = {}

        # del → argumentetiketter → vägar
        self._index: dict = defaultdict(lambda: defaultdict(list))
        self._egna_ord: dict[int, int] = {}
        self._lokala: dict[int, dict] = {}
        self._globala: dict[int, list] = {}
        self._händelser: dict[int, list] = {}
        self._ordningar: dict[int, list] = {}
        self._konstanta: dict[int, list] = {}
        self._orden: dict[int, dict] = {}
        self._anropsnod: dict[int, dict] = {}
        self._noder: dict[int, list] = {}
        self._konstkort: dict[int, list] = {}
        self._klasser: dict[int, list] = {}
        self._klass_möjlig: dict = {}
        for del_, vägar in karta["vägar"].items():
            for väg in vägar:
                self._index[del_][väg.argument].append(väg)
                i = id(väg)
                self._egna_ord[i] = sum(1 for h in väg.händelser if h[0] == "form")
                self._lokala[i] = {k: v for k, v in väg.villkor
                                   if isinstance(k, tuple) and k[0] in ("utdata", "längd")}
                self._globala[i] = [(k, v) for k, v in väg.villkor
                                    if not (isinstance(k, tuple) and k[0] in ("utdata", "längd"))]
                self._händelser[i] = [h for h in väg.händelser if h[0] in KORTHÄNDELSER]
                self._ordningar[i] = [(h[2], h[3], h[4]) for h in väg.händelser
                                      if h[0] == "ordning"]
                self._konstanta[i] = [(h[2], h[3]) for h in väg.händelser
                                      if h[0] == "form" and not isinstance(h[2], tuple)]
                self._orden[i] = dict(getattr(väg, "ord", ()))
                self._anropsnod[i] = {nr: (barn, self._anropsetiketter(arg))
                                      for nr, barn, arg in väg.anrop}
                self._noder[i] = [self._anropsnod[i][nr] for nr, _, _ in väg.anrop]
                self._klasser[i] = [svar for k, svar in väg.villkor
                                    if isinstance(k, tuple) and k[0] == "ordklass"]
        self._vägar = [v for grupper in self._index.values()
                       for vägar in grupper.values() for v in vägar]
        self._räkna_minsta_ord()
        # Kortare vägar först, så att en uttömmande genomgång hittar korta
        # meningar tidigt.
        for grupper in self._index.values():
            for vägar in grupper.values():
                vägar.sort(key=lambda v: self._min_väg[id(v)])

    # ── det minsta antalet ord, för att skära bort det som inte ryms ──

    @staticmethod
    def _anropsetiketter(argument) -> tuple:
        return tuple(sorted((namn, etikett) for namn, etikett, _ in argument))

    def _räkna_minsta_ord(self) -> None:
        """Minsta antal ord varje del och varje väg kan ge, som en fixpunkt.

        Delarna anropar varandra i cykler — satsen i bisatsen — så värdena
        räknas om tills inget sjunker längre.
        """
        minst: dict = defaultdict(lambda: math.inf)
        self._min_väg: dict[int, float] = {}
        ändrat = True
        while ändrat:
            ändrat = False
            for del_, grupper in self._index.items():
                for etiketter, vägar in grupper.items():
                    for väg in vägar:
                        n = self._egna_ord[id(väg)] + sum(
                            minst[(barn, self._anropsetiketter(arg))]
                            for _, barn, arg in väg.anrop)
                        self._min_väg[id(väg)] = n
                        if n < minst[(del_, etiketter)]:
                            minst[(del_, etiketter)] = n
                            ändrat = True
        self._minst = minst

    # ── 1. vägarna fogas ihop ──

    def _nåbarhet(self, mål: Kort | None) -> tuple[set, dict] | None:
        """Vilka delar som kan innehålla målet, och vilka vägar som har det själva.

        En fixpunkt, som för minsta antalet ord: en del kan innehålla målet om en
        av dess vägar har det eller anropar en del som kan innehålla det. Ett
        formkort kan finnas i varje form, så där skär nåbarheten inte bort något.
        """
        if mål is None:
            return None
        if mål not in self._nåcache:
            celler = (self._ljudceller(mål.nyckel[1])
                      if mål.typ == "regel" and mål.nyckel[0] == "ljud" else None)
            målklass = None
            if mål.typ in ("ord", "oregelbunden"):
                rad = self.conn.execute("SELECT ordklass FROM Koncept WHERE nyckel = ?",
                                        (mål.nyckel[0],)).fetchone()
                målklass = rad[0] if rad else None

            def bär(h, klasser: dict) -> bool:
                if mål.typ == "regel" and mål.nyckel[0] == "val":
                    return h[0] == "regel" and (h[2], h[3]) == mål.nyckel[1:]
                if mål.typ == "regel" and mål.nyckel[0] == "ordning":
                    return h[0] == "ordning" and h[2] == mål.nyckel[1]
                if mål.typ == "egenskap":
                    return h[0] == "egenskap" and h[3] == mål.nyckel[1]
                if mål.typ == "rektion":
                    return h[0] == "rektion" and tuple(h[3:5]) == mål.nyckel[1:3]
                if h[0] != "form":
                    return False
                symbolisk = isinstance(h[2], tuple)
                if mål.typ == "ändelse":
                    return h[3] == mål.nyckel[2]
                if mål.typ in ("ord", "oregelbunden"):
                    # En symbolisk form kan bara bära ordet om platsens ordklass är
                    # ordets. Läste vägen inte klassen kan det inte uteslutas.
                    if symbolisk:
                        klass = klasser.get(h[2][1])
                        möjlig = klass is None or klass == målklass
                    else:
                        möjlig = h[2] == mål.nyckel[0]
                    return möjlig and (mål.typ == "ord" or h[3] == mål.nyckel[2])
                return h[3] in celler

            egen = {}
            for v in self._vägar:
                klasser = {k[1]: svar for k, svar in v.villkor
                           if isinstance(k, tuple) and k[0] == "ordklass"}
                egen[id(v)] = any(bär(h, klasser) for h in self._händelser[id(v)])
            når: set = set()
            ändrat = True
            while ändrat:
                ändrat = False
                for del_, grupper in self._index.items():
                    for etiketter, vägar in grupper.items():
                        if (del_, etiketter) in når:
                            continue
                        if any(egen[id(v)] or any((b, self._anropsetiketter(a)) in når
                                                  for _, b, a in v.anrop) for v in vägar):
                            når.add((del_, etiketter))
                            ändrat = True
            self._nåcache[mål] = (når, egen)
        return self._nåcache[mål]

    def _ljudceller(self, regel: str) -> set:
        """Cellerna där ljudregeln finns i något ords form."""
        if regel not in self._ljudcache:
            kort = Kort(self.språk, "regel", ("ljud", regel))
            celler = set()
            for rad in self.conn.execute(
                    """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
                       JOIN Koncept k ON k.id = l.koncept_id WHERE l.språk = ?""",
                    (self.språk,)).fetchall():
                celler.update(c for c, k in self.tabell.former(rad).items() if kort in k)
            self._ljudcache[regel] = celler
        return self._ljudcache[regel]

    def _delen(self, del_: str, etiketter: tuple, bindning: dict, villkor: dict,
               budget: float, tillåten: Tillåten = None, kedja: tuple = (),
               nåbar: tuple | None = None, måste: bool = False) -> Iterator[tuple]:
        """Varje sammansättning av delen med högst `budget` ord.

        Ger (villkor, händelser, ord, utdata, har_målet): villkoren med meningens
        namn, händelserna i hela delträdet, antalet ord, den översta vägens utdata
        och om målet finns i delträdet. En del med samma argument förekommer högst
        två gånger längs en gren (`kedja`). Kort som säkert syns och inte är
        tillåtna skär bort vägen direkt: formerna av bestämda koncept, och
        ordningsregler vars båda led har ord. Med `måste` ger delen bara
        sammansättningar som innehåller målet (`nåbar` ur `_nåbarhet`).
        """
        nod = (del_, etiketter)
        if kedja.count(nod) >= 2 or (måste and nod not in nåbar[0]):
            return
        kedja = kedja + (nod,)
        for väg in self._index[del_].get(etiketter, ()):
            i = id(väg)
            if self._min_väg[i] > budget:
                continue
            egen = nåbar is not None and nåbar[1][i]
            if måste and not egen and not any(n in nåbar[0] for n in self._noder[i]):
                continue
            if tillåten is not None and not (self._konstanta_tillåtna(i, tillåten)
                                             and self._säkra_ordningar_tillåtna(i, tillåten)
                                             and self._klasserna_möjliga(i, tillåten)):
                continue
            nya = _slå_ihop(villkor, [(_döp_nyckel(k, bindning), v)
                                      for k, v in self._globala[i]])
            if nya is None:
                continue
            händelser = [_döp_händelse(h, bindning) for h in self._händelser[i]]
            for v, h, n, har in self._anropen(väg, 0, bindning, nya, händelser,
                                              self._egna_ord[i], budget, tillåten, kedja,
                                              {}, nåbar, måste, egen):
                yield v, h, n, väg.utdata, har

    def _anropen(self, väg, i: int, bindning: dict, villkor: dict, händelser: list,
                 ord: int, budget: float, tillåten: Tillåten, kedja: tuple,
                 antal: dict, nåbar: tuple | None, måste: bool, har: bool) -> Iterator[tuple]:
        if i == len(väg.anrop):
            if (måste and not har) or (tillåten is not None
                                       and not self._ordningar_tillåtna(väg, antal, tillåten)):
                return
            yield villkor, händelser, ord, har
            return
        nr, barn, argument = väg.anrop[i]
        noder = self._noder[id(väg)]
        etiketter = noder[i][1]
        barnbindning = {namn: _döp(ref, bindning) for namn, _, ref in argument
                        if ref is not None}
        resten = sum(self._minst[n] for n in noder[i + 1:])
        lokala = self._lokala[id(väg)]
        # Kan inget senare anrop ge målet måste det här ge det.
        barnet_måste = måste and not har and not any(n in nåbar[0] for n in noder[i + 1:])
        for v, h, n, utdata, barnet_har in self._delen(
                barn, etiketter, barnbindning, villkor, budget - ord - resten, tillåten,
                kedja, nåbar, barnet_måste):
            if not self._utdata_passar(lokala, nr, utdata, n):
                continue
            yield from self._anropen(väg, i + 1, bindning, v, händelser + h, ord + n,
                                     budget, tillåten, kedja, {**antal, nr: n}, nåbar,
                                     måste, har or barnet_har)

    def _konstanta_tillåtna(self, i: int, tillåten: Callable) -> bool:
        if i not in self._konstkort:
            kort = []
            for koncept, cell in self._konstanta[i]:
                try:
                    lexem = self.u.lexem(koncept)
                except RenderingsFel:
                    continue               # flera lemman: avgörs av renderingen
                kort.extend(self.tabell.kort(lexem, cell))
            self._konstkort[i] = kort
        return all(tillåten(k) for k in self._konstkort[i])

    def _säkra_ordningar_tillåtna(self, i: int, tillåten: Callable) -> bool:
        """Ordningsregler som syns vilka delar som än väljs, prövade innan något
        fogas ihop: båda leden har en form ur vägen, eller ett ord från en del
        som alltid ger minst ett ord."""
        orden, noder = self._orden[i], self._anropsnod[i]

        def säkert_ord(led) -> bool:
            for nr in led:
                b = orden.get(nr)
                if b is None:
                    continue
                if b[0] == "form" or (b[0] == "del" and self._minst[noder[b[1]]] >= 1):
                    return True
            return False

        return all(tillåten(Kort(self.språk, "regel", ("ordning", namn)))
                   for namn, före, efter in self._ordningar[i]
                   if säkert_ord(före) and säkert_ord(efter))

    def _klasserna_möjliga(self, i: int, tillåten: Callable) -> bool:
        """Har varje ordklass vägen läser något ord vars ordkort är tillåtet?

        En sluten klass där inget ord är tillåtet — inga pronomen — skär bort
        vägen innan något fogas ihop.
        """
        for klass in self._klasser[i]:
            nyckel = (klass, tillåten)
            if nyckel not in self._klass_möjlig:
                self._klass_möjlig[nyckel] = any(
                    tillåten(Kort(self.språk, "ord", (lexem["nyckel"], lexem["variant"] or "")))
                    for lexem in self._lexemen(klass))
            if not self._klass_möjlig[nyckel]:
                return False
        return True

    def _ordningar_tillåtna(self, väg, antal: dict, tillåten: Callable) -> bool:
        """Har varje ordningsregel vars båda led säkert har ord ett tillåtet kort?

        Ett led har säkert ord om det innehåller en form som slogs upp i vägen,
        eller ett ord från ett anrop vars delträd gav ord. Allt annat avgörs av
        renderingen.
        """
        orden = self._orden[id(väg)]

        def har_ord(led) -> bool:
            for nr in led:
                b = orden.get(nr)
                if b is not None and (b[0] == "form" or antal.get(b[1], 0) > 0):
                    return True
            return False

        return all(tillåten(Kort(self.språk, "regel", ("ordning", namn)))
                   for namn, före, efter in self._ordningar[id(väg)]
                   if har_ord(före) and har_ord(efter))

    @staticmethod
    def _utdata_passar(lokala: dict, nr: int, utdata, n: int) -> bool:
        """Fick anroparen den sorts utdata, och den längd, den räknade med?

        Allt en del slår upp skrivs ut, och det går upp genom delen som returnerar
        det, så en lista är lika lång som delträdets ord.
        """
        sort = lokala.get(("utdata", nr))
        if sort is None or sort not in _sort(utdata):
            return False
        if sort == "none":
            return n == 0
        if sort == "ord":
            return n == 1
        for nyckel, svar in lokala.items():
            if nyckel[0] != "längd" or nyckel[1] != nr:
                continue
            if len(nyckel) == 2 or svar != "längre":
                if n != svar:
                    return False
            elif n < nyckel[2]:
                return False
        return True

    # ── 2. orden binds ──

    def _mening(self, v: dict, rot: str, ordet) -> S.Mening:
        def fält(namn):
            return v.get(f"{rot}.{namn}")

        def enum(namn, typ):
            etikett = fält(namn)
            return {} if etikett is None else {namn: typ(etikett)}

        ut: dict = {"verb": ordet(f"{rot}.verb", ("Mening", "verb")),
                    "subjekt": self._nf(v, f"{rot}.subjekt", ordet)}
        for namn in ("objekt", "io", "jämförelse"):
            if fält(namn) == "NF":
                ut[namn] = self._nf(v, f"{rot}.{namn}", ordet)
        if fält("predikativ") == "adjektiv":
            ut["predikativ"] = ordet(f"{rot}.predikativ", ("Mening", "predikativ"))
        elif fält("predikativ") == "NF":
            ut["predikativ"] = self._nf(v, f"{rot}.predikativ", ordet)
        adverbial = fält("adverbial")
        if adverbial == "adverb":
            ut["adverbial"] = (ordet(f"{rot}.adverbial.0", ("Mening", "adverbial")),)
        elif adverbial == "prepositionsfras":
            ut["adverbial"] = (S.Prepositionsfras(
                ordet(f"{rot}.adverbial.0.preposition", ("Prepositionsfras", "preposition")),
                self._nf(v, f"{rot}.adverbial.0.komplement", ordet)),)
        elif adverbial == "bisats":
            ut["adverbial"] = (self._bisats(v, f"{rot}.adverbial.0", ordet),)
        if fält("komplement") == "verb":
            ut["komplement"] = ordet(f"{rot}.komplement", ("Mening", "komplement"))
        for namn, typ in (("grad", S.Grad), ("diates", S.Diates), ("tid", S.Tidsreferens),
                          ("aspekt", S.Aspekt), ("modus", S.Satsmodus)):
            ut.update(enum(namn, typ))
        for namn in ("fråga", "negerad"):
            ut[namn] = fält(namn) == "True"
        if fält("bisats") == "bisats":
            ut["bisats"] = self._bisats(v, f"{rot}.bisats", ordet)
        fråga_om = fält("fråga_om")
        if fråga_om in S.FRÅGESLOTTAR:
            ut["fråga_om"] = fråga_om
        elif fråga_om == "frågadverb":
            ut["fråga_om"] = ordet(f"{rot}.fråga_om", ("Mening", "fråga_om"))
        return S.Mening(**ut)

    def _nf(self, v: dict, rot: str, ordet) -> S.Nominalfras:
        def fält(namn):
            return v.get(f"{rot}.{namn}")

        ut: dict = {"koncept": ordet(f"{rot}.koncept", ("Nominalfras", "koncept"))}
        for namn, typ in (("bestämdhet", S.Bestämdhet), ("numerus", S.Numerus)):
            if fält(namn) is not None:
                ut[namn] = typ(fält(namn))
        if fält("attribut") == "ett":
            grad = v.get(f"{rot}.attribut.0.grad")
            ut["attribut"] = (S.Attribut(
                ordet(f"{rot}.attribut.0.koncept", ("Attribut", "koncept")),
                S.Grad(grad) if grad is not None else S.Grad.POSITIV),)
        if fält("possessiv") == "symbol":
            ut["possessiv"] = ordet(f"{rot}.possessiv", ("Nominalfras", "possessiv"))
        ut["possessiv_koreferent"] = fält("possessiv_koreferent") == "True"
        if fält("referent") not in (None, "None"):
            ut["referent"] = S.Referentgenus(fält("referent"))
        if fält("frågedeterminant") == "symbol":
            ut["frågedeterminant"] = ordet(f"{rot}.frågedeterminant",
                                           ("Nominalfras", "frågedeterminant"))
        if fält("ägare") == "NF":
            ut["ägare"] = self._nf(v, f"{rot}.ägare", ordet)
        return S.Nominalfras(**ut)

    def _bisats(self, v: dict, rot: str, ordet) -> S.Bisats:
        return S.Bisats(ordet(f"{rot}.subjunktion", ("Bisats", "subjunktion")),
                        self._mening(v, f"{rot}.sats", ordet))

    def _lexemen(self, ordklass: str) -> list:
        if ordklass not in self._rader:
            self._rader[ordklass] = self.conn.execute(
                """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
                   JOIN Koncept k ON k.id = l.koncept_id
                   WHERE l.språk = ? AND k.ordklass = ? ORDER BY l.id""",
                (self.språk, ordklass)).fetchall()
        return self._rader[ordklass]

    def _uppfyller(self, lexem, vad: tuple, svar) -> bool:
        u, nyckel = self.u, lexem["nyckel"]
        sort = vad[0]
        if sort == "har":
            return u.har_form(lexem, vad[1]) == svar
        if sort == "egenskap":
            return u._egenskapsvärde(lexem, vad[1]) == svar
        if sort == "koncept":
            return u.koncept(nyckel, vad[1]) == svar
        if sort == "mänsklig":
            return u.mänsklig(nyckel) == svar
        if sort == "tilltal":
            return u.tilltal(nyckel) == svar
        if sort == "förljud":
            return u.förljud(lexem) == svar
        if sort == "operator":
            return u.operator(lexem) == svar
        if sort == "infinitivmarkör":
            return u.infinitivmarkör(nyckel) == svar
        if sort == "komplementform":
            return u.komplementform(nyckel) == svar
        raise KeyError(vad)

    @staticmethod
    def _celler(text: str, händelser: list) -> tuple:
        return tuple(sorted({h[2] for h in händelser
                             if h[0] == "form" and h[1] == ("sym", text)}))

    def _kandidater(self, text: str, sort: tuple, villkor: dict, händelser: list,
                    tillåten: Tillåten) -> list:
        """Lexemen som kan stå för det symboliska konceptet `text`."""
        klass = villkor.get(("ordklass", text))
        klasser = (klass,) if klass is not None else FÄLTKLASSER[sort]
        krav = tuple(sorted(((k[2:], svar) for k, svar in villkor.items()
                             if isinstance(k, tuple) and k[0] == "lex" and k[1] == text),
                            key=repr))
        celler = self._celler(text, händelser)
        nyckel = (klasser, krav)
        if nyckel not in self._kandidatcache:
            self._kandidatcache[nyckel] = [
                lexem for ordklass in klasser for lexem in self._lexemen(ordklass)
                if all(self._uppfyller(lexem, vad, svar) for vad, svar in krav)]
        kandidater = self._kandidatcache[nyckel]
        if tillåten is not None:
            kandidater = [lexem for lexem in kandidater
                          if all(tillåten(k) for c in celler for k in self.tabell.kort(lexem, c))]
        return kandidater

    def _signatur(self, lexem, celler: tuple) -> tuple:
        """Det som kan få två ord att ge olika kort i samma mening.

        Formkortens mönster i de celler meningen använder, vilka celler ordet har
        och vilka av dem som har samma form, och de egenskaper renderaren läser
        när ett beslut tvingas fram. Två ord med samma signatur ger samma
        mening med samma synliga beslut, så en uttömmande genomgång behöver
        bara pröva det ena.
        """
        nyckel = (lexem["id"], celler)
        if nyckel not in self._signaturer:
            u = self.u
            former = {c: f for c, f in u._celler(lexem).items() if f}
            lika: dict = defaultdict(set)
            for c, f in former.items():
                lika[f].add(c)
            koncept = lexem["nyckel"]
            self._signaturer[nyckel] = (
                tuple(tuple(sorted((k.typ, k.nyckel) for k in self.tabell.kort(lexem, c)
                                   if k.typ in ("ändelse", "regel"))) for c in celler),
                frozenset(frozenset(c) for c in lika.values()),
                tuple(u._egenskapsvärde(lexem, n) if n in ("reflexiv", "komparation")
                      or n in lexem.keys() else None for n in EGENSKAPER
                      if n != "reflexiv" or u.språk == "sv"),
                tuple(u.koncept(koncept, n) for n in KONCEPTEGENSKAPER),
                u.mänsklig(koncept), u.tilltal(koncept),
                u.förljud(lexem) if u.språk in ("en",) else None,
                u.operator(lexem) if u.språk in ("en",) and lexem["ordklass"] == "Verb" else None)
        return self._signaturer[nyckel]

    def _grupper(self, kandidater: list, celler: tuple) -> list[list]:
        grupper: dict = {}
        for lexem in kandidater:
            grupper.setdefault(self._signatur(lexem, celler), []).append(lexem)
        return list(grupper.values())

    def _bär(self, mål: Kort, koncept, lexem, händelser: list) -> bool:
        """Kan ordet på platsen `koncept` — ett lexem, eller en konceptnyckel
        när lexem är None — vara det som prövar målet?"""
        nyckel = lexem["nyckel"] if lexem is not None else koncept
        if mål.typ in ("egenskap", "rektion"):
            sort, namn = (("egenskap", mål.nyckel[1:2]) if mål.typ == "egenskap"
                          else ("rektion", mål.nyckel[1:3]))
            return nyckel == mål.nyckel[0] and any(
                h[0] == sort and h[1] == koncept and tuple(h[2:2 + len(namn)]) == namn
                for h in händelser)
        if lexem is None:
            try:
                lexem = self.u.lexem(koncept)
            except RenderingsFel:
                return True            # flera lemman: kan inte uteslutas här
        return any(mål in self.tabell.kort(lexem, h[2]) for h in händelser
                   if h[0] == "form" and h[1] == koncept)

    def _meningar_ur(self, villkor: dict, händelser: list, tillåten: Tillåten,
                     mål: Kort | None = None, grupperat: bool = False) -> Iterator[S.Mening]:
        """Meningarna ur en sammansättning, ett ordval i taget.

        `grupperat` prövar ett ord per signatur i stället för varje ord.
        """
        platser: dict[str, tuple] = {}

        def spana(text, sort):
            platser.setdefault(text, sort)
            return text

        self._mening(villkor, "m", spana)
        kandidater = {text: self._kandidater(text, sort, villkor, händelser, tillåten)
                      for text, sort in platser.items()}
        if any(not k for k in kandidater.values()):
            return

        # Ett mål som hör till ett ord binds till ett ord som bär det: ett
        # formkort till ord vars form har kortet, en egenskap till sitt ord.
        # Annars prövas hela ordförrådet och de flesta meningar saknar målet.
        urval = [kandidater]
        ordbundet = mål is not None and not (mål.typ == "regel" and mål.nyckel[0] != "ljud")
        if ordbundet and not any(self._bär(mål, h[1], None, händelser) for h in händelser
                                 if h[0] in ("form", "egenskap", "rektion")
                                 and not isinstance(h[1], tuple)):
            urval = []
            for text in platser:
                bärare = [lexem for lexem in kandidater[text]
                          if self._bär(mål, ("sym", text), lexem, händelser)]
                if bärare:
                    urval.append({**kandidater, text: bärare})

        kontroller = self._kontroller(villkor, platser)
        if kontroller is None:
            return
        for kandidatval in urval:
            grupperna = {text: (self._grupper(lista, self._celler(text, händelser))
                                if grupperat else [[lexem] for lexem in lista])
                         for text, lista in kandidatval.items()}
            for bundna in self._bindningar(grupperna, kontroller):
                try:
                    mening = self._mening(villkor, "m", lambda text, _: bundna[text])
                except (TypeError, ValueError):
                    continue
                if self.validator.duger(mening) and not self.validator.valensbrott(mening):
                    yield mening

    def _kontroller(self, villkor: dict, platser: dict) -> list[tuple] | None:
        """Konceptens krav (6.1 punkt 6) som par av platser, prövade så fort
        orden på båda är bundna. None när mallen aldrig kan bli giltig.

        Det är samma krav som `Validator` prövar på den färdiga meningen, som
        fortfarande avgör. Här skär de bara bort ordval tidigt: annars prövas
        varje kombination av verb och substantiv innan det visar sig att inget
        verb har den valens mallen kräver.
        """
        v = self.validator
        ut: list[tuple] = []
        for text in platser:
            if text.split(".")[-1] != "verb":
                continue
            rot = text[:-len(".verb")]

            def fält(namn, rot=rot):
                return villkor.get(f"{rot}.{namn}")

            bisats = fält("bisats") == "bisats"
            if bisats and fält("objekt") == "NF":
                return None
            fyllda = frozenset(s for s in ("objekt", "io", "predikativ", "komplement")
                               if fält(s) not in (None, "None")) | (
                frozenset({"objekt"}) if bisats else frozenset())

            def ram(b, text=text, fyllda=fyllda, bisats=bisats):
                verb = b[text]
                valens = v.valens(verb)
                if valens is not None:
                    slottar = v.mönsterslottar(verb)
                    if fyllda not in {(r & slottar) | ({"komplement"} & slottar)
                                      for bit, r in v.RAMAR.items() if valens & bit}:
                        return False
                return not bisats or v.tillåter_bisats(verb)

            ut.append(((text,), ram))
            passiv = fält("diates") not in (None, S.Diates.AKTIV.value)
            led = [s for s in ("subjekt", "objekt", "io")
                   if s == "subjekt" or fält(s) == "NF"]
            for slot in led:
                nf = f"{rot}.{slot}.koncept"
                if nf not in platser:
                    continue

                def semantik(b, text=text, nf=nf, slot=slot, passiv=passiv):
                    krav = v.krav_för(b[text])
                    if passiv and "objekt" in krav:
                        krav = {**krav, "subjekt": krav["objekt"]}
                    return slot not in krav or v._uppfyller(v.semantik(b[nf]), krav[slot])

                ut.append(((text, nf), semantik))
            for i, a in enumerate(led):
                for c in led[i + 1:]:
                    pa, pc = f"{rot}.{a}.koncept", f"{rot}.{c}.koncept"
                    if pa in platser and pc in platser:
                        ut.append(((pa, pc), lambda b, pa=pa, pc=pc: (
                            b[pa] != b[pc] or v.person(b[pa]) not in (1, 2))))
            adverb = f"{rot}.adverbial.0"
            if adverb in platser:
                bit = TIDSBIT[S.Tidsreferens(fält("tid") or S.Tidsreferens.NUTID.value)]
                ut.append(((adverb,), lambda b, adverb=adverb, bit=bit: (
                    (krav := v.tempuskrav(b[adverb])) is None or bool(krav & bit))))
        for text in platser:
            if text.endswith(".attribut.0.koncept"):
                huvud = text[:-len(".attribut.0.koncept")] + ".koncept"
                ut.append(((text, huvud), lambda b, text=text, huvud=huvud: (
                    not (alt := v.attributkrav(b[text]))
                    or v._uppfyller(v.semantik(b[huvud]), alt))))
        return ut

    @staticmethod
    def _bindningar(grupperna: dict, kontroller: list) -> Iterator[dict]:
        """Varje val av ord som klarar kontrollerna, med bakåtspårning.

        Varje plats har grupper av ord. Ur varje grupp används det första ord som
        leder till en hel mening. Verben binds först, eftersom de flesta krav utgår
        från dem; sedan frashuvudena och sist resten.
        """
        ordning = sorted(grupperna, key=lambda t: (
            0 if t.split(".")[-1] == "verb" else 1 if t.endswith(".koncept") else 2,
            len(grupperna[t])))
        plats = {t: i for i, t in enumerate(ordning)}
        per_steg: dict[int, list] = defaultdict(list)
        for behöver, prov in kontroller:
            if all(p in plats for p in behöver):
                per_steg[max(plats[p] for p in behöver)].append(prov)
        bundna: dict = {}

        def steg(i: int) -> Iterator[dict]:
            if i == len(ordning):
                yield dict(bundna)
                return
            text = ordning[i]
            for grupp in grupperna[text]:
                for lexem in grupp:
                    bundna[text] = lexem["nyckel"]
                    if not all(prov(bundna) for prov in per_steg[i]):
                        continue
                    fann = False
                    for resultat in steg(i + 1):
                        fann = True
                        yield resultat
                    if fann:
                        break
            bundna.pop(text, None)

        yield from steg(0)

    # ── 3. meningen renderas ──

    def _pröva(self, mening: S.Mening, mål: Kort | None,
               tillåten: Tillåten, ord: int) -> Träff | None:
        try:
            ut = spåra(self.renderare, mening)
            if self.par is not None:
                self.par.rendera(mening)
        except RenderingsFel:
            return None
        kort = frozenset(k for k, _ in meningens_kort(self.tabell, ut))
        if mål is not None and mål not in kort:
            return None
        if tillåten is not None and not all(tillåten(k) for k in kort):
            return None
        return Träff(mening, ut.text, len(ut.ord), kort)

    @staticmethod
    def _kan_innehålla(händelser: list, mål: Kort) -> bool:
        """Kan en mening ur mallen pröva målet? Bara det som syns i händelserna."""
        if mål.typ == "regel" and mål.nyckel[0] == "val":
            return ("regel", mål.nyckel[1], mål.nyckel[2]) in händelser
        if mål.typ == "regel" and mål.nyckel[0] == "ordning":
            return ("ordning", mål.nyckel[1]) in händelser
        if mål.typ == "egenskap":
            return any(h[0] == "egenskap" and h[2] == mål.nyckel[1] for h in händelser)
        if mål.typ == "rektion":
            return any(h[0] == "rektion" and h[2:4] == mål.nyckel[1:3] for h in händelser)
        return any(h[0] == "form" for h in händelser)

    def meningar(self, mål: Kort | None = None, tillåten: Tillåten = None, *,
                 högst_ord: int, per_mall: int | None = None) -> Iterator[Träff]:
        """Giltiga meningar som prövar `mål`, av kort som `tillåten` godtar.

        Kommer i ordning efter antal ord, upp till `högst_ord`. `per_mall` begränsar
        hur många ordval som prövas för varje sammansättning av vägar; None prövar
        alla.
        """
        sedda: set = set()
        # Två specar som ger samma mening med samma kort är samma mening här.
        visade: set = set()
        nåbar = self._nåbarhet(mål)
        for n in range(1, högst_ord + 1):
            for villkor, händelser, ord, _, _ in self._delen(
                    "rendera", ROT, {"m": "m"}, {}, n, tillåten, (), nåbar, nåbar is not None):
                if ord != n or (mål is not None and not self._kan_innehålla(händelser, mål)):
                    continue
                träffar = 0
                for mening in self._meningar_ur(villkor, händelser, tillåten, mål):
                    if mening in sedda:
                        continue
                    sedda.add(mening)
                    träff = self._pröva(mening, mål, tillåten, ord)
                    if träff is None or (träff.text, träff.kort) in visade:
                        continue
                    visade.add((träff.text, träff.kort))
                    yield träff
                    träffar += 1
                    if per_mall is not None and träffar >= per_mall:
                        break

    def finns(self, mål: Kort, tillåten: Tillåten) -> Träff | None:
        """En giltig mening som prövar `mål` av kort som `tillåten` godtar, eller None.

        Uttömmande: varje sammansättning där ingen del upprepas mer än en gång
        längs en gren, och ett ord per signatur på varje plats. None betyder
        alltså att ingen sådan mening finns.
        """
        sedda: set = set()
        nåbar = self._nåbarhet(mål)
        for villkor, händelser, ord, _, _ in self._delen(
                "rendera", ROT, {"m": "m"}, {}, math.inf, tillåten, (), nåbar, True):
            if not self._kan_innehålla(händelser, mål):
                continue
            for mening in self._meningar_ur(villkor, händelser, tillåten, mål, grupperat=True):
                if mening in sedda:
                    continue
                sedda.add(mening)
                träff = self._pröva(mening, mål, tillåten, ord)
                if träff is not None:
                    return träff
        return None
