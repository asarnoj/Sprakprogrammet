"""Förklaringar — varför en mening föll, och vilka andra meningar som faller av samma skäl.

KÄRNAN 4.2 och 6.7. En fråga till sammansättningen som svarar nej måste gå
igenom varje mening som går att bygga. Utan förklaringar renderas varje ordval i
varje sammansättning, och de flesta faller av samma skäl: ett förbjudet beslut
syns, vilka ord som än står där. En fråga om engelskans bestämda artikel utan
valet `bestämd_artikel` hade 50 484 sammansättningar och renderade omkring 210
ordval i var och en (mätt 2026-09-14).

ETT BEVIS säger att ett kort syns i varje mening som innehåller en viss del av
en sammansättning — delen med samma vägar i den och i delarna under den — när
orden på delens platser har vissa egenskaper och specfälten den läser har vissa
värden. Beviset tas ur en rendering. Meningen renderas en gång som den är och en
gång med beslutet tvingat till ett annat utfall, och allt renderaren läste under
delen skrivs ner.

Beviset vilar på det kartan redan förutsätter och prövar (6.7):

1. Renderaren är deterministisk och läser ord bara genom `Uppslag`, också när
   den läser om ett ord den redan skrivit, genom ordets koncept. Kartan stoppar
   varje annan läsning som en förbigång och har inga förbigångar. En jämförelse
   mellan två platsers koncept stoppar inte kartan, så den skrivs ner här, och
   en del där den förekommer får inget bevis. Ändrar renderaren ett ord efter
   uppslaget, som "a" till "an", jämförs orden som de skrevs ut.
2. En del påverkar resten av meningen bara genom det den lämnar tillbaka, och
   anroparen läser bara vad sorts utdata det är och hur långt. Renderaren sätter
   inget tillstånd utöver meningens ord, och ett fel från en del avbryter hela
   renderingen.

Därav följer två saker. Lämnar den tvingade delen tillbaka lika mycket som den
verkliga, är resten av meningen densamma i båda renderingarna, var delen än
står. Lämnar den tillbaka en lista med ett annat antal ord gäller detsamma där
varje del ovanför godtar den nya längden: anroparen följer då samma väg, och dess
egen lista blir lika mycket längre eller kortare. Beviset bär ändringen, och
sammansättningen prövar den del för del uppåt. Och delen gör detsamma i en annan
mening om den får samma svar: samma svar på varje läsning av orden på dess
platser, samma värde i varje specfält den läser, och samma delar under sig.

ETT ORD HAR ÄNDRATS när orden från samma ställe i renderaren, i samma led och
med samma koncept, inte är samma former i samma ordning (`rendering/spår.py`).
Beviset räknar formerna per ställe och led inne i delen. Skiljer sig antalet av
någon form mellan renderingarna har något ord ändrats, också om ord med samma
nyckel står utanför delen, eftersom de är desamma i båda. Ett ställe där två
platsers ord slås upp används inte som vittne: två ord som i en annan mening
har samma koncept skulle där kunna byta plats med varandra.

Ett bevis används på två sätt. En del vars bevis uppfylls av varje ord som kan
stå på dess platser byggs inte vidare, och ett ordval som uppfyller ett bevis
renderas inte. Inget av det är en uppskattning, eftersom det som hoppas över
hade fallit. Med `Sammansättare.kontroll` hoppas ingenting över. Varje
förutsägelse prövas då mot renderingen, och ett brott är `Bevisfel`.
"""

from __future__ import annotations

import inspect
from collections import Counter, defaultdict
from dataclasses import dataclass, field, fields

from ..kortmodell import Kort, beslutskort
from ..rendering import spec as S
from ..rendering.spec import RenderingsFel
from ..rendering.spår import Utskrift, _rendera
from ..rendering.uppslag import GENOMSKINLIGA, Ord


class Bevisfel(AssertionError):
    """En mening som ett bevis sade skulle falla gick att bygga."""


# ── sammansättningens träd ───────────────────────────────────────────────


