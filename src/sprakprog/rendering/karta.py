"""Kartan: renderarens beslutsträd, genomgånget uttömmande del för del.

KÄRNAN 6.7. En renderare ställer frågor medan den skriver — är satsen nekad, är
subjektet i plural, är ordet neutrum — och frågorna och svaren bildar ett träd.
Kartan går igenom trädet genom att köra renderaren med ett ORAKEL som svarar på
varje läsning och prövar alla svar, ett i taget, djupet först. Det är inte
sampling: varje väg gås igenom.

DELAR. Hela satsen i ett stycke har tiotals miljoner vägar, men varje
frasfunktion läser bara en liten del av specen. Metoder märkta `@frasdel` gås
därför igenom för sig. När en del går igenom ersätts de andra delarna av
stubbar som bara noterar anropet.

INDATA OCH UTDATA räknas ut, de skrivs inte. En del prövas med de argument dess
anropare faktiskt skickar — de värden som förekommer i anroparnas vägar, och för
specobjekt de fält anroparen redan läst. Omvänt får en anropare veta vad en del
kan lämna tillbaka: ingenting, ett ord eller en lista med ett visst antal ord.
Det spelar roll där anroparen förgrenar på det, som när negationen hamnar efter
det första av verbfrasens ord. Delarna gås igenom om tills varken indata eller
utdata ändras.

FÖRBIGÅNGAR. Orakelt ger renderaren symboliska koncept och ett symboliskt
`Uppslag`. Läser renderaren något förbi gränssnittet — ett lexems kolumn direkt,
en konceptnyckel i en jämförelse eller tabell, en databasanslutning — stoppar
vägen med `Förbigång`. Kartan hittar alltså själv det KÄRNAN 8.3 kräver ska vara
lagat.

LISTLÄNGDER. En del som lämnar en lista sammanfattas med listans möjliga
längder, men bara så noga som anroparna läser dem: läser de bara första ordet
räcker det att veta om listan är tom. Annars skulle en del som innehåller sig
själv — satsen i bisatsen i satsen — få allt längre listor för varje varv, och
genomgången skulle aldrig ta slut.

VÄGARNA SPARAS. Varje väg som renderar klart sparas med sina villkor — vad
orakelt svarade på varje läsning — sina händelser och sina anrop, med vilka
specobjekt och koncept varje argument var. Sammansättningen (steg 2) fogar
ihop vägarna till hela meningar genom att döpa om delens namn till meningens.
Ett symboliskt koncept står i händelserna som ("sym", väg), så att det går att
skilja från en konceptnyckel. Varje ord vägen skapar beskrivs — en form, eller
ett ord från ett anrop — så att sammansättningen kan avgöra om en ordningsregels
led har ord.

Vilka beslut som syns avgör inte kartan. Det beror på vilka ord meningen får och
på om andra delar vägrar, och avgörs av spåret på den riktiga meningen (KÄRNAN
4.2, 8.3).

Ordens egenskaper tar sina möjliga värden ur databasen per ordklass: ett
substantivs genus kan vara det som något svenskt substantiv har. Samband mellan
egenskaper hos samma ord följer inte med, så kartan är en övermängd; sökningen
binder sedan orden till verkliga lexem (KÄRNAN 6.7).

Kör:  python -m sprakprog.rendering.karta sv [FIL]    (FIL: spara vägarna)
"""

from __future__ import annotations

import inspect
import math
import pickle
import sqlite3
import sys
import time
from collections import Counter, defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from . import RENDERARE
from . import spec as S
from .spec import RenderingsFel
from .uppslag import dela_klass, klassnamn, MÄNSKLIG, TILLTAL, Uppslag, Val

# ── sådant som stoppar en väg ────────────────────────────────────────────


class Förbigång(Exception):
    """Renderaren läste något förbi gränssnittet."""


class Vänta(Exception):
    """En del anropades vars utdata ännu inte är känt. Vägen gås om senare."""


# ── specens typer ────────────────────────────────────────────────────────

#: Vilka ordklasser ett koncept i ett visst specfält kan ha. Det är specens
#: egna typer, som de beskrivs i `rendering/spec.py`.
FÄLTKLASSER = {
    ("Mening", "verb"): ("Verb",),
    ("Mening", "komplement"): ("Verb",),
    ("Mening", "predikativ"): ("Adjektiv",),
    ("Mening", "fråga_om"): ("Frågadverb",),
    ("Mening", "adverbial"): ("Adverb",),
    # neg_heller står avsiktligt utanför: dess engelska lemma "not either"
    # är diskontinuerligt och går inte att slå upp som ett ord.
    ("Mening", "negation"): ("Negationsadverb/satsnegation",
                             "Negationsadverb/satsadverbial"),
    ("Nominalfras", "koncept"): ("Substantiv", "Pronomen",
                                 "Kvantifikator/huvudord"),
    ("Nominalfras", "possessiv"): ("Possessiv",),
    ("Nominalfras", "frågedeterminant"): ("Interrogativdeterminant",),
    ("Nominalfras", "demonstrativ"): ("Demonstrativ",),
    ("Nominalfras", "kvantifikator"): ("Kvantifikator/bestämning",),
    ("Nominalfras", "räkneord"): ("Räkneord/grundtal",),
    # Ordningstalet böjs som ett adjektiv och står på attributets plats:
    # "den andra boken", "the second book".
    ("Attribut", "koncept"): ("Adjektiv", "Räkneord/ordningstal"),
    ("Prepositionsfras", "preposition"): ("Preposition",),
    ("Bisats", "subjunktion"): ("Subjunktion",),
}


