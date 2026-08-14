"""Meningsgeneratorn — löser fram en mening ur repetitionskön.

Premissen ur GENERATOR.md: meningar författas inte, de löses fram. Systemet
ser vilka kort som är förfallna och konstruerar en mening som tränar dem,
blandat med ord användaren redan kan.

Sökningen är sampla-och-poängsätt. Att välja verb, mönster, fyllnad och alla
grammatiska parametrar så att budgeten träffas, förfallna kort täcks och
restriktionerna hålls är i allmänhet NP-svårt — men genomströmningen gör det
ointressant: 41 000 kandidater i sekunden mätt, så tusen kandidater kostar
tre hundradelar och den bästa av dem är gott nog. Skillnaden mellan bästa och
näst bästa mening är omätbar för användaren.

Kedjan per mening:

    kön          förfallna kort, svagast först
    samplaren    kandidater byggda RUNT målorden, giltiga från början
    renderaren   texten, och beroendekartan som säger vilka kort den rörde
    poängen      sex termer, budget och koncentration bland dem
    valet        bästa kandidaten, eller den minst dåliga

Sista ledet är viktigt: sökningen misslyckas aldrig. Finns ingen bra mening
tas den minst dåliga, och det förfallna kort som inte gick att bygga kring
skjuts upp till nästa gång — GENERATOR.md, "täckande med reservutgång".
"""

from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass

from ..kort import Schemaläggare, spec_json
from ..rendering import (
    EngelskRenderare, FranskRenderare, ItalienskRenderare, JapanskRenderare,
    Mening, RenderingsFel, SpanskRenderare, SvenskRenderare, TyskRenderare,
    Uppslag, Validator,
)
from .poang import Poäng, Poängsättare
from .rattning import Anmärkning, Rättare, Rättning
from .urval import Ordförråd, Samplare

RENDERARE = {"sv": SvenskRenderare, "en": EngelskRenderare, "de": TyskRenderare,
             "fr": FranskRenderare, "es": SpanskRenderare,
             "it": ItalienskRenderare, "ja": JapanskRenderare}


@dataclass(frozen=True, slots=True)
class Förslag:
    mening: Mening
    #: Meningen på MÅLSPRÅKET — facit.
    text: str
    #: Samma mening på KÄLLSPRÅKET — uppgiften användaren ser. None när
    #: kursen saknar källspråk, alltså när systemet provas utan uppgift.
    uppgift: str | None = None
    kort: list = None
    poäng: Poäng = None
    #: (koncept, variant, cell) i den ordning formerna slogs upp. Rättningen
    #: behöver den för att veta vilket ord i facit som kom varifrån.
    uppslag: list = None


