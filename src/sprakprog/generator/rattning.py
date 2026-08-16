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
from dataclasses import dataclass, field

from ..rendering import Uppslag

#: Språk som skriver med mellanslag mellan orden. Japanskan gör inte det.
ORDMELLANRUM = ("sv", "en", "de", "fr", "es", "it")


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

    def __str__(self) -> str:
        säkerhet = "  (osäker)" if self.osäker else ""
        skrev = self.skrev or "—"
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

    # ── uppslag ──────────────────────────────────────────────────────

    def _celler_för(self, koncept: str, variant: str | None) -> dict[str, str]:
        try:
            return {c: f for c, f in self.u._celler(
                self.u.lexem(koncept, variant)).items() if f}
        except Exception:
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

    def _skyll(self, skrev: str, väntat: str, koncept: str, variant: str | None,
               cell: str) -> tuple[int | None, str, bool]:
        """(kort_id, förklaring, osäker) för ETT felskrivet ord.

        Ordningen är den GENERATOR.md föreskriver: låt datan avgöra så långt
        den räcker, och gå till historiken först när den tar slut.
        """
        kort = self._kort_för(koncept, variant, cell)
        stamkort = next((k for k in kort if k["typ"] in ("stam", "form")), None)
        systemkort = next((k for k in kort if k["typ"] == "system"), None)

        celler = self._celler_för(koncept, variant)
        träffar = [c for c, f in celler.items() if _normalisera(f) == skrev]

        if not träffar:
            # Ingen form av ordet alls — då är det ordet som brast, inte
            # böjningen. Ett ord man inte kan hämta fram går inte att böja.
            ordkort = self._ordkort(koncept, variant)
            return (ordkort["id"] if ordkort else None,
                    f"ingen form av {koncept}, alltså fel ord", False)

        # Rätt ord, fel cell. Stamuppdelningen säger vilket kort som brast —
        # men bara när det FINNS en uppdelning. En rest är hela formen i ett
        # kort, och då är den frågan meningslös.
        if stamkort is not None and stamkort["typ"] == "form":
            return (stamkort["id"],
                    f"formen för {self._cellista(träffar)}, inte {cell} — "
                    f"ordet har ingen härledbar stam här", False)
        if stamkort is not None and systemkort is not None:
            stam = _normalisera(stamkort["facit"])
            if stam and skrev.startswith(stam):
                return (systemkort["id"],
                        f"rätt stam {stamkort['facit']!r}, fel ändelse — "
                        f"{self._cellista(träffar)} i stället för {cell}", False)
            return (stamkort["id"],
                    f"fel stam — skrev formen för {self._cellista(träffar)}", False)

        enda = stamkort or systemkort
        if enda is not None:
            return (enda["id"],
                    f"formen för {self._cellista(träffar)}, inte {cell}", False)

        # Datan räcker inte: skyll på det svagaste kortet i ledet.
        # Felattribution självläker — skyller systemet fel klarar det kortet
        # sin extra repetition, och det rätta förblir svagt.
        if kort:
            svagast = min(kort, key=lambda k: k["stabilitet"] or 0)
            return svagast["id"], "kunde inte avgöras ur formen — svagaste kortet", True
        return None, "inget kort hör till ordet", True

    # ── rättning ─────────────────────────────────────────────────────

    def rätta(self, svar: str, facit: str, uppslag: list[tuple[str, str | None, str]],
              kort: list) -> Rättning:
        """Betygsätt varje kort utifrån användarens svar.

        `uppslag` är renderarens beroendekarta som lista: (koncept, variant,
        cell) i den ordning formerna slogs upp. Den kommer från samma
        instrumentering generatorn redan använder.
        """
        utfall = {k["id"]: True for k in kort}
        if _normalisera(svar) == _normalisera(facit):
            return Rättning(True, utfall, [])

        anmärkningar: list[Anmärkning] = []
        if self.språk in ORDMELLANRUM:
            anmärkningar = self._ordvis(svar, facit, uppslag)
        else:
            anmärkningar = self._delsträngar(svar, uppslag)

        for a in anmärkningar:
            if a.kort_id is not None:
                utfall[a.kort_id] = False
        return Rättning(False, utfall, anmärkningar)

    def _ordvis(self, svar: str, facit: str,
                uppslag: list[tuple[str, str | None, str]]) -> list[Anmärkning]:
        """Ordvis diff, och ett uppslag per avvikelse."""
        s = _normalisera(svar).split()
        f = _normalisera(facit).split()
        # Positionerna i facit som en form slogs upp för. Sandhi kan slå ihop
        # två uppslag till ett ord, så kopplingen är ungefärlig — därför
        # matchas formen mot ordet innan slutsatsen dras.
        matcher = difflib.SequenceMatcher(None, f, s, autojunk=False)
        ut: list[Anmärkning] = []
        for tagg, i1, i2, j1, j2 in matcher.get_opcodes():
            if tagg == "equal":
                continue
            for n, pos in enumerate(range(i1, i2)):
                väntat = f[pos]
                skrev = s[j1 + n] if j1 + n < j2 else ""
                träff = self._hitta_uppslag(väntat, uppslag)
                if träff is None:
                    ut.append(Anmärkning(skrev, väntat, "hör inte till något kort"))
                    continue
                koncept, variant, cell = träff
                kid, förklaring, osäker = self._skyll(
                    skrev, väntat, koncept, variant, cell)
                ut.append(Anmärkning(skrev, väntat, förklaring, kid, osäker))
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
                                     kid, osäker=True))
        return ut

    def _hitta_uppslag(self, ord: str, uppslag: list[tuple[str, str | None, str]]):
        """Vilket formuppslag gav det här ordet i facit?"""
        for koncept, variant, cell in uppslag:
            form = self._celler_för(koncept, variant).get(cell)
            if form and _normalisera(form) == ord:
                return koncept, variant, cell
        return None