class Symbol(str):
    """Ett koncept som inte är valt. Får skickas till `Uppslag`, men inte jämföras.

    Att jämföra ett symboliskt koncept med en konceptnyckel, eller slå upp det i
    en tabell, är att läsa lexikonet förbi gränssnittet. Jämförelser med
    strängar som inte är konceptnycklar — `"subjekt"` — är specens egna
    diskriminatorer och ger falskt.
    """
    sort: tuple[str, str]
    text: str
    nycklar: frozenset = frozenset()

    def __eq__(self, annan):
        if isinstance(annan, Symbol):
            return self.text == annan.text
        if isinstance(annan, str) and str.__str__(annan) in Symbol.nycklar:
            raise Förbigång(f"jämför konceptet {self.text} med konceptnyckeln {annan!r}")
        return False

    def __ne__(self, annan):
        return not self.__eq__(annan)

    def __hash__(self):
        raise Förbigång(f"slår upp konceptet {self.text} i en tabell")


def _symbol(text: str, sort: tuple[str, str]) -> Symbol:
    s = Symbol(f"<{text}>")
    s.text, s.sort = text, sort
    return s


# ── lata specobjekt ──────────────────────────────────────────────────────


@dataclass
class _Kontext:
    körning: "Körning"
    väg: str
    begränsning: dict       # relativ nyckel → frozenset av etiketter
    relativ: str


class _Lat:
    """Markering för de lata specobjekten."""


def _lat(klass, körning, väg, begränsning, relativ=""):
    obj = object.__new__(klass)
    object.__setattr__(obj, "_k", _Kontext(körning, väg, begränsning, relativ))
    return obj


def _enumdomän(enum) -> list:
    return [(e.value, lambda e=e: e) for e in enum]


def _booldomän() -> list:
    return [("False", lambda: False), ("True", lambda: True)]


def _domän(k: _Kontext, klass: str, namn: str) -> list:
    """(etikett, fabrik) för fältet. Fabriken skapar värdet först när det väljs."""
    väg = f"{k.väg}.{namn}"
    rel = f"{k.relativ}.{namn}" if k.relativ else namn
    kör, begr = k.körning, k.begränsning

    def nf():
        return _lat(LatNominalfras, kör, väg, begr, rel)

    def sym(sort):
        return lambda: _symbol(väg, sort)

    ingen = ("None", lambda: None)
    if klass == "Mening":
        return {
            "verb": [("symbol", sym(("Mening", "verb")))],
            "subjekt": [("NF", nf)],
            "objekt": [ingen, ("NF", nf)],
            "io": [ingen, ("NF", nf)],
            "predikativ": [ingen, ("adjektiv", sym(("Mening", "predikativ"))),
                           ("NF", nf)],
            "adverbial": [
                ("tom", lambda: ()),
                ("adverb", lambda: (_symbol(f"{väg}.0", ("Mening", "adverbial")),)),
                ("prepositionsfras", lambda: (_lat(LatPrepositionsfras, kör,
                                                   f"{väg}.0", begr, f"{rel}.0"),)),
                ("bisats", lambda: (_lat(LatBisats, kör, f"{väg}.0", begr,
                                         f"{rel}.0"),)),
            ],
            "komplement": [ingen, ("verb", sym(("Mening", "komplement")))],
            "grad": _enumdomän(S.Grad),
            "jämförelse": [ingen, ("NF", nf)],
            "diates": _enumdomän(S.Diates),
            "fråga": _booldomän(),
            "negerad": _booldomän(),
            "negation": [("symbol", sym(("Mening", "negation")))],
            "tid": _enumdomän(S.Tidsreferens),
            "aspekt": _enumdomän(S.Aspekt),
            "bisats": [ingen, ("bisats", lambda: _lat(LatBisats, kör, väg, begr, rel))],
            "fråga_om": [ingen, *((s, lambda s=s: s) for s in S.FRÅGESLOTTAR),
                         ("frågadverb", sym(("Mening", "fråga_om")))],
            "modus": _enumdomän(S.Satsmodus),
        }[namn]
    if klass == "Nominalfras":
        return {
            "koncept": [("symbol", sym(("Nominalfras", "koncept")))],
            "bestämdhet": _enumdomän(S.Bestämdhet),
            "numerus": _enumdomän(S.Numerus),
            "attribut": [("tom", lambda: ()),
                         ("ett", lambda: (_lat(LatAttribut, kör, f"{väg}.0", begr,
                                               f"{rel}.0"),))],
            "possessiv": [ingen, ("symbol", sym(("Nominalfras", "possessiv")))],
            "possessiv_koreferent": _booldomän(),
            "referent": [ingen, *_enumdomän(S.Referentgenus)],
            "frågedeterminant": [ingen, ("symbol", sym(("Nominalfras",
                                                        "frågedeterminant")))],
            "ägare": [ingen, ("NF", nf)],
            "demonstrativ": [ingen, ("symbol", sym(("Nominalfras",
                                                    "demonstrativ")))],
            "kvantifikator": [ingen, ("symbol", sym(("Nominalfras",
                                                     "kvantifikator")))],
            "räkneord": [ingen, ("symbol", sym(("Nominalfras", "räkneord")))],
        }[namn]
    if klass == "Attribut":
        return {"koncept": [("symbol", sym(("Attribut", "koncept")))],
                "grad": _enumdomän(S.Grad)}[namn]
    if klass == "Prepositionsfras":
        return {"preposition": [("symbol", sym(("Prepositionsfras", "preposition")))],
                "komplement": [("NF", nf)]}[namn]
    if klass == "Bisats":
        return {"subjunktion": [ingen, ("symbol", sym(("Bisats", "subjunktion")))],
                "sats": [("Mening", lambda: _lat(LatMening, kör, väg, begr, rel))]}[namn]
    raise KeyError(klass)


