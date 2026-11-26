"""Spåret: vad en rendering redovisade, var det syns och vad alternativen ger.

KÄRNAN 6.2, 7.3 och 8.3 punkt 5. Ett besluts POSITIONER är de utskrivna ord
vars form beslutet bestämde. Här räknas de ut i stället för att märkas för
hand: beslutet tvingas till vart och ett av sina andra utfall, meningen
renderas om, och de ord som ändras är positionerna. Ett substantiv i plural
ändras inte när genuset tvingas om, och då har genuset inte prövats — det
behöver ingen regel säga.

Ett beslut kan också synas som en LUCKA: att ett ord inte står där. Tvingas
verbet att vara reflexivt skjuts ett "sig" in efter det, men inget befintligt
ord ändras. Luckan är platsen mellan två ord, och den räknas bara när inget ord
runt den redan har ändrats.

Omrenderingarna är också de alternativ rättningen jämför svaret med när den
avgör om ett kort förklarar en avvikelse (7.3).

En ordningsregel behöver ingen omrendering. Dess alternativ är de två leden i
omvänd ordning, och dess positioner är orden i båda leden.

Spåret kontrollerar två saker om renderaren, och varje brott är ett fel i
renderaren: att varje ordningsregel stämmer med den färdiga meningen, och att
varje uppslagen form syns i den. En form som slås upp men aldrig skrivs ut
skulle annars räknas som prövad.
"""

from __future__ import annotations

from dataclasses import dataclass

from .spec import Mening, RenderingsFel
from .uppslag import Ord, Spår


@dataclass(frozen=True, slots=True)
class Beslut:
    """Ett redovisat beslut i en rendering."""
    #: egenskap · rektion · regel · ordning
    sort: str
    #: (sort, led, …, n) — se `Spår.id` och `Uppslag`
    id: tuple
    #: Utfallet i den här meningen. None för en ordningsregel.
    utfall: object
    #: Index i `Utskrift.ord` för de ord beslutet bestämde.
    positioner: tuple[int, ...]
    #: Luckor beslutet bestämde: lucka i ligger före ord i, lucka len(ord) sist.
    luckor: tuple[int, ...]
    #: Utfall → meningens ord när beslutet tvingas till det. Bara utfall som
    #: gick att rendera; för en ordningsregel nyckeln "omvänd".
    alternativ: dict
    #: Beslutets möjliga utfall, också de som vägrade renderas.
    domän: tuple = ()

    @property
    def namn(self) -> str:
        """Beslutets namn: regelns, eller egenskapens och rektionens."""
        return "/".join(str(x) for x in self.id[2:-1])

    @property
    def syns(self) -> bool:
        """Syns beslutet i meningen? Annars prövades det inte."""
        return bool(self.positioner or self.luckor)


@dataclass(frozen=True, slots=True)
class Utskrift:
    text: str
    ord: tuple[Ord, ...]
    beslut: tuple[Beslut, ...]


class Redovisningsfel(AssertionError):
    """Renderarens redovisning stämmer inte med meningen den skrev."""


def _rendera(renderare, m: Mening, tvång: dict | None = None):
    u = renderare.u
    spår = Spår(tvång)
    u.spår = spår
    try:
        text = renderare.rendera(m)
        return text, tuple(renderare.osammansmält), spår
    finally:
        u.spår = None