class Generator:
    def __init__(self, språk_db: sqlite3.Connection, kort_db: sqlite3.Connection,
                 språk: str, *, källspråk: str | None = None,
                 nivå: int = 21, cefr: str = "C2",
                 budget: float = 1.5, frö: int | None = None) -> None:
        self.språk = språk
        self.källspråk = källspråk
        self.språk_db = språk_db
        self.kort_db = kort_db
        self.rng = random.Random(frö)
        self.renderare = RENDERARE[språk](språk_db)
        # UPPGIFTEN ÄR SAMMA SPEC PÅ ETT ANNAT SPRÅK. Det är hela skälet till
        # att `Mening` är språkoberoende: frågan och svaret är inte två texter
        # som råkar höra ihop utan en enda specifikation, renderad två gånger.
        # Utan den här renderaren finns ingen uppgift att ställa, bara ett
        # facit att visa.
        self.källrenderare = RENDERARE[källspråk](språk_db) if källspråk else None
        self.validator = Validator(språk_db)
        self.schemaläggare = Schemaläggare(kort_db)
        self.poängsättare = Poängsättare(kort_db, self.schemaläggare, budget)
        self.samplare = Samplare(
            Ordförråd(språk_db, språk, cefr), nivå, self.rng)
        self._karta = self._läs_karta()
        self._kort = {r["id"]: r for r in kort_db.execute(
            "SELECT * FROM Kort WHERE språk = ?", (språk,))}
        # Ordkortet hänger på KONCEPTET och inte på cellen, så det ligger
        # inte i Cellkort. Att glömma det gjorde att varje mening
        # attribuerade noll ordkort — det mest grundläggande av alla.
        self.rättare = Rättare(språk_db, kort_db, språk)
        self._ordkort: dict[tuple, int] = {
            (r["koncept"], r["variant"]): r["id"]
            for r in self._kort.values() if r["typ"] == "ord"}

    def _läs_karta(self) -> dict:
        karta: dict = {}
        for r in self.kort_db.execute(
                """SELECT språk, koncept, variant, cell, kort_id
                   FROM Cellkort WHERE språk = ?""", (self.språk,)):
            karta.setdefault(
                (r["koncept"], r["variant"], r["cell"]), []).append(r["kort_id"])
        return karta

    # ── rendering med beroendekarta ──────────────────────────────────

    def _rendera(self, m: Mening) -> tuple[str, list, list] | None:
        """Texten och de kort meningen rörde, eller None om den inte går.

        Instrumenteringen är samma väg som nåbarhetsmätningen använder, och
        det är hela skälet att renderarna måste hämta former genom
        `Uppslag.form` — en form som hämtas förbi den går inte att knyta
        till ett kort.
        """
        rörda: list = []
        original = Uppslag.form

        def logga(själv, lexem, cell):
            rörda.append((lexem["nyckel"], lexem["variant"], cell))
            return original(själv, lexem, cell)

        Uppslag.form = logga
        try:
            text = self.renderare.rendera(m)
        except (RenderingsFel, KeyError, ValueError):
            return None
        finally:
            Uppslag.form = original

        idn: set[int] = set()
        for nyckel in rörda:
            idn.update(self._karta.get(nyckel, ()))
        for koncept, variant, _ in rörda:
            kid = self._ordkort.get((koncept, variant))
            if kid is not None:
                idn.add(kid)
        kort = [self._kort[i] for i in idn if i in self._kort]
        return text, kort, rörda

    # ── generering ───────────────────────────────────────────────────

    def föreslå(self, *, kandidater: int = 1000, kölängd: int = 30,
                nu=None) -> Förslag | None:
        """Bästa meningen av `kandidater` försök."""
        kö = self.schemaläggare.förfallna(self.språk, kölängd, nu)
        if not kö:
            kö = self.schemaläggare.osedda(self.språk, kölängd)
        förfallna = {k["id"] for k in kö}
        mål = [k["koncept"] for k in kö if k["koncept"]] or [None]

        bäst: Förslag | None = None
        for _ in range(kandidater):
            m = self.samplare.kandidat(kring=self.rng.choice(mål))
            if m is None or self.validator.validera(m):
                continue
            resultat = self._rendera(m)
            if resultat is None:
                continue
            text, kort, uppslag = resultat
            p = self.poängsättare.sätt(kort, förfallna, nu)
            if bäst is not None and p.total <= bäst.poäng.total:
                continue
            # Källspråket renderas FÖRST NU och inte för varje kandidat.
            # Det är samma beslut som allt annat i sökningen: gör det dyra
            # bara för den kandidat som faktiskt kan vinna. En mening som
            # inte går att STÄLLA är oanvändbar hur bra den än är, så den
            # förkastas, men det händer sällan nog att det inte lönar sig
            # att kontrollera i förväg.
            uppgift = None
            if self.källrenderare is not None:
                uppgift = self._rendera_källa(m)
                if uppgift is None:
                    continue
            bäst = Förslag(m, text, uppgift, kort, p, uppslag)
        if bäst is not None:
            self.poängsättare.minns(
                {k["koncept"] for k in bäst.kort if k["koncept"]})
        return bäst

    def _rendera_källa(self, m: Mening) -> str | None:
        """Meningen på källspråket, eller None om det språket inte når den.

        Ingen instrumentering: uppgiftens ord är inte användarens kort. Det
        är målspråket som övas, källspråket bara ställer frågan.
        """
        try:
            return self.källrenderare.rendera(m)
        except (RenderingsFel, KeyError, ValueError):
            return None

    def rätta(self, förslag: Förslag, svar: str) -> Rättning:
        """Användarens text → ett betyg per kort."""
        return self.rättare.rätta(svar, förslag.text, förslag.uppslag or [],
                                  förslag.kort)

    def svara(self, förslag: Förslag, svar: str, *, källspråk: str | None = None,
              nu=None) -> Rättning:
        """Rätta OCH registrera — hela slingan i ett anrop."""
        rättning = self.rätta(förslag, svar)
        self.registrera(förslag, rättning.utfall,
                        källspråk=källspråk or self.källspråk, nu=nu)
        return rättning

    def registrera(self, förslag: Förslag, utfall: dict[int, bool],
                   *, källspråk: str | None = None, nu=None) -> int:
        return self.schemaläggare.registrera_mening(
            self.språk, spec_json(förslag.mening), förslag.text, utfall,
            källspråk=källspråk or self.källspråk,
            budget=self.poängsättare.budget, nu=nu)


__all__ = ["Anmärkning", "Förslag", "Generator", "Ordförråd", "Poäng",
           "Poängsättare", "Rättare", "Rättning", "Samplare"]