def _fält(klass_namn: str, fältnamn: frozenset):
    def läs(self, namn):
        if namn not in fältnamn:
            return object.__getattribute__(self, namn)
        k = object.__getattribute__(self, "_k")
        nyckel = f"{k.väg}.{namn}"
        rel = f"{k.relativ}.{namn}" if k.relativ else namn
        domän = _domän(k, klass_namn, namn)
        tillåtna = k.begränsning.get(rel)
        if tillåtna is not None:
            domän = [d for d in domän if d[0] in tillåtna]
        return k.körning.välj_värde(nyckel, domän)
    return läs


def _latklass(bas):
    namn = frozenset(f.name for f in bas.__dataclass_fields__.values())
    return type(f"Lat{bas.__name__}", (bas, _Lat),
                {"__slots__": ("_k",), "__getattribute__": _fält(bas.__name__, namn)})


LatMening = _latklass(S.Mening)
LatNominalfras = _latklass(S.Nominalfras)
LatAttribut = _latklass(S.Attribut)
LatPrepositionsfras = _latklass(S.Prepositionsfras)
LatBisats = _latklass(S.Bisats)
LATA = {"Mening": LatMening, "Nominalfras": LatNominalfras, "Attribut": LatAttribut,
        "Prepositionsfras": LatPrepositionsfras, "Bisats": LatBisats}


# ── symboliska ord och stubbarnas utdata ─────────────────────────────────


class SymOrd(str):
    """Ett ord i en väg. `nr` är dess plats i skapelseordningen."""
    nr: int
    längder: frozenset | None = None     # bara för ett ord som står för en dels okända ord
    del_: str | None = None              # den delen
    koncept = None                       # för ett uppslaget ord, som `Ord.koncept`
    variant = None


# En mängd listlängder innehåller exakta tal och högst en undre gräns
# ("minst", t), som står för alla längder från t och uppåt.


def _lägsta(n) -> int:
    return n[1] if isinstance(n, tuple) else n


def _normera(längder) -> frozenset:
    längder = set(längder)
    gränser = [n[1] for n in längder if isinstance(n, tuple)]
    if not gränser:
        return frozenset(längder)
    t = min(gränser)
    return frozenset({n for n in längder if not isinstance(n, tuple) and n < t}
                     | {("minst", t)})


def _plus(a, b):
    if isinstance(a, tuple) or isinstance(b, tuple):
        return ("minst", _lägsta(a) + _lägsta(b))
    return a + b


def _tak(längder, djup) -> frozenset:
    """Längderna så noga som anroparna läser dem: exakta under `djup`, annars bara att de når dit."""
    return _normera(("minst", min(_lägsta(n), djup)) if isinstance(n, tuple) or n >= djup
                    else n for n in längder)


class Block:
    """Utdata från en stubbad del som är en lista.

    Orakelt avslöjar bara det anroparen läser. Itereras listan står det okända
    som ett enda ord i anroparens lista. Läser anroparen ett visst ord eller
    listans början — `vf[0]`, `bisats[:1]` — väljs bara om listan når så långt.
    Läser den längden eller slutet väljs längden.
    """

    def __init__(self, körning, nr, del_, längder):
        self._körning, self._nr, self._del = körning, nr, del_
        self._längder = _normera(längder)   # hela listans möjliga längder
        self._ord: list = []                # de kända orden, från början
        self._rest: SymOrd | None = None    # det okända, som ett ord
        self._längdtips = False

    def _förläng(self, k: int) -> None:
        while len(self._ord) < k:
            ord = self._körning.nytt_ord(f"<del{self._nr}:{len(self._ord)}>")
            self._körning.beskriv_ord(ord, ("del", self._nr, len(self._ord)))
            self._ord.append(ord)

    def _se(self, djup) -> None:
        """Anroparen läser listan till `djup`. Är delen inte sammanfattad så noga, väntar vägen."""
        if not self._körning.karta.räcker(self._del, djup):
            raise Vänta(self._del)

    def _minst(self, k: int) -> bool:
        """Har listan minst k ord? Orakelt väljer bland de svar som syns."""
        self._längdtips = False
        if len(self._ord) >= k:
            return True
        if self._längder == {len(self._ord)}:
            return False
        if any(isinstance(n, tuple) and n[1] < k for n in self._längder):
            self._se(k)
        kortare = sorted({m for n in self._längder
                          for m in (range(n[1], k) if isinstance(n, tuple) else (n,))
                          if m < k})
        längre = ["längre"] if any(isinstance(n, tuple) or n >= k
                                   for n in self._längder) else []
        svar = self._körning.orakel.välj(("längd", self._nr, k), kortare + längre)
        if svar == "längre":
            self._längder = _normera(
                ("minst", max(n[1], k)) if isinstance(n, tuple) else n
                for n in self._längder if isinstance(n, tuple) or n >= k)
            self._förläng(k)
            return True
        self._längder = frozenset({svar})
        self._förläng(svar)
        return False

    def _fixera(self):
        self._längdtips = False
        if any(isinstance(n, tuple) for n in self._längder):
            self._se(math.inf)
            raise RuntimeError(f"{self._del}: längden läses i sin helhet, "
                               f"men den har ingen övre gräns")
        if len(self._längder) > 1:
            n = self._körning.orakel.välj(("längd", self._nr), sorted(self._längder))
            self._längder = frozenset({n})
        self._förläng(next(iter(self._längder)))
        return self._ord

    def __iter__(self):
        k = len(self._ord)
        rest = _normera(("minst", max(n[1] - k, 0)) if isinstance(n, tuple) else n - k
                        for n in self._längder)
        if rest == {0}:
            return iter(list(self._ord))
        if self._rest is None or self._rest.längder != rest:
            text = f"<del{self._nr}:{k}…>" if self._ord else f"<del{self._nr}>"
            self._rest = self._körning.nytt_ord(text)
            self._rest.längder, self._rest.del_ = rest, self._del
            self._körning.beskriv_ord(self._rest, ("del", self._nr, "rest", k))
        self._längdtips = True
        return _Helhet(self, [*self._ord, self._rest])

    def __len__(self):
        # `lista.extend(block)`, `[*block]` och `list(block)` frågar efter
        # längden som ett tips, direkt efter iter() och före första ordet. Det
        # är inget beslut i renderaren och får inte förgrena vägen.
        if self._längdtips:
            self._längdtips = False
            return 1
        return len(self._fixera())

    def __getitem__(self, i):
        if isinstance(i, int) and i >= 0:
            if not self._minst(i + 1):
                raise IndexError(i)
            return self._ord[i]
        if (isinstance(i, slice) and i.step is None and (i.start or 0) >= 0
                and i.stop is not None and i.stop >= 0):
            self._minst(i.stop)
            return self._ord[i]
        return self._fixera()[i]

    def __bool__(self):
        return self._minst(1)


