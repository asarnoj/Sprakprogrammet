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

En mening som faller på ett förbjudet val lämnar ett bevis efter sig
(`forklaring.py`): den del av sammansättningen där valet syns, och vad orden och
fälten där måste vara. Varje senare sammansättning och ordval som beviset täcker
hoppas över, också i senare frågor där samma kort är förbjudet.
"""

from __future__ import annotations

import itertools
import math
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterator

from ..kortmodell import Formtabell, Kort, meningens_kort
from ..rendering import RENDERARE, RenderingsFel, spåra
from ..rendering import spec as S
from ..rendering.karta import FÄLTKLASSER
from ..rendering.restriktioner import TIDSBIT, Validator
from .forklaring import (Bevisfel, Nod, absolut, bevisa, bevisa_osynligt,
                         uppfyller)

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


#: Namn som `Sammansättare._verben_möjliga` läser: verbet, satsens ramfält,
#: diatesen och subjektets koncept.
_VERBNAMN = ("verb", "bisats", "objekt", "io", "predikativ", "komplement", "diates",
             "subjekt.koncept")


def _rör_verb(text) -> bool:
    return isinstance(text, str) and any(text == n or text.endswith("." + n)
                                         for n in _VERBNAMN)


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
        self._nivåtabell: dict[str, str] = {}
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
        self._verbläsning: dict[int, bool] = {}
        # Vägens villkor och händelser med meningens namn, per väg och plats, och
        # vägarnas prov mot de tillåtna korten, per fråga.
        self._döpcache: dict = {}
        self._vägar_för: Tillåten = None
        self._vägar_tillåtna: dict[int, bool] = {}
        # Vad delar gav, per fråga: (minnesnyckel, projektion) → utfallen. Ett
        # sammanhang sparas när det kommer för andra gången, ett tomt direkt.
        self._minne_för: Tillåten = None
        self._minne_bevis = 0
        self._minne: dict = {}
        self._sedda: set = set()
        # Förklaringarna (`forklaring.py`): delens nyckel → bevis.
        self._bevis: dict[int, list] = defaultdict(list)
        self._bevismängd: set = set()
        self._obevisbara: set = set()
        self._atomcache: dict = {}
        self._nodnycklar: dict = {}
        self._filtrerat_för: Tillåten = None
        self._filtrerat: dict = {}
        self._klasser_per_lista: dict = {}
        self._ram_möjlig: dict = {}
        self._ramcache: dict = {}
        self._ramar: dict = {}
        self._semantik_möjlig: dict = {}
        self._provcache: dict = {}
        self._gallringar: dict = {}
        self._bärarcache: dict = {}
        #: Prövas varje förutsägelse mot renderingen, i stället för att hoppas över?
        self.kontroll = False
        #: Frågans mål, som bevisen om osynlighet gäller.
        self._mål: Kort | None = None
        self._nytt_bevis = False
        self.statistik: Counter = Counter()
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
                self._verbläsning[i] = self._läser_verb(väg)
        self._vägar = [v for grupper in self._index.values()
                       for vägar in grupper.values() for v in vägar]
        self._räkna_minsta_ord()
        self._räkna_delarnas_räckvidd()
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
        # En del ger detsamma igen när allt den kan läsa är lika: samma argument,
        # samma kedja och samma villkor under argumenten (`_projektion`). De
        # villkor den lägger till har namn under argumenten och kan inte krocka
        # med anroparens. Minnet töms när ett nytt bevis lärs (`_minnesnyckel`).
        minne = self._minnesnyckel(nod, bindning, budget, tillåten, kedja, måste)
        samlade = None
        if minne is not None:
            minne = (minne, self._projektion(bindning, villkor, nod))
            if minne in self._minne:
                self.statistik["delar ur minnet"] += 1
                for tillägg, h, n, utdata, har, barnet in self._minne[minne]:
                    v = villkor
                    if tillägg:
                        v = dict(villkor)
                        v.update(tillägg)
                    yield v, h, n, utdata, har, barnet
                return
            if minne in self._sedda:
                samlade = []
            self._sedda.add(minne)
        gav = False
        kedja = kedja + (nod,)
        for väg in self._index[del_].get(etiketter, ()):
            i = id(väg)
            if self._min_väg[i] > budget:
                continue
            # En väg som anropar en del som redan står två gånger längs grenen
            # blir aldrig klar, så dess övriga anrop behöver inte gås igenom.
            if any(kedja.count(n) >= 2 for n in self._noder[i]):
                continue
            egen = nåbar is not None and nåbar[1][i]
            if måste and not egen and not any(n in nåbar[0] for n in self._noder[i]):
                continue
            if tillåten is not None and not self._vägen_tillåten(i, tillåten):
                continue
            globala, händelser = self._döpt(i, bindning)
            nya = _slå_ihop(villkor, globala)
            if nya is None:
                continue
            if self._verbläsning[i] and not self._verben_möjliga(nya, händelser, tillåten):
                continue
            for v, h, n, har, barn, väntande in self._anropen(
                    väg, 0, bindning, nya, händelser, self._egna_ord[i], budget, tillåten,
                    kedja, {}, nåbar, måste, egen, (), frozenset()):
                nod = self._nod(väg, bindning, barn)
                nod.ord = n
                # En ändrad längd som delarna under lämnade och den här delen
                # godtog når roten: meningen faller.
                bevisad = del_ == "rendera" and bool(väntande)
                # Annars förs den vidare om delen lämnar en lista.
                upp = (väntande if all(isinstance(u, tuple) for u in väg.utdata)
                       else frozenset())
                if tillåten is not None and nod.nyckel in self._bevis:
                    bevis = self._aktiva(nod, v, tillåten, fullständig=False)
                    lika = [b for b in bevis if not b.ändring]
                    bevisad = bevisad or bool(lika) and self._täckt(
                        nod, v, h, tillåten, False, lika)
                    for ändring in {b.ändring for b in bevis if b.ändring}:
                        if self._täckt(nod, v, h, tillåten, False,
                                       [b for b in bevis if b.ändring == ändring]):
                            upp = upp | {ändring}
                if bevisad:
                    self.statistik["delar bevisade"] += 1
                    if not self.kontroll:
                        continue
                    nod.täckt = True
                nod.väntande = upp
                gav = True
                if samlade is not None:
                    samlade.append(({k: x for k, x in v.items() if k not in villkor},
                                    h, n, väg.utdata, har, nod))
                yield v, h, n, väg.utdata, har, nod
        if minne is not None and (samlade is not None or not gav):
            self._minne[minne] = samlade or []

    def _anropen(self, väg, i: int, bindning: dict, villkor: dict, händelser: list,
                 ord: int, budget: float, tillåten: Tillåten, kedja: tuple,
                 antal: dict, nåbar: tuple | None, måste: bool, har: bool,
                 noderna: tuple, väntande: frozenset) -> Iterator[tuple]:
        if i == len(väg.anrop):
            if (måste and not har) or (tillåten is not None
                                       and not self._ordningar_tillåtna(väg, antal, tillåten)):
                return
            yield villkor, händelser, ord, har, noderna, väntande
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
        for v, h, n, utdata, barnet_har, nod in self._delen(
                barn, etiketter, barnbindning, villkor, budget - ord - resten, tillåten,
                kedja, nåbar, barnet_måste):
            if not self._utdata_passar(lokala, nr, utdata, n):
                continue
            if ((nod.verb or self._rör_subjekt(nod))
                    and not self._verben_möjliga(v, händelser + h, tillåten)):
                continue
            # Delen kan ha fått ett bevis efter att den byggdes: samma del
            # återanvänds i tusentals sammansättningar, och anroparen är den
            # som bygger vidare på den.
            if self._bevisad(nod, v, händelser + h, tillåten):
                self.statistik["delar bevisade"] += 1
                if not self.kontroll:
                    continue
                nod.täckt = True
            godtagna = frozenset(ä for ä in nod.väntande
                                 if self._längden_passar(lokala, nr, n + ä))
            yield from self._anropen(väg, i + 1, bindning, v, händelser + h, ord + n,
                                     budget, tillåten, kedja, {**antal, nr: n}, nåbar,
                                     måste, har or barnet_har, noderna + (nod,),
                                     väntande | godtagna)

    # ── förklaringarna (forklaring.py) ──

    def _nod(self, väg, bindning: dict, barn: tuple) -> Nod:
        nyckel = self._nodnycklar.setdefault((id(väg), tuple(b.nyckel for b in barn)),
                                             len(self._nodnycklar))
        nod = Nod(väg, bindning, barn, nyckel)
        nod.verb = self._verbläsning[id(väg)] or any(b.verb for b in barn)
        return nod

    def _läser_verb(self, väg) -> bool:
        """Kan vägen ändra svaret från `_verben_möjliga`?

        Svaret beror på satsens fält i `RAMFÄLT`, på vad som läses om verbet och
        på verbets former. En väg som inte rör något av det lämnar svaret som
        det var, så frågan behöver inte ställas om efter den. Namnen prövas som
        vägen själv har dem, också ett argument som heter `verb`, så att hellre
        för många vägar räknas än för få.
        """
        for k, _ in väg.villkor:
            if _rör_verb(k) or (isinstance(k, tuple) and len(k) > 1 and _rör_verb(k[1])):
                return True
        return any(h[0] == "form" and isinstance(h[2], tuple) and _rör_verb(h[2][1])
                   for h in väg.händelser)

    def _räkna_delarnas_räckvidd(self) -> None:
        """Vilka delar anropar andra, och vilka kan fråga `_verben_möjliga` — som
        en fixpunkt, eftersom delarna anropar varandra i cykler."""
        self._delar_med_anrop = {(d, e) for d, grupper in self._index.items()
                                 for e, vägar in grupper.items() if any(v.anrop for v in vägar)}
        self._verbdelar: set = set()
        ändrat = True
        while ändrat:
            ändrat = False
            for d, grupper in self._index.items():
                for e, vägar in grupper.items():
                    if (d, e) not in self._verbdelar and any(
                            self._verbläsning[id(v)]
                            or any((b, self._anropsetiketter(a)) in self._verbdelar
                                   for _, b, a in v.anrop)
                            for v in vägar):
                        self._verbdelar.add((d, e))
                        ändrat = True

    def _projektion(self, bindning: dict, villkor: dict, nod: tuple) -> frozenset:
        """Det i villkoren som delen och delarna under den kan läsa.

        Delen läser meningen bara genom sina argument, så dess villkor, dess
        platsers ord och dess fält har namn under argumentens namn i meningen.
        Kan delen fråga `_verben_möjliga` läser den också satsernas ramfält och
        verb, var de än står.
        """
        prefix = tuple(bindning.values())
        verb = nod in self._verbdelar
        ut = []
        for k, v in villkor.items():
            text = k if isinstance(k, str) else (k[1] if len(k) > 1 else None)
            if not isinstance(text, str):
                continue
            if (verb and _rör_verb(text)) or any(text == p or text.startswith(p + ".")
                                                 for p in prefix):
                ut.append((k, v))
        return frozenset(ut)

    def _minnesnyckel(self, nod: tuple, bindning: dict, budget: float,
                      tillåten: Tillåten, kedja: tuple, måste: bool) -> tuple | None:
        """Nyckeln för minnet av vad delar gav, eller None för en del utan anrop,
        som är billigare att gå igenom än att minnas."""
        if nod not in self._delar_med_anrop:
            return None
        # Minnet gäller för en fråga och så länge inga nya bevis lärts: ett bevis
        # som kommit till sedan dess ska få skära bort det som minnet annars gav.
        if tillåten is not self._minne_för or len(self._bevismängd) != self._minne_bevis:
            self._minne_för, self._minne, self._sedda = tillåten, {}, set()
            self._minne_bevis = len(self._bevismängd)
        return (nod, tuple(bindning.items()), budget, måste, kedja)

    def _döpt(self, i: int, bindning: dict) -> tuple[list, list]:
        """Vägens villkor och händelser med meningens namn. Listorna delas och
        får inte ändras."""
        nyckel = (i, tuple(bindning.items()))
        if nyckel not in self._döpcache:
            self._döpcache[nyckel] = (
                [(_döp_nyckel(k, bindning), v) for k, v in self._globala[i]],
                [_döp_händelse(h, bindning) for h in self._händelser[i]])
        return self._döpcache[nyckel]

    def _vägen_tillåten(self, i: int, tillåten: Callable) -> bool:
        """Vägens egna prov mot de tillåtna korten, som bara beror på vägen."""
        if tillåten is not self._vägar_för:
            self._vägar_för, self._vägar_tillåtna = tillåten, {}
        if i not in self._vägar_tillåtna:
            self._vägar_tillåtna[i] = (self._konstanta_tillåtna(i, tillåten)
                                       and self._säkra_ordningar_tillåtna(i, tillåten)
                                       and self._klasserna_möjliga(i, tillåten)
                                       and self._platserna_möjliga(i, tillåten))
        return self._vägar_tillåtna[i]

    def _platserna_möjliga(self, i: int, tillåten: Callable) -> bool:
        """Finns ett tillåtet ord för varje plats där vägen själv slår upp en form?

        Orden räknas med vägens egna läsningar och celler. Senare delar kan bara
        lägga till läsningar och celler, och alltså göra orden färre, så en tom
        plats här blir aldrig fylld. Utan den här frågan byggs en bisats färdig i
        varje sammansättning vars genitivägare kräver en ändelse som inte är
        tillåten: 5,4 miljoner sammansättningar i en fråga om engelskans «why»
        (mätt 2026-09-15).
        """
        villkor = dict(self._globala[i])
        former = [("form", h[2], h[3]) for h in self._händelser[i] if h[0] == "form"]
        for _, koncept, _ in former:
            if (isinstance(koncept, tuple) and villkor.get(("ordklass", koncept[1])) is not None
                    and not self._kandidater(koncept[1], None, villkor, former, tillåten)):
                return False
        return True

    def _aktiva(self, nod: Nod, villkor: dict, tillåten: Callable,
                fullständig: bool) -> list:
        """Delens bevis för förbjudna kort, där fälten stämmer med meningen.

        Ett fält som ännu inte är satt kan sättas av en senare del, så innan
        sammansättningen är `fullständig` avgör det inget.
        """
        ut = []
        for b in self._bevis.get(nod.nyckel, ()):
            if b.syns:
                if tillåten(b.kort):
                    continue        # kortet är tillåtet: att det syns gör inget
            elif b.kort != self._mål:
                continue            # osynligheten gäller bara frågans eget mål
            for rel, etikett in b.fält:
                namn = absolut(nod.bindning, rel)
                if namn is None or (villkor[namn] != etikett if namn in villkor
                                    else not (fullständig and etikett is None)):
                    break
            else:
                if all(absolut(nod.bindning, rel) is not None for rel, _, _ in b.platser):
                    ut.append(b)
        return ut

    def _bevisad(self, nod: Nod, villkor: dict, händelser: list,
                 tillåten: Tillåten) -> bool:
        """Faller varje mening med delen, med de bevis som finns nu?"""
        if tillåten is None or nod.nyckel not in self._bevis:
            return False
        bevis = [b for b in self._aktiva(nod, villkor, tillåten, fullständig=False)
                 if not b.ändring]
        return bool(bevis) and self._täckt(nod, villkor, händelser, tillåten, False, bevis)

    def _täckt(self, nod: Nod, villkor: dict, händelser: list, tillåten: Callable,
               fullständig: bool, bevis: list | None = None) -> bool:
        """Faller varje mening med delen, vilka ord som än står på dess platser?

        Orden som kan stå på en plats delas upp efter vilka av bevisens villkor
        de uppfyller, och varje kombination av grupper måste uppfylla ett bevis.
        Utan `bevis` används delens alla aktiva bevis.
        """
        if bevis is None:
            bevis = self._aktiva(nod, villkor, tillåten, fullständig)
        if not bevis:
            return False
        atomer: dict = defaultdict(dict)
        sorter: dict = {}
        for b in bevis:
            for rel, sort, villkoren in b.platser:
                text = absolut(nod.bindning, rel)
                sorter[text] = sort
                for atom in villkoren:
                    atomer[text].setdefault(atom, len(atomer[text]))
        grupper = {}
        for text, index in atomer.items():
            lista = self._kandidater(text, sorter[text], villkor, händelser, tillåten)
            if not lista:
                return True            # inget ord kan stå där: ingen mening alls
            nyckel = (id(lista), tuple(index))
            if nyckel not in self._klasser_per_lista:
                self._klasser_per_lista[nyckel] = (lista, {
                    tuple(uppfyller(self, atom, lexem["nyckel"]) for atom in index)
                    for lexem in lista})
            grupper[text] = self._klasser_per_lista[nyckel][1]
        texter = list(grupper)
        for val in itertools.product(*(grupper[t] for t in texter)):
            svar = dict(zip(texter, val))
            if not any(all(svar[text][atomer[text][atom]]
                           for rel, _, villkoren in b.platser
                           for text in (absolut(nod.bindning, rel),)
                           for atom in villkoren)
                       for b in bevis):
                return False
        return True

    def _giltiga(self, rot: Nod, villkor: dict, tillåten: Callable) -> list[tuple]:
        """Varje del i en färdig sammansättning med bevis som gäller där: (del, bevis).

        Ett bevis som ändrar delens längd gäller bara om varje del ovanför
        godtar den nya längden.
        """
        ut: list[tuple] = []

        def gå(nod: Nod, kedja: tuple) -> None:
            if nod.nyckel in self._bevis:
                bevis = [b for b in self._aktiva(nod, villkor, tillåten, fullständig=True)
                         if not b.ändring or self._godtas(nod, kedja, b.ändring)]
                if bevis:
                    ut.append((nod, bevis))
            for (nr, _, _), barn in zip(nod.väg.anrop, nod.barn):
                gå(barn, kedja + ((nod, nr),))

        gå(rot, ())
        return ut

    def _godtas(self, nod: Nod, kedja: tuple, ändring: int) -> bool:
        """Godtar varje del ovanför att delens lista blir `ändring` ord längre?

        `kedja` är (del, anropets nummer) från roten ner till delens anropare.
        En del som godtar längden följer samma väg, och dess egen lista ändras
        lika mycket — men bara en lista har en längd att föra vidare.
        """
        barn = nod
        for steg, (förälder, nr) in enumerate(reversed(kedja)):
            if steg and not all(isinstance(u, tuple) for u in barn.väg.utdata):
                return False
            if not self._längden_passar(self._lokala[id(förälder.väg)], nr,
                                        barn.ord + ändring):
                return False
            barn = förälder
        return True

    def _någon_täckt(self, giltiga: list, villkor: dict, händelser: list,
                     tillåten: Callable) -> bool:
        return any(self._täckt(nod, villkor, händelser, tillåten, True, bevis)
                   for nod, bevis in giltiga)

    def _avfärdad(self, giltiga: list, villkor: dict, bundna: dict,
                  tillåten: Callable) -> bool:
        """Uppfyller ordvalet ett bevis? Då faller meningen utan att renderas."""
        for nod, bevis in giltiga:
            for b in bevis:
                if all((nyckel := bundna.get(absolut(nod.bindning, rel))) is not None
                       and all(uppfyller(self, atom, nyckel) for atom in villkoren)
                       for rel, _, villkoren in b.platser):
                    return True
        return False

    def _lär(self, rot: Nod, villkor: dict, bundna: dict, platser: dict, ut,
             kort: frozenset, tillåten: Callable, mål: Kort | None = None) -> bool:
        """Ett bevis ur en mening som inte dög. True om det är nytt.

        Föll meningen på ett förbjudet val bevisas att valet syns; syns inte
        målet bevisas i stället att det inte kan synas här. Ett bevis räcker för
        att meningen ska falla, så sökningen slutar vid det första. En
        sammansättning där ett kort inte gick att bevisa prövas inte igen för
        samma kort.
        """
        if mål is not None and mål not in kort and (rot.nyckel, mål, False) not in self._obevisbara:
            bevis = bevisa_osynligt(self, rot, villkor, bundna, platser, ut, mål)
            if bevis is None:
                self._obevisbara.add((rot.nyckel, mål, False))
            elif bevis not in self._bevismängd:
                self._bevismängd.add(bevis)
                self._bevis[bevis.nod].append(bevis)
                self.statistik["bevis: syns inte"] += 1
                return True
        for k in sorted(kort, key=str):
            if (tillåten(k) or k.typ != "regel" or k.nyckel[0] != "val"
                    or (rot.nyckel, k, True) in self._obevisbara):
                continue
            bevis = bevisa(self, rot, villkor, bundna, platser, ut, k)
            if bevis is None:
                self._obevisbara.add((rot.nyckel, k, True))
                continue
            if bevis in self._bevismängd:
                return False
            self._bevismängd.add(bevis)
            self._bevis[bevis.nod].append(bevis)
            self.statistik["bevis"] += 1
            return True
        return False

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
        return Sammansättare._längden_passar(lokala, nr, n)

    @staticmethod
    def _längden_passar(lokala: dict, nr: int, n: int) -> bool:
        """Godtar anroparen en lista med `n` ord från anropet `nr`?"""
        if lokala.get(("utdata", nr)) != "lista":
            return False
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
        subjunktion = (ordet(f"{rot}.subjunktion", ("Bisats", "subjunktion"))
                       if v.get(f"{rot}.subjunktion") == "symbol" else None)
        return S.Bisats(subjunktion, self._mening(v, f"{rot}.sats", ordet))

    #: Ordens ordning tills frekvenserna finns (5.6): CEFR-nivån i databasen,
    #: och sedan konceptets nyckel, så att ordningen blir densamma varje gång.
    NIVÅER = ("A1", "A2", "B1")

    def _nivå(self, koncept: str) -> int:
        """Hur grundläggande ordet är. Ett ord utan nivå kommer sist."""
        if not self._nivåtabell:
            self._nivåtabell = {r[0]: r[1] for r in self.conn.execute(
                "SELECT nyckel, nivå FROM Koncept")}
        nivå = self._nivåtabell.get(koncept)
        return self.NIVÅER.index(nivå) if nivå in self.NIVÅER else len(self.NIVÅER)

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

    @staticmethod
    def _lexkrav(villkor: dict) -> dict:
        """Läsningarna av varje plats ord, samlade i ett svep över villkoren."""
        ut: dict = defaultdict(list)
        for k, svar in villkor.items():
            if isinstance(k, tuple) and k[0] == "lex":
                ut[k[1]].append((k[2:], svar))
        return ut

    def _kandidater(self, text: str, sort: tuple, villkor: dict, händelser: list,
                    tillåten: Tillåten, lexkrav: dict | None = None) -> list:
        """Lexemen som kan stå för det symboliska konceptet `text`. `lexkrav` är
        `_lexkrav(villkor)`, när den som frågar om flera platser redan har den."""
        klass = villkor.get(("ordklass", text))
        klasser = (klass,) if klass is not None else FÄLTKLASSER[sort]
        if lexkrav is None:
            krav = frozenset((k[2:], svar) for k, svar in villkor.items()
                             if isinstance(k, tuple) and k[0] == "lex" and k[1] == text)
        else:
            krav = frozenset(lexkrav.get(text, ()))
        nyckel = (klasser, krav)
        if nyckel not in self._kandidatcache:
            self._kandidatcache[nyckel] = sorted(
                (lexem for ordklass in klasser for lexem in self._lexemen(ordklass)
                 if all(self._uppfyller(lexem, vad, svar) for vad, svar in krav)),
                key=lambda lexem: (self._nivå(lexem["nyckel"]), lexem["nyckel"]))
        kandidater = self._kandidatcache[nyckel]
        if tillåten is None:
            return kandidater
        # Samma lista genom hela frågan, så att förklaringarna kan minnas hur
        # listans ord delas upp.
        if tillåten is not self._filtrerat_för:
            self._filtrerat_för, self._filtrerat = tillåten, {}
            self._klasser_per_lista, self._ram_möjlig = {}, {}
            self._gallringar, self._bärarcache, self._semantik_möjlig = {}, {}, {}
        celler = self._celler(text, händelser)
        if (nyckel, celler) not in self._filtrerat:
            self._filtrerat[(nyckel, celler)] = [
                lexem for lexem in kandidater
                if all(tillåten(k) for c in celler for k in self.tabell.kort(lexem, c))]
        return self._filtrerat[(nyckel, celler)]

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
                     mål: Kort | None = None, grupperat: bool = False,
                     hoppa: Callable | None = None,
                     förbud: list | None = None) -> Iterator[tuple]:
        """Meningarna ur en sammansättning, ett ordval i taget: (mening, orden, platserna).

        `grupperat` prövar ett ord per signatur i stället för varje ord. Ett
        ordval som `hoppa` säger faller byggs inte. `förbud` är bevisen som
        gäller i sammansättningen, som [(plats, villkor), …]: ett ordval där
        varje plats uppfyller sina villkor faller.
        """
        platser: dict[str, tuple] = {}

        def spana(text, sort):
            platser.setdefault(text, sort)
            return text

        self._mening(villkor, "m", spana)
        lexkrav = self._lexkrav(villkor)
        kandidater = {text: self._kandidater(text, sort, villkor, händelser, tillåten, lexkrav)
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
                bärare = self._bärare(mål, text, kandidater[text], händelser)
                if bärare:
                    urval.append({**kandidater, text: bärare})

        kontroller = self._kontroller(villkor, platser)
        if kontroller is None:
            return
        urval = [val for val in (self._gallrade(kandidatval, kontroller)
                                 for kandidatval in urval) if val is not None]
        prov = [(behöver, art, lambda bundna, behöver=behöver, art=art, f=f: self._provsvar(
                    art, f, behöver, tuple(bundna[p] for p in behöver)))
                for behöver, art, f in kontroller]
        # Bevisen prövas på orden innan de binds, inte på varje färdigt ordval:
        # ett bevis på en plats stryker platsens ord som uppfyller det, och ett
        # bevis på flera överger en bindning så fort dess platser uppfyller det.
        # Annars byggs varje kombination av de andra orden och hoppas över en i
        # taget: 17 miljoner ordval i en fråga om engelskans «why» (mätt 2026-09-15).
        for platserna in förbud or ():
            if not all(text in platser for text, _ in platserna):
                continue
            if len(platserna) == 1:
                ((text, atomer),) = platserna
                gallrade = []
                for val in urval:
                    kvar = [lexem for lexem in val[text]
                            if not all(uppfyller(self, a, lexem["nyckel"]) for a in atomer)]
                    if kvar:
                        gallrade.append({**val, text: kvar})
                urval = gallrade
            else:
                prov.append((tuple(text for text, _ in platserna), ("bevis",),
                             lambda bundna, platserna=platserna: not all(
                                 all(uppfyller(self, a, bundna[text]) for a in atomer)
                                 for text, atomer in platserna)))
        for kandidatval in urval:
            grupperna = {text: (self._grupper(lista, self._celler(text, händelser))
                                if grupperat else [[lexem] for lexem in lista])
                         for text, lista in kandidatval.items()}
            for bundna in self._bindningar(grupperna, prov):
                if hoppa is not None and hoppa(bundna):
                    self.statistik["ordval bevisade"] += 1
                    continue
                try:
                    mening = self._mening(villkor, "m", lambda text, _: bundna[text])
                except (TypeError, ValueError):
                    continue
                if self.validator.duger(mening) and not self.validator.valensbrott(mening):
                    yield mening, bundna, platser

    def _provsvar(self, art: tuple, prov: Callable, behöver: tuple, nycklar: tuple) -> bool:
        """Ett kravs svar för orden `nycklar`. Svaret beror bara på vad kravet är
        (`art`) och på orden, inte på var i meningen de står, så det sparas."""
        k = (art, nycklar)
        if k not in self._provcache:
            self._provcache[k] = bool(prov(dict(zip(behöver, nycklar))))
        return self._provcache[k]

    def _bärare(self, mål: Kort, text: str, kandidater: list, händelser: list) -> list:
        """Orden på platsen som kan bära målet. Svaret beror på platsens egna
        händelser, och samma lista ges för samma fråga så att gallringen sparas."""
        egna = tuple(h for h in händelser if h[1] == ("sym", text))
        k = (mål, text, id(kandidater), egna)
        if k not in self._bärarcache:
            self._bärarcache[k] = (kandidater, [
                lexem for lexem in kandidater if self._bär(mål, ("sym", text), lexem, händelser)])
        return self._bärarcache[k][1]

    def _gallrade(self, kandidatval: dict, kontroller: list) -> dict | None:
        """Platsernas ord gallrade med kraven innan orden binds, eller None när en
        plats blir tom och ingen bindning finns.

        Ett krav på en plats stryker de ord som inte klarar det. Ett krav på två
        platser stryker de ord som inget kvarvarande ord på den andra platsen
        klarar det med, tills inget mer stryks (bågkonsistens). Ett struket ord
        kan inte ingå i någon bindning, så gallringen ändrar inte vilka meningar
        som finns. Utan den prövas varje ord på platser som binds tidigare mot
        alla ord på en plats där kravet aldrig uppfylls: engelskans "X knows why Y
        …" utan något verb som tar en frågebisats. Svaret beror bara på listorna
        och kraven och sparas.
        """
        nyckel = (tuple((behöver, art) for behöver, art, _ in kontroller),
                  tuple((text, id(lista)) for text, lista in sorted(kandidatval.items())))
        if nyckel not in self._gallringar:
            val = dict(kandidatval)
            for behöver, art, prov in kontroller:
                if len(behöver) == 1 and behöver[0] in val:
                    text = behöver[0]
                    val[text] = [lexem for lexem in val[text]
                                 if self._provsvar(art, prov, behöver, (lexem["nyckel"],))]
            par = [k for k in kontroller if len(k[0]) == 2 and all(p in val for p in k[0])]
            tom = not all(val.values())
            ändrat = True
            while ändrat and not tom:
                ändrat = False
                for behöver, art, prov in par:
                    for i in (0, 1):
                        x, y = behöver[i], behöver[1 - i]
                        kvar = [lx for lx in val[x] if any(
                            self._provsvar(art, prov, behöver,
                                           (lx["nyckel"], ly["nyckel"]) if i == 0
                                           else (ly["nyckel"], lx["nyckel"]))
                            for ly in val[y])]
                        if len(kvar) < len(val[x]):
                            val[x], ändrat = kvar, True
                            tom = tom or not kvar
            self._gallringar[nyckel] = (kandidatval, None if tom else val)
        return self._gallringar[nyckel][1]

    def _kontroller(self, villkor: dict, platser: dict) -> list[tuple] | None:
        """Konceptens krav (6.1 punkt 6) som (platser, art, prov), prövade så fort
        orden på platserna är bundna. None när mallen aldrig kan bli giltig. `art`
        säger vad provet räknar ut, oberoende av platserna, så att svaren kan
        sparas.

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

            ramen = self._ramen(fält)
            if ramen is None:
                return None
            ut.append(((text,), ("ram", ramen), lambda b, text=text, ramen=ramen:
                       self._ramen_passar(b[text], *ramen)))
            passiv = fält("diates") not in (None, S.Diates.AKTIV.value)
            led = [s for s in ("subjekt", "objekt", "io")
                   if s == "subjekt" or fält(s) == "NF"]
            for slot in led:
                nf = f"{rot}.{slot}.koncept"
                if nf not in platser:
                    continue

                def semantik(b, text=text, nf=nf, slot=slot, passiv=passiv):
                    return self._semantiken_passar(b[text], b[nf], slot, passiv)

                ut.append(((text, nf), ("semantik", slot, passiv), semantik))
            for i, a in enumerate(led):
                for c in led[i + 1:]:
                    pa, pc = f"{rot}.{a}.koncept", f"{rot}.{c}.koncept"
                    if pa in platser and pc in platser:
                        ut.append(((pa, pc), ("olika",), lambda b, pa=pa, pc=pc: (
                            b[pa] != b[pc] or v.person(b[pa]) not in (1, 2))))
            adverb = f"{rot}.adverbial.0"
            if adverb in platser:
                bit = TIDSBIT[S.Tidsreferens(fält("tid") or S.Tidsreferens.NUTID.value)]
                ut.append(((adverb,), ("tempus", bit), lambda b, adverb=adverb, bit=bit: (
                    (krav := v.tempuskrav(b[adverb])) is None or bool(krav & bit))))
        for text in platser:
            if text.endswith(".attribut.0.koncept"):
                huvud = text[:-len(".attribut.0.koncept")] + ".koncept"
                ut.append(((text, huvud), ("attribut",), lambda b, text=text, huvud=huvud: (
                    not (alt := v.attributkrav(b[text]))
                    or v._uppfyller(v.semantik(b[huvud]), alt))))
        return ut

    #: Satsens fält som avgör vilken valensram verbet måste ha.
    RAMFÄLT = ("bisats", "objekt", "io", "predikativ", "komplement")

    @staticmethod
    def _ramen(fält: Callable) -> tuple[frozenset, bool] | None:
        """Slottarna satsen fyller och om den har en argumentbisats, eller None
        när mallen aldrig kan bli giltig."""
        bisats = fält("bisats") == "bisats"
        if bisats and fält("objekt") == "NF":
            return None
        fyllda = frozenset(s for s in ("objekt", "io", "predikativ", "komplement")
                           if fält(s) not in (None, "None")) | (
            frozenset({"objekt"}) if bisats else frozenset())
        return fyllda, bisats

    def _ramen_passar(self, verb: str, fyllda: frozenset, bisats: bool) -> bool:
        nyckel = (verb, fyllda, bisats)
        if nyckel not in self._ramcache:
            v = self.validator
            valens = v.valens(verb)
            svar = not bisats or v.tillåter_bisats(verb)
            if valens is not None:
                slottar = v.mönsterslottar(verb)
                svar = svar and fyllda in {(r & slottar) | ({"komplement"} & slottar)
                                           for bit, r in v.RAMAR.items() if valens & bit}
            self._ramcache[nyckel] = svar
        return self._ramcache[nyckel]

    def _semantiken_passar(self, verb: str, koncept: str, slot: str, passiv: bool) -> bool:
        """Uppfyller konceptet verbets krav på sloten? I passiv ställer verbet
        objektets krav på subjektet."""
        v = self.validator
        krav = v.krav_för(verb)
        if passiv and "objekt" in krav:
            krav = {**krav, "subjekt": krav["objekt"]}
        return slot not in krav or v._uppfyller(v.semantik(koncept), krav[slot])

    @staticmethod
    def _rör_subjekt(nod: Nod) -> bool:
        """Står delen på en sats subjekt, så att den kan göra verbets krav på
        subjektet omöjliga?"""
        return any(ref.endswith(".subjekt") for ref in nod.bindning.values())

    #: Ett fyllt värde för varje ramfält, så som `_ramen` läser dem.
    FYLLT = {"bisats": "bisats", "objekt": "NF", "io": "NF", "predikativ": "NF",
             "komplement": "verb"}

    def _möjliga_ramar(self, kända: tuple) -> frozenset:
        """Ramarna satsen kan få, när fälten i `kända` är lästa och resten kan bli
        tomma eller fyllda. Ett fält som ingen del läser är tomt i den färdiga
        meningen, men en senare del kan läsa det, så båda prövas."""
        if kända not in self._ramar:
            fälten = dict(kända)
            okända = [f for f in self.RAMFÄLT if f not in fälten]
            ramar = set()
            for fyllda in itertools.product((False, True), repeat=len(okända)):
                val = {**fälten, **{f: self.FYLLT[f] if fylld else None
                                    for f, fylld in zip(okända, fyllda)}}
                ramen = self._ramen(val.get)
                if ramen is not None:
                    ramar.add(ramen)
            self._ramar[kända] = frozenset(ramar)
        return self._ramar[kända]

    def _verben_möjliga(self, villkor: dict, händelser: list, tillåten: Tillåten) -> bool:
        """Finns i varje sats ett verb med en valensram satsen kan få, och ett
        subjekt som uppfyller verbets krav?

        Ramen beror bara på verbet och satsens fält (`RAMFÄLT`), och kravet på
        subjektet på verbet, subjektet och diatesen. Ett läst fält ändras inte,
        ett oläst kan bli vad som helst, och senare delar kan bara göra
        kandidaterna färre. En sats där inget verb passar, eller inget par av
        verb och subjekt, blir därför aldrig giltig. Utan den här frågan går
        sammansättningen igenom varje nominalfras och bisats i en sats som redan
        är omöjlig: 350 000 sammansättningar för svenskans «den», och 438 000 på
        två minuter för engelskans «why», där inget verb som tar en frågebisats
        godtar ett naket subjekt (mätt 2026-09-14 och -15).
        """
        # Satsernas verb och platsernas läsningar i ett svep över villkoren.
        lexkrav: dict = defaultdict(list)
        rötter = []
        for nyckel, svar in villkor.items():
            if isinstance(nyckel, tuple):
                if nyckel[0] == "lex":
                    lexkrav[nyckel[1]].append((nyckel[2:], svar))
            elif svar == "symbol" and nyckel.endswith(".verb"):
                rötter.append(nyckel)
        for nyckel in rötter:
            rot = nyckel[:-len(".verb")]
            ramar = self._möjliga_ramar(tuple((f, villkor[f"{rot}.{f}"]) for f in self.RAMFÄLT
                                              if f"{rot}.{f}" in villkor))
            if not ramar:
                return False
            lista = self._kandidater(nyckel, ("Mening", "verb"), villkor, händelser, tillåten,
                                     lexkrav)
            k = (id(lista), ramar)
            if k not in self._ram_möjlig:
                self._ram_möjlig[k] = (lista, [
                    lexem["nyckel"] for lexem in lista
                    if any(self._ramen_passar(lexem["nyckel"], *ramen) for ramen in ramar)])
            verben = self._ram_möjlig[k][1]
            if not verben:
                return False
            diates = villkor.get(f"{rot}.diates")
            passiva = ((False, True) if diates is None
                       else (diates != S.Diates.AKTIV.value,))
            subjekten = self._kandidater(f"{rot}.subjekt.koncept", ("Nominalfras", "koncept"),
                                         villkor, händelser, tillåten, lexkrav)
            k2 = (k, id(subjekten), passiva)
            if k2 not in self._semantik_möjlig:
                self._semantik_möjlig[k2] = (subjekten, any(
                    self._provsvar(("semantik", "subjekt", passiv),
                                   lambda b, passiv=passiv: self._semantiken_passar(
                                       b["verb"], b["nf"], "subjekt", passiv),
                                   ("verb", "nf"), (verb, lexem["nyckel"]))
                    for passiv in passiva for verb in verben for lexem in subjekten))
            if not self._semantik_möjlig[k2][1]:
                return False
        return True

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
        for behöver, _, prov in kontroller:
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

    def _pröva(self, mening: S.Mening, mål: Kort | None, tillåten: Tillåten) -> tuple:
        """(träffen eller None, utskriften, korten). Utskriften och korten är None
        när meningen inte går att rendera i båda språken."""
        try:
            ut = spåra(self.renderare, mening)
            if self.par is not None:
                self.par.rendera(mening)
        except RenderingsFel:
            return None, None, None
        kort = frozenset(k for k, _ in meningens_kort(self.tabell, ut))
        if (mål is not None and mål not in kort) or (
                tillåten is not None and not all(tillåten(k) for k in kort)):
            return None, ut, kort
        return Träff(mening, ut.text, len(ut.ord), kort), ut, kort

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
                 högst_ord: int, per_mall: int | None = None,
                 grupperat: bool = False) -> Iterator[Träff]:
        """Giltiga meningar som prövar `mål`, av kort som `tillåten` godtar.

        Kommer i ordning efter antal ord, upp till `högst_ord`. `per_mall` begränsar
        hur många ordval som prövas för varje sammansättning av vägar; None prövar
        alla. `grupperat` prövar ett ord per signatur i stället för varje ord: två
        ord med samma signatur ger samma kort i samma mening, så den som bara
        behöver en mening per korttäckning slipper de andra.
        """
        sedda: set = set()
        self._mål = mål
        # Två specar som ger samma mening med samma kort är samma mening här.
        visade: set = set()
        nåbar = self._nåbarhet(mål)
        for n in range(1, högst_ord + 1):
            for villkor, händelser, ord, _, _, _ in self._delen(
                    "rendera", ROT, {"m": "m"}, {}, n, tillåten, (), nåbar, nåbar is not None):
                if ord != n or (mål is not None and not self._kan_innehålla(händelser, mål)):
                    continue
                träffar = 0
                for mening, _, _ in self._meningar_ur(villkor, händelser, tillåten, mål,
                                                      grupperat=grupperat):
                    if mening in sedda:
                        continue
                    sedda.add(mening)
                    träff = self._pröva(mening, mål, tillåten)[0]
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

        En mening som faller på ett förbjudet val lämnar ett bevis, och det som
        beviset täcker hoppas över (`forklaring.py`). Med `kontroll` hoppas inget
        över: varje mening som ett bevis täcker renderas, och en träff bland dem
        är `Bevisfel`.
        """
        sedda: set = set()
        self._mål = mål
        nåbar = self._nåbarhet(mål)
        while True:
            träff = self._leta(mål, tillåten, nåbar, sedda)
            if träff is not None or not self._nytt_bevis:
                return träff
            # Ett nytt bevis gäller från början: uppräkningen har redan gått
            # förbi de delar det skär bort, och kommer inte tillbaka dit.
            self.statistik["omstarter"] += 1

    def _leta(self, mål: Kort, tillåten: Tillåten, nåbar, sedda: set) -> Träff | None:
        """Ett varv genom sammansättningarna. Slutar också när ett nytt bevis lärts."""
        self._nytt_bevis = False
        for villkor, händelser, ord, _, _, rot in self._delen(
                "rendera", ROT, {"m": "m"}, {}, math.inf, tillåten, (), nåbar, True):
            if not self._kan_innehålla(händelser, mål):
                continue
            noder = rot.alla()
            # Kontrolläget prövar påståendet bakom `_verben_möjliga` på det som når
            # hit: en sats där inget verb passar ramen ger ingen mening. Att en sats
            # som redan var omöjlig förblir det följer av att lästa fält inte ändras
            # och att kandidaterna bara blir färre; att pröva det kräver att allt
            # under den byggs, och det är just det som tar för lång tid.
            död = self.kontroll and not self._verben_möjliga(villkor, händelser, tillåten)
            giltiga = self._giltiga(rot, villkor, tillåten) if tillåten is not None else []
            täckt = tillåten is not None and (
                any(n.täckt for n in noder)
                or self._någon_täckt(giltiga, villkor, händelser, tillåten))
            if täckt and not self.kontroll:
                self.statistik["sammansättningar bevisade"] += 1
                continue
            hoppa = (None if self.kontroll or tillåten is None else
                     lambda bundna: self._avfärdad(giltiga, villkor, bundna, tillåten))
            förbud = None if hoppa is None else [
                [(absolut(nod.bindning, rel), atomer) for rel, _, atomer in b.platser]
                for nod, bevis in giltiga for b in bevis]
            for mening, bundna, platser in self._meningar_ur(
                    villkor, händelser, tillåten, mål, grupperat=True, hoppa=hoppa,
                    förbud=förbud):
                if mening in sedda:
                    continue
                sedda.add(mening)
                förutsagd = död or täckt or (self.kontroll and tillåten is not None
                                             and self._avfärdad(giltiga, villkor, bundna, tillåten))
                träff, ut, kort = self._pröva(mening, mål, tillåten)
                if död:
                    raise Bevisfel(f"«{mening}» byggdes ur en sammansättning där inget "
                                   f"verb skulle passa ramen")
                if förutsagd:
                    if träff is not None:
                        raise Bevisfel(f"«{träff.text}» prövar {mål} av tillåtna kort, "
                                       f"men ett bevis sade att meningen faller")
                    self.statistik["förutsägelser bekräftade"] += 1
                    continue
                if träff is not None:
                    return träff
                if (tillåten is not None and ut is not None
                        and self._lär(rot, villkor, bundna, platser, ut, kort, tillåten, mål)):
                    self._nytt_bevis = True
                    if not self.kontroll:
                        return None
                    giltiga = self._giltiga(rot, villkor, tillåten)
                    täckt = self._någon_täckt(giltiga, villkor, händelser, tillåten)
        return None
