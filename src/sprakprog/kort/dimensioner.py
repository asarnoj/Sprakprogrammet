"""Böjningsdimensioner som nivåer — en universell lista, projicerad per språk.

FRÅGAN SOM LÖSTES HÄR. Nivåstegen har 21 konstruktioner som styr vad en
MENING får innehålla, och de är samma för alla sju språken därför att de
sitter på konceptlagret. Böjningens egna axlar styrdes inte alls: franskans
sex personändelser skapades allihop på nivå 1.

Att göra varje böjningsdimension till en nivå gick inte rakt av — franskan har
60 sådana celler, tyskan 42 och svenskan NOLL, eftersom svenska verb inte
personböjs. En stege per språk hade brutit den delade axeln.

JULIUS LÖSNING (2026-08-27): *"Man hade kunnat ha en universell nivålista som
är detaljerad, och sen renderas nivålistan olika för de olika språken genom
att gå igenom och se att vissa rader faktiskt bidrar till något nytt i
språket."* Listan förblir universell; STEGEN blir en projektion av den. Samma
form som renderarna redan har — universell spec, språkspecifik realisering.

VAD "BIDRAR MED NÅGOT NYTT" BETYDER, och varför det inte är ett val:

    En cell lär ut något nytt om dess ÄNDELSE inte redan är känd från en
    tidigare cell i SAMMA böjningsklass.

Franskans K0 (-er-verben) har `pres_1sg = e` och `pres_3sg = e`. Har man lärt
sig den första finns ingenting kvar att lära i den andra — samma sträng, samma
tabell. K1 har `s` och `t` på samma två celler, och där är det två moment.

Kriteriet är alltså inte en tröskel någon satt, utan strängidentitet i data
som redan finns. Det är samma predikat som strukturkontrollen i
`meningsgranskning` använder för att hitta TAPPADE distinktioner — där är
"två specar renderar likadant" ett fel, här är det ett urvalskriterium.

PER KLASS OCH INTE PER SPRÅK. Synligheten sitter på ändelsetabellen, inte på
språket: `1sg` mot `3sg` är tomt i franskans K0 och meningsfullt i K1. Kort
av typen `system` hör redan till en klass och inte till ett ord, så
granulariteten finns i kortmodellen — ingen omskrivning behövs.

OREGELBUNDENHET RÖR INTE DET HÄR. Ett oregelbundet verb hör ändå till en
ändelsetabell; det som gör det oregelbundet ligger i STAMkorten bredvid
(`avoir` har stammarna `a` och `av`) och i sista hand i ett `form`-kort för
hela ordet. Därför räcker tre ändelseklasser för franskan.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ÄNDELSEFIL = Path(__file__).resolve().parents[3] / "ordbok" / "ändelser.tsv"

#: TEMPUSORDNINGEN ÄR ETT VAL, och det enda i den här filen.
#:
#: Allt annat räknas: vilka celler som finns, vilka som lär ut något nytt,
#: vilka klasser de gäller i. Men VILKEN TEMPUS SOM SKA LÄRAS FÖRST är en
#: pedagogisk fråga och inget faktum om språken — därför står den här, som en
#: läsbar lista över fjorton värden, i stället för att gömmas i en sorterings-
#: funktion eller spridas över nittio cellnamn.
#:
#: Ordningen: ordboksformen först, eftersom det är så ord slås upp och lärs
#: in. Sedan presens, dåtid, och den form som bygger de sammansatta tiderna.
#: Framtid och imperfekt därefter, och de modala och japanskspecifika
#: formerna sist — de förutsätter att grundtempus sitter.
#:
#: Namnen kommer ur `paradigm/_legend.yaml` och är desamma i alla sju språken.
#: Ett värde som saknas här hamnar sist, så en ny tempus i ordboken bryter
#: ingenting — den syns bara i slutet tills någon placerar den.
TEMPUSORDNING = ("Inf", "Pres", "Pret", "Sup", "PresPer", "Imperf", "Fut",
                 "Imp", "Kond", "Te", "Neg", "Pot", "Vol")


def _axelrang(cell, legend) -> tuple:
    """Cellens plats i paradigmet: tempus, diates, numerus, person.

    NUMERUS FÖRE PERSON, alltså 1sg, 2sg, 3sg, 1pl, 2pl, 3pl — böjnings-
    tabellens egen ordning, och samma som `_rang` ger pronomenen. Person före
    numerus hade gett 1sg, 1pl, 2sg, 2pl, vilket ingen läromedelstabell
    använder.
    """
    a = cell.axlar
    tempusnamn = {v: k for k, v in legend.get("tempus", {}).items()}
    t = tempusnamn.get(a.get("tempus"))
    plats = (TEMPUSORDNING.index(t) if t in TEMPUSORDNING
             else len(TEMPUSORDNING))
    # OTAGGAD DIATES BETYDER AKTIV, inte "före aktiv". Engelskans yaml
    # utelämnar `diates` på en del celler medan franskans skriver ut den, och
    # eftersom listan tar den LÄGSTA rangen över språken vann den otaggade:
    # `pres_1pl` fick 0 och sorterade före `pres_3sg` som fick 1. Franskans
    # steg blev 1sg, 2sg, 1pl, 2pl, 3pl, 3sg.
    #
    # Numerus och person behåller 0 för otaggat, och där ÄR det rätt: en cell
    # utan person — svenskans `pres`, japanskans `masu` — gör ingen
    # personskillnad alls och är paradigmets omarkerade form. Den hör först.
    # DIATES SLÅR TEMPUS. Hela aktivum innan något passivum, och det är en
    # starkare regel än tempusordningen: svenskans `inf_passiv` (läsas) kom
    # annars före `pres` (läser), eftersom infinitiv rankas före presens.
    # Passiv infinitiv är ett av paradigmets sista moment, inte ett av dess
    # första — man lär sig hela den aktiva böjningen först.
    #
    # Samma sak i japanskan: `ukemi` låg tvåa och hör hemma sist.
    return (a.get("diates") or 1,      # Aktiv (1) före Passiv (2)
            plats,
            a.get("numerus") or 0,     # Sg (1) före Pl (2), omarkerad först
            a.get("person") or 0,      # P1, P2, P3, omarkerad först
            cell.id)


def universella_celler(ordklass: str = "Verb") -> tuple[str, ...]:
    """Unionen av alla språks celler, i paradigmets ordning.

    LISTAN HÄRLEDS, den författas inte. Mitt första försök var handskrivet —
    `pres_1sg`, `pres_2sg`, … — alltså en fransk lista med universella
    anspråk. Mätt mot datan missade den 11 av svenskans 12 celler, 15 av
    tyskans 31 och ALLA tio japanska. Svenskan fick ett enda steg, och det var
    listans fel och inte svenskans.
    """
    from ..kaikki_mappning.paradigm import ladda_legend, ladda_slot
    legend = ladda_legend()
    rang: dict[str, tuple] = {}
    for språk in sorted({s for s, _ in ändelsetabeller(ordklass)}):
        try:
            slot = ladda_slot(språk, ordklass, legend)
        except FileNotFoundError:
            continue
        for cell in slot.celler:
            # SAMMA CELLNAMN KAN FINNAS I FLERA SPRÅK, och axlarna ska vara
            # desamma. Är de det inte tar vi den lägsta rangen — ett namn kan
            # bara ha en plats i en delad lista.
            r = _axelrang(cell, legend)
            if cell.id not in rang or r < rang[cell.id]:
                rang[cell.id] = r
    return tuple(sorted(rang, key=lambda c: rang[c]))


def ändelsetabeller(ordklass: str = "Verb") -> dict[tuple[str, str], dict[str, str]]:
    """(språk, klass) → {cell: ändelse}. Läst ur `ordbok/ändelser.tsv`."""
    ut: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    with ÄNDELSEFIL.open(encoding="utf-8") as f:
        for rad in csv.DictReader(f, delimiter="\t"):
            if rad["ordklass"] == ordklass:
                ut[(rad["språk"], rad["klass"])][rad["cell"]] = rad["ändelse"]
    return dict(ut)


def projicera(celler: tuple[str, ...] | None = None,
              ordklass: str = "Verb") -> dict[str, list[tuple[str, set[str]]]]:
    """språk → [(cell, klasser där cellen lär ut en NY ändelse)].

    Celler som ingen klass realiserar utelämnas helt — det är där stegen
    kortas av sig själv. En cell som bara några klasser realiserar står kvar
    med just de klasserna, och det är den partiella raden: nivån gäller de
    böjningstabeller där det finns något att lära.
    """
    celler = celler or universella_celler(ordklass)
    tabeller = ändelsetabeller(ordklass)
    per_språk: dict[str, list[tuple[str, set[str]]]] = {}
    for språk in sorted({s for s, _ in tabeller}):
        klasser = {k: t for (s, k), t in tabeller.items() if s == språk}
        # Vad varje klass redan lärt ut när vi vandrar nerför listan.
        kända: dict[str, set[str]] = {k: set() for k in klasser}
        steg: list[tuple[str, set[str]]] = []
        for cell in celler:
            nya = set()
            for klass, tabell in klasser.items():
                ändelse = tabell.get(cell)
                if ändelse is None or ändelse in kända[klass]:
                    continue
                kända[klass].add(ändelse)
                nya.add(klass)
            if nya:
                steg.append((cell, nya))
        per_språk[språk] = steg
    return per_språk


#: Konstruktioner som INTE går att bygga förrän en viss böjning är införd.
#:
#: Utan det här kunde flätningen lägga "tempus" på steg 9 medan
#: preteritumändelserna kom på steg 30 — och då möter användaren dåtid i en
#: mening trettio steg innan något kort lär ut hur dåtid böjs. Det är precis
#: det felet hela böjningsstegen finns för att laga, återinfört av
#: flätningen.
#:
#: De ÖVRIGA sexton konstruktionerna klarar sig med presens aktivum och har
#: därför ingen rad här. Beroendet är en grammatisk sanning och inte ett val:
#: `ANVÄNDER["tempus"]` säger `m.tid is not NUTID`, alltså krävs former för
#: en annan tid.
BEROENDE: dict[str, tuple[str, ...]] = {
    "tempus":    ("Pret", "Imperf", "Fut"),
    "perfekt":   ("Sup", "PresPer"),
    "imperativ": ("Imp",),
}

#: `passiv` beror inte på en TEMPUS utan på diatesen, och behandlas därför
#: för sig — se `stege`.
PASSIVKONSTRUKTION = "passiv"


def stege(språk: str, ordklass: str = "Verb") -> list[tuple[str, str]]:
    """Den sammanflätade stegen: [(typ, namn)] där typ är 'konstruktion' eller 'böjning'.

    TVÅ STEGAR MED HELT OLIKA LÄNGD. Konstruktionerna är tjugo och samma i
    alla språk; böjningsstegen är fyra i engelskan och fyrtiofem i spanskan.
    Att varva dem ett-och-ett hade tömt den korta långt före den långa, så
    flätningen är PROPORTIONELL: båda listorna sträcks över samma intervall
    och slås ihop på position. Franskan får då ungefär två böjningssteg per
    konstruktion, engelskan ungefär en femtedel.

    Proportionen räknas ur listornas längd och är alltså inte ett val.

    BEROENDEN BRYTER PROPORTIONEN, och ska göra det. En konstruktion som
    kräver en böjning flyttas ner till strax efter den — se `BEROENDE`.
    """
    from ..generator.urval import NIVÅ
    from ..kaikki_mappning.paradigm import ladda_legend, ladda_slot

    böjning = [cell for cell, _ in projicera(ordklass=ordklass).get(språk, [])]
    konstruktioner = [NIVÅ[n] for n in sorted(NIVÅ)]
    if not böjning:
        return [("konstruktion", k) for k in konstruktioner]

    legend = ladda_legend()
    tempusnamn = {v: k for k, v in legend.get("tempus", {}).items()}
    try:
        axlar = {c.id: c.axlar for c in ladda_slot(språk, ordklass, legend).celler}
    except FileNotFoundError:
        axlar = {}

    def sist_med(villkor) -> int:
        """Index för den SISTA böjningscell som uppfyller villkoret, annars −1."""
        träffar = [i for i, cell in enumerate(böjning) if villkor(axlar.get(cell, {}))]
        return träffar[-1] if träffar else -1

    krav: dict[str, int] = {}
    for namn, tempus in BEROENDE.items():
        krav[namn] = sist_med(
            lambda a, t=tempus: tempusnamn.get(a.get("tempus")) in t)
    krav[PASSIVKONSTRUKTION] = sist_med(lambda a: a.get("diates") == 2)

    # Proportionell position i [0, 1) för varje rad i båda listorna.
    rader: list[tuple[float, int, str, str]] = []
    for i, cell in enumerate(böjning):
        rader.append(((i + 1) / len(böjning), 0, "böjning", cell))
    for i, namn in enumerate(konstruktioner):
        pos = (i + 1) / len(konstruktioner)
        # Ligger konstruktionen före sitt krav skjuts den ner precis efter.
        gräns = krav.get(namn, -1)
        if gräns >= 0:
            pos = max(pos, (gräns + 1) / len(böjning))
        # 1 = konstruktionen kommer EFTER böjningen på samma position, så
        # den böjning ett krav pekar på hinner före.
        rader.append((pos, 1, "konstruktion", namn))
    rader.sort(key=lambda r: (r[0], r[1]))
    return [(typ, namn) for _, _, typ, namn in rader]