class _Helhet:
    """Iteratorn över en `Block` vars längd inte är vald: de kända orden och resten."""

    def __init__(self, block: Block, ord: list) -> None:
        self._block, self._ord = block, iter(ord)

    def __iter__(self):
        return self

    def __next__(self):
        self._block._längdtips = False
        return next(self._ord)


# ── det symboliska uppslaget ─────────────────────────────────────────────


class SymLexem:
    """Ett lexem för ett symboliskt koncept. Dess kolumner går inte att läsa."""

    def __init__(self, koncept: Symbol, variant):
        self.koncept, self.variant = koncept, variant

    def __getitem__(self, namn):
        raise Förbigång(f"läser lexem[{namn!r}] för {self.koncept.text} direkt")


class Lexikon:
    """Egenskapernas möjliga värden per ordklass, ur databasen."""

    def __init__(self, verklig: Uppslag) -> None:
        self.u = verklig
        self._rader: dict = {}
        self._cache: dict = {}
        self.klasser = {klassnamn(*r) for r in verklig.conn.execute(
            """SELECT DISTINCT k.ordklass, k.roll FROM Koncept k JOIN Lexem l
               ON l.koncept_id = k.id WHERE l.språk = ?""", (verklig.språk,))}

    def rader(self, klass: str):
        """Lexemen i en klass. `klass` kan bära en roll: "Räkneord/grundtal"."""
        if klass not in self._rader:
            ordklass, roll = dela_klass(klass)
            self._rader[klass] = self.u.conn.execute(
                f"""SELECT l.*, k.ordklass, k.roll, k.nyckel FROM Lexem l
                    JOIN Koncept k ON k.id = l.koncept_id
                    WHERE l.språk = ? AND k.ordklass = ?
                      AND k.roll IS {'?' if roll else 'NULL'}""",
                (self.u.språk, ordklass, *((roll,) if roll else ()))).fetchall()
        return self._rader[klass]

    def värden(self, ordklass: str, vad: tuple) -> list:
        nyckel = (ordklass, vad)
        if nyckel not in self._cache:
            rader = self.rader(ordklass)
            sort = vad[0]
            if sort == "har":
                mängd = {bool(self.u._celler(r).get(vad[1])) for r in rader}
            elif sort == "egenskap":
                mängd = {self.u._egenskapsvärde(r, vad[1]) for r in rader}
            elif sort == "koncept":
                mängd = {self.u.koncept(r["nyckel"], vad[1]) for r in rader}
            elif sort == "förljud":
                mängd = {self.u.förljud(r) for r in rader}
            elif sort == "operator":
                mängd = {self.u.operator(r) for r in rader}
            elif sort == "mänsklig":
                mängd = {self.u.mänsklig(r["nyckel"]) for r in rader}
            elif sort == "tilltal":
                mängd = {TILLTAL.get(r["nyckel"]) for r in rader}
            else:
                raise KeyError(vad)
            self._cache[nyckel] = sorted(mängd, key=repr) or [None]
        return self._cache[nyckel]