class Nod:
    """En del i en sammansättning.

    `väg` är vägen genom delen, `bindning` vad dess argument heter i meningen,
    och `barn` delarna den anropade, i ordning. `nyckel` är densamma för samma
    väg med samma delar under, var i meningen delen än står. `ord` är antalet
    ord under delen. `väntande` är de ändrade längder som bevis under delen
    lämnar och som delen godtar, så att anroparen kan pröva dem. `täckt` sätts i
    kontrolläget på en del som annars hade hoppats över.
    """
    __slots__ = ("väg", "bindning", "barn", "nyckel", "ord", "väntande", "täckt", "verb")

    def __init__(self, väg, bindning: dict, barn: tuple, nyckel: int) -> None:
        self.väg, self.bindning, self.barn, self.nyckel = väg, bindning, barn, nyckel
        self.ord, self.väntande, self.täckt, self.verb = 0, frozenset(), False, False

    def alla(self) -> list["Nod"]:
        ut = [self]
        for b in self.barn:
            ut.extend(b.alla())
        return ut


def relativ(bindning: dict, text: str) -> tuple | None:
    """Ett namn i meningen som (argument, resten) hos delen, eller None."""
    bäst = None
    for arg, ref in bindning.items():
        if (text == ref or text.startswith(ref + ".")) and (
                bäst is None or len(ref) > len(bindning[bäst])):
            bäst = arg
    return None if bäst is None else (bäst, text[len(bindning[bäst]):])


def absolut(bindning: dict, rel: tuple) -> str | None:
    ref = bindning.get(rel[0])
    return None if ref is None else ref + rel[1]


# ── genomlysningen ───────────────────────────────────────────────────────


class Platsnyckel(str):
    """Konceptnyckeln på en plats i meningen, under en genomlyst rendering.

    Nyckeln är densamma som i en vanlig rendering. Platsen följer med, så att
    varje läsning går att knyta till den plats den gällde.
    """
    plats: str

    def __eq__(self, annan):
        svar = str.__eq__(self, annan)
        if svar is not NotImplemented and _Logg.aktiv is not None:
            _Logg.aktiv.jämförelse(self, annan, svar)
        return svar

    def __ne__(self, annan):
        svar = self.__eq__(annan)
        return svar if svar is NotImplemented else not svar

    __hash__ = str.__hash__


def platsnyckel(nyckel: str, plats: str) -> Platsnyckel:
    p = Platsnyckel(nyckel)
    p.plats = plats
    return p


def _spårklass(bas):
    namn = frozenset(f.name for f in fields(bas))

    def läs(self, fält):
        värde = object.__getattribute__(self, fält)
        if fält in namn and _Logg.aktiv is not None:
            _Logg.aktiv.fält.append(
                (_Logg.aktiv.nu, f"{object.__getattribute__(self, '_väg')}.{fält}"))
        return värde

    return type(f"Spårad{bas.__name__}", (bas,),
                {"__slots__": ("_väg",), "__getattribute__": läs})


_SPÅRADE = {bas: _spårklass(bas) for bas in
            (S.Mening, S.Nominalfras, S.Attribut, S.Prepositionsfras, S.Bisats)}


def spårad_spec(obj, väg: str):
    """Specen med varje fältläsning märkt med kartans namn på fältet: m.subjekt.numerus."""
    klass = _SPÅRADE.get(type(obj))
    if klass is None:
        return obj
    ny = object.__new__(klass)
    for f in fields(obj):
        värde = getattr(obj, f.name)
        if isinstance(värde, tuple):
            värde = tuple(spårad_spec(e, f"{väg}.{f.name}.{i}") for i, e in enumerate(värde))
        else:
            värde = spårad_spec(värde, f"{väg}.{f.name}")
        object.__setattr__(ny, f.name, värde)
    object.__setattr__(ny, "_väg", väg)
    return ny


@dataclass
class _Anrop:
    del_: str
    förälder: int | None
    barn: list = field(default_factory=list)
    #: ("none",), ("ord",) eller ("lista", längd)
    retur: tuple | None = None


