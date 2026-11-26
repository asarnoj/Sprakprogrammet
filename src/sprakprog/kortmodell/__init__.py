"""Kortmodellen — steg 3 i kärnans byggordning (KÄRNAN 3 och punkt 9).

Två frågor besvaras här, och ingen av dem med något skrivet för hand.

VILKA KORT EN FORM BESTÅR AV (3.4). En form är ordet plus de formkort som
bestämde den: klassens ändelse, ljudreglerna och ordets undantagskort.
Böjningsreglerna i `bojning/` förutsäger formen och namnger ändelsens klass.
Vilka undantag och ljudregler en form beror på räknas ut på samma sätt som
spåret räknar ut positioner: kortet tas bort, formerna förutsägs igen, och de
former som ändras är kortets. `köper` bestämmer därför också `köpte` och
`köpt`, och ljudregeln i `kände` också `känt`.

VILKET KORT ETT REDOVISAT BESLUT ÄR (3.2, 8.3). Ett val ger ett kort per
utfall, en ordningsregel ett kort, en egenskap ett kort per ord och egenskap,
och en rektion ett kort per styrande ord, slot och krav.

Vilken DEL av formen varje kort står för (3.4, 7.3) räknas inte ut här än.
Den behövs först av rättningen.

Paketet hör till den nya kärnan och importerar inget ur den gamla (`kort`,
`generator`).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..bojning import Spår, en, sv
from ..bojning.kontroll import huvudformer
from ..rendering.spår import Beslut, Utskrift
from ..rendering.uppslag import Uppslag

REGLER = {"sv": sv, "en": en}

#: Ordfamiljen växer med ordförrådet, mönsterfamiljen gör det inte (3.2).
ORDFAMILJEN = frozenset({"ord", "oregelbunden", "egenskap", "rektion"})


class Kortfel(Exception):
    """Kortmodellen, böjningsreglerna och datan stämmer inte med varandra."""


@dataclass(frozen=True, slots=True, order=True)
class Kort:
    """Ett kort. Identiteten är språk, typ och nyckel (3.2, 3.10).

        ord           (koncept, variant)
        oregelbunden  (koncept, variant, cell) — cellen som visar undantaget
        ändelse       (ordklass, klass, cell)
        egenskap      (koncept, namn)
        rektion       (koncept, slot, namn)
        regel         ("val", val, utfall) · ("ordning", namn) · ("ljud", namn)
    """
    språk: str
    typ: str
    nyckel: tuple

    @property
    def familj(self) -> str:
        return "ord" if self.typ in ORDFAMILJEN else "mönster"

    def __str__(self) -> str:
        return f"{self.typ}:{'/'.join(str(x) for x in self.nyckel if x != '')}"


class Formtabell:
    """(lexem, cell) → korten formen består av, med ordkortet först."""

    def __init__(self, u: Uppslag) -> None:
        if u.språk not in REGLER:
            raise Kortfel(f"{u.språk}: böjningsreglerna (steg 0) finns inte än")
        self.u, self.språk, self.regler = u, u.språk, REGLER[u.språk]
        self._tabell: dict[int, dict[str, tuple[Kort, ...]]] = {}
        #: (lexem-id, cell): former som bryter mot en regel utan undantag
        self.datafel: set[tuple[int, str]] = set()
        #: (lexem-id, cell): former i celler böjningsreglerna inte tar upp
        self.utan_regel: set[tuple[int, str]] = set()

    def former(self, lexem) -> dict[str, tuple[Kort, ...]]:
        if lexem["id"] not in self._tabell:
            self._tabell[lexem["id"]] = self._räkna(lexem)
        return self._tabell[lexem["id"]]

    def kort(self, lexem, cell: str) -> tuple[Kort, ...]:
        former = self.former(lexem)
        if cell not in former:
            raise Kortfel(f"{self.språk}/{lexem['lemma']}: cellen {cell!r} har ingen form")
        return former[cell]

    def _räkna(self, lexem) -> dict[str, tuple[Kort, ...]]:
        celler = {c: f for c, f in self.u._celler(lexem).items() if f}
        nyckel = (lexem["nyckel"], lexem["variant"] or "")
        ord = Kort(self.språk, "ord", nyckel)

        def undantag(cell: str) -> Kort:
            return Kort(self.språk, "oregelbunden", (*nyckel, cell))

        ok = self.regler.ORDKLASSER.get(lexem["ordklass"])
        if ok is None:
            # Sluten eller oböjlig ordklass: inga regler, så varje form utom
            # grundformen är ett undantag (3.4), och ett oböjligt ord har bara
            # sitt ordkort (3.9).
            return {c: (ord,) if f == lexem["lemma"] or len(celler) == 1
                    else (ord, undantag(c)) for c, f in celler.items()}

        info, facit = ok.bas(celler, lexem)
        fel = ok.datafel(facit, info)
        prövas = {c: f for c, f in facit.items() if c in ok.ordning and c not in fel}
        kända, _ = huvudformer(ok, info, prövas)
        spår = Spår()
        förutsagt = ok.förutsäg(info, kända, spår)

        beror: dict[str, set[Kort]] = defaultdict(set)

        def ändrade(förutsägelse: dict, kort: Kort) -> None:
            for c in facit:
                if förutsägelse.get(c) != förutsagt.get(c):
                    beror[c].add(kort)

        for kortcell in kända:
            utan = {c: f for c, f in kända.items() if c != kortcell}
            ändrade(ok.förutsäg(info, utan, Spår()), undantag(kortcell))
        for regel in sorted(set().union(*spår.per_cell.values())):
            ändrade(ok.förutsäg(info, kända, Spår(frozenset({regel}))),
                    Kort(self.språk, "regel", ("ljud", regel)))

        ut: dict[str, tuple[Kort, ...]] = {}
        for cell in celler:
            if cell in fel or cell in kända:
                if cell in fel:
                    self.datafel.add((lexem["id"], cell))
                ut[cell] = (ord, undantag(cell))
            elif cell not in ok.ordning:
                if facit[cell] == info["bas"]:
                    ut[cell] = (ord,)
                else:
                    self.utan_regel.add((lexem["id"], cell))
                    ut[cell] = (ord, undantag(cell))
            elif förutsagt.get(cell) != facit[cell]:
                raise Kortfel(
                    f"{self.språk}/{lexem['lemma']}: reglerna ger {förutsagt.get(cell)!r} "
                    f"i {cell}, datan {facit[cell]!r}, och inget kort täcker skillnaden")
            else:
                ändelse = ((Kort(self.språk, "ändelse",
                                 (lexem["ordklass"], spår.klasser[cell], cell)),)
                           if cell in spår.klasser else ())
                ut[cell] = (ord, *ändelse, *sorted(beror[cell]))
        return ut


def beslutskort(språk: str, b: Beslut) -> Kort:
    """Kortet ett redovisat beslut är. Id:ts form står i `Uppslag`."""
    if b.sort == "regel":
        return Kort(språk, "regel", ("val", b.id[2], b.utfall))
    if b.sort == "ordning":
        return Kort(språk, "regel", ("ordning", b.id[2]))
    if b.sort == "egenskap":
        return Kort(språk, "egenskap", (b.id[2], b.id[3]))
    if b.sort == "rektion":
        return Kort(språk, "rektion", tuple(b.id[2:5]))
    raise Kortfel(f"okänd sorts beslut: {b.sort!r}")


def meningens_kort(tabell: Formtabell, ut: Utskrift) -> list[tuple[Kort, frozenset]]:
    """Varje kort i meningen med sina platser, ("ord", i) och ("lucka", i).

    Formkorten står på sitt ords plats. Ett beslut som inte syns prövades inte
    och tas inte med (6.2).
    """
    kort: list[tuple[Kort, frozenset]] = []
    for i, o in enumerate(ut.ord):
        lexem = tabell.u.lexem(o.koncept, o.variant)
        for k in tabell.kort(lexem, o.cell):
            kort.append((k, frozenset({("ord", i)})))
    for b in ut.beslut:
        if b.syns:
            platser = {("ord", i) for i in b.positioner} | {("lucka", g) for g in b.luckor}
            kort.append((beslutskort(tabell.språk, b), frozenset(platser)))
    return kort