class SymUppslag:
    """Uppslagets gränssnitt, med orakelt som svar på symboliska koncept."""

    def __init__(self, körning: "Körning", verklig: Uppslag, lexikon: Lexikon):
        self._körning, self._verklig, self._lexikon = körning, verklig, lexikon
        self._led: list[str] = []
        self.språk = verklig.språk

    def __getattr__(self, namn):
        raise Förbigång(f"Uppslag.{namn} finns inte i gränssnittet")

    # ── hjälp ──

    def _välj(self, nyckel, värden):
        return self._körning.orakel.välj(nyckel, list(värden))

    def _klass(self, koncept: Symbol) -> str:
        klasser = [k for k in FÄLTKLASSER[koncept.sort] if k in self._lexikon.klasser]
        return self._välj(("ordklass", koncept.text), klasser)

    def _lexvärde(self, koncept: Symbol, vad: tuple):
        klass = self._klass(koncept)
        return self._välj(("lex", koncept.text, *vad),
                          self._lexikon.värden(klass, vad))

    def _etikett(self, koncept):
        return ("sym", koncept.text) if isinstance(koncept, Symbol) else koncept

    def _händelse(self, *h):
        self._körning.händelser.append((h[0], tuple(self._led), *h[1:]))

    # ── lexem och läsningar utan kunskap ──

    def lexem(self, koncept, variant=None):
        if isinstance(koncept, Symbol):
            return SymLexem(koncept, variant)
        return self._verklig.lexem(koncept, variant)

    def ordklass(self, lexem):
        if isinstance(lexem, SymLexem):
            return self._klass(lexem.koncept)
        return lexem["ordklass"]

    def lemma(self, lexem):
        if isinstance(lexem, SymLexem):
            return f"<{lexem.koncept.text}>"
        return lexem["lemma"]

    def har_form(self, lexem, cell):
        if isinstance(lexem, SymLexem):
            return self._lexvärde(lexem.koncept, ("har", cell))
        return self._verklig.har_form(lexem, cell)

    def koncept(self, nyckel, namn):
        if isinstance(nyckel, Symbol):
            return self._lexvärde(nyckel, ("koncept", namn))
        return self._verklig.koncept(nyckel, namn)

    def mänsklig(self, koncept):
        if isinstance(koncept, Symbol):
            return self._lexvärde(koncept, ("mänsklig",))
        return self._verklig.mänsklig(koncept)

    def tilltal(self, koncept):
        if isinstance(koncept, Symbol):
            return self._lexvärde(koncept, ("tilltal",))
        return self._verklig.tilltal(koncept)

    def förljud(self, lexem):
        if isinstance(lexem, SymLexem):
            return self._lexvärde(lexem.koncept, ("förljud",))
        return self._verklig.förljud(lexem)

    def operator(self, lexem):
        if isinstance(lexem, SymLexem):
            return self._lexvärde(lexem.koncept, ("operator",))
        return self._verklig.operator(lexem)

    def kontrollera_naken(self, nf):
        return Uppslag.kontrollera_naken(self, nf)

    def kontrollera_räkneord(self, nf):
        return Uppslag.kontrollera_räkneord(self, nf)

    def frågepronomen(self, koncept):
        return Uppslag.frågepronomen(self, koncept)

    # ── kunskap ──

    def form(self, lexem, cell):
        if isinstance(lexem, SymLexem):
            if not self._lexvärde(lexem.koncept, ("har", cell)):
                raise RenderingsFel(f"{lexem.koncept.text}: cellen {cell!r} saknas")
            koncept = ("sym", lexem.koncept.text)
        else:
            self._verklig.form(lexem, cell)
            koncept = lexem["nyckel"]
        text = koncept[1] if isinstance(koncept, tuple) else koncept
        ord = self._körning.nytt_ord(f"<{text}:{cell}>")
        if isinstance(lexem, SymLexem):
            ord.koncept, ord.variant = lexem.koncept, lexem.variant
        else:
            ord.koncept, ord.variant = lexem["nyckel"], lexem["variant"]
        self._händelse("form", koncept, cell, ord.nr)
        self._körning.beskriv_ord(ord, ("form", koncept, cell))
        return ord

    def form_för(self, koncept, cell, variant=None):
        return self.form(self.lexem(koncept, variant), cell)

    def egenskap(self, lexem, namn):
        if isinstance(lexem, SymLexem):
            värde = self._lexvärde(lexem.koncept, ("egenskap", namn))
            koncept = ("sym", lexem.koncept.text)
        else:
            värde = self._verklig._egenskapsvärde(lexem, namn)
            koncept = lexem["nyckel"]
        if värde is not None:
            self._händelse("egenskap", koncept, namn, värde)
        return värde

    def egenskap_för(self, koncept, namn, variant=None):
        return self.egenskap(self.lexem(koncept, variant), namn)

    def rektion(self, koncept, slot, namn, värde):
        self._händelse("rektion", self._etikett(koncept), slot, namn, värde)
        return värde

    def infinitivmarkör(self, verb):
        if isinstance(verb, Symbol):
            markör = self._välj(("lex", verb.text, "infinitivmarkör"),
                                self._verklig.rektionsdomän("komplement",
                                                            "infinitivmarkör"))
        else:
            markör = self._verklig.infinitivmarkör(verb)
        return self.rektion(verb, "komplement", "infinitivmarkör", markör)

    def komplementform(self, verb):
        if isinstance(verb, Symbol):
            form = self._välj(("lex", verb.text, "komplementform"),
                              self._verklig.rektionsdomän("komplement", "verbform"))
        else:
            form = self._verklig.komplementform(verb)
        return self.rektion(verb, "komplement", "verbform", form)

    def regel(self, val: Val, utfall: str) -> str:
        if utfall not in val.utfall:
            raise ValueError(f"{val.namn}: {utfall!r} är inget av utfallen")
        self._händelse("regel", val.namn, utfall)
        return utfall

    def ordning(self, namn, före, efter) -> None:
        self._händelse("ordning", namn, self._nr(före), self._nr(efter))

    def ordföljd(self, regel) -> None:
        self._händelse("ordföljd", regel)

    @contextmanager
    def led(self, namn):
        self._led.append(namn)
        try:
            yield
        finally:
            self._led.pop()

    def _nr(self, ord) -> tuple:
        ut = []
        for o in ord:
            if not isinstance(o, SymOrd):
                raise Förbigång(f"ordet {o!r} kom inte från ett uppslag")
            ut.append(o.nr)
        return tuple(ut)


# ── en körning: en väg genom en del ──────────────────────────────────────


class Orakel:
    """Svarar på varje fråga; nästa körning byter det sista valet med alternativ kvar."""

    def __init__(self, prefix: list[int]):
        self.prefix = prefix
        self.val: list[tuple] = []          # (nyckel, antal, index, etikett)
        self._minne: dict = {}

    def välj(self, nyckel, alternativ: list):
        if nyckel in self._minne:
            return self._minne[nyckel]
        if not alternativ:
            raise RenderingsFel(f"inget möjligt värde för {nyckel}")
        i = len(self.val)
        index = self.prefix[i] if i < len(self.prefix) else 0
        värde = alternativ[index]
        self.val.append((nyckel, len(alternativ), index, värde))
        self._minne[nyckel] = värde
        return värde

    def nästa(self) -> list[int] | None:
        j = len(self.val) - 1
        while j >= 0 and self.val[j][2] + 1 >= self.val[j][1]:
            j -= 1
        if j < 0:
            return None
        return [v[2] for v in self.val[:j]] + [self.val[j][2] + 1]


