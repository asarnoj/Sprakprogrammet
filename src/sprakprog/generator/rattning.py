"""Rättning — från användarens text till ett betyg per kort.

Det här är ledet som stänger slingan. Generatorn bygger meningen och
schemaläggaren tar emot `kort_id → klarade det`; den här modulen fyller i
den ordboken.

MEKANISK RÄTTNING FÖRST (GENERATOR.md, "Attribution"). Databasen har varje
form med sina axelkoordinater, så frågan "vad skrev användaren egentligen"
är ett uppslag och inte en gissning:

    skrev "gab", förväntat "gaben"     rätt ord, fel cell — skiljer på numerus
    skrev "nahm", förväntat "gaben"    ingen form av geben — fel ord

STAMUPPDELNINGEN LOKALISERAR FELET. Samma analys som avgör vilka kort som
finns avgör också vilket av dem som fallerade: skiljer sig bara ÄNDELSEN är
det systemkortet som brast, skiljer sig STAMMEN är det ordets eget kort.
"größte" mot "größten" är ändelsen; "großen" mot "größten" är stammen.

SYNKRETISMEN SITTER I FÖRKLARINGEN, INTE I BETYGET. 77 % av tyskans celler
delar sin form med en annan cell, och när användaren skriver fel form matchar
den i hälften av fallen FLERA celler — det går då inte att veta vilken hen
menade. Men BETYGET behöver inte veta det: skulden avgörs av stamuppdelningen
mot den VÄNTADE cellen, inte av vilken cell användaren siktade på. Mätt med
känd skada: rätt kort i 98 % av fallen med fel form, 100 % med fel ord och
100 % med utelämnat ord, och noll fall där fel kort skylldes.

Förklaringen räknar därför upp ALLA celler formen kan vara, i stället för att
välja den första och låta som om den vet. Det är också mer användbart: att en
form täcker tre celler är en sak att lära sig.

KOORDINATDIFF FÖRE STAMUPPDELNING. Cellen är ofta en FUNKTION av något
annat kort: `n_nom` valdes därför att substantivet är neutrum. Skrev
användaren en form som hade varit rätt vid ett annat genus är det
genuskunskapen som brast, inte artikelparadigmet — och det avgörs genom att
byta ut genuskomponenten i cellnamnet, inte genom att titta på historiken.

INGET BETYG ÄR BÄTTRE ÄN FEL BETYG. Går ett fel inte att knyta till ett kort
tas alla kort bakom den formen UR utfallet i stället för att stå kvar som
rätt. Default-True var ingen lucka utan en lögn åt fel håll: ett felskrivet
flerordigt verb gav Good till just de kort användaren nyss fällde.

NÄR DATAN INTE RÄCKER finns tre mekanismer, i tur och ordning — meningen
vittnar, historiken avgör, självrättning erbjuds. Den första och tredje
kräver mer kontext respektive ett gränssnitt; den här modulen implementerar
den andra och lämnar de andra två som en anmärkning användaren kan agera på.

KÄND GRÄNS: japanskan skrivs utan mellanslag, så en ordvis diff finns inte
att göra. Där jämförs i stället varje väntad form som delsträng, vilket är
grövre — det säger att formen saknas men inte vad som stod i stället.
"""

from __future__ import annotations

import difflib
import sqlite3
import unicodedata
from dataclasses import dataclass, field, replace

from ..rendering import RENDERARE, RenderingsFel, Uppslag

#: Språk som skriver med mellanslag mellan orden. Japanskan gör inte det.
ORDMELLANRUM = ("sv", "en", "de", "fr", "es", "it")

#: Genusvärde → de token språkets cellnamn byggs av. Speglar renderarnas
#: egna tabeller: de.GENUSNAMN {1:m, 2:f, 3:n}, sv UTRUM/NEUTRUM (som heter
#: m/f i celler enligt _legend.yaml, och utr/neu i artikelparadigmet),
#: romansk MASKULIN/FEMININ.
#:
#: Tabellen finns för att kunna DIFFA KOORDINATER i stället för strängar.
#: `n_nom` valdes därför att substantivet är neutrum; skriver användaren en
#: form som hör till `f_nom` är den ekonomiska läsningen att hen räknade
#: fram cellen ur fel genus — inte att hen kunde cellen och skrev fel sträng.
#: KASUS SOM KOORDINAT, samma form som genus. Bara tyskan har kasus i
#: cellnamnen; romanska språk realiserar rektionen med preposition i stället,
#: och det är ett ORD i diffen och inte en koordinat i en cell.
KASUSTOKEN = {
    "de": {1: ("nom",), 2: ("akk",), 4: ("dat",), 8: ("gen",)},
}

#: Kasusens namn i förklaringen. Samma tal som `rendering/de.py` använder —
#: IntFlag, Nom=1, Ack=2, Dat=4, Gen=8.
KASUSNAMN = {1: "nominativ", 2: "ackusativ", 4: "dativ", 8: "genitiv"}

GENUSTOKEN = {
    "de": {1: ("m",), 2: ("f",), 3: ("n",)},
    "sv": {1: ("m", "utr"), 2: ("f", "neu")},
    "fr": {1: ("m",), 2: ("f",)},
    "es": {1: ("m",), 2: ("f",)},
    "it": {1: ("m",), 2: ("f",)},
}


def _normalisera(text: str) -> str:
    """Bort med skiljetecken och versalisering — de är inte kort."""
    utan = "".join(
        " " if unicodedata.category(t).startswith("P") and t != "'" else t
        for t in text)
    return " ".join(utan.lower().split())


@dataclass(frozen=True, slots=True)
class Anmärkning:
    """Ett fel, med vad systemet trodde att det berodde på."""
    skrev: str
    väntat: str
    slutsats: str
    kort_id: int | None = None
    osäker: bool = False

    #: SLUTSATSEN SOM NYCKEL, vid sidan av den svenska texten.
    #:
    #: `slutsats` är prosa på svenska och gick rakt ut i gränssnittet, som är
    #: på engelska. Skärmen sa ordagrant "fel stam — skrev formen för
    #: pres_3sg": ett svenskt omdöme och ett internt cellnamn, mitt i en
    #: engelsk rättning. Samma sak för ordföljdsreglerna, vars facit är
    #: "finita verbet på plats två i huvudsats".
    #:
    #: Texten bor därför i `T` i sida.html, där all annan gränssnittstext bor,
    #: och backend skickar nyckeln plus det som ska fyllas i. Ett andra
    #: programspråk blir då en kolumn där och ingenting här.
    #:
    #: `slutsats` STÅR KVAR och är fortfarande svensk prosa: den är vad
    #: `__str__` skriver, alltså vad som hamnar i loggar och i
    #: felsvepets utskrifter. Att ta bort den vore att göra proven svårare att
    #: läsa för att gränssnittet skulle bli rätt.
    nyckel: str = ""
    #: Det nyckeln behöver fyllas med — ett koncept, en cellista, en form.
    arg: str = ""

    #: Ordet var RÄTT men stod på fel plats. Då fälls inget kort — se
    #: `_flyttade`. Skiljs från `kort_id is None`, som betyder motsatsen:
    #: att felet var verkligt men inte gick att knyta till ett kort.
    ordföljd: bool = False

    #: Orden skulle ha smält samman (elision, sammandragning). Samma sorts
    #: undantag som `ordföljd`: felet är verkligt och ska SÄGAS, men det har
    #: inget kort och får därför varken fälla eller undanhålla något. Utan
    #: flaggan drog anmärkningen med sig korten bakom den sammansmälta
    #: token, alltså just de kort användaren visade korrekt.
    sandhi: bool = False

    def __str__(self) -> str:
        säkerhet = "  (osäker)" if self.osäker else ""
        skrev = self.skrev or "—"
        if self.ordföljd:
            return f"{self.väntat!r} står på fel plats: {self.slutsats}"
        return f"{skrev!r} skulle vara {self.väntat!r}: {self.slutsats}{säkerhet}"