class _Logg:
    """Vad en genomlyst rendering läste, anrop för anrop."""
    aktiv: "_Logg | None" = None

    def __init__(self) -> None:
        self.anrop: list[_Anrop] = []
        self.stack: list[int] = []
        self.läsningar: list[tuple] = []      # (anrop, plats, läsning)
        self.jämförelser: list[tuple] = []    # (anrop, plats, med, svar)
        self.fält: list[tuple] = []           # (anrop, fältets namn)
        self.uppslag: dict = {}               # ordets nyckel → (anrop, led, ställe, källa, variant, cell)
        self.ord: tuple = ()                  # de utskrivna orden
        self.beslut: dict = {}                # beslutets id → anrop
        self.rader: dict[int, tuple] = {}     # id(rad) → (källa, variant)
        self._behåll: list = []

    @property
    def nu(self) -> int | None:
        return self.stack[-1] if self.stack else None

    def jämförelse(self, nyckel: Platsnyckel, annan, svar: bool) -> None:
        med = (("plats", annan.plats) if isinstance(annan, Platsnyckel)
               else ("nyckel", str.__str__(annan)))
        self.jämförelser.append((self.nu, nyckel.plats, med, svar))

    def under(self, rot: int) -> set[int]:
        ut, kö = set(), [rot]
        while kö:
            a = kö.pop()
            ut.add(a)
            kö.extend(self.anrop[a].barn)
        return ut


#: Uppslagets läsningar av ord: metoden → vad argumenten är. Övriga metoder
#: läser inga ord själva (`form_för`, `kontrollera_naken`) eller bär bara
#: redovisning (`regel`, `ordning`, `rektion`, `led`); `lemma` står bara i
#: felmeddelanden.
LÄSNINGAR = {
    "lexem": ("nyckel", None), "ordklass": ("rad",), "har_form": ("rad", None),
    "koncept": ("nyckel", None), "mänsklig": ("nyckel",), "tilltal": ("nyckel",),
    "förljud": ("rad",), "operator": ("rad",), "frågepronomen": ("nyckel",),
    "form": ("rad", None), "egenskap": ("rad", None),
    "infinitivmarkör": ("nyckel",), "komplementform": ("nyckel",),
}


def _svar(namn: str, u, argument: list, svar):
    """Svaret som det jämförs: ett lexem och en form är bara att de fanns, och en
    egenskap är ordets egen, också där ett beslut tvingade den."""
    if namn == "lexem":
        return ("rad",)
    if isinstance(svar, Ord):
        return ("ord",)
    if namn == "egenskap":
        return u._egenskapsvärde(argument[0], argument[1])
    return svar


def _läsning(logg: _Logg, u, namn: str, verklig, roller: tuple):
    def omslag(*args, **kwargs):
        plats, norm, vanliga = None, [], []
        for i, a in enumerate(args):
            roll = roller[i] if i < len(roller) else None
            if roll == "nyckel" and isinstance(a, Platsnyckel):
                plats = a.plats
                norm.append(("@nyckel",))
                vanliga.append(str.__str__(a))
            elif roll == "rad":
                källa, variant = logg.rader.get(id(a), (("okänd",), None))
                if källa[0] == "plats":
                    plats = källa[1]
                    norm.append(("@rad", variant))
                else:
                    norm.append(("rad", källa, variant))
                vanliga.append(a)
            else:
                norm.append(a)
                vanliga.append(a)
        läsning = (namn, tuple(norm), tuple(sorted(kwargs.items())))
        try:
            svar = verklig(*vanliga, **kwargs)
        except RenderingsFel:
            if plats is not None:
                logg.läsningar.append((logg.nu, plats, (*läsning, ("fel",))))
            raise
        if namn == "lexem":
            variant = args[1] if len(args) > 1 else kwargs.get("variant")
            källa = ("plats", plats) if plats is not None else ("nyckel", vanliga[0])
            logg.rader[id(svar)] = (källa, variant)
            logg._behåll.append(svar)
        elif namn == "form":
            källa, variant = logg.rader.get(id(args[0]), (("okänd",), None))
            logg.uppslag[svar.nyckel] = (logg.nu, svar.nyckel[1], svar.nyckel[2], källa,
                                         variant, vanliga[1])
            if källa[0] == "plats":
                # Ordet bär sitt koncept vidare, och renderaren kan slå upp det
                # igen: "a" eller "an" läses på nästa ords koncept.
                svar.koncept = platsnyckel(svar.koncept, källa[1])
        if plats is not None:
            logg.läsningar.append((logg.nu, plats, (*läsning, _svar(namn, u, vanliga, svar))))
        return svar
    GENOMSKINLIGA.add(omslag.__code__)
    return omslag