class Körning:
    def __init__(self, karta: "Kartritare", orakel: Orakel):
        self.karta, self.orakel = karta, orakel
        self.händelser: list[tuple] = []
        self.anrop: list[tuple] = []
        #: (nr, del, ((parameter, etikett, referens), …)) — referensen är
        #: specobjektets eller konceptets väg hos anroparen, None för ett värde
        self.anropsställen: list[tuple] = []
        #: ordets nr → ("form", koncept, cell) eller ("del", anropets nr, plats)
        self.ordbeskrivning: dict[int, tuple] = {}
        self._ordnr = 0
        self._specval: dict = {}

    def nytt_ord(self, text: str) -> SymOrd:
        o = SymOrd(text)
        o.nr, self._ordnr = self._ordnr, self._ordnr + 1
        return o

    def välj_värde(self, nyckel: str, domän: list):
        """Ett specfält: orakelt väljer etikett, fabriken skapar värdet en gång."""
        if nyckel in self._specval:
            return self._specval[nyckel]
        etikett = self.orakel.välj(nyckel, [e for e, _ in domän])
        värde = dict(domän)[etikett]()
        self._specval[nyckel] = värde
        return värde

    def läsningar(self) -> list[tuple]:
        return [(v[0], v[3]) for v in self.orakel.val]

    def beskriv_ord(self, ord: SymOrd, beskrivning: tuple) -> None:
        self.ordbeskrivning[ord.nr] = beskrivning

    # ── stubbarna ──

    def beskriv(self, värde, läsningar) -> tuple:
        if isinstance(värde, _Lat):
            k = object.__getattribute__(värde, "_k")
            prefix = k.väg + "."
            projektion = frozenset(
                (n[len(prefix):], e) for n, e in läsningar
                if isinstance(n, str) and n.startswith(prefix))
            return ("lat", type(värde).__mro__[1].__name__, projektion)
        if isinstance(värde, Symbol):
            return ("symbol", värde.sort)
        if isinstance(värde, (SymOrd, Block, list, tuple)):
            raise Förbigång(f"en del skickar ord som argument: {värde!r}")
        try:
            hash(värde)
        except TypeError:
            raise Förbigång(f"argumentet {värde!r} går inte att beskriva") from None
        return ("värde", värde)

    def anropa(self, del_: str, metod, args, kwargs):
        bundna = self.karta.signaturer[del_].bind(None, *args, **kwargs)
        bundna.apply_defaults()
        läsningar = self.läsningar()
        värden = list(bundna.arguments.items())[1:]
        argument = tuple((namn, self.beskriv(v, läsningar)) for namn, v in värden)
        nr = self._ordnr
        self._ordnr += 1
        self.anrop.append((del_, argument))
        self.anropsställen.append((nr, del_, tuple(
            (namn, _etikett(d), _referens(v))
            for (namn, d), (_, v) in zip(argument, värden))))
        self.händelser.append(("del", del_, tuple(_etikett(d) for _, d in argument), nr))
        utdata = self.karta.utdata_för(del_, argument)
        if not utdata:
            raise Vänta(del_)
        sorter = sorted({"none" if u == "none" else "ord" if u == "ord" else "lista"
                         for u in utdata})
        sort = self.orakel.välj(("utdata", nr), sorter)
        if sort == "none":
            return None
        if sort == "ord":
            ord = self.nytt_ord(f"<del{nr}>")
            self.beskriv_ord(ord, ("del", nr, "ord"))
            return ord
        return Block(self, nr, del_, (u[1] for u in utdata if isinstance(u, tuple)))


def _referens(värde) -> str | None:
    """Specobjektets eller konceptets väg hos anroparen; None för ett värde."""
    if isinstance(värde, _Lat):
        return object.__getattribute__(värde, "_k").väg
    if isinstance(värde, Symbol):
        return värde.text
    return None


def _etikett(deskriptor: tuple) -> str:
    if deskriptor[0] == "värde":
        v = deskriptor[1]
        return f"värde:{v.value if isinstance(v, Enum) else v!r}"
    if deskriptor[0] == "symbol":
        return f"symbol:{deskriptor[1][0]}.{deskriptor[1][1]}"
    return f"lat:{deskriptor[1]}"


def _utdatasort(resultat, djup=math.inf) -> set:
    """Vad en del lämnade tillbaka: "none", "ord" eller ("lista", n) för varje möjlig längd n.

    Längderna är exakta under `djup` (6.7, se `Kartritare.djup`).
    """
    if resultat is None:
        return {"none"}
    if isinstance(resultat, str):
        return {"ord"}
    längder = {0}
    for o in resultat:
        bidrag = o.längder if isinstance(o, SymOrd) and o.längder is not None else {1}
        längder = _normera(_plus(a, b) for a in längder for b in bidrag)
    return {("lista", n) for n in _tak(längder, djup)}


# ── kartritaren ──────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Väg:
    """En väg genom en del som renderade klart.

    argument   ((parameter, etikett), …) — delens egna argument
    villkor    ((nyckel, svar), …) — orakelts svar på varje läsning; nycklarna
               är delens egna namn: "nf.bestämdhet", ("lex", "nf.koncept", …),
               och ("utdata", nr) och ("längd", nr, …) för anropens utdata
    händelser  det vägen redovisade, i ordning
    anrop      ((nr, del, ((parameter, etikett, referens), …)), …)
    utdata     vad delen lämnade tillbaka (`_utdatasort`)
    ord        ((nr, beskrivning), …) — ("form", koncept, cell) eller
               ("del", anropets nr, plats) för varje ord vägen skapade
    """
    argument: tuple
    villkor: tuple
    händelser: tuple
    anrop: tuple
    utdata: frozenset
    ord: tuple = ()


@dataclass
class Delkarta:
    namn: str
    vägar: Counter = field(default_factory=Counter)     # status → antal
    utfall: set = field(default_factory=set)
    klara: list = field(default_factory=list)           # Väg, en per klar väg
    förbigångar: Counter = field(default_factory=Counter)
    kraschar: Counter = field(default_factory=Counter)
    genomgångar: int = 0
    sekunder: float = 0.0
    tak: bool = False