def spåra(renderare, m: Mening) -> Utskrift:
    """Rendera `m` och räkna ut varje besluts positioner och alternativ."""
    text, ord, spår = _rendera(renderare, m)
    index = {o.nyckel: i for i, o in enumerate(ord)}
    beslut: list[Beslut] = []
    for händelse in spår.händelser:
        sort = händelse[0]
        if sort == "form":
            if händelse[1].nyckel not in index:
                raise Redovisningsfel(
                    f"formen {händelse[1]!r} ({händelse[1].koncept}, "
                    f"{händelse[1].cell}) slogs upp men syns inte i {text!r}")
            continue
        if sort == "ordning":
            _, id, före, efter = händelse
            fi, ei = _index(före, index, id, text), _index(efter, index, id, text)
            if max(fi) > min(ei):
                raise Redovisningsfel(
                    f"ordningsregeln {id[2]} säger {list(före)} före "
                    f"{list(efter)}, men meningen är {text!r}")
            beslut.append(Beslut("ordning", id, None, tuple(sorted({*fi, *ei})),
                                 (), {"omvänd": _omvänd(ord, fi, ei)}))
            continue
        _, id, utfall, domän = händelse
        positioner: set[int] = set()
        luckor: set[int] = set()
        alternativ: dict = {}
        for annat in domän or ():
            if annat == utfall:
                continue
            try:
                _, tvingad, _ = _rendera(renderare, m, {id: annat})
            except RenderingsFel:
                continue
            alternativ[annat] = tvingad
            ändrade, nya_luckor = _ändrade(ord, tvingad)
            positioner |= ändrade
            luckor |= nya_luckor
        beslut.append(Beslut(sort, id, utfall, tuple(sorted(positioner)),
                             tuple(sorted(luckor)), alternativ, tuple(domän or ())))
    return Utskrift(text, ord, tuple(beslut))


def _index(led, index, id, text) -> list[int]:
    try:
        return [index[o.nyckel] for o in led]
    except (KeyError, AttributeError):
        raise Redovisningsfel(
            f"ordningsregeln {id[2]} ordnar {list(led)}, som inte syns i "
            f"{text!r}") from None


def _omvänd(ord, fi: list[int], ei: list[int]) -> tuple[Ord, ...]:
    """Meningen med de två leden i omvänd ordning."""
    början, slut = min(fi), max(ei)
    mellan = [ord[i] for i in range(början, slut + 1)
              if i not in fi and i not in ei]
    return (*ord[:början], *(ord[i] for i in ei), *mellan,
            *(ord[i] for i in fi), *ord[slut + 1:])


def _ändrade(faktisk, tvingad) -> tuple[set[int], set[int]]:
    """Ord och luckor i `faktisk` som den tvingade renderingen ändrade.

    Ett ord har ändrats om det saknas i den tvingade renderingen, har en annan
    form där, eller har flyttat i förhållande till de andra orden. Flyttade ord
    är de som faller utanför den längsta följd som behåller sin ordning.

    Ett ord som bara finns i den tvingade renderingen ger en lucka mellan de
    stabila ord det står mellan — om inget ord mellan dem redan har ändrats. Då
    är det inskjutna ordet en del av den ändringen och ingen egen plats.
    """
    här = {o.nyckel: i for i, o in enumerate(faktisk)}
    där = {o.nyckel: j for j, o in enumerate(tvingad)}
    ändrade = {i for i, o in enumerate(faktisk)
               if o.nyckel not in där or tvingad[där[o.nyckel]] != o}
    kvar = [i for i in range(len(faktisk)) if i not in ändrade]
    ändrade |= set(kvar) - _längsta_ordnade(
        kvar, [där[faktisk[i].nyckel] for i in kvar])

    def stabil(t) -> int | None:
        i = här.get(t.nyckel)
        return None if i is None or i in ändrade else i

    luckor: set[int] = set()
    for j, o in enumerate(tvingad):
        if o.nyckel in här:
            continue
        föregående = max((i for t in tvingad[:j] if (i := stabil(t)) is not None),
                         default=-1)
        nästa = min((i for t in tvingad[j + 1:] if (i := stabil(t)) is not None),
                    default=len(faktisk))
        if not any(föregående < i < nästa for i in ändrade):
            luckor.add(föregående + 1)
    return ändrade, luckor


def _längsta_ordnade(index: list[int], plats: list[int]) -> set[int]:
    """De index vars platser bildar den längsta växande följden."""
    if not index:
        return set()
    längd = [1] * len(index)
    före = [-1] * len(index)
    for b in range(len(index)):
        for a in range(b):
            if plats[a] < plats[b] and längd[a] + 1 > längd[b]:
                längd[b], före[b] = längd[a] + 1, a
    i = max(range(len(index)), key=längd.__getitem__)
    ut = set()
    while i != -1:
        ut.add(index[i])
        i = före[i]
    return ut
