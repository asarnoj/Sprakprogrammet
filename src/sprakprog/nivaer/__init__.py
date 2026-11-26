"""Nivåerna — steg 4 i kärnans byggordning (KÄRNAN 4 och punkt 9).

En nivå är det minsta steg som gör minst ett nytt kort prövbart i princip (4.1).
Nivåkorten är de som inte växer med ordförrådet: mönsterkorten (ändelser och
regler) och korten för slutna ordklasser. Ett korts krav är de andra nivåkorten
i en mening som prövar kortet, och nivåerna är grafens starka komponenter.

Kravet är version 1 (4.2): nivåkorten i den FÖRSTA mening sammansättningen
hittar. Den frågan går fort, eftersom sökningen slutar vid första meningen.
Med `krymp` förbjuds sedan ett kort i taget, och mängden blir bevisat minst —
men varje nej kräver att allt som går att bygga gås igenom, och det tar dygn för
ett språk. Krympningen ändrar bara ordningen mellan korten, aldrig vad som går
att pröva. Kortets andra minsta mängder, och valet mellan dem efter täckning,
kommer med frekvenserna (steg P2).
"""

from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass
from typing import Callable, Iterable

from ..kortmodell import Formtabell, Kort
from ..sammansattning import Sammansättare, Träff

#: Ordklasser som inte växer med ordförrådet (KÄRNAN 4.1): pronomen, artiklar,
#: possessiv, räkneord och de andra funktionsordens klasser. Ett ord i en öppen
#: klass — substantiv, verb, adjektiv, adverb, interjektion — är upplåst från
#: början (3.1), också när renderaren använder det som hjälpverb.
SLUTNA_ORDKLASSER = frozenset({
    "Pronomen", "Possessiv", "Demonstrativ", "Frågepronomen", "Relativpronomen",
    "Frågadverb", "Interrogativdeterminant", "Artikel", "Konjunktion",
    "Subjunktion", "Preposition", "Negationsadverb", "Räkneord", "Kvantifikator",
})


class Nivåkort:
    """Avgör vilka kort som är nivåkort, och räknar upp dem."""

    def __init__(self, tabell: Formtabell) -> None:
        self.tabell = tabell
        self.u = tabell.u
        self._ordklass: dict[str, str] = {}
        self._nycklar: frozenset[str] | None = None
        self._varianter: dict[str, tuple[str, ...]] = {}

    def ordklass(self, koncept: str) -> str:
        if koncept not in self._ordklass:
            rad = self.u.conn.execute(
                "SELECT ordklass FROM Koncept WHERE nyckel = ?", (koncept,)).fetchone()
            self._ordklass[koncept] = rad[0] if rad else ""
        return self._ordklass[koncept]

    def nycklar(self) -> frozenset[str]:
        """Varje konceptnyckel i databasen, för att känna igen dem i en spec."""
        if self._nycklar is None:
            self._nycklar = frozenset(
                r[0] for r in self.u.conn.execute("SELECT nyckel FROM Koncept"))
        return self._nycklar

    def varianter(self, koncept: str) -> tuple[str, ...]:
        """Konceptets varianter i språket, som ordkortens andra nyckelled."""
        if koncept not in self._varianter:
            self._varianter[koncept] = tuple(
                r[0] or "" for r in self.u.conn.execute(
                    """SELECT l.variant FROM Lexem l JOIN Koncept k
                       ON k.id = l.koncept_id
                       WHERE k.nyckel = ? AND l.språk = ?""",
                    (koncept, self.tabell.språk)))
        return self._varianter[koncept]

    def __call__(self, kort: Kort) -> bool:
        if kort.typ in ("ändelse", "regel"):
            return True
        if kort.typ in ("ord", "oregelbunden"):
            return self.ordklass(kort.nyckel[0]) in SLUTNA_ORDKLASSER
        return False

    def alla(self, karta: dict) -> set[Kort]:
        """Varje nivåkort i språket: regler ur kartans vägar, formkort ur tabellen."""
        språk = self.tabell.språk
        ut: set[Kort] = set()
        for vägar in karta["vägar"].values():
            for väg in vägar:
                for h in väg.händelser:
                    if h[0] == "regel":
                        ut.add(Kort(språk, "regel", ("val", h[2], h[3])))
                    elif h[0] == "ordning":
                        ut.add(Kort(språk, "regel", ("ordning", h[2])))
        rader = self.u.conn.execute(
            """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id WHERE l.språk = ?""",
            (språk,)).fetchall()
        for lexem in rader:
            for kort in self.tabell.former(lexem).values():
                ut.update(k for k in kort if self(k))
        return ut


