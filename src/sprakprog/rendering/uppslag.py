"""Uppslagslagret — koncept + cell → ordform, och redovisningen av renderarens beslut.

Renderaren ska aldrig känna till Former-tabellens axelkodning. Den frågar
efter "bok, bestämd singular" via cell-ID och får tillbaka en sträng.

Cellmatchningen återanvänder `_former_per_cell` från granskningen i stället
för att skriva en ny. Den logiken har rättats två gånger (SCHEMA.md §5 om
bitmask-kollaps, och kandidaten som tillhör en mer specifik cell) och en
andra implementation skulle med säkerhet återinföra samma buggar.

REDOVISNINGEN (KÄRNAN 8.3). Allt renderaren vet om språket hämtas här, och
därför är det här varje beslut blir synligt. Fem sorters anrop bär kunskap
som kan bli kort:

    form       ordformen i en cell
    egenskap   en egenskap hos ordet som syns på ett annat ord (genus)
    rektion    vad ett styrande ord kräver (infinitivmarkör, kasus)
    regel      ett val mellan namngivna utfall (bestämning, tempusform)
    ordning    att ett led står före ett annat (svo, adverbial_sist)

Övriga läsningar — ordklass, lemma, om en cell finns, konceptets person — bär
ingen kunskap i sig, men måste ändå gå hit så att kartan (KÄRNAN 6.7) ser dem.

När ett `Spår` är satt loggas varje kunskapsanrop, och ett beslut kan tvingas
till ett annat utfall. `rendering/spår.py` räknar på det sättet ut var ett
beslut syns: de ord som ändras när beslutet tvingas fram.
"""

from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass

from ..generering.granskning import _former_per_cell
from ..kaikki_mappning.paradigm import ladda_legend, ladda_slot
from .spec import NAKEN, TILLTAL, Numerus, RenderingsFel

# docs/BITMASK.md §11. Enda biten uppslaget behöver känna till, och bara
# för att välja mellan vem och vad.
MÄNSKLIG = 32

#: Kolumner på Koncept som renderaren får läsa. Listan är sluten, så att en
#: läsning av något annat syns som ett fel i stället för att gå förbi.
KONCEPTKOLUMNER = ("person", "numerus", "räknebar", "semantik")

#: Hur ett reflexivt verb syns i lemmat (KÄRNAN 3.5, TYSTA_BESLUT A8). Bara de
#: språk vars renderare läser egenskapen genom `egenskap` står här.
REFLEXIVT_LEMMA = {"sv": lambda lemma: lemma.endswith(" sig")}


def frasdel(metod):
    """Märker en renderarmetod som en DEL: något kartan går igenom för sig.

    En del är en frasfunktion med uttryckliga indata — specobjektet den får och
    de argument den anropas med. Kartan (`rendering/karta.py`) ersätter de andra
    delarna med stubbar när den går igenom en del, och det är märkningen som
    säger var gränserna går (KÄRNAN 6.7).
    """
    metod.frasdel = True
    return metod


def _anropsställe() -> tuple[str, int]:
    """Funktionen och raden i renderaren som gjorde uppslaget."""
    ram = sys._getframe(1)
    while ram.f_code.co_filename == __file__:
        ram = ram.f_back
    return ram.f_code.co_name, ram.f_lineno


@dataclass(frozen=True, slots=True)
class Val:
    """Ett beslut mellan namngivna utfall. Varje utfall är ett kort.

    Utfallen är de sätt språket självt kan realisera samma sak på. Renderaren
    grenar på det utfall `Uppslag.regel` lämnar tillbaka och inte på specen,
    så att vart och ett av dem kan tvingas fram.
    """
    namn: str
    utfall: tuple[str, ...]