@dataclass(frozen=True, slots=True)
class Rättning:
    korrekt: bool
    utfall: dict[int, bool]
    anmärkningar: list[Anmärkning] = field(default_factory=list)


class Rättare:
    def __init__(self, språk_db: sqlite3.Connection, kort_db: sqlite3.Connection,
                 språk: str) -> None:
        self.u = Uppslag(språk_db, språk)
        self.kort_db = kort_db
        self.språk = språk
        #: stam → koncept, läst lat. Se `_bär_stammen`.
        self._stammar: dict[str, set[str]] | None = None
        #: Renderaren, BARA för dess sandhi. Rättningen bygger inga meningar
        #: — den behöver veta hur två ord smälter ihop till ett, och det
        #: svaret finns bara i koden som gjorde det. Se `_sammansmälta`.
        self._renderare = RENDERARE[språk](språk_db)

    # ── uppslag ──────────────────────────────────────────────────────

    def _celler_för(self, koncept: str, variant: str | None) -> dict[str, str]:
        """Alla ifyllda former för ett lexem, eller tomt om det inte finns.

        SMAL FÅNGST MED FLIT. Det stod `except Exception` här, och mätt över
        hela lexikonet — 5 149 lexem i sju språk — kastar `_celler` aldrig.
        Grenen var alltså död, och det enda den kunde göra var att svälja en
        framtida bugg: ett `TypeError` ur en kodändring hade blivit "inga
        celler", och rättningen hade tyst slutat attribuera i stället för att
        säga ifrån.
        """
        try:
            return {c: f for c, f in self.u._celler(
                self.u.lexem(koncept, variant)).items() if f}
        except (RenderingsFel, KeyError):
            return {}

    def _kort_för(self, koncept: str, variant: str | None, cell: str) -> list:
        return self.kort_db.execute(
            """SELECT k.* FROM Cellkort c JOIN Kort k ON k.id = c.kort_id
               WHERE c.språk = ? AND c.koncept = ? AND c.cell = ?
                 AND (c.variant IS ? OR c.variant = ?)""",
            (self.språk, koncept, cell, variant, variant)).fetchall()

    def _ordkort(self, koncept: str, variant: str | None):
        return self.kort_db.execute(
            """SELECT * FROM Kort WHERE språk = ? AND typ = 'ord'
               AND koncept = ? AND (variant IS ? OR variant = ?)""",
            (self.språk, koncept, variant, variant)).fetchone()

    def _stamindex(self) -> dict[str, set[str]]:
        """stam → de koncept som har den. Läses en gång och sparas."""
        if self._stammar is None:
            self._stammar = {}
            for r in self.kort_db.execute(
                    """SELECT koncept, facit FROM Kort
                       WHERE språk = ? AND typ = 'stam' AND koncept IS NOT NULL
                         AND facit IS NOT NULL AND facit <> ''""", (self.språk,)):
                self._stammar.setdefault(
                    _normalisera(r["facit"]), set()).add(r["koncept"])
        return self._stammar

    def _bär_stammen(self, skrev: str, koncept: str) -> bool:
        """Bär försöket `koncept`s stam — eller är det ett ANNAT ord?

        DEN LÄNGSTA MATCHANDE STAMMEN FÖRKLARAR FÖRSÖKET. En naken
        prefixregel duger inte: stammarna är korta, och `a` (avoir) är
        prefix till halva franskan. Mätt över hela beståndet — varje äkta
        form prövad mot alla andra koncepts stammar — matchar 21 % av de
        franska formerna NÅGON främmande stam. Låter man i stället den
        längsta matchningen avgöra faller det till 3 % (fr), 6 % (de) och
        0 % (en).

        Regeln är alltså ingen tröskel utan en bästa förklaring: skrev
        användaren `aime` när `a` väntades är `aim-` en längre förklaring än
        `a-`, och då är det ett annat ord — inte avoir felböjt.
        """
        index = self._stamindex()
        träffar = [st for st in index if st and skrev.startswith(st)]
        if not träffar:
            return False
        längst = max(len(st) for st in träffar)
        return any(koncept in index[st] for st in träffar if len(st) == längst)

    # ── attribution ──────────────────────────────────────────────────

    @staticmethod
    def _cellista(träffar: list[str]) -> str:
        """Cellerna en skriven form kan vara — alla, inte den första.

        Att välja en av flera vore att påstå något systemet inte vet.
        """
        if len(träffar) == 1:
            return träffar[0]
        if len(träffar) == 2:
            return f"{träffar[0]} or {träffar[1]}"
        return ", ".join(träffar[:-1]) + f" or {träffar[-1]}"

    def _genuskort(self, koncept: str):
        return self.kort_db.execute(
            """SELECT * FROM Kort WHERE språk = ? AND typ = 'egenskap'
               AND egenskap = 'genus' AND koncept = ?""",
            (self.språk, koncept)).fetchone()

    def _genusbytet(self, cell: str, träffar: list[str], genus: int) -> bool:
        """Skulle den skrivna formen vara rätt om ordet haft ett ANNAT genus?"""
        return self._koordinatbytet(
            cell, träffar, GENUSTOKEN.get(self.språk, {}), genus)

    def _koordinatbytet(self, cell: str, träffar: list[str],
                        tokens: dict, eget) -> bool:
        """Skulle formen vara rätt om EN koordinat haft ett annat värde?

        Det är hela koordinatdiffen. Cellnamnet är en koordinat — `n_nom` är
        (genus=n, kasus=nom) — så frågan går att ställa exakt: byt ut
        komponenten mot varje annat värde språket har, och se om någon av de
        cellerna är en av dem användaren faktiskt skrev.

        Är svaret ja brast KUNSKAPEN OM KOORDINATEN, inte formen i
        paradigmet. Det avgörandet läser paradigmets koordinatsystem och inte
        användarens historik — det behöver alltså inte anta att människor är
        regelbundna, vilket de inte är.

        Samma kod svarar på genusfrågan och rektionsfrågan; det är bara
        koordinaten som byts. A7 föreskrev generaliseringen och det här är
        den: `_genusbytet` är nu ett anrop med `GENUSTOKEN`, rektionen ett
        med `KASUSTOKEN`.
        """
        egna = tokens.get(eget)
        if not egna:
            return False
        delar = cell.split("_")
        plats = next((i for i, d in enumerate(delar) if d in egna), None)
        if plats is None:
            return False          # cellen bär inte koordinaten — t.ex. plural
        for annat, andra in tokens.items():
            if annat == eget:
                continue
            for t in andra:
                kandidat = list(delar)
                kandidat[plats] = t
                if "_".join(kandidat) in träffar:
                    return True
        return False

    def _rektionskort(self, koncept: str, slot: str):
        return self.kort_db.execute(
            """SELECT * FROM Kort WHERE språk = ? AND typ = 'rektion'
               AND egenskap = 'kasus' AND koncept = ? AND cell = ?""",
            (self.språk, koncept, slot)).fetchone()

    def _rektionsgivaren(self, cell: str, träffar: list[str],
                         rektioner: list) -> tuple[str, str] | None:
        """Vilket VERB styrde kasusen — och brister dess rektion?

        Samma form som `_genusgivaren`, och det är hela poängen med A7:s
        punkt 3. Skillnaden är vem kunskapen hör till. `dem Mann` i stället
        för `den Mann` är inte ett fel i artikelparadigmet — formen är helt
        korrekt, bara för dativ — och vad som avgör vilken kasus frasen SKA
        ha är verbet: `helfen` tar dativ, `fragen` ackusativ.

        Kandidaterna är de verb vars rektion renderaren faktiskt slog upp
        (`Uppslag.rektion`). Passar EXAKT EN av dem koordinatdiffen är svaret
        entydigt; passar flera säger vi ingenting, precis som D1 gör. Två
        rektioner i samma mening — `geben` styr både objekt och io — är ett
        äkta tolkningsfall, och att välja den första vore att gissa.
        """
        tokens = KASUSTOKEN.get(self.språk, {})
        if not tokens:
            return None
        träffande = []
        for koncept, slot, namn in rektioner:
            if namn != "kasus":
                continue
            rad = self._rektionskort(koncept, slot)
            if rad is None or rad["facit"] is None:
                continue
            try:
                kasus = int(rad["facit"])
            except (TypeError, ValueError):
                continue
            if self._koordinatbytet(cell, träffar, tokens, kasus):
                träffande.append((koncept, slot))
        return träffande[0] if len(träffande) == 1 else None

    def _genusgivaren(self, cell: str, träffar: list[str],
                      egenskaper: list) -> str | None:
        """Vilket substantiv styrde cellen — och brister dess genus?

        Kandidaterna är de ord vars genus renderaren faktiskt slog upp när
        meningen byggdes. Passar EXAKT ETT av dem koordinatdiffen är svaret
        entydigt. Passar flera vet vi inte vilket av dem användaren tänkte
        på, och då säger vi ingenting — två neutrumord i samma mening är ett
        äkta tolkningsfall, och att välja det första vore att gissa.
        """
        träffande = []
        for koncept, namn in egenskaper:
            if namn != "genus":
                continue
            rad = self._genuskort(koncept)
            if rad is None or rad["facit"] is None:
                continue
            try:
                genus = int(rad["facit"])
            except (TypeError, ValueError):
                continue
            if self._genusbytet(cell, träffar, genus):
                träffande.append(koncept)
        return träffande[0] if len(träffande) == 1 else None

    def _skyll(self, skrev: str, väntat: str, koncept: str, variant: str | None,
               cell: str, egenskaper: list | None = None,
               rektioner: list | None = None
               ) -> tuple[int | None, str, bool, str, str]:
        """(kort_id, förklaring, osäker, nyckel, arg) för ETT felskrivet ord.

        `nyckel` och `arg` är samma slutsats som `förklaring`, men i en form
        gränssnittet kan sätta text på själv — se `Anmärkning.nyckel`.

        Ordningen är den GENERATOR.md föreskriver: låt datan avgöra så långt
        den räcker, och gå till historiken först när den tar slut.
        """
        kort = self._kort_för(koncept, variant, cell)
        stamkort = next((k for k in kort if k["typ"] in ("stam", "form")), None)
        systemkort = next((k for k in kort if k["typ"] == "system"), None)

        celler = self._celler_för(koncept, variant)
        träffar = [c for c, f in celler.items() if _normalisera(f) == skrev]

        if not träffar:
            # STAMMEN I FÖRSÖKET BEVISAR ATT ORDET HÄMTADES FRAM. Skrev
            # användaren `existerer` när `existez` väntades är `exist-` där:
            # ordet fanns, ändelsen brast. Att kalla det "fel ord" är att
            # underkänna kunskap användaren visade — och värre än så, för ett
            # fallerat ordkort SKYDDAR sina form- och stamkort (A4), så
            # böjningsfelet blev varken bedömt eller ens registrerat.
            #
            # A4:s regel är riktig men villkoret var för brett. Regeln säger
            # "kan man inte hämta fram ordet ALLS prövades böjningen aldrig".
            # Koden prövade i stället "är det här exakt en känd cellform" —
            # och varje felböjning är per definition ingen känd cellform.
            # Skyddet gällde alltså precis de fall det inte var till för.
            #
            # Nu är ordkortet kvar som svar bara när försöket inte ens bär
            # stammen. Bär det stammen faller det till systemkortet nedan,
            # alltså till ändelsen — vilket är vad som faktiskt gick fel.
            if (systemkort is not None and stamkort is not None
                    and stamkort["typ"] == "stam"
                    and self._bär_stammen(skrev, koncept)):
                return (systemkort["id"],
                        f"rätt stam {stamkort['facit']!r}, men {skrev!r} är "
                        f"ingen form av {koncept} — ändelsen brast", False,
                        "ändelsen_brast", stamkort["facit"])
            # Ingen form av ordet alls — då är det ordet som brast, inte
            # böjningen. Ett ord man inte kan hämta fram går inte att böja.
            ordkort = self._ordkort(koncept, variant)
            return (ordkort["id"] if ordkort else None,
                    f"ingen form av {koncept}, alltså fel ord", False,
                    "fel_ord", "")

        # RÄTT CELL AV FEL SKÄL. Innan stamuppdelningen får avgöra: skulle
        # formen användaren skrev vara RÄTT om substantivet haft ett annat
        # genus? Då är det inte artikelparadigmet som brister utan kunskapen
        # om ordets genus, och det är ett eget kort.
        #
        # Utan det här steget skylldes "die Kind" alltid på artikelns
        # formkort — alltså på det kort som möts i nästan varje mening och
        # därför nästan säkert sitter — medan genuset för just Kind, ett av
        # 159 enskilda fakta med låg exponering, gick fritt. Fel kort i
        # praktiskt taget varje verkligt fall.
        # RÄTT FORM AV FEL KASUS, samma fråga ett steg upp. Skrev användaren
        # `dem Mann` där `den Mann` väntades är artikelformen inte påhittad —
        # den är korrekt för dativ. Vad som avgör kasusen är VERBET, och det
        # är ett eget kort (rektion). Utan det här steget skylldes felet på
        # artikelns formkort, alltså på det kort som möts i nästan varje
        # mening, medan rektionen för just `helfen` gick fri.
        #
        # Före genus, eftersom rektionen är den yttre orsaken: bytte
        # användaren kasus är genuset oförändrat och genusdiffen skulle inte
        # slå till ändå — men ordningen ska säga vilken fråga som är först.
        styrande = self._rektionsgivaren(cell, träffar, rektioner or [])
        if styrande is not None:
            rad = self._rektionskort(*styrande)
            if rad is not None:
                verb, slot = styrande
                kasus = KASUSNAMN.get(int(rad["facit"]), rad["facit"])
                return (rad["id"],
                        f"formen stämmer för en annan kasus — {verb} styr "
                        f"{slot} till {kasus}",
                        False, "fel_rektion", f"{verb} · {slot} · {kasus}")

        givare = self._genusgivaren(cell, träffar, egenskaper or [])
        if givare is not None:
            genuskort = self._genuskort(givare)
            if genuskort is not None:
                return (genuskort["id"],
                        f"formen stämmer för ett annat genus — {givare} styr "
                        f"{cell}", False, "fel_genus", givare)

        # Rätt ord, fel cell. Stamuppdelningen säger vilket kort som brast —
        # men bara när det FINNS en uppdelning. En rest är hela formen i ett
        # kort, och då är den frågan meningslös.
        if stamkort is not None and stamkort["typ"] == "form":
            return (stamkort["id"],
                    f"formen för {self._cellista(träffar)}, inte {cell} — "
                    f"ordet har ingen härledbar stam här", False,
                    "fel_form_orgelbunden", self._cellista(träffar))
        if stamkort is not None and systemkort is not None:
            stam = _normalisera(stamkort["facit"])
            if stam and skrev.startswith(stam):
                return (systemkort["id"],
                        f"rätt stam {stamkort['facit']!r}, fel ändelse — "
                        f"{self._cellista(träffar)} i stället för {cell}", False,
                        "fel_ändelse", self._cellista(träffar))
            return (stamkort["id"],
                    f"fel stam — skrev formen för {self._cellista(träffar)}", False,
                    "fel_stam", self._cellista(träffar))

        enda = stamkort or systemkort
        if enda is not None:
            return (enda["id"],
                    f"formen för {self._cellista(träffar)}, inte {cell}", False,
                    "fel_cell", self._cellista(träffar))

        # Datan räcker inte: skyll på det svagaste kortet i ledet.
        # Felattribution självläker — skyller systemet fel klarar det kortet
        # sin extra repetition, och det rätta förblir svagt.
        if kort:
            svagast = min(kort, key=lambda k: k["stabilitet"] or 0)
            return (svagast["id"],
                    "kunde inte avgöras ur formen — svagaste kortet", True,
                    "svagaste", "")
        return None, "inget kort hör till ordet", True, "inget_kort", ""

    # ── rättning ─────────────────────────────────────────────────────

    def _ordföljdskortet(self, kort: list, ordföljder: list):
        """Det kort som ska bära ett ordföljdsfel — eller inget.

        A7 punkt 2, sista stycket: är bara EN ordföljdsregel schemalagd i
        meningen är svaret entydigt. Är flera det vet vi inte vilken som
        brast, och då säger vi ingenting — precis som D1 gör, och av samma
        skäl som pinne 7 finns till för att undvika.

        SCHEMALAGD, inte tillämpad. En mening tillämpar nästan alltid sin
        grundordföljd (`v2`, `svo`, `sov`), men de reglerna är per E6 lyfta
        ur schemat — de möts i varje mening och går inte att spaca. Räknade
        vi dem här skulle svaret ALLTID vara "flera regler, alltså tystnad",
        och den lågfrekventa regel som faktiskt brast — bisatsordföljden,
        inversionen — skulle aldrig kunna fällas. Det är samma urval som
        `förfallna` gör, sett från rättningens håll.
        """
        tillämpade = set(ordföljder)
        kandidater = [k for k in kort
                      if k["typ"] == "ordföljd" and k["schemalagt"]
                      and k["egenskap"] in tillämpade]
        return kandidater[0] if len(kandidater) == 1 else None

    def rätta(self, svar: str, facit: str, uppslag: list[tuple[str, str | None, str]],
              kort: list, egenskaper: list | None = None,
              rektioner: list | None = None,
              ordföljder: list | None = None,
              osammansmält: list[str] | None = None) -> Rättning:
        """Betygsätt varje kort utifrån användarens svar.

        `uppslag` är renderarens beroendekarta som lista: (koncept, variant,
        cell) i den ordning formerna slogs upp. Den kommer från samma
        instrumentering generatorn redan använder.
        """
        utfall = {k["id"]: True for k in kort}
        if _normalisera(svar) == _normalisera(facit):
            return Rättning(True, utfall, [])

        # SVARET GENOM SAMMA SANDHI. Blir det då facit har användaren
        # producerat varje FORM rätt och bara missat sammansmältningen:
        # `Je apprends` mot `J'apprends.` är rätt pronomen, rätt böjning,
        # rätt ordföljd — och en elision som inte gjordes.
        #
        # Det är en egen sorts fel och det har INGET KORT. Elisionen står
        # inte i `ORDFÖLJD` och är ingen böjning; den är en fonologisk regel
        # som renderaren tillämpar. Så länge den saknar kort gäller D3:
        # säg vad som var fel, mät ingenting på det, och straffa inte de
        # kort som faktiskt visades.
        #
        # Utan det här ledet gick fallet inte att skilja från "fel ord": före
        # rättelsen fick alla sju korten GOOD, och efter den första
        # rättelsen hölls hela meningen inne. Båda var fel, åt var sitt håll.
        if self._bara_sandhi(svar, facit):
            return Rättning(False, utfall, [Anmärkning(
                _normalisera(svar), _normalisera(facit),
                "formerna är rätt men ska smälta samman — "
                f"{_normalisera(facit)}", None, False,
                nyckel="sandhi", arg=_normalisera(facit), sandhi=True)])

        anmärkningar: list[Anmärkning] = []
        if self.språk in ORDMELLANRUM:
            anmärkningar = self._ordvis(svar, facit, uppslag,
                                        egenskaper or [], rektioner or [],
                                        osammansmält)
        else:
            anmärkningar = self._delsträngar(svar, uppslag)

        # RÄTT ORD PÅ FEL PLATS fäller inget ORDKORT — användaren hämtade
        # fram ordet och böjde det rätt, och det är ett bevis. Men skulden
        # finns, och sedan A7 punkt 2 har den ett kort att landa på.
        ordföljdskort = (self._ordföljdskortet(kort, ordföljder or [])
                         if any(a.ordföljd for a in anmärkningar) else None)
        if ordföljdskort is not None:
            # `Anmärkning` är frozen, så kortet skrivs in genom att bygga om
            # raden — inte genom att tilldela. Det är avsiktligt: en
            # anmärkning ska inte kunna ändras efter att den skapats.
            anmärkningar = [
                replace(a, kort_id=ordföljdskort["id"],
                        slutsats=f"{a.slutsats} — {ordföljdskort['facit']}",
                        arg=ordföljdskort["facit"])
                if a.ordföljd else a
                for a in anmärkningar]
        for a in anmärkningar:
            if a.sandhi:
                # Sagt, inte mätt. Se `Anmärkning.sandhi`.
                continue
            if a.ordföljd:
                # Är regeln entydig fälls den. Är den det inte säger systemet
                # fortfarande vad som var fel utan att mäta något — vilket är
                # D3:s princip och inte en brist.
                if ordföljdskort is not None:
                    utfall[ordföljdskort["id"]] = False
                continue
            if a.kort_id is not None:
                utfall[a.kort_id] = False
                # ETT FÄLLT ORDKORT SKYDDAR ALLT BAKOM SIN FORM, inte bara
                # stam och form. A4 säger att böjning förutsätter ordet, och
                # skyddet i `Schemaläggare._skyddade` gäller `stam` och
                # `form` — men ÄNDELSEN är ett `system`-kort och hade ingen
                # koppling till ordet att skyddas genom.
                #
                # Mätt fall: facit `Vous coûtez.`, användaren skrev
                # `nous coüter`. Ordkortet för `coûter` föll, som det ska —
                # och ändelsekortet `ez` fick GOOD, trots att svaret var en
                # infinitiv där bokstäverna `ez` inte förekom. FSRS fick veta
                # att ändelsen sitter i samma stund som användaren visade
                # motsatsen.
                #
                # Vägen är uppslagets: den form ordet skulle haft pekar på
                # alla kort som hänger på den cellen, oavsett typ. Ordkortet
                # självt undantas — det är just det som fälldes.
                #
                # Hellre ingen mätning än en felaktig, samma regel som
                # nedan: ett kort utan historik är ärligt osäkert, ett kort
                # med falsk historik är värre än tomt.
                #
                # OCH SAMMA SAK NÄR GENUSET FALLER. Genuset väljer formen,
                # så ett fel genus betyder att den rätta formen aldrig
                # skrevs: `die Bruder` för `Der Bruder` lämnade `form:der`
                # stående som rätt fast strängen inte fanns i svaret.
                #
                # SAMMA SAK NÄR STAMMEN FALLER. Är det STAMMEN som brast var
                # hela formen fel, och ändelsen för den cellen visades inte
                # heller: `Männern` för `Mann` är stam `Männ` plus ändelse
                # `ern` där `Mann` plus `∅` väntades. Att låta `nom_sg ∅`
                # stå kvar som rätt är att belöna en ändelse användaren
                # aldrig skrev — mätt 17 gånger på 420 tyska prövningar.
                #
                # ÅT ANDRA HÅLLET GÄLLER DET INTE. Faller ÄNDELSEN har
                # stammen per definition visats — det är så `_skyll` kom
                # fram till att det var ändelsen — och att undanhålla den
                # vore att kasta bevis man har.
                if (self._är_ordkort(a.kort_id)
                        or self._valde_hela_formen(a.kort_id)):
                    for kid in self._kan_ha_burit(a.väntat, uppslag):
                        if kid != a.kort_id:
                            utfall.pop(kid, None)
                continue
            # OATTRIBUERAT FEL: vi vet att ordet blev fel men inte vilket kort
            # som bar det. Då får inget kort som kan ha burit ordet betygsättas
            # alls — de TAS UR utfallet i stället för att stå kvar som rätt.
            #
            # Att låta dem stå kvar var inte en lucka utan en LÖGN åt fel håll.
            # Mätt fall: facit "A cloud lies down.", användaren skrev "A cloud
            # lie down." — systemet såg felet, kunde inte knyta det till ett
            # kort (formen "lies down" är två ord, diffen ett), och skickade
            # Good till BÅDA korten för verbet som just blivit fel. FSRS fick
            # veta att formen sitter, precis när användaren bevisat motsatsen,
            # och sköt kortet längre bort.
            #
            # Hellre ingen mätning än en felaktig: ett kort utan historik är
            # ärligt osäkert, ett kort med falsk historik är värre än tomt.
            bakom = self._kan_ha_burit(a.väntat, uppslag)
            if bakom:
                for kid in bakom:
                    utfall.pop(kid, None)
                continue
            if not _normalisera(a.väntat):
                # ETT EXTRA ORD HAR INGEN MOTPART ATT SPÅRA. Anmärkningen
                # säger att användaren skrev något som inte hörde hit, och
                # det är sant och värt att visa — men det pekar inte ut något
                # kort, och det ogiltigförklarar inte heller de andra. En
                # dubblerad preposition gör inte verbets böjning osäker.
                #
                # Utan det här ledet drog varje extra ord hela meningen ur
                # betygsättningen, vilket är att kasta bevis man HAR.
                continue
            # OCH GÅR INTE ENS DET, HÅLLS HELA MENINGEN INNE. Uppslaget är
            # per FORM men diffen per TOKEN, och sandhi kan slå ihop två
            # uppslag till en token: `je` + `apprends` blir `j'apprends`, och
            # då finns ingen form i uppslaget som matchar det felskrivna
            # ordet. `_kan_ha_burit` svarar tomt, och utan det här ledet
            # hände då INGENTING — alla kort stod kvar som rätt.
            #
            # Mätt: facit `J'apprends.`, svar `Je apprends`. Svaret var fel,
            # och sju kort av sju fick Good. FSRS fick veta att stammen,
            # ändelsen och ordföljden alla sitter, i samma stund som
            # användaren missat elisionen.
            #
            # Att hålla inne hela meningen kastar riktiga bevis — stammen och
            # ändelsen VAR rätt — och det är ett verkligt pris. Men modulens
            # regel är den andra: inget betyg är bättre än fel betyg. Ett
            # kort utan historik är ärligt osäkert; ett med falsk historik
            # ljuger vidare i veckor.
            utfall.clear()
            break
        return Rättning(False, utfall, anmärkningar)

    def _smälter_ihop(self, osammansmält: list[str]) -> bool:
        """SLÅR sandhi ihop ord här, eller byter den bara ut dem?

        Skillnaden avgör om den osammansmälta listan får användas som facit.
        Franskans elision SLÅR IHOP — `je` + `existe` blir ett ord — och då
        är listan den enda som har tokengränsen kvar. Engelskans `a` → `an`
        BYTER UT ett ord utan att röra antalet, och där är den osammansmälta
        listan direkt fel: den innehåller `a` medan facit har `an`, så varje
        korrekt skrivet `an` hade sett ut som ett fel.

        Mätt när regressionen infördes: `A cat will not give…` fällde
        ordkortet vid en ren omkastning, därför att diffen ställde `an` mot
        `a`. Villkoret är alltså antalet ord, inte deras innehåll.
        """
        smälter = getattr(self._renderare, "sandhi", None)
        if smälter is None:
            return False
        try:
            return len(smälter(list(osammansmält))) < len(osammansmält)
        except (RenderingsFel, KeyError, ValueError, IndexError):
            return False

    def _dela_vid_sandhi(self, tokens: list[str],
                         osammansmält: list[str]) -> list[str]:
        """Dela upp de tokens som sandhi skulle ha smält ihop.

        Svaret kan vara skrivet MED sammansmältning (`J'exister`) eller UTAN
        (`Je exister`). Diffen går mot de osammansmälta orden, så det första
        måste delas upp — annars ser ett korrekt skrivet svar ut som ett fel.

        Gränsen hämtas ur renderarens egen sandhi och inte ur en egen regel:
        smälter `je` + `existe` till `j'existe` är prefixet `j'`, alltså det
        som blir kvar när det andra ordet dras av. Ett svar som börjar på
        `j'` delas då i `je` plus resten — och resten är just det som ska
        ställas mot `existe`.

        Sammandragningar där formen inte SLUTAR på det andra ordet — franskans
        `de` + `le` → `du` — går inte att dela så, och lämnas ihop. Där är
        felet ändå på ett ord och inte i en gräns.
        """
        smälter = getattr(self._renderare, "sandhi", None)
        if smälter is None or len(osammansmält) < 2:
            return tokens
        par: list[tuple[str, str]] = []
        for a, b in zip(osammansmält, osammansmält[1:]):
            try:
                smält = smälter([a, b])
            except (RenderingsFel, KeyError, ValueError, IndexError):
                continue
            if len(smält) != 1:
                continue
            hel, nb = _normalisera(smält[0]), _normalisera(b)
            if nb and hel.endswith(nb) and len(hel) > len(nb):
                par.append((hel[:-len(nb)], _normalisera(a)))
        if not par:
            return tokens
        ut: list[str] = []
        for t in tokens:
            for prefix, första in par:
                if prefix and t.startswith(prefix) and len(t) > len(prefix):
                    ut += [första, t[len(prefix):]]
                    break
            else:
                ut.append(t)
        return ut

    def _bara_sandhi(self, svar: str, facit: str) -> bool:
        """Blir svaret facit om man tillämpar renderarens egen sandhi?

        Frågan ställs till DEN SOM GJORDE DET. En egen tabell över elisioner
        och sammandragningar skulle kunna glida isär från renderarens, och
        det är just den sortens dubblering som gör att två delar av systemet
        kan säga olika saker om samma språk.

        Bara för språk som HAR sandhi, och bara när svaret faktiskt skiljer
        sig från facit — annars svarar den ja på en redan rätt mening.
        """
        smälter = getattr(self._renderare, "sandhi", None)
        if smälter is None:
            return False
        ord_ = _normalisera(svar).split()
        if not ord_:
            return False
        try:
            return _normalisera(" ".join(smälter(ord_))) == _normalisera(facit)
        except (RenderingsFel, KeyError, ValueError, IndexError):
            return False

    def _är_ordkort(self, kort_id: int) -> bool:
        """Är det ordet självt som fälldes, inte dess böjning?"""
        rad = self.kort_db.execute(
            "SELECT typ FROM Kort WHERE id = ?", (kort_id,)).fetchone()
        return rad is not None and rad["typ"] == "ord"

    def _valde_hela_formen(self, kort_id: int) -> bool:
        """Fälldes något som avgör VILKEN FORM som skulle skrivas?

        Då skrevs formen aldrig, och ingenting bakom den har visats.

        `stam` och `form` bär formen direkt. `egenskap` — genus — gör det
        indirekt men lika hårt: genuset VÄLJER formen, så ett fel genus
        betyder att den rätta formen aldrig producerades.

        Mätt fall, tyskan: facit `Der Bruder weiß ihre Nachmittage.`,
        användaren skrev `die Bruder`. Genuskortet föll, som det ska — och
        `form:der` fick GOOD, trots att strängen `der` inte fanns i svaret.
        Två sådana på 280 tyska prövningar; noll efter rättelsen, och utan
        att tystnaden ökade med en enda (96 före, 96 efter). Det är ovanligt
        för den här modulen — varje tidigare skärpning har kostat mätningar.
        """
        rad = self.kort_db.execute(
            "SELECT typ FROM Kort WHERE id = ?", (kort_id,)).fetchone()
        return rad is not None and rad["typ"] in ("stam", "form", "egenskap")

    def _kan_ha_burit(self, väntat: str,
                      uppslag: list[tuple[str, str | None, str]]) -> set[int]:
        """Alla kort bakom den FORM som det felskrivna ordet ingick i.

        Frågan är inte "vilket kort bar ordet" — den gick vi just bet på —
        utan "vilka kort går INTE att frikänna". Svaret hämtas samma väg som
        allt annat: uppslaget säger vilken form som slogs upp, och Cellkort
        säger vilka kort som hänger på den cellen.

        Det är därför vägen går via uppslaget och inte via en strängjämförelse
        mot kortens facit. En flerordig form som `lies down` bärs av TVÅ kort
        — formkortet `lies down` och ändelsekortet `s` — och det senare har
        ingenting i sitt facit som liknar det felskrivna ordet. Det var
        dessutom precis det kort användaren fällde när hen skrev `lie`.
        """
        ord = _normalisera(väntat)
        if not ord:
            return set()
        träffar: set[int] = set()
        former = []
        for koncept, variant, cell in uppslag:
            form = self._celler_för(koncept, variant).get(cell)
            former.append(form)
            if not form:
                continue
            delar = _normalisera(form).split()
            if ord in delar or _normalisera(form) == ord:
                for k in self._kort_för(koncept, variant, cell):
                    träffar.add(k["id"])
        if träffar:
            return träffar
        # SANDHI SLÅR IHOP TVÅ UPPSLAG TILL EN TOKEN, och då matchar ingen
        # form ordet. `je` + `apprends` blir `j'apprends`; varken `je` eller
        # `apprends` finns i den strängen, så jämförelsen ovan går bet.
        #
        # Det gick inte att laga med delsträngar — elisionen tar bort en
        # bokstav — och inte med en egen tabell heller, för då skulle den
        # kunna glida isär från renderarens. Frågan ställs därför till DEN
        # SOM GJORDE DET: smälter renderarens sandhi ihop de två formerna
        # till precis det här ordet?
        return self._sammansmälta(ord, uppslag, former)

    def _sammansmälta(self, ord: str,
                      uppslag: list[tuple[str, str | None, str]],
                      former: list[str | None]) -> set[int]:
        """Korten bakom en token som sandhi bildat av FLERA uppslag.

        Går grannvis, för det är så sandhi arbetar: den ser på det den nyss
        lagt ut och nästa ord. En kedja av tre — sammandragning följd av
        elision — fångas genom att fönstret växer tills det inte längre ger
        en enda token.

        Mätt före: ett fel i en elision höll HELA meningen utanför
        betygsättningen, eftersom ingen koppling gick att göra. 19 av 60
        franska felsvar gav då noll mätning.
        """
        # INTE ALLA SPRÅK HAR SANDHI. Tyskan och japanskan smälter inte
        # ihop ord, och saknar därför metoden helt — då finns ingen
        # sammansmältning att spåra och svaret är tomt.
        smälter = getattr(self._renderare, "sandhi", None)
        if smälter is None:
            return set()
        träffar: set[int] = set()
        for i in range(len(uppslag)):
            for j in range(i + 2, min(i + 5, len(uppslag) + 1)):
                bitar = [f for f in former[i:j] if f]
                if len(bitar) < 2:
                    continue
                try:
                    smält = smälter(list(bitar))
                except (RenderingsFel, KeyError, ValueError, IndexError):
                    continue
                if len(smält) == 1 and _normalisera(smält[0]) == ord:
                    for koncept, variant, cell in uppslag[i:j]:
                        for k in self._kort_för(koncept, variant, cell):
                            träffar.add(k["id"])
                    return träffar
        return träffar

    def _flerordiga(self, uppslag: list[tuple[str, str | None, str]]) -> set[str]:
        """Alla flerordiga former lexemen i meningen KAN realisera.

        Inte bara de celler som faktiskt slogs upp: användaren kan ha skrivit
        en annan form av samma ord — `lie down` när facit har `lies down` —
        och den ska kännas igen som EN enhet i svaret också, annars går diffen
        isär på mitten.
        """
        former: set[str] = set()
        for koncept, variant, _ in uppslag:
            for form in self._celler_för(koncept, variant).values():
                n = _normalisera(form)
                if " " in n:
                    former.add(n)
        return former

    @staticmethod
    def _segmentera(text: str, flerordiga: set[str]) -> list[str]:
        """Dela en normaliserad sträng i enheter, längsta form först.

        EN FLERORDIG FORM ÄR ETT ORD för rättningen. Diffen jämförde tidigare
        ord för ord, medan uppslaget lämnar `lies down` som en enda form —
        alltså matchade varken `lies` eller `down` mot något uppslag, och
        felet kunde inte knytas till något kort. Partikelverben är 11 av
        engelskans 206 kortformer men fanns i 19 % av meningarna.
        """
        if not flerordiga:
            return text.split()
        ord = text.split()
        längst = max(len(f.split()) for f in flerordiga)
        ut: list[str] = []
        i = 0
        while i < len(ord):
            for n in range(min(längst, len(ord) - i), 1, -1):
                kandidat = " ".join(ord[i:i + n])
                if kandidat in flerordiga:
                    ut.append(kandidat)
                    i += n
                    break
            else:
                ut.append(ord[i])
                i += 1
        return ut

    @staticmethod
    def _foga_samman(enheter: list[str], flerordiga: set[str]) -> list[str]:
        """Slå ihop en form vars delar står ISÄR i satsen.

        Tyskans avskiljbara partikel lossnar från verbet och går sist:
        "Das Kind wacht jetzt auf" — formen är `wacht auf`, men orden står på
        plats 3 och 5. Sammanfogningen ovan hittar bara det som står intill,
        så utan det här steget blev partikelverbet oattribuerbart så fort
        något stod emellan, vilket det oftast gör.

        Delarna måste stå i RÄTT ORDNING; det är hela spärren mot att foga
        ihop ord som råkar finnas i meningen. Formen läggs på den första
        delens plats och de övriga tas bort, så att ordföljden i övrigt är
        orörd och diffen kan jämföra facit mot svar enhet för enhet.
        """
        for form in sorted(flerordiga, key=lambda f: -len(f.split())):
            delar = form.split()
            if len(delar) < 2:
                continue
            platser: list[int] = []
            i = 0
            for d in delar:
                while i < len(enheter) and enheter[i] != d:
                    i += 1
                if i >= len(enheter):
                    break
                platser.append(i)
                i += 1
            if len(platser) != len(delar):
                continue
            if platser == list(range(platser[0], platser[0] + len(delar))):
                continue                      # stod redan intill varandra
            bort = set(platser[1:])
            enheter = [form if n == platser[0] else e
                       for n, e in enumerate(enheter) if n not in bort]
        return enheter

    @staticmethod
    def _flyttade(f: list[str], s: list[str], opkoder: list) -> set[str]:
        """Ord som finns på BÅDA sidor av diffen, men på olika platser.

        En omkastning ser i difflib ut som ett borttaget plus ett tillagt ord,
        aldrig som ett "flyttat" — verktyget har inget sådant begrepp. Men
        samma token i både `delete`/`replace` på facitsidan och
        `insert`/`replace` på svarssidan kan bara betyda att ordet stod där,
        fast på fel plats.

        Utan det här steget föll omkastningen ned i `_skyll`, som frågade
        vilken cell som renderar till tomma strängen, inte hittade någon, och
        drog slutsatsen "ingen form av konceptet, alltså fel ord". Alltså fick
        ORDKORTET Again — och via `_skyddade` undanhölls dessutom dess stam-
        och formkort. Användaren kunde ordet, skrev det korrekt, och fick veta
        att hen inte kunde det.

        Fallet där ordet är BÅDE flyttat och felböjt faller ut rätt av sig
        självt: då är det inte samma token längre, så bara flytten känns igen
        medan formfelet attribueras som vanligt.

        Mängder och inte multimängder: står samma ord två gånger i meningen
        och bara den ena förekomsten flyttades skonas båda. Det gör systemet
        för försiktigt, aldrig för tvärsäkert, och det är rätt håll att fela
        åt.
        """
        borttagna: list[str] = []
        tillagda: list[str] = []
        for tagg, i1, i2, j1, j2 in opkoder:
            if tagg in ("delete", "replace"):
                borttagna += f[i1:i2]
            if tagg in ("insert", "replace"):
                tillagda += s[j1:j2]
        return set(borttagna) & set(tillagda)

    def _ordvis(self, svar: str, facit: str,
                uppslag: list[tuple[str, str | None, str]],
                egenskaper: list | None = None,
                rektioner: list | None = None,
                osammansmält: list[str] | None = None) -> list[Anmärkning]:
        """Ordvis diff, och ett uppslag per avvikelse."""
        flerordiga = self._flerordiga(uppslag)
        s = self._foga_samman(
            self._segmentera(_normalisera(svar), flerordiga), flerordiga)
        f = self._foga_samman(
            self._segmentera(_normalisera(facit), flerordiga), flerordiga)
        # DIFFEN GÅR MOT DE OSAMMANSMÄLTA ORDEN, inte mot den färdiga texten.
        #
        # Sandhi slår ihop `je` + `existe` till `j'existe`, och då finns
        # ingen tokengräns mellan pronomenet och verbet. Diffen kunde därför
        # bara säga att `je` inte var `j'existe` — den kunde INTE se att
        # `exister` var fel böjning av `existe`, för de två stod aldrig mot
        # varandra. Mätt fall: `Je exister` för `J'existe.` gav ändelsen
        # UNDANHÅLLEN när den skulle ha FALLIT; böjningsfelet försvann bakom
        # elisionen.
        #
        # Renderaren lämnar numera ifrån sig sin ordlista före sandhi
        # (`osammansmält`), och svarets tokens delas vid samma gränser. Då
        # står `existe` mot `exister` och stamuppdelningen kan göra sitt.
        sandhi_missad = False
        if (osammansmält and self.språk in ORDMELLANRUM
                and self._smälter_ihop(osammansmält)):
            f = self._foga_samman(
                [_normalisera(o) for o in osammansmält if _normalisera(o)],
                flerordiga)
            delad = self._dela_vid_sandhi(s, osammansmält)
            # SKREV ANVÄNDAREN ISÄR DET SOM SKA SMÄLTA IHOP? Delningen ovan
            # gör ingenting när svaret redan står isär — och står facit ihop
            # är det i sig ett fel, oberoende av vad orden innehåller.
            #
            # Utan den här flaggan rapporterades bara det ANDRA felet: `je
            # apprender` fick "fel ändelse" och elisionen nämndes inte alls,
            # fast användaren missat två saker.
            sandhi_missad = (delad == s
                             and len(f) > len(self._foga_samman(
                                 self._segmentera(_normalisera(facit),
                                                  flerordiga), flerordiga)))
            s = delad
        # Positionerna i facit som en form slogs upp för.
        opkoder = difflib.SequenceMatcher(None, f, s, autojunk=False).get_opcodes()
        ut: list[Anmärkning] = []

        # OMKASTNINGARNA TAS UT UR DIFFEN INNAN RESTEN BEDÖMS. Ett flyttat ord
        # rubbar uppriktningen för sina grannar: mätt fall, facit
        # "Une nourriture coûte." och svaret "nourriture Une coûtent." — där
        # hamnade det felböjda verbet i en `delete` utan motpart, så `_skyll`
        # såg tomma strängen och drog slutsatsen "fel ord" i stället för "fel
        # ändelse". Plockas de flyttade orden bort från BÅDA sidor blir det
        # som återstår en ren diff igen, och formfelet attribueras rätt.
        if sandhi_missad:
            ut.append(Anmärkning(
                _normalisera(svar), _normalisera(facit),
                "orden ska smälta samman — " + _normalisera(facit),
                None, False, nyckel="sandhi", arg=_normalisera(facit),
                sandhi=True))
        flyttade = self._flyttade(f, s, opkoder)
        if flyttade:
            ut += [Anmärkning(o, o, "rätt ord på fel plats — ordföljden",
                              nyckel="ordföljd",
                              ordföljd=True)
                   for o in sorted(flyttade)]
            f = [o for o in f if o not in flyttade]
            s = [o for o in s if o not in flyttade]
            opkoder = difflib.SequenceMatcher(
                None, f, s, autojunk=False).get_opcodes()

        for tagg, i1, i2, j1, j2 in opkoder:
            if tagg == "equal":
                continue
            for n, pos in enumerate(range(i1, i2)):
                väntat = f[pos]
                skrev = s[j1 + n] if j1 + n < j2 else ""
                träff = self._hitta_uppslag(väntat, uppslag)
                if träff is None:
                    ut.append(Anmärkning(skrev, väntat,
                                         "hör inte till något kort",
                                         nyckel="inget_kort"))
                    continue
                koncept, variant, cell = träff
                kid, förklaring, osäker, nyckel, arg = self._skyll(
                    skrev, väntat, koncept, variant, cell, egenskaper,
                    rektioner)
                ut.append(Anmärkning(skrev, väntat, förklaring, kid, osäker,
                                     nyckel=nyckel, arg=arg))
            # ORD SOM INTE SKA FINNAS DÄR. Loopen ovan går över FACITS
            # positioner, så vid en `insert` är intervallet tomt och ett
            # tillagt ord gav ingen anmärkning alls — hela den feltypen var
            # osynlig för rättningen. Den fäller inget kort (vi vet inte
            # vilket), men användaren ska få se den.
            for m in range(j1 + (i2 - i1), j2):
                ut.append(Anmärkning(s[m], "",
                                     "ord som inte hör till meningen",
                                     nyckel="extra_ord"))
        return ut

    def _delsträngar(self, svar: str,
                     uppslag: list[tuple[str, str | None, str]]) -> list[Anmärkning]:
        """Japanska: varje väntad form söks som delsträng.

        Grövre än en diff — den säger att formen saknas, inte vad som stod
        i stället — men japanskan skrivs utan mellanslag och en ordvis diff
        finns inte att göra.
        """
        ut: list[Anmärkning] = []
        for koncept, variant, cell in uppslag:
            form = self._celler_för(koncept, variant).get(cell)
            if form and form not in svar:
                kort = self._kort_för(koncept, variant, cell)
                kid = kort[0]["id"] if kort else None
                ut.append(Anmärkning("", form, f"formen saknas i svaret ({cell})",
                                     kort_id=kid, osäker=True,
                                     nyckel="saknas", arg=cell))
        return ut

    def _hitta_uppslag(self, ord: str, uppslag: list[tuple[str, str | None, str]]):
        """Vilket formuppslag gav det här ordet i facit?"""
        for koncept, variant, cell in uppslag:
            form = self._celler_för(koncept, variant).get(cell)
            if form and _normalisera(form) == ord:
                return koncept, variant, cell
        return None