class Krav:
    """Ett nivåkorts minsta kortmängd (KÄRNAN 4.2)."""

    def __init__(self, sammansättare: Sammansättare, nivå: Nivåkort) -> None:
        self.s, self.nivå = sammansättare, nivå
        self.frågor = 0

    def _finns(self, mål: Kort, tillåtna: frozenset | None) -> Träff | None:
        """En mening som prövar målet av ordkort och nivåkort ur `tillåtna`
        (None = alla)."""
        nivå = self.nivå

        def tillåten(k: Kort) -> bool:
            return k == mål or not nivå(k) or tillåtna is None or k in tillåtna

        self.frågor += 1
        return self.s.finns(mål, tillåten)

    def _nivåkorten(self, träff: Träff, mål: Kort) -> frozenset:
        return frozenset(k for k in träff.kort if self.nivå(k)) - {mål}

    #: Fält som bara LÄSES när ett annat fält är sant, och vars förval är en
    #: konceptnyckel. `Mening.negation` bär `neg_inte` också när `negerad` är
    #: False — «Läses inte alls när `negerad` är falsk» (rendering/spec.py) —
    #: och utan villkoret hade varje krav fått negationsadverbet med sig. Det är
    #: enda fältet med den formen: av specens nio fält med ett strängförval är
    #: åtta StrEnum, och inget av deras värden är en konceptnyckel
    #: (mätt 2026-11-03).
    VILLKORADE_FÄLT = {"negation": "negerad"}

    def _specens_koncept(self, x) -> set[str]:
        """Varje konceptnyckel meningens SPEC faktiskt använder.

        Specen är dataklasser hela vägen ner, så en genomgång av fälten räcker.
        Ett fält som bara läses när en flagga är satt hoppas över när flaggan är
        falsk (`VILLKORADE_FÄLT`); resten tas med. Listan är annars en
        ÖVERMÄNGD med avsikt — den ska hellre innehålla ett kort för mycket än
        ett för lite, se `_tillräcklig`.
        """
        ut: set[str] = set()
        if isinstance(x, str):
            if x in self.nivå.nycklar():
                ut.add(x)
        elif dataclasses.is_dataclass(x) and not isinstance(x, type):
            for f in dataclasses.fields(x):
                villkor = self.VILLKORADE_FÄLT.get(f.name)
                if villkor and not getattr(x, villkor, False):
                    continue
                ut |= self._specens_koncept(getattr(x, f.name))
        elif isinstance(x, (list, tuple, set, frozenset)):
            for y in x:
                ut |= self._specens_koncept(y)
        return ut

    def _specens_nivåkort(self, träff: Träff) -> frozenset:
        """Nivåkorten för de ord specen använder, prövade eller inte."""
        språk = self.nivå.tabell.språk
        return frozenset(
            kort for koncept in self._specens_koncept(träff.mening)
            for variant in self.nivå.varianter(koncept)
            if self.nivå(kort := Kort(språk, "ord", (koncept, variant))))

    def _tillräcklig(self, mål: Kort, träff: Träff,
                     mängd: frozenset) -> tuple[frozenset, Träff] | None:
        """Kravet så att meningen går att BYGGA, inte bara att pröva.

        VARFÖR DET HÄR STEGET FINNS. Kravet lästes ur `träff.kort`, alltså ur de
        kort meningen PRÖVAR — och ett beslut som inte syns prövas inte (6.2).
        Men sökningen måste ändå få använda ordet. Mätt 2026-10-27:
        `regel:val/satsart/imperativ` fick kravet TOMT, eftersom dess bevis
        «Se!» → «See!» bara prövar `ord:per_se` och kortet självt. Imperativens
        subjekt skrivs inte ut och prövas därför inte, men utan ett pronomen går
        meningen inte att bygga: `finns()` svarade NEJ med bevisets två kort
        tillåtna och JA när allt var tillåtet.

        Följden var att kortet låstes upp DAG ETT — tomt krav betyder upplåst
        (4.5) — medan dess subjekt ligger på nivå 26 och kortet självt på nivå
        82. Varje dagsplan valde det, ingen mening gick att bygga, och det
        hamnade i karantän: ett brott mot 5.1, som säger att dag ett:s karantän
        ska vara tom «annars går kursen inte att börja», och mot §11:s nollkrav.

        BARA JA-FRÅGOR. Kravet är de prövade nivåkorten plus specens, och den
        enda sökfrågan är om den mängden räcker — en fråga vars svar är JA för
        både friska och trasiga kort, och ett ja kostar ~1 s (§12). Den första
        versionen frågade i stället om den SMALA mängden räckte, alltså det enda
        kortet vars svar är NEJ, och ett nej kostar hela rummet: ombygget av
        engelskan gick 13 h 45 min utan att bli klart (mätt 2026-11-02). Samma
        asymmetri som §12 beskriver, och den gör skillnad på metod, inte på
        svar.

        MÄNGDEN ÄR DÄRFÖR INTE BEVISAT MINST, och ska inte vara det: 4.2
        version 1 kräver det inte, `krymp` är det stället där minimering får
        kosta, och ett FÖR STORT krav låser bara upp kortet senare medan ett
        för litet lurar grinden (4.4) att öppna ett kort som inte går att bygga.
        Specens kandidater är inte heller fritt valda: de är orden den här
        meningen använder.

        BEVISET BLIR VERIFIERINGENS MENING, inte den som söktes fram med allt
        tillåtet. Frågan «räcker mängden?» svaras med en mening, och det är den
        meningen vi vet går att bygga av kravet. Den ursprungliga vet vi bara
        bygger av ALLT, och skulle specgenomgången ha missat ett kort den
        behöver vore beviset (3.10) inte infriat när grinden öppnar det.

        Räcker inte heller den mängden svarar metoden None, och kortet räknas
        som oprövbart.
        """
        större = mängd | (self._specens_nivåkort(träff) - {mål})
        if större == mängd:
            return mängd, träff
        bevis = self._finns(mål, större)
        return (större, bevis) if bevis is not None else None

    def mängd(self, mål: Kort,
              krymp: bool = False) -> tuple[frozenset, frozenset] | None:
        """Kortets krav OCH beviset, eller None om ingen mening prövar kortet.

        Den första mening sammansättningen hittar ger mängden (version 1, 4.2).
        Med `krymp` förbjuds ett kort i taget, och går det fortfarande att bygga
        en mening tas den mindre mängden. När inget kort går att ta bort är
        mängden bevisat minst, men varje nej kostar en uttömmande genomgång.

        BEVISET ÄR MENINGENS KORT, och det är 4.2:s egen andra halva: «Kortet
        går att pröva när kravet är infört, och meningen sparas som dess bevis
        (3.10).» Förut kastades meningen och bara kraven behölls, och då fick
        passet söka fram paketet (3.10) själv — en gång per kort och dag, med
        allt dagen redan valt tillåtet. Kostnaden växte med den tillåtna
        mängden: `regel:ordning/hjälpverb_före_huvudverb` togs på 5,3 s ensamt
        och på över två minuter när dagens tjugo valda kort var lånekort
        (mätt 2026-09-27). Beviset gör sökningen onödig: paketet är bevisets
        kort minus de införda, och beviset vilar bara på kravet, som grinden
        (4.4) redan har sett infört.

        MENINGEN SJÄLV SPARAS INTE, bara dess kort. Paketet är precis den
        mängden, och `Mening` har ingen serialisering. Den behövs först för
        3.10:s omkontroll mot entydighetsfiltret (6.5), som inte är byggt.
        """
        träff = self._finns(mål, None)
        if träff is None:
            return None
        tillräcklig = self._tillräcklig(mål, träff, self._nivåkorten(träff, mål))
        if tillräcklig is None:
            return None
        mängd, träff = tillräcklig
        krympte = krymp
        while krympte:
            krympte = False
            for kort in sorted(mängd, key=str):
                mindre = self._finns(mål, mängd - {kort})
                if mindre is None:
                    continue
                # Också den mindre meningen kan behöva ord den inte prövar, så
                # kravet räknas om likadant. Krympningen räknas bara som en
                # krympning om mängden blev strikt mindre — annars hade
                # borttagandet och påläggandet kunnat växla om varandra i evighet.
                nytt = self._tillräcklig(mål, mindre, self._nivåkorten(mindre, mål))
                if nytt is None or not (nytt[0] < mängd):
                    continue
                mängd, träff = nytt
                krympte = True
                break
        return mängd, frozenset(träff.kort)