class Ord(str):
    """Ett utskrivet ord, och vad det slogs upp som.

    `nyckel` är ("form", led, ställe, koncept, n): det n:te uppslaget av
    konceptet från samma ställe i renderaren, inom samma led i specen. Nyckeln
    står still när en ordföljdsregel flyttar ordet och när ett uppslag i ett
    annat led tillkommer eller försvinner — två renderingar av samma spec kan
    därför jämföras ord för ord. Ledet skiljer subjektets "den" från objektets,
    och stället skiljer subjektets "jag" från reflexivets "mig", som båda är
    `pronomen_1sg`. Nyckeln sätts bara när ett spår är aktivt.
    """
    koncept: str
    variant: str | None
    cell: str
    nyckel: tuple | None = None


class Spår:
    """Vad en rendering redovisade, och vilka beslut som tvingas fram.

    Ett besluts id är dess sort, nyckel och ordningsnummer bland beslut med
    samma nyckel. I en tvingad rendering är id:t detsamma som i den
    ursprungliga fram till beslutet, eftersom renderingen är deterministisk.
    """

    def __init__(self, tvång: dict | None = None) -> None:
        self.händelser: list[tuple] = []
        self.tvång: dict = dict(tvång or {})
        self._räknare: Counter = Counter()

    def id(self, *nyckel) -> tuple:
        n = self._räknare[nyckel]
        self._räknare[nyckel] += 1
        return (*nyckel, n)