class Kartritare:
    TAK = 3_000_000

    def __init__(self, språk: str, conn: sqlite3.Connection) -> None:
        self.språk = språk
        self.klass = RENDERARE[språk]
        self.verklig = Uppslag(conn, språk)
        self.lexikon = Lexikon(self.verklig)
        Symbol.nycklar = frozenset(r[0] for r in conn.execute(
            "SELECT nyckel FROM Koncept"))
        self.delar = {n: m for n, m in inspect.getmembers(self.klass, inspect.isfunction)
                      if getattr(m, "frasdel", False)}
        self.metoder = {**self.delar, "rendera": self.klass.rendera}
        self.signaturer = {n: inspect.signature(m) for n, m in self.metoder.items()}
        #: del → parameter → {etikett: deskriptor}; lata deskriptorer samlar
        #: sina projektioner i en mängd
        self.indata: dict = defaultdict(lambda: defaultdict(dict))
        self.projektioner: dict = defaultdict(lambda: defaultdict(set))
        #: del → [(argumentetiketter, utdatasorter)]
        self.utdata: dict = defaultdict(list)
        self.anropare: dict = defaultdict(set)
        self.kartor: dict[str, Delkarta] = {}
        #: del → hur långt anroparna läser dess listor (math.inf = hela). Delens
        #: listlängder sammanfattas bara så noga, så att en del som innehåller
        #: sig själv ändå får en ändlig sammanfattning.
        self.djup: dict = defaultdict(int)
        self.sammanfattat: dict = {}         # del → djupet dess utdata räknades med
        self.djup_ökat: set = set()

    # ── listlängder ──

    def läs_till(self, del_: str, djup) -> None:
        if djup > self.djup[del_]:
            self.djup[del_] = djup
            self.djup_ökat.add(del_)

    def räcker(self, del_: str, djup) -> bool:
        """Är delens utdata sammanfattad minst till `djup`? Annars begärs det."""
        if self.sammanfattat.get(del_, 0) >= djup:
            return True
        self.läs_till(del_, djup)
        return False

    # ── indata ──

    def _lägg_till_anrop(self, del_: str, argument) -> bool:
        ändrad = False
        for namn, d in argument:
            etikett = _etikett(d)
            if etikett not in self.indata[del_][namn]:
                self.indata[del_][namn][etikett] = d
                ändrad = True
            if d[0] == "lat" and d[2] not in self.projektioner[del_][(namn, etikett)]:
                self.projektioner[del_][(namn, etikett)].add(d[2])
                ändrad = True
        return ändrad

    def _begränsning(self, del_: str, namn: str, etikett: str) -> dict:
        """Fält som varje anropare läst före anropet, med de värden de läste."""
        projektioner = self.projektioner[del_][(namn, etikett)]
        if not projektioner:
            return {}
        per_anrop = [defaultdict(set) for _ in projektioner]
        for mål, projektion in zip(per_anrop, projektioner):
            for rel, e in projektion:
                mål[rel].add(e)
        gemensamma = set.intersection(*(set(p) for p in per_anrop))
        return {rel: frozenset().union(*(p[rel] for p in per_anrop))
                for rel in gemensamma}

    # ── utdata ──

    def utdata_för(self, del_: str, argument) -> set:
        konstanter = {namn: _etikett(d) for namn, d in argument if d[0] == "värde"}
        ut: set = set()
        for etiketter, sorter in self.utdata[del_]:
            if all(etiketter.get(n) == e for n, e in konstanter.items()):
                ut |= sorter
        return ut

    # ── genomgången ──

    def _kör(self, del_: str, körning: Körning):
        orakel = körning.orakel
        u = SymUppslag(körning, self.verklig, self.lexikon)
        r = object.__new__(self.klass)
        r.u = u
        for namn, metod in self.delar.items():
            setattr(r, namn, (lambda n, m: lambda *a, **kw:
                              körning.anropa(n, m, a, kw))(namn, metod))
        metod = self.metoder[del_]
        kwargs, etiketter = {}, {}
        for namn in list(self.signaturer[del_].parameters)[1:]:
            val = self.indata[del_][namn]
            etikett = orakel.välj(("argument", namn), sorted(val))
            d = val[etikett]
            etiketter[namn] = etikett
            if d[0] == "värde":
                kwargs[namn] = d[1]
            elif d[0] == "symbol":
                kwargs[namn] = _symbol(f"{namn}", d[1])
            else:
                kwargs[namn] = _lat(LATA[d[1]], körning, namn,
                                    self._begränsning(del_, namn, etikett))
        return etiketter, metod(r, **kwargs)

    def gå_igenom(self, del_: str) -> Delkarta:
        karta = Delkarta(del_, genomgångar=self.kartor.get(del_, Delkarta(del_)).genomgångar + 1)
        start = time.perf_counter()
        djup = self.djup[del_]
        if djup > self.sammanfattat.get(del_, 0):
            # En noggrannare sammanfattning räknas från början. Annars lever
            # den grövre kvar i delens anrop till sig själv — passivens be i
            # verbfrasen — och blir aldrig exakt.
            self.utdata[del_] = []
        nya_utdata: list = []
        nya_anrop: list = []
        prefix: list[int] | None = []
        körningar = 0
        while prefix is not None:
            if körningar >= self.TAK:
                karta.tak = True
                break
            körningar += 1
            if körningar % 100_000 == 0:
                print(f"    … {del_}: {körningar} vägar, {dict(karta.vägar)}, "
                      f"{time.perf_counter() - start:.0f} s", flush=True)
            orakel = Orakel(prefix)
            körning = Körning(self, orakel)
            try:
                etiketter, resultat = self._kör(del_, körning)
                karta.vägar["klar"] += 1
                sorter = _utdatasort(resultat, djup)
                # Står delens lista för en annan dels okända ord, läses de
                # orden minst lika långt.
                if resultat is not None and not isinstance(resultat, str):
                    for o in resultat:
                        if isinstance(o, SymOrd) and o.del_ is not None:
                            self.läs_till(o.del_, djup)
                nya_utdata.append((etiketter, sorter))
                karta.utfall.add((tuple(körning.händelser), frozenset(sorter)))
                karta.klara.append(Väg(
                    tuple(sorted(etiketter.items())),
                    tuple((v[0], v[3]) for v in orakel.val
                          if not (isinstance(v[0], tuple) and v[0][0] == "argument")),
                    tuple(körning.händelser), tuple(körning.anropsställen),
                    frozenset(sorter), tuple(sorted(körning.ordbeskrivning.items()))))
            except RenderingsFel:
                karta.vägar["vägrar"] += 1
            except Förbigång as e:
                karta.vägar["förbigång"] += 1
                karta.förbigångar[str(e)] += 1
            except Vänta:
                karta.vägar["väntar"] += 1
            except Exception as e:                                  # noqa: BLE001
                karta.vägar["krasch"] += 1
                rad = e.__traceback__
                while rad.tb_next is not None:
                    rad = rad.tb_next
                karta.kraschar[f"{type(e).__name__}: {e} "
                               f"({rad.tb_frame.f_code.co_name}:{rad.tb_lineno})"] += 1
            prefix = orakel.nästa()
            # Anrop som gjordes innan vägen vägrade eller väntade är ändå
            # anrop: delen skulle ha renderats, och dess indata ska med.
            nya_anrop.extend(körning.anrop)
        karta.sekunder = time.perf_counter() - start
        self.kartor[del_] = karta
        self.utdata[del_] = nya_utdata
        self.sammanfattat[del_] = djup
        return karta, nya_anrop

    def rita(self, rapport=print) -> dict[str, Delkarta]:
        """Gå igenom alla delar tills varken indata eller utdata ändras."""
        self.indata["rendera"]["m"]["lat:Mening"] = ("lat", "Mening", frozenset())
        kö = deque(["rendera"])
        i_kö = {"rendera"}
        while kö:
            del_ = kö.popleft()
            i_kö.discard(del_)
            gamla = {(tuple(sorted(e.items())), frozenset(s))
                     for e, s in self.utdata[del_]}
            gammalt_djup = self.sammanfattat.get(del_)
            karta, anrop = self.gå_igenom(del_)
            if rapport:
                rapport(f"  {del_:18} genomgång {karta.genomgångar}: "
                        f"{dict(karta.vägar)}  {karta.sekunder:.1f} s")
            for barn, argument in anrop:
                self.anropare[barn].add(del_)
                if self._lägg_till_anrop(barn, argument) and barn not in i_kö:
                    kö.append(barn)
                    i_kö.add(barn)
            nya = {(tuple(sorted(e.items())), frozenset(s))
                   for e, s in self.utdata[del_]}
            # Anropare som väntade på en noggrannare sammanfattning går om även
            # när den blev likadan.
            if nya != gamla or self.sammanfattat[del_] != gammalt_djup:
                for förälder in self.anropare[del_]:
                    if förälder not in i_kö:
                        kö.append(förälder)
                        i_kö.add(förälder)
            for ökad in sorted(self.djup_ökat):
                if ökad not in i_kö:
                    kö.append(ökad)
                    i_kö.add(ökad)
            self.djup_ökat.clear()
        return self.kartor

    def spara(self, fil) -> None:
        """Spara vägarna, så att sammansättningen slipper rita kartan igen."""
        data = {"språk": self.språk,
                "parametrar": {n: list(s.parameters)[1:] for n, s in self.signaturer.items()},
                "vägar": {n: k.klara for n, k in self.kartor.items()}}
        Path(fil).write_bytes(pickle.dumps(data))