def starka_komponenter(noder: Iterable, kanter: dict) -> list[frozenset]:
    """Grafens starka komponenter, var och en efter de komponenter den kräver.

    Tarjans algoritm ger en komponent först när allt den når är klart, och en
    kant går från ett kort till det kort det kräver — så komponenterna kommer i
    den ordning nivåerna kan öppnas.
    """
    index: dict = {}
    lägst: dict = {}
    stack: list = []
    på_stack: set = set()
    ut: list[frozenset] = []

    def besök(nod) -> None:
        index[nod] = lägst[nod] = len(index)
        stack.append(nod)
        på_stack.add(nod)
        for granne in sorted(kanter.get(nod, ()), key=str):
            if granne not in index:
                besök(granne)
                lägst[nod] = min(lägst[nod], lägst[granne])
            elif granne in på_stack:
                lägst[nod] = min(lägst[nod], index[granne])
        if lägst[nod] == index[nod]:
            komponent = set()
            while True:
                x = stack.pop()
                på_stack.discard(x)
                komponent.add(x)
                if x == nod:
                    break
            ut.append(frozenset(komponent))

    for nod in sorted(noder, key=str):
        if nod not in index:
            besök(nod)
    return ut


@dataclass
class Nivåkarta:
    """Kraven och nivåerna för ett språk."""
    krav: dict          # kort → dess minsta mängd
    nivåer: list        # starka komponenter, i den ordning de kan öppnas
    oprövbara: list     # kort utan någon giltig mening
    bevis: dict         # kort → korten i den mening som bevisar det (3.10)