class Uppslag:
    """Slår upp lexem och former för ETT språk."""

    def __init__(self, conn: sqlite3.Connection, språk: str) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.språk = språk
        self._legend = ladda_legend()
        self._slot: dict[str, object] = {}
        # Cellmatchningen är dyr och svaret beror bara på lexemet. Utan
        # cache körs den om för varje enskild ordform: ett brett svep över
        # databasen gick från minuter till sekunder med den här raden.
        self._cellcache: dict[int, dict[str, str]] = {}
        self._konceptcache: dict[tuple[str, str], object] = {}
        self._domän: dict = {}
        #: Sätts av `rendering/spår.py` under en spårad rendering.
        self.spår: Spår | None = None
        self._led: list[str] = []

    @contextmanager
    def led(self, namn: str):
        """Renderingen går in i specens led `namn`: subjekt, objekt, attribut0.

        Ledens väg ingår i varje ords och besluts id. Den är också gränsen
        mellan de delar kartan går igenom var för sig (KÄRNAN 6.7).
        """
        self._led.append(namn)
        try:
            yield
        finally:
            self._led.pop()

    # ── lexem ────────────────────────────────────────────────────────

    def lexem(self, koncept: str, variant: str | None = None) -> sqlite3.Row:
        """Hitta lexemet för ett koncept i det här språket.

        `variant` behövs när ett koncept har flera lemman i samma språk —
        sv hans/sin, es ser/estar. Utan den är uppslaget tvetydigt och vi
        vägrar hellre än gissar.
        """
        rader = self.conn.execute(
            """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id
               WHERE k.nyckel = ? AND l.språk = ?""",
            (koncept, self.språk),
        ).fetchall()
        if not rader:
            raise RenderingsFel(f"{self.språk}: inget lexem för konceptet {koncept!r}")
        if len(rader) == 1:
            return rader[0]

        träffar = [r for r in rader if r["variant"] == variant]
        if len(träffar) == 1:
            return träffar[0]

        # Etiketten 'neutral' betyder omarkerad form: ja 私 mot 僕, あなた mot
        # 君. Skillnaden är register, som ligger utanför projektets scope
        # (se ARBETSLOGG_till_2026-08-15.md), så den omarkerade formen är rätt default när
        # meningen inte säger något annat.
        if variant is None:
            neutrala = [r for r in rader if r["variant"] == "neutral"]
            if len(neutrala) == 1:
                return neutrala[0]
        varianter = sorted(str(r["variant"]) for r in rader)
        raise RenderingsFel(
            f"{self.språk}: {koncept!r} har {len(rader)} lemman "
            f"(varianter: {', '.join(varianter)}) och variant={variant!r} "
            f"pekar inte ut ett enda")

    # ── läsningar utan kunskap ───────────────────────────────────────

    def ordklass(self, lexem: sqlite3.Row) -> str:
        return lexem["ordklass"]

    def lemma(self, lexem: sqlite3.Row) -> str:
        """Lemmat, för felmeddelanden. Renderaren fattar inga beslut på det."""
        return lexem["lemma"]

    def har_form(self, lexem: sqlite3.Row, cell: str) -> bool:
        """Finns cellen, och är den ifylld?"""
        return bool(self._celler(lexem).get(cell))

    def koncept(self, nyckel: str, namn: str):
        """En kolumn på Koncept: person, numerus, räknebarhet eller semantik."""
        if namn not in KONCEPTKOLUMNER:
            raise ValueError(f"Koncept.{namn} är ingen läsbar kolumn "
                             f"({', '.join(KONCEPTKOLUMNER)})")
        k = (nyckel, namn)
        if k not in self._konceptcache:
            rad = self.conn.execute(
                f"SELECT {namn} FROM Koncept WHERE nyckel = ?", (nyckel,)).fetchone()
            self._konceptcache[k] = rad[0] if rad else None
        return self._konceptcache[k]

    def mänsklig(self, koncept: str) -> bool:
        return bool((self.koncept(koncept, "semantik") or 0) & MÄNSKLIG)

    def tilltal(self, koncept: str) -> str | None:
        """Vem subjektskonceptet tilltalar i en imperativ — 2sg, 2pl, artig, 1pl —
        eller None. Renderaren jämför aldrig konceptnycklar själv (KÄRNAN 6.7)."""
        return TILLTAL.get(koncept)

    # ── former ───────────────────────────────────────────────────────

    def _celler(self, lexem: sqlite3.Row) -> dict[str, str]:
        if lexem["id"] not in self._cellcache:
            rader = self.conn.execute(
                "SELECT * FROM Former WHERE lexem_id = ?", (lexem["id"],)).fetchall()
            self._cellcache[lexem["id"]] = _former_per_cell(
                rader, self._slot_för(lexem["ordklass"]))
        return self._cellcache[lexem["id"]]

    def infinitivmarkör(self, verb: str) -> str | None:
        """Konceptnyckeln för markören framför ett infinitivkomplement.

        None = ren infinitiv. Läses ur det språkspecifika mönstret, samma
        väg som kasusrektionen och den romanska io-prepositionen.

        GÅR GENOM `rektion`, också när markören saknas: att ett modalverb tar
        ren infinitiv — "vill läsa", aldrig "vill att läsa" — är lika mycket
        kunskap om verbet som att ett annat tar markören (TYSTA_BESLUT A6).
        """
        rad = self.conn.execute(
            """SELECT p.nyckel FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               JOIN Koncept p ON p.id = mk.preposition_koncept_id
               WHERE k.nyckel = ? AND m.språk = ? AND mk.slot = 'komplement'""",
            (verb, self.språk)).fetchone()
        return self.rektion(verb, "komplement", "infinitivmarkör",
                            rad["nyckel"] if rad else None)

    def kontrollera_naken(self, nf) -> None:
        """En naken SINGULAR kräver ett oräknebart huvudord.

        "vatten", "vin", "kaffe" går bra; "bok" gör det inte — "hon läser
        bok" finns inte i något av de sju språken. Plural är fri: "böcker är
        dyra" är den generiska frasen för räknebara ord, och oräknebara har
        ingen plural att be om.

        `Koncept.räknebar` fylldes långt innan någon konstruktion behövde
        den. Det här är den första som gör det — samma sak som hände med
        MönsterKrav.frastyp och hjälpverbskolumnen.
        """
        if nf.bestämdhet not in NAKEN or nf.numerus is not Numerus.SG:
            return
        if self.koncept(nf.koncept, "räknebar"):
            raise RenderingsFel(
                f"{self.språk}/{nf.koncept}: naken singular kräver ett "
                f"oräknebart ord — 'vatten' går, 'bok' gör det inte. "
                f"Räknebara ord tar artikel i singular eller står i plural")

    def frågepronomen(self, koncept: str) -> str:
        """vem eller vad — avgörs på det EFTERFRÅGADE, inte på slotten.

        "Vem läser boken?" men "Vad läser flickan?": samma slot, olika ord,
        och skillnaden ligger i om svaret är mänskligt. Semantikbiten som
        restriktionerna redan använder räcker för att avgöra det, så
        frågeordet behöver ingen egen taggning.
        """
        return ("frågepronomen_person" if self.mänsklig(koncept)
                else "frågepronomen_sak")

    def _slot_för(self, ordklass: str):
        if ordklass not in self._slot:
            self._slot[ordklass] = ladda_slot(
                self.språk, ordklass, legend=self._legend)
        return self._slot[ordklass]

    def form(self, lexem: sqlite3.Row, cell: str) -> Ord:
        """Ordformen i en given cell. Kastar hellre än returnerar tomt."""
        celler = self._celler(lexem)
        if cell not in celler:
            känd = ", ".join(sorted(celler))
            raise RenderingsFel(
                f"{self.språk}/{lexem['lemma']}: cellen {cell!r} finns inte i "
                f"{lexem['ordklass']}-paradigmet (har: {känd})")
        form = celler[cell]
        if not form:
            raise RenderingsFel(
                f"{self.språk}/{lexem['lemma']}: cellen {cell!r} är tom — "
                f"formen saknas i databasen")
        ord = Ord(form)
        ord.koncept, ord.variant, ord.cell = lexem["nyckel"], lexem["variant"], cell
        if self.spår is not None:
            ord.nyckel = self.spår.id("form", tuple(self._led), _anropsställe(),
                                      lexem["nyckel"])
            self.spår.händelser.append(("form", ord))
        return ord

    def form_för(self, koncept: str, cell: str, variant: str | None = None) -> Ord:
        return self.form(self.lexem(koncept, variant), cell)

    # ── kunskap som kan bli kort ─────────────────────────────────────

    def egenskap(self, lexem: sqlite3.Row, namn: str):
        """En LEXIKAL egenskap som avgör vilken cell som ska slås upp.

        Genus är inget cellvärde utan det som VÄLJER cellen: `das` slogs upp i
        `n_nom` därför att Kind är neutrum, och den kunskapen är ett eget kort
        som meningen prövade. Att läsa `lexem["genus"]` direkt förbi den här
        gör kortet osynligt.

        Egenskapen loggas varje gång den läses, också där den inte syns — i
        svensk plural avgör genuset ingenting. Om den syntes räknas ut av
        spåret, som tvingar fram det andra genuset och ser vilka ord som
        ändras.
        """
        värde = self._egenskapsvärde(lexem, namn)
        # Saknas värdet finns inget att kunna: "du" har inget genus i datan, och
        # renderaren faller tillbaka på utrum. Då redovisas ingen egenskap.
        if self.spår is None or värde is None:
            return värde
        id = self.spår.id("egenskap", tuple(self._led), lexem["nyckel"], namn)
        värde = self.spår.tvång.get(id, värde)
        self.spår.händelser.append(("egenskap", id, värde, self.egenskapsdomän(namn)))
        return värde

    def _egenskapsvärde(self, lexem: sqlite3.Row, namn: str):
        if namn == "reflexiv":
            return REFLEXIVT_LEMMA[self.språk](lexem["lemma"])
        if namn == "komparation":
            # Syntetisk komparation finns precis när komparativcellen är
            # ifylld; för svenskan har de 111 adjektiven antingen alla tre
            # komparationscellerna eller ingen (mätt 2026-09-13).
            return "syntetisk" if self.har_form(lexem, "komp") else "perifrastisk"
        return lexem[namn]

    def egenskapsdomän(self, namn: str) -> tuple | None:
        """Egenskapens möjliga värden i språket, eller None om de inte är kända."""
        if namn == "genus":
            if "genus" not in self._domän:
                self._domän["genus"] = tuple(r[0] for r in self.conn.execute(
                    """SELECT DISTINCT genus FROM Lexem
                       WHERE språk = ? AND genus IS NOT NULL ORDER BY genus""",
                    (self.språk,)))
            return self._domän["genus"]
        return {"reflexiv": (False, True),
                "komparation": ("syntetisk", "perifrastisk")}.get(namn)

    def egenskap_för(self, koncept: str, namn: str, variant: str | None = None):
        return self.egenskap(self.lexem(koncept, variant), namn)

    def rektion(self, koncept: str, slot: str, namn: str, värde):
        """Vad ett STYRANDE ord kräver av en slot.

        Genus är ett faktum om SUBSTANTIVET; rektion är ett faktum om ordet som
        styr frasen — `helfen` tar dativ, `vilja` tar ren infinitiv — så nyckeln
        är det styrande konceptet plus slotten, inte det uppslagna lexemet.
        """
        if self.spår is None:
            return värde
        id = self.spår.id("rektion", tuple(self._led), koncept, slot, namn)
        värde = self.spår.tvång.get(id, värde)
        self.spår.händelser.append(
            ("rektion", id, värde, self.rektionsdomän(slot, namn)))
        return värde

    def rektionsdomän(self, slot: str, namn: str) -> tuple | None:
        if (slot, namn) == ("komplement", "infinitivmarkör"):
            k = ("rektion", slot, namn)
            if k not in self._domän:
                self._domän[k] = (None, *(r[0] for r in self.conn.execute(
                    """SELECT DISTINCT p.nyckel FROM Mönster m
                       JOIN MönsterKrav mk ON mk.mönster_id = m.id
                       JOIN Koncept p ON p.id = mk.preposition_koncept_id
                       WHERE m.språk = ? AND mk.slot = 'komplement'
                       ORDER BY p.nyckel""", (self.språk,))))
            return self._domän[k]
        return None

    def regel(self, val: Val, utfall: str) -> str:
        """Renderaren väljer `utfall` i beslutet `val`. Lämnar tillbaka utfallet.

        Renderaren ska grena på det som kommer tillbaka och inte på specen: i
        en tvingad rendering är det ett annat utfall än det specen gav.
        """
        if utfall not in val.utfall:
            raise ValueError(f"{val.namn}: {utfall!r} är inget av utfallen "
                             f"{val.utfall}")
        if self.spår is None:
            return utfall
        id = self.spår.id("regel", tuple(self._led), val.namn)
        utfall = self.spår.tvång.get(id, utfall)
        self.spår.händelser.append(("regel", id, utfall, val.utfall))
        return utfall

    def ordning(self, namn: str, före, efter) -> None:
        """Ordföljdsregeln `namn`: varje ord i `före` står före varje ord i `efter`.

        Renderaren bygger ordningen själv; anropet redovisar den. Spåret
        kontrollerar att regeln stämmer med den färdiga meningen, så att
        redovisningen inte kan glida isär från koden. Tomma led loggas inte —
        då finns inget att ordna.
        """
        # Den gamla kärnans logg, som känner reglerna under det här namnet.
        # Tas bort när den gamla kärnan raderas (KÄRNAN 8.1).
        self.ordföljd(namn)
        if self.spår is not None and före and efter:
            id = self.spår.id("ordning", tuple(self._led), namn)
            self.spår.händelser.append(("ordning", id, tuple(före), tuple(efter)))

    def ordföljd(self, regel: str) -> None:
        """Den gamla kärnans ordföljdslogg. Nya renderare anropar `ordning`.

        Står kvar för de sex renderare som ännu inte redovisar enligt KÄRNAN
        8.3, och för den gamla generatorn som lyssnar på den. Tas bort med den
        gamla kärnan.
        """