def _regel(logg: _Logg, u, verklig):
    def omslag(*args, **kwargs):
        svar = verklig(*args, **kwargs)
        logg.beslut[u.spår.händelser[-1][1]] = logg.nu
        return svar
    GENOMSKINLIGA.add(omslag.__code__)
    return omslag


def _del(logg: _Logg, namn: str, verklig):
    def omslag(*args, **kwargs):
        nr = len(logg.anrop)
        if logg.stack:
            logg.anrop[logg.stack[-1]].barn.append(nr)
        logg.anrop.append(_Anrop(namn, logg.nu))
        logg.stack.append(nr)
        try:
            ut = verklig(*args, **kwargs)
        finally:
            logg.stack.pop()
        logg.anrop[nr].retur = (("none",) if ut is None else ("ord",) if isinstance(ut, str)
                                else ("lista", len(ut)))
        return ut
    GENOMSKINLIGA.add(omslag.__code__)
    return omslag


def genomlys(renderare, mening, tvång: dict | None = None) -> tuple:
    """Rendera och skriv ner varje anrop, läsning, fältläsning och uppslag.

    `mening` ska vara byggd med `platsnyckel` och `spårad_spec`. Ger (text, ord, logg).
    """
    logg = _Logg()
    u = renderare.u
    delar = [n for n, m in inspect.getmembers(type(renderare), inspect.isfunction)
             if getattr(m, "frasdel", False)] + ["rendera"]
    for namn, roller in LÄSNINGAR.items():
        setattr(u, namn, _läsning(logg, u, namn, getattr(u, namn), roller))
    u.regel = _regel(logg, u, u.regel)
    for namn in delar:
        setattr(renderare, namn, _del(logg, namn, getattr(renderare, namn)))
    _Logg.aktiv = logg
    try:
        text, ord, _ = _rendera(renderare, mening, tvång)
        logg.ord = ord
    finally:
        _Logg.aktiv = None
        for namn in (*LÄSNINGAR, "regel"):
            vars(u).pop(namn, None)
        for namn in delar:
            vars(renderare).pop(namn, None)
    return text, ord, logg


# ── bevisen ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Bevis:
    """`kort` syns i varje mening med delen `nod` där platserna och fälten stämmer.

    platser  ((plats, sort, villkor), …) — platsen som (argument, resten) hos delen
    fält     ((fält, etikett), …) — etiketten meningen har i fältet, None för ingen
    ändring  hur många fler ord delens lista har med beslutet tvingat; är den
             inte 0 gäller beviset bara där delarna ovanför godtar längden
    """
    kort: Kort
    nod: int
    platser: tuple
    fält: tuple
    ändring: int = 0


def bevisa(s, rot: Nod, villkor: dict, bundna: dict, platser: dict,
           ut: Utskrift, kort: Kort) -> Bevis | None:
    """Ett bevis för att `kort` syns, ur meningen `ut` som föll på det, eller None."""
    statistik = s.statistik
    beslut = [b for b in ut.beslut
              if b.sort == "regel" and b.syns and beslutskort(s.språk, b) == kort]
    if not beslut:
        statistik["obevisat: inget beslut"] += 1
        return None
    mening = spårad_spec(s._mening(villkor, "m",
                                   lambda text, _: platsnyckel(bundna[text], text)), "m")
    try:
        _, ord_a, a = genomlys(s.renderare, mening)
    except RenderingsFel:
        statistik["obevisat: genomlysningen vägrar"] += 1
        return None
    if [str(o) for o in ord_a] != [str(o) for o in ut.ord]:
        statistik["obevisat: en annan mening"] += 1
        return None
    noder = _para(a, 0, rot, {}) if a.anrop and a.anrop[0].del_ == "rendera" else None
    if noder is None:
        statistik["obevisat: anropen följer inte sammansättningen"] += 1
        return None
    bäst = None
    for b in beslut:
        d = a.beslut.get(b.id)
        if d is None:
            continue
        for annat in b.alternativ:
            try:
                _, _, f = genomlys(s.renderare, mening, {b.id: annat})
            except RenderingsFel:
                continue
            funnet = _bevis_för(s, a, f, d, noder, villkor, bundna, platser, kort)
            if funnet is not None and (bäst is None or funnet[0] < bäst[0]):
                bäst = funnet
    if bäst is None:
        statistik["obevisat: inget vittne"] += 1
        return None
    return bäst[1]