class _Avläsare(pickle.Unpickler):
    """Kartan sparas oftast av `python -m`, och då heter modulen `__main__`."""

    def find_class(self, modul, namn):
        if modul == "__main__" and namn == "Väg":
            return Väg
        return super().find_class(modul, namn)


def ladda(fil) -> dict:
    """En sparad karta: {"språk", "parametrar": del → namn, "vägar": del → [Väg]}."""
    with open(fil, "rb") as f:
        return _Avläsare(f).load()


def main() -> None:
    språk = sys.argv[1] if len(sys.argv) > 1 else "sv"
    conn = sqlite3.connect("sprak.db")
    ritare = Kartritare(språk, conn)
    start = time.perf_counter()
    print(f"Kartan för {språk}:")
    kartor = ritare.rita()
    if len(sys.argv) > 2:
        ritare.spara(sys.argv[2])
        print(f"sparade vägarna i {sys.argv[2]}")
    print(f"\n{'del':18} {'vägar':>9} {'klara':>8} {'vägrar':>7} {'förbi':>6} "
          f"{'krasch':>6} {'väntar':>6} {'utfall':>7} {'genomg.':>7} {'läses':>6}")
    for namn, k in sorted(kartor.items()):
        djup = ritare.sammanfattat.get(namn, 0)
        print(f"{namn:18} {sum(k.vägar.values()):>9} {k.vägar['klar']:>8} "
              f"{k.vägar['vägrar']:>7} {k.vägar['förbigång']:>6} "
              f"{k.vägar['krasch']:>6} {k.vägar['väntar']:>6} {len(k.utfall):>7} "
              f"{k.genomgångar:>7} {'hela' if djup == math.inf else djup:>6}"
              f"{'  TAK' if k.tak else ''}")
    print(f"\n{time.perf_counter() - start:.1f} s totalt")
    for namn, k in sorted(kartor.items()):
        for text, n in k.förbigångar.most_common(5):
            print(f"  FÖRBIGÅNG {namn} ×{n}: {text}")
        for text, n in k.kraschar.most_common(5):
            print(f"  KRASCH {namn} ×{n}: {text}")


if __name__ == "__main__":
    main()