def rita_nivåer(krav: Krav, kort: Iterable[Kort],
                rapport: Callable[[str], None] | None = print,
                krymp: bool = False, täckning=None) -> Nivåkarta:
    """Varje korts krav, grafen och nivåerna (4.1, 4.2).

    Med `täckning` ordnas nivåerna efter ny täckning per kort (5.6) i stället
    för i den godtyckliga ordning den topologiska sorteringen råkar ge. Utan
    den behålls komponentordningen, så att nivåerna går att räkna fram även
    innan användningarna är mätta.
    """
    mängder: dict = {}
    bevis: dict = {}
    for k in sorted(kort, key=str):
        t, frågor = time.perf_counter(), krav.frågor
        svar = krav.mängd(k, krymp)
        mängder[k] = None if svar is None else svar[0]
        if svar is not None:
            bevis[k] = svar[1]
        if rapport:
            text = ("inte prövbart" if mängder[k] is None
                    else "{" + ", ".join(sorted(map(str, mängder[k]))) + "}")
            rapport(f"  {k}: {text}  ({krav.frågor - frågor} frågor, "
                    f"{time.perf_counter() - t:.1f} s)")
    valda = {k: m for k, m in mängder.items() if m is not None}
    kanter = {k: {d for d in m if d in valda} for k, m in valda.items()}
    nivåer = starka_komponenter(valda, kanter)
    if täckning is not None:
        from .tackning import ordna_nivåer
        nivåer = ordna_nivåer(nivåer, valda, täckning)
    return Nivåkarta(valda, nivåer,
                     sorted((k for k, m in mängder.items() if m is None), key=str),
                     bevis)