def _para(logg: _Logg, nr: int, nod: Nod, ut: dict) -> dict | None:
    """Anropen i renderingen, parade med sammansättningens delar."""
    anrop = logg.anrop[nr]
    if len(anrop.barn) != len(nod.barn):
        return None
    ut[nr] = nod
    for barn_nr, barn, (_, del_, _) in zip(anrop.barn, nod.barn, nod.väg.anrop):
        if logg.anrop[barn_nr].del_ != del_ or _para(logg, barn_nr, barn, ut) is None:
            return None
    return ut


def _bevis_för(s, a: _Logg, f: _Logg, d: int, noder: dict, villkor: dict,
               bundna: dict, platser: dict, kort: Kort) -> tuple | None:
    """Det minsta beviset för ett tvingat utfall: den innersta del kring beslutet
    som har ett vittne och lämnar tillbaka samma sorts utdata i båda renderingarna.

    Ger ((antal delar, om längden ändras), bevis): mindre är bättre, och vid
    samma storlek går ett bevis med oförändrad längd före.
    """
    nr = d
    while nr is not None:
        anrop, tvingat = a.anrop[nr], f.anrop[nr]
        if anrop.förälder is None or tvingat.retur == anrop.retur:
            ändring = 0
        elif tvingat.del_ == anrop.del_ and anrop.retur[0] == tvingat.retur[0] == "lista":
            ändring = tvingat.retur[1] - anrop.retur[1]
        else:
            ändring = None
        if ändring is not None:
            bevis = _delens_bevis(s, a, f, nr, noder[nr], villkor, bundna, platser, kort,
                                  ändring)
            if bevis is not None:
                return (len(noder[nr].alla()), ändring != 0), bevis
        nr = anrop.förälder
    return None


def _utskrivna(poster: list, bundna: dict) -> Counter:
    """Orden som (koncept, text), så som spåret jämför dem."""
    return Counter((bundna[k[1]] if k[0] == "plats" else k[1], text)
                   for k, _, _, text in poster)


def _mall(poster: list) -> tuple:
    """Platsens ord som sin cell, övriga ord som sin text."""
    return tuple(sorted(("@", v, c) if k[0] == "plats" else ("ord", k[1], text)
                        for k, v, c, text in poster))


def _delens_bevis(s, a: _Logg, f: _Logg, nr: int, nod: Nod, villkor: dict,
                  bundna: dict, platser: dict, kort: Kort, ändring: int) -> Bevis | None:
    from . import _döp

    under = (a.under(nr), f.under(nr))
    loggar = ((a, under[0]), (f, under[1]))
    villkoren: dict = defaultdict(set)
    for logg, inne in loggar:
        for anrop, plats, läsning in logg.läsningar:
            if anrop in inne:
                villkoren[plats].add(("läs", *läsning))
        for anrop, plats, med, svar in logg.jämförelser:
            if anrop in inne:
                if med[0] == "plats":
                    s.statistik["delbevis: två platser jämförs"] += 1
                    return None
                villkoren[plats].add(("lika", med[1], svar))

    # De utskrivna orden, per ställe och led, med uppslaget de kom från. Ett ord
    # som inte slogs upp har ingen nyckel och jämförs inte av spåret heller.
    grupper: dict = defaultdict(lambda: ([], []))
    for i, (logg, inne) in enumerate(loggar):
        for o in logg.ord:
            post = logg.uppslag.get(o.nyckel)
            if post is None or post[0] not in inne:
                continue
            _, led, ställe, källa, variant, cell = post
            if källa[0] == "okänd":
                s.statistik["delbevis: okänd källa"] += 1
                return None
            grupper[(led, ställe)][i].append((källa, variant, cell, str(o)))
    vittne = None
    for i_a, i_f in grupper.values():
        poster = i_a + i_f
        platsnamn = {k[1] for k, _, _, _ in poster if k[0] == "plats"}
        if len(platsnamn) > 1 or _utskrivna(i_a, bundna) == _utskrivna(i_f, bundna):
            continue
        if not platsnamn:
            vittne = (None, None)
            break
        # Ett platsord som renderaren ändrade efter uppslaget har ingen form att
        # räkna fram i en annan mening, så det kan inte vara vittne.
        if vittne is None and all(text == str(s.u.form(s.u.lexem(bundna[k[1]], v), c))
                                  for k, v, c, text in poster if k[0] == "plats"):
            vittne = (next(iter(platsnamn)), ("former", _mall(i_a), _mall(i_f)))
    if vittne is None:
        s.statistik["delbevis: inget vittne"] += 1
        return None
    if vittne[0] is not None:
        villkoren[vittne[0]].add(vittne[1])

    platsdel = []
    for plats, atomer in villkoren.items():
        rel = relativ(nod.bindning, plats)
        if rel is None or plats not in platser:
            s.statistik["delbevis: plats utanför delen"] += 1
            return None
        platsdel.append((rel, platser[plats], tuple(sorted(atomer, key=repr))))

    egna = {_döp(k, n.bindning) for n in nod.alla()
            for k, _ in s._globala[id(n.väg)] if isinstance(k, str)}
    fältdel: dict = {}
    for logg, inne in loggar:
        for anrop, namn in logg.fält:
            if anrop in inne and namn not in egna:
                rel = relativ(nod.bindning, namn)
                if rel is None:
                    s.statistik["delbevis: fält utanför delen"] += 1
                    return None
                fältdel[rel] = villkor.get(namn)
    return Bevis(kort, nod.nyckel, tuple(sorted(platsdel, key=repr)),
                 tuple(sorted(fältdel.items(), key=repr)), ändring)


def uppfyller(s, villkor: tuple, nyckel: str) -> bool:
    """Uppfyller ordet med konceptet `nyckel` ett av bevisets villkor på en plats?"""
    k = (villkor, nyckel)
    if k not in s._atomcache:
        s._atomcache[k] = _uppfyller(s.u, villkor, nyckel)
    return s._atomcache[k]


def _uppfyller(u, villkor: tuple, nyckel: str) -> bool:
    try:
        if villkor[0] == "lika":
            return (nyckel == villkor[1]) == villkor[2]
        if villkor[0] == "former":
            return _former_mall(u, villkor[1], nyckel) != _former_mall(u, villkor[2], nyckel)
        _, namn, norm, kwargs, svar = villkor
        argument = []
        for a in norm:
            if a == ("@nyckel",):
                argument.append(nyckel)
            elif isinstance(a, tuple) and a[:1] == ("@rad",):
                argument.append(u.lexem(nyckel, a[1]))
            elif isinstance(a, tuple) and a[:1] == ("rad",):
                argument.append(u.lexem(a[1][1], a[2]))
            else:
                argument.append(a)
        try:
            ut = getattr(u, namn)(*argument, **dict(kwargs))
        except RenderingsFel:
            return svar == ("fel",)
        return _svar(namn, u, argument, ut) == svar
    except RenderingsFel:
        return False


def _former_mall(u, mall: tuple, nyckel: str) -> Counter:
    räkning: Counter = Counter()
    for post in mall:
        if post[0] == "@":
            räkning[(nyckel, str(u.form(u.lexem(nyckel, post[1]), post[2])))] += 1
        else:
            räkning[(post[1], post[2])] += 1
    return räkning
