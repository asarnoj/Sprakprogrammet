"""Gemensam bas för de romanska renderarna.

Franskan byggdes först och ensam. När spanskan och italienskan skulle till
visade det sig att de delar nästan allt: substantiv med sg/pl, adjektiv och
particip som kongruerar i genus och numerus, possessiv som följer det ägda,
fyra pronomenserier, och prepositionsrealiserat indirekt objekt.

Det som faktiskt skiljer ligger som klassattribut här nedanför. Tre saker
är värda att peka ut, för de är inte kosmetiska:

  SAMMANSATT_DÅTID   Franskan och italienskan bygger perfektiv dåtid av
                     hjälpverb plus particip (a donné, ha dato). Spanskan
                     använder ett syntetiskt pretteritum (dio). Samma
                     specifikation, två helt olika verbfraser.

  hjälpverb          fr avoir/être och it avere/essere väljs per verb ur
                     Lexem.hjälpverb. Spanskan har bara haber och läser
                     aldrig kolumnen.

  artikelcell        Italienskan har fonologiskt betingade allomorfer
                     (il/lo, i/gli) som ligger som egna celler i Former.
                     Franskan och spanskan har inga.

Sandhi — elision och sammandragning — ligger kvar i renderaren och inte i
Former, eftersom den beror på NÄSTA ord och därför inte kan lagras som en
cell. Italienskans lo/gli är motsatt fall: allomorfen bestäms av det
följande ordet men är lexikaliserad nog att vara en riktig form.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from .spec import (
    Aspekt, Attribut, Bestämdhet, Bisats, Diates, Grad, Mening, Nominalfras,
    NAKEN, Numerus, Referentgenus, attribut_med_grad, bestämd_fras,
    FRÅGESLOTTAR, RenderingsFel, Satsmodus, Tidsreferens, slutar, tilltal,
)
from .uppslag import Uppslag

MASKULIN, FEMININ = 1, 2

# _legend.yaml tempus: Vol = konjunktiv. Samma bit som subj-cellerna
# i Former bär, och den MönsterKrav.tempus använder.
KONJUNKTIVBIT = 1024

ENKELT_TEMPUS = {
    (Tidsreferens.NUTID, Aspekt.PERFEKTIV): "pres",
    (Tidsreferens.NUTID, Aspekt.IMPERFEKTIV): "pres",
    (Tidsreferens.FÖRFLUTEN, Aspekt.IMPERFEKTIV): "imperf",
    (Tidsreferens.FRAMTID, Aspekt.PERFEKTIV): "fut",
    (Tidsreferens.FRAMTID, Aspekt.IMPERFEKTIV): "fut",
}


def _kön(genus: int) -> str:
    return "msc" if genus == MASKULIN else "fem"


def _tal(numerus: Numerus) -> str:
    return "pl" if numerus is Numerus.PL else "sg"


class RomanskRenderare:
    SPRÅK: str
    SUBJEKTSCELL: str
    TONISK: str
    SAMMANSATT_DÅTID: bool
    # Spanskan bildar ALLTID perfekt med haber. Franskan och italienskan
    # väljer per verb ur Lexem.hjälpverb, som därför bara är ifylld för dem.
    HJÄLPVERB_FAST: str | None = None
    VOKAL = set("aeiouyàâäéèêëîïôöûüùáíóúñòì")
    SAMMANDRAG: dict[tuple[str, str], str] = {}

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.u = Uppslag(conn, self.SPRÅK)
        self.conn = conn

    # ── språkspecifika krokar ────────────────────────────────────────

    def possessivcell(self, genus: int, numerus: Numerus) -> str:
        raise NotImplementedError

    def possessivartikel(self, nf: Nominalfras) -> bool:
        """Ska bestämd artikel stå före possessiven? Bara italienskan."""
        return False

    def obestämd_under_negation(self, roll: str, negerad: bool) -> str | None:
        """Ersätter negationen den obestämda artikeln? Sträng, annars None.

        Franskan gör det (`ne trouve pas de chat`); spanskan och italienskan
        gör det inte. Se `FranskRenderare`.
        """
        return None

    def artikelcell(self, genus: int, numerus: Numerus, huvudord: str,
                    bestämd: bool) -> str:
        """Cell i artikelparadigmet. `huvudord` behövs bara för italienskan."""
        if numerus is Numerus.PL:
            return "m_pl" if genus == MASKULIN else "f_pl"
        return "m_sg" if genus == MASKULIN else "f_sg"

    # ── rektion ──────────────────────────────────────────────────────

    def modusrektion(self, styrande: str, slot: str) -> int | None:
        """Vilket modus ordet styr på slotten. Samma uppslag som kasus.

        Ligger på det STYRANDE ordets språkspecifika mönster — subjunktionen
        eller verbet — och läses precis som tyskans kasusrektion. 1024 är
        konjunktiv (_legend.yaml Vol); NULL är indikativ.
        """
        rad = self.conn.execute(
            """SELECT mk.tempus FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               WHERE k.nyckel = ? AND m.språk = ? AND mk.slot = ?
                 AND mk.tempus IS NOT NULL""",
            (styrande, self.SPRÅK, slot)).fetchone()
        return rad["tempus"] if rad else None

    def preposition_för(self, verb: str, slot: str) -> str | None:
        rad = self.conn.execute(
            """SELECT p.nyckel FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               JOIN Koncept p ON p.id = mk.preposition_koncept_id
               WHERE k.nyckel = ? AND m.språk = ? AND mk.slot = ?""",
            (verb, self.SPRÅK, slot),
        ).fetchone()
        # SAKNAS RADEN LOGGAS INGENTING. Att verbet inte kräver en
        # preposition är inte kunskap ett kort bär — det finns inget
        # rektionskort för frånvaron, och en logg utan kort vore brus i
        # nåbarhetsmätningen. Se `uppslag.rektion`.
        if rad is None:
            return None
        return self.u.rektion(verb, slot, "preposition", rad["nyckel"])

    # ── nominalfras ──────────────────────────────────────────────────

    def nominalfras(self, nf: Nominalfras, roll: str = "objekt", *,
                    negerad: bool = False) -> list[str]:
        huvud = self.u.lexem(
            nf.koncept, nf.referent.value if nf.referent else None)

        if huvud["ordklass"] == "Pronomen":
            if nf.attribut or nf.possessiv is not None:
                raise RenderingsFel(
                    f"{self.SPRÅK}/{huvud['lemma']}: ett pronomen kan inte ta "
                    f"artikel, attribut eller possessiv")
            if roll == "subjekt":
                return [self.u.form(huvud, self.SUBJEKTSCELL)]
            if roll == "efter_preposition":
                return [self.u.form(huvud, self.TONISK)]
            raise RenderingsFel(
                f"{self.SPRÅK}/{huvud['lemma']}: objektspronomen är klitika och "
                f"står FÖRE verbet, inte där ett substantiv står. "
                f"Klitikaplacering är inte byggd — se RENDERARE_KRAV §3.9")

        self.u.kontrollera_naken(nf)

        # LOGGAS I BÅDA NUMERUS, till skillnad från tyskan och svenskan.
        # Spanskan och italienskan skiljer genus även i plural — "los libros"
        # mot "las mesas", "i libri" mot "le tavole" — så en plural prövar
        # genuset lika mycket som en singular.
        #
        # Franskans bestämda och obestämda plural är däremot genusneutrala
        # (les, des), och där överkrediteras genuskortet av en pluralfras
        # UTAN attributivt adjektiv. Med adjektiv är franskan tillbaka i
        # samma läge ("les grandes maisons"), så felet gäller en delmängd av
        # en delmängd. Det står här hellre än att en tredje regel läggs till
        # för ett språk som ännu inte har någon kurs.
        genus = self.u.egenskap(huvud, "genus")
        if genus is None:
            raise RenderingsFel(
                f"{self.SPRÅK}/{huvud['lemma']}: genus saknas — artikel, "
                f"adjektiv och possessiv kongruerar alla med det")

        huvudform = self.u.form(huvud, _tal(nf.numerus))
        före: list[str] = []
        if nf.frågedeterminant is not None:
            # "quel livre", "qué libro", "quale libro" — determinanten tar
            # artikelns plats, och frasen står utan artikel.
            före.append(self.u.form_för(
                nf.frågedeterminant,
                self.frågedeterminantcell(genus, nf.numerus)))
        elif nf.possessiv is not None:
            # Italienskan sätter BESTÄMD ARTIKEL före possessiven: "il mio
            # libro". Spanskan och franskan gör inte det ("su libro", "son
            # livre"), så villkoret är språkets och inte konstruktionens.
            possessivform = self.u.form_för(
                nf.possessiv, self.possessivcell(genus, nf.numerus))
            if self.possessivartikel(nf):
                # Allomorfen väljs på NÄSTA ord, och det är possessiven som
                # följer artikeln — inte huvudordet. "il suo amico", inte
                # "lo suo amico": det är suo som avgör, inte amico.
                före.append(self.u.form_för("artikel_bestamd", self.artikelcell(
                    genus, nf.numerus, possessivform, bestämd=True)))
            före.append(possessivform)
        elif nf.bestämdhet in NAKEN:
            # De romanska språken saknar naken fras nästan helt, och de
            # skiljer dessutom SORT från MÄNGD där de fyra andra inte gör
            # det: "les livres sont chers" men "je bois de l'eau".
            #
            # Generisk tar bestämd artikel. Partitiv tar de/di plus samma
            # artikel — och sammandragningen du/della sköts av sandhi, exakt
            # som för genitivet, så konstruktionen kostade ingen ny data.
            if nf.bestämdhet is Bestämdhet.PARTITIV and self.PARTITIV_MED_PREPOSITION:
                före.append(self.u.form_för("prep_av", "inv"))
            elif nf.bestämdhet is Bestämdhet.PARTITIV:
                # Spanskan står naken i mängdbetydelse: "bebo agua".
                pass
            if not (nf.bestämdhet is Bestämdhet.PARTITIV
                    and not self.PARTITIV_MED_PREPOSITION):
                före.append(self.u.form_för("artikel_bestamd", self.artikelcell(
                    genus, nf.numerus, huvudform, bestämd=True)))
        else:
            bestämd = nf.bestämdhet is Bestämdhet.BESTÄMD
            ersatt = (None if bestämd else
                      self.obestämd_under_negation(roll, negerad))
            if ersatt is not None:
                före.append(ersatt)
            else:
                före.append(self.u.form_för(
                    "artikel_bestamd" if bestämd else "artikel_obestamd",
                    self.artikelcell(genus, nf.numerus, huvudform, bestämd)))

        # Adjektivets plats är lexikal, inte regelstyrd: de flesta romanska
        # adjektiv står efter substantivet, men en liten grupp står före.
        efter: list[str] = []
        for attribut in nf.attribut:
            a = attribut_med_grad(attribut)
            if a.grad is Grad.SUPERLATIV and not bestämd_fras(nf):
                # "un libro más interesante" ÄR komparativen — de romanska
                # språken skiljer graderna med artikeln och kan inte märka
                # en obestämd superlativ alls. Att rendera den vore att
                # tyst ge tillbaka komparativen.
                raise RenderingsFel(
                    f"{self.SPRÅK}/{a.koncept}: attributiv superlativ kräver "
                    f"bestämd fras — graden markeras med artikeln")
            adjektiv = self.u.lexem(a.koncept)
            delar = self.attributgrad(a, adjektiv, genus, nf.numerus)
            # Komparation kan FLYTTA adjektivet. es/it ställer det komparerade
            # efter huvudordet oavsett var positiven står: "un libro mayor",
            # aldrig "un mayor libro". Franskan behåller placeringen — "le
            # plus grand livre" — och markerar i stället superlativen med
            # dubblerad artikel när adjektivet står efter: "le livre le plus
            # grand". Utan den vore komparativ och superlativ omöjliga att
            # skilja åt, eftersom plus/más/più är samma ord i båda.
            efterställd = (a.grad is not Grad.POSITIV
                           and self.KOMPARERAD_EFTERSTÄLLD) or not adjektiv["prenominal"]
            if (efterställd and a.grad is Grad.SUPERLATIV
                    and self.DUBBEL_SUPERLATIVARTIKEL):
                delar = [self.u.form_för(
                    "artikel_bestamd",
                    self.artikelcell(genus, nf.numerus, delar[0], bestämd=True)),
                    *delar]
            (efter if efterställd else före).extend(delar)

        # "le livre de la fille" — romanska språk uttrycker genitiv med
        # preposition, inte med kasus, och attributet står efter huvudordet.
        # Sammandragningen de+le→du och di+il→del sköts av sandhi().
        if nf.ägare is not None:
            efter.append(self.u.form_för("prep_av", "inv"))
            efter.extend(self.nominalfras(nf.ägare))

        return [*före, huvudform, *efter]

    # ── verb ─────────────────────────────────────────────────────────

    #: Artigt tilltal kongruerar INTE som det betyder. Konceptet
    #: `pronomen_2sg_formal` är andra person singular — det tilltalar en
    #: enda person — men morfologiskt följer det något annat, och vad skiljer
    #: sig mellan språken. Skillnaden är lexikal, syns bara när pronomenet
    #: står som subjekt i en påståendesats, och hittades av generatorn:
    #: "Sie fliegst", "Usted vuelas", "Lei voli", "Vous voles".
    ARTIG_KONGRUENS = (3, "sg")

    def _subjektsform(self, nf: Nominalfras) -> tuple[int, str, int]:
        if nf.koncept == "pronomen_2sg_formal":
            person, numerus = self.ARTIG_KONGRUENS
            return person, numerus, MASKULIN
        rad = self.conn.execute(
            "SELECT person, numerus FROM Koncept WHERE nyckel = ?",
            (nf.koncept,)).fetchone()
        person = rad["person"] if rad and rad["person"] else 3
        numerus = "pl" if nf.numerus is Numerus.PL else "sg"
        if rad and rad["numerus"] == 2:
            numerus = "pl"
        if nf.referent is not None:
            genus = FEMININ if nf.referent is Referentgenus.FEMININ else MASKULIN
        else:
            genus = self.u.egenskap_för(nf.koncept, "genus") or MASKULIN
        return person, numerus, genus

    def verbdelar(self, m: Mening, föregående_objekt=None) -> list[str]:
        if m.modus is Satsmodus.IMPERATIV:
            tal = tilltal(m, self.SPRÅK, tuple(self.IMPERATIVCELL))
            celler = self.NEKAD_IMPERATIVCELL if m.negerad else {}
            return [self.u.form_för(
                m.verb, celler.get(tal) or self.IMPERATIVCELL[tal])]
        if m.diates is not Diates.AKTIV:
            # "le livre est lu", "el libro es leído" — vara plus particip
            # som kongruerar med subjektet, precis som être-participen i
            # sammansatt dåtid. Spanskan använder ser, inte estar.
            #
            # KOPULAN bär hela tempus- och aspektapparaten och böjs som
            # vilket verb som helst. Den går därför genom den aktiva grenen,
            # och därmed faller de sammansatta passiverna ut gratis: "a été
            # lu", "è stato letto", "ha sido leído". Att stato kongruerar i
            # italienskan men été inte gör det i franskan följer av
            # hjälpverbsvalet, som redan står i datan — essere tar essere,
            # être tar avoir.
            _, numerus, genus = self._subjektsform(m.subjekt)
            kopula = replace(m, verb="verb_vara", diates=Diates.AKTIV,
                             objekt=None, predikativ=None)
            return [*self.verbdelar(kopula),
                    self.u.form_för(m.verb, f"pp_{_kön(genus)}_{numerus}")]
        """`föregående_objekt` är (genus, numerus) för ett objektsklitikum.

        Med 'ha'-hjälpverbet kongruerar participet med det direkta objektet
        BARA när objektet står före verbet — vilket det gör just när det är
        ett klitikum: "la fille les lui a donnés". Står objektet efter sker
        ingen kongruens: "la fille a donné les livres".
        """
        person, numerus, subjektsgenus = self._subjektsform(m.subjekt)
        # En efterfrågad SUBJEKTSSLOT kongruerar med frågeordet, inte med
        # svaret. "Wer ändert uns?" — wer är alltid tredje person singular,
        # hur många svaret än råkar vara. Utan det här blev det "Wer ändern
        # uns?", och felet hittades av generatorn.
        if m.fråga_om == "subjekt" and m.subjekt.frågedeterminant is None:
            person, numerus = 3, "sg"
        variant = self.kopulavariant(m)

        # Perfekt är alltid sammansatt. Perfektiv dåtid är det bara i
        # franskan och italienskan — spanskan har ett syntetiskt preteritum
        # där, vilket är hela skillnaden mellan "ha leído" och "leyó".
        sammansatt = m.aspekt is Aspekt.PERFEKT or (
            self.SAMMANSATT_DÅTID and m.tid is Tidsreferens.FÖRFLUTEN
            and m.aspekt is Aspekt.PERFEKTIV)
        if sammansatt:
            # Varianten måste följa med: es verb_vara är två lexem (ser och
            # estar) och uppslaget vägrar gissa. Utan den gick den enkla
            # grenen rätt medan den sammansatta kastade fel på samma verb.
            verb = self.u.lexem(m.verb, variant)
            hjälp = self.HJÄLPVERB_FAST or verb["hjälpverb"]
            if hjälp == "båda":
                # 'båda' betyder att valet inte kan avgöras på lexemet utan
                # på användningen: transitivt tar avere ("ha corso i 100 m"),
                # intransitivt essere ("è corso via"). Meningen vet vilket,
                # eftersom den säger om det finns ett direkt objekt — och det
                # är precis därför kolumnen fick värdet 'båda' i stället för
                # att gissas när den fylldes.
                hjälp = "ha" if m.objekt is not None else "vara"
            if hjälp not in ("ha", "vara"):
                raise RenderingsFel(
                    f"{self.SPRÅK}/{verb['lemma']}: hjälpverb={hjälp!r} — "
                    f"sammansatt dåtid kan inte byggas utan att veta vilket")
            # Particip med 'vara' kongruerar med subjektet (elle est venue,
            # è andata); med 'ha' gör det inte det när objektet står efter.
            if hjälp == "vara":
                cell = f"pp_{_kön(subjektsgenus)}_{numerus}"
            elif föregående_objekt is not None:
                objgenus, objnumerus = föregående_objekt
                cell = f"pp_{_kön(objgenus)}_{_tal(objnumerus)}"
            else:
                cell = "pp_msc_sg"
            # HJÄLPVERBET BÄR TEMPUS, participet är oföränderligt. Det är
            # hela poängen med en sammansatt form, och tre fall följer:
            #
            #   pluskvamperfekt   imperfekt   "elle avait lu"
            #   futurum exaktum   futurum     "elle aura lu"
            #   perfekt           presens     "elle a lu"
            #
            # FUTURUM SAKNADES och föll igenom till presens, så `perfekt +
            # framtid` gav ett vanligt perfekt: `Elle a acheté un chat` för
            # `elle aura acheté un chat`. Modellgranskningen 2026-08-29
            # flaggade konstruktionen i ALLA SJU språken — varje renderare
            # tappade framtiden på samma sätt, vilket är signaturen för ett
            # hål i den delade formen och inte sju buggar. Här rättas de tre
            # romanska: `aura acheté`, `habrá comprado`, `avrà comprato`.
            #
            # I konjunktiv är det likaså HJÄLPVERBET som byter modus:
            # "qu'il ait lu", "que haya leído", "che abbia letto".
            if m.modus is Satsmodus.KONJUNKTIV:
                hjälpstam = self.konjunktivstam(m)
            elif m.aspekt is Aspekt.PERFEKT and m.tid is Tidsreferens.FÖRFLUTEN:
                hjälpstam = "imperf"
            elif m.aspekt is Aspekt.PERFEKT and m.tid is Tidsreferens.FRAMTID:
                hjälpstam = "fut"
            else:
                hjälpstam = "pres"
            return [self.u.form_för("verb_ha" if hjälp == "ha" else "verb_vara",
                                    f"{hjälpstam}_{person}{numerus}",
                                    "hjälpverb" if hjälp == "ha" else None),
                    self.u.form(verb, cell)]

        if m.modus is Satsmodus.KONJUNKTIV:
            stam = self.konjunktivstam(m)
        elif m.tid is Tidsreferens.FÖRFLUTEN and m.aspekt is Aspekt.PERFEKTIV:
            stam = "pret"
        else:
            stam = ENKELT_TEMPUS.get((m.tid, m.aspekt))
        if stam is None:
            raise RenderingsFel(
                f"{self.SPRÅK}: {m.tid}/{m.aspekt} saknar mappning till cell")
        return [self.u.form_för(m.verb, f"{stam}_{person}{numerus}", variant)]

    # ── sandhi ───────────────────────────────────────────────────────

    def sandhi(self, ord: list[str]) -> list[str]:
        """Elision och sammandragning mellan intilliggande ord.

        ORDNINGEN MELLAN DE TVÅ ÄR SPRÅKENS EGEN. Italienskan drar ihop
        först och eliderar RESULTATET — `di` + `la` + `acqua` blir `della`
        och sedan `dell'acqua`. Franskan gör tvärtom: eliderar artikeln
        sker ingen sammandragning alls, så `à` + `le` + `enfant` blir
        `à l'enfant` och inte `au enfant`. Därför frågar
        slingan `sammandrar` innan den drar ihop, och den behöver NÄSTA ord
        för att kunna svara.
        """
        ut: list[str] = []
        for i, o in enumerate(ord):
            if ut:
                ersättning = self.SAMMANDRAG.get((ut[-1], o))
                nästa = ord[i + 1] if i + 1 < len(ord) else ""
                if ersättning is not None and self.sammandrar(ut[-1], o, nästa):
                    ut[-1] = ersättning
                    continue
                if self.eliderar(ut[-1], o):
                    # Sista vokalen faller: le → l', ne → n', que → qu'.
                    ut[-1] = ut[-1][:-1] + "'" + o
                    continue
            ut.append(o)
        return ut

    def eliderar(self, första: str, andra: str) -> bool:
        return False

    def sammandrar(self, första: str, andra: str, nästa: str) -> bool:
        """Ska sammandragningen ske, givet vad som följer? Se `sandhi`."""
        return True

    # ── klitika ──────────────────────────────────────────────────────

    DUBBLERAR = False

    def _pronomen(self, nf: Nominalfras | None):
        """Lexemet om frasen är ett rent pronomen, annars None."""
        if nf is None:
            return None
        lx = self.u.lexem(nf.koncept, nf.referent.value if nf.referent else None)
        return lx if lx["ordklass"] == "Pronomen" else None

    def _klitika(self, nf: Nominalfras | None, cell: str):
        """(form, person) för ett objektspronomen, annars None."""
        lx = self._pronomen(nf)
        if lx is None:
            return None
        rad = self.conn.execute(
            "SELECT person FROM Koncept WHERE nyckel = ?", (nf.koncept,)).fetchone()
        return self.u.form(lx, cell), (rad["person"] if rad else 3) or 3

    def _objektskongruens(self, nf: Nominalfras | None):
        """(genus, numerus) för ett objektsklitikum, för participkongruens."""
        if nf is None:
            return None
        rad = self.conn.execute(
            "SELECT numerus FROM Koncept WHERE nyckel = ?", (nf.koncept,)).fetchone()
        numerus = (Numerus.PL if (rad and rad["numerus"] == 2)
                   or nf.numerus is Numerus.PL else Numerus.SG)
        if nf.referent is not None:
            genus = FEMININ if nf.referent is Referentgenus.FEMININ else MASKULIN
        else:
            genus = self.u.egenskap_för(nf.koncept, "genus") or MASKULIN
        return genus, numerus

    # Reflexivpronomenets konceptnyckel per person och numerus.
    #
    # Bara TREDJE person har ett eget reflexivt pronomen i de tre språken.
    # Första och andra lånar det vanliga objektsklitikat — "je me lave" är
    # samma `me` som i "il me voit" — och därför står bara 1 och 2 här;
    # tredje person faller igenom till `pronomen_reflexiv`.
    REFLEXIVKLITIKA = {(1, "sg"): "pronomen_1sg", (2, "sg"): "pronomen_2sg",
                       (1, "pl"): "pronomen_1pl", (2, "pl"): "pronomen_2pl"}

    def reflexivt(self, lemma: str) -> bool:
        """Bär lemmat ett reflexivpronomen?

        FRÅGAN STÄLLS TILL LEMMAT därför att det är där pronomenet står:
        ordboken skriver `se réveiller`, `despertarse`, `svegliarsi`. De
        BÖJDA formerna är nakna — `réveille`, `despierto`, `sveglio` — så
        den som renderar måste sätta tillbaka pronomenet. Gjorde den inte
        det blev facit `Je réveille` för "jag vaknar", och användaren fick
        fel på ett rätt svar.
        """
        raise NotImplementedError

    def reflexivklitikum(self, m: Mening) -> str | None:
        """Reflexivpronomenet i SUBJEKTETS person, None om verbet inte är det.

        Pronomenet kongruerar med subjektet och inte med verbet: je **me**
        lave, tu **te** laves, il **se** lave. Det är därför det inte kan
        ligga i paradigmet — samma verbform tar olika pronomen.
        """
        if not self.reflexivt(self.u.lexem(m.verb, self.kopulavariant(m))["lemma"]):
            return None
        return self._reflexivform(m.subjekt)

    def _reflexivform(self, subjekt: Nominalfras) -> str:
        """Klitikat som kongruerar med subjektet.

        VARIANTEN MÅSTE FÖLJA MED. Spanskans `pronomen_2pl` är två lemman
        med olika klitika — vosotros ger `os`, ustedes ger `se` — så ett
        uppslag utan variant pekar inte ut ett enda och kastar. Samma väg
        som `_pronomen` tar för objektsklitika.
        """
        person, numerus, _ = self._subjektsform(subjekt)
        koncept = self.REFLEXIVKLITIKA.get((person, numerus), "pronomen_reflexiv")
        variant = (subjekt.referent.value if subjekt.referent is not None
                   and koncept == subjekt.koncept else None)
        return self.u.form(self.u.lexem(koncept, variant), "cod")

    # Fäster ett reflexivt INFINITIVKOMPLEMENT sitt pronomen på infinitiven?
    # Spanskan och italienskan gör det ("quiero despertarme", "voglio
    # svegliarmi"), franskan ställer det som eget ord före ("je veux me
    # réveiller"). Det är samma skillnad som vid jakande imperativ.
    REFLEXIV_INFINITIV_ENKLITISK: bool = True

    def infinitivstam(self, inf: str) -> str:
        """Infinitiven utan klitikum, redo att få ett nytt påfäst."""
        raise NotImplementedError

    def infinitivkomplement(self, m: Mening) -> list[str]:
        """Infinitivkomplementet, med reflexivpronomen när verbet kräver det.

        Pronomenet kongruerar med SATSENS subjekt och inte med infinitiven:
        "je veux me réveiller", aldrig "je veux se réveiller". Lemmat bär
        alltid pronomenet, men infinitivCELLEN gör det bara i spanskan — och
        i italienskan bara ibland. Därför läses reflexiviteten ur lemmat och
        formen byggs, i stället för att cellen litas på.
        """
        inf = self.u.form_för(m.komplement, "inf")
        if not self.reflexivt(self.u.lexem(m.komplement, None)["lemma"]):
            return [inf]
        klitikum = self._reflexivform(m.subjekt)
        if not self.REFLEXIV_INFINITIV_ENKLITISK:
            return [klitikum, inf]
        return [self.infinitivstam(inf) + klitikum]

    # Tilltal → imperativcell. De tre språken skiljer sig på artigheten:
    # franskan lånar 2pl-formen (vouvoiement), spanskan och italienskan har
    # en egen tredjepersonsform (usted, Lei).
    IMPERATIVCELL: dict[str, str] = {}
    # Nekad imperativ är INTE alltid samma form som den jakande. Spanskan
    # byter till konjunktiv i hela paradigmet ("¡no leas!"), italienskan
    # bara i 2sg, och där till infinitiv ("non leggere!"). Tom = oförändrad.
    NEKAD_IMPERATIVCELL: dict[str, str] = {}
    # Bildas partitiven med de/di + artikel? fr och it ja ("de l'eau",
    # "dell'acqua"), spanskan nej — den står naken ("bebo agua").
    PARTITIV_MED_PREPOSITION: bool = True

    # Ställs ett komparerat adjektiv alltid efter huvudordet? es/it ja,
    # franskan nej — där behåller adjektivet sin lexikala placering.
    KOMPARERAD_EFTERSTÄLLD: bool = True
    # Upprepas den bestämda artikeln före superlativen? Bara franskan:
    # "le livre le plus grand".
    DUBBEL_SUPERLATIVARTIKEL: bool = False

    # Har språket en levande imperfektkonjunktiv? Franskans är litterär,
    # som passé simple, och paradigmet saknar cellerna.
    HAR_IMPERFEKTKONJUNKTIV: bool = True

    # Franskans ne har ingen motsvarighet i es/it, som klarar sig med en
    # enda preverbal partikel.
    NEKANDE_FÖRLED: str | None = None
    # Franskan inleder ja/nej-frågor med est-ce que. Spanskan och
    # italienskan behåller ordföljden och markerar bara med skiljetecken.
    FRÅGEINLEDNING: str | None = None
    FRÅGETECKEN_FÖRE: str = ""
    UTROPSTECKEN_FÖRE: str = ""

    def negation(self, m: Mening) -> tuple[list[str], list[str]]:
        """(före verbet, efter verbet). Romanska språk skiljer sig här.

        es och it sätter en partikel före verbet: "no lee", "non legge".
        Franskan klämmer in verbet mellan två: "ne lit pas". Förledet ne
        finns inte som lexem i databasen — det är en ren grammatisk klitika
        utan egen betydelse, hårdkodad här på samma sätt som japanskans
        partiklar. Efterledet pas ligger däremot i neg_inte.
        """
        if not m.negerad:
            return [], []
        if self.NEKANDE_FÖRLED is not None:
            return [self.NEKANDE_FÖRLED], [self.u.form_för("neg_inte", "inv")]
        return [self.u.form_för("neg_inte", "inv")], []

    def ordna_klitika(self, cod, coi) -> list[str]:
        """Inbördes ordning mellan klitika framför verbet.

        Franskans regel: första och andra person står först (me le donne),
        tredje person tvärtom (le lui donne). Det är inte godtyckligt utan
        två skilda serier som råkar dela plats.
        """
        if cod and coi:
            return ([coi[0], cod[0]] if coi[1] in (1, 2)
                    else [cod[0], coi[0]])
        return [x[0] for x in (cod, coi) if x]

    # ── sats ─────────────────────────────────────────────────────────

    def kopulavariant(self, m: Mening) -> str | None:
        """Vilken kopula språket ska använda. Bara spanskan har ett val."""
        return None

    def predikativ(self, m: Mening) -> list[str]:
        if isinstance(m.predikativ, str) and m.grad is not Grad.POSITIV:
            # Franskan är alltid perifrastisk. Spanskan och italienskan har
            # suppletiva former för ett fåtal (mayor, maggiore) och bygger
            # resten med más/più — datan avgör vilket.
            _, numerus, genus = self._subjektsform(m.subjekt)
            tal = Numerus.PL if numerus == "pl" else Numerus.SG
            stam = "komp" if m.grad is Grad.KOMPARATIV else "superl"
            adjektiv = self.u.lexem(m.predikativ)
            celler = self.u._celler(adjektiv)
            cell = next((c for c in (f"{stam}_{_kön(genus)}_{_tal(tal)}",
                                     f"{stam}_{_tal(tal)}") if celler.get(c)), None)
            if cell is not None:
                ut = [self.u.form(adjektiv, cell)]
            else:
                ut = [self.u.form_för("komp_mer" if m.grad is Grad.KOMPARATIV
                                      else "komp_mest", "inv"),
                      self.u.form_för(m.predikativ,
                                      f"pos_{_kön(genus)}_{_tal(tal)}")]
            if m.grad is Grad.SUPERLATIV:
                # Romansk superlativ kräver bestämd artikel: "le plus
                # grand", "el más grande". Utan den är frasen komparativ.
                # Artikeln kongruerar med subjektet.
                artikel = self.artikelcell(genus, tal, ut[0], bestämd=True)
                ut.insert(0, self.u.form_för("artikel_bestamd", artikel))
            if m.jämförelse is not None:
                ut.append(self.u.form_för("komp_än", "inv"))
                ut += self.nominalfras(m.jämförelse)
            return ut
        if isinstance(m.predikativ, str):
            # Romanska predikativ kongruerar med subjektet i genus och
            # numerus: "elle est heureuse", "ils sont heureux".
            _, numerus, genus = self._subjektsform(m.subjekt)
            tal = Numerus.PL if numerus == "pl" else Numerus.SG
            return [self.u.form_för(
                m.predikativ, f"pos_{_kön(genus)}_{_tal(tal)}")]
        # Yrkesbeteckningar står utan artikel: "elle est médecin".
        return [self.u.form(self.u.lexem(m.predikativ.koncept),
                            _tal(m.predikativ.numerus))]

    def satsled(self, m: Mening) -> list[str]:
        """Satsens ord. Romansk bisats har samma ordföljd som huvudsatsen.

        Det som SKILJER är modus: en rad subjunktioner styr konjunktiv
        ("bien qu\'il vienne", "antes de que venga", "benché venga"), och
        vilka de är skiljer sig mellan de tre språken. Se `bisats`.
        """
        ord: list[str] = []
        if m.fråga and self.FRÅGEINLEDNING:
            ord.append(self.FRÅGEINLEDNING)
        # Wh-frågan flyttar frågeordet först. Subjektsfrågan låter det ta
        # subjektets plats och behåller rak ordföljd; övriga frågor kastar
        # om subjekt och verb i es/it och skjuter in est-ce que i fr.
        frågeord = self.frågeord(m)
        # Subjektet står efter verbet i es/it när något annat än subjektet
        # efterfrågas: "¿Qué dio la chica?". Franskan slipper inversionen
        # genom est-ce que, som är hela skälet att den konstruktionen finns.
        inverterar = (frågeord is not None and m.fråga_om != "subjekt"
                      and not self.FRÅGEINLEDNING)
        if inverterar:
            self.u.ordföljd("inversion_wh")
        if frågeord is not None:
            ord += frågeord
            if m.fråga_om != "subjekt" and self.FRÅGEINLEDNING:
                # est-ce que är franskans sätt att SLIPPA inversionen, och
                # därmed en egen regel att lära sig — se `FRÅGEINLEDNING`.
                self.u.ordföljd("est_ce_que")
                ord.append(self.FRÅGEINLEDNING)
        # Imperativen säger inte ut den tilltalade, och subjektsfrågan har
        # frågeordet på subjektets plats.
        if (m.modus is not Satsmodus.IMPERATIV
                and m.fråga_om != "subjekt" and not inverterar):
            ord += self.nominalfras(m.subjekt, "subjekt")

        # Objektspronomen realiseras som klitika FÖRE verbet, inte på
        # substantivets plats. Det är därför nominalfras() vägrar rollen
        # "objekt" för pronomen — de ska aldrig hamna där.
        cod = self._klitika(m.objekt, "cod")
        coi = self._klitika(m.io, "coi")
        refl = self.reflexivklitikum(m)
        if coi is None and self.DUBBLERAR and m.io is not None:
            coi = self._dubblering(m.io)
            if coi is not None:
                self.u.ordföljd("klitikadubblering")
        if (m.modus is Satsmodus.IMPERATIV and not m.negerad
                and (cod is not None or coi is not None or refl is not None)):
            # JAKANDE imperativ fäster klitikan EFTER verbet, och inte som
            # ett eget ord: "donne-le-moi", "¡dámelo!", "dammelo!". Enklisen
            # har egna regler i varje språk — bindestreck och moi/toi i
            # franskan, accentflytt i spanskan, konsonantfördubbling i
            # italienskan — och byggs inte av samma maskineri som proklisen.
            # Den NEKADE imperativen är proklitisk som alla andra satser
            # ("no me lo des") och går därför igenom här.
            # Reflexivet räknas hit: "réveille-toi", "¡despiértate!",
            # "svegliati!" är enklitiska OCH byter form (me→moi, te→toi i
            # franskan). Att vägra är ärligare än att svara "réveille te".
            raise RenderingsFel(
                f"{self.SPRÅK}: jakande imperativ med klitika kräver enklis "
                f"— inte byggd. Nekad imperativ fungerar.")

        före, efter = self.negation(m)
        ord += före
        if cod is not None or coi is not None or refl is not None:
            self.u.ordföljd("klitika_före")
        # Reflexivet står FÖRST i klitikakedjan: "je me le rappelle", aldrig
        # "je le me rappelle". Det tillhör me/te/se-serien, som i sin tur
        # står före le/la/les — samma två serier som `ordna_klitika` skiljer.
        ord += ([refl] if refl is not None else []) + self.ordna_klitika(cod, coi)
        verb = self.verbdelar(m, self._objektskongruens(m.objekt) if cod else None)
        # Negationens efterled hamnar efter det FINITA verbet, inte efter
        # participet: "elle n'a pas donné", aldrig "elle n'a donné pas".
        ord.append(verb[0])
        ord += efter
        ord += verb[1:]
        if inverterar:
            ord += self.nominalfras(m.subjekt, "subjekt")
        else:
            # SVO är det som gäller NÄR INGET FLYTTAR. Loggas här och inte
            # vid ingången, så att regeln mäts på de meningar den faktiskt
            # styr och inte på dem där inversionen tog över.
            self.u.ordföljd("svo")

        if m.komplement is not None:
            markör = self.u.infinitivmarkör(m.verb)
            if markör is not None:
                ord.append(self.u.form_för(markör, "inv"))
            ord += self.infinitivkomplement(m)
        if m.predikativ is not None:
            ord += self.predikativ(m)
        if m.objekt is not None and cod is None and m.fråga_om != "objekt":
            ord += self.nominalfras(m.objekt, "objekt",
                                    negerad=m.negerad)
        if (m.io is not None and self._pronomen(m.io) is None
                and m.fråga_om != "io"):
            prep = self.preposition_för(m.verb, "io")
            if prep is not None:
                ord.append(self.u.form_för(prep, "inv"))
                ord += self.nominalfras(m.io, "efter_preposition")
            else:
                ord += self.nominalfras(m.io, "objekt")
        for adverbial in m.adverbial:
            if isinstance(adverbial, str):
                ord.append(self.u.form_för(adverbial, "inv"))
            elif isinstance(adverbial, Bisats):
                ord += self.bisats(adverbial)   # adverbialbisats: bara subjunktionen styr
            else:
                # Sammandragningen de+le→du sköts av sandhi, precis som
                # för genitivet — samma mekanism, annan preposition.
                ord.append(self.u.form_för(adverbial.preposition, "inv"))
                ord += self.nominalfras(adverbial.komplement)
        if m.bisats is not None:
            ord += self.bisats(m.bisats, styrande=m)
        return ord

    def attributgrad(self, a: Attribut, adjektiv, genus: int,
                     numerus: Numerus) -> list[str]:
        """Attributets form i sin grad. Perifrastisk när cellen saknas.

        De romanska språken komparerar nästan alltid perifrastiskt: bara
        ett tiotal adjektiv per språk har suppletiva former (meilleur,
        mayor, migliore). Datan avgör, precis som för predikativet.

        Superlativens bestämda artikel sätts INTE här. Attributet sitter i
        en nominalfras som redan har en artikel, och "il libro più grande"
        tar bara en — till skillnad från predikativet, som står utan fras
        och därför måste ta med sin egen.
        """
        if a.grad is Grad.POSITIV:
            return [self.u.form(adjektiv, f"pos_{_kön(genus)}_{_tal(numerus)}")]
        stam = "komp" if a.grad is Grad.KOMPARATIV else "superl"
        celler = self.u._celler(adjektiv)
        cell = next((c for c in (f"{stam}_{_kön(genus)}_{_tal(numerus)}",
                                 f"{stam}_{_tal(numerus)}") if celler.get(c)), None)
        if cell is not None:
            return [self.u.form(adjektiv, cell)]
        return [self.u.form_för("komp_mer" if a.grad is Grad.KOMPARATIV
                                else "komp_mest", "inv"),
                self.u.form(adjektiv, f"pos_{_kön(genus)}_{_tal(numerus)}")]

    def konjunktivstam(self, m: Mening) -> str:
        """Presens eller imperfekt konjunktiv, valt på SATSENS egen tid.

        Tidsföljden (concordancia de tiempos) styrs egentligen av den
        överordnade satsens tempus, men bisatsens eget tempus säger samma
        sak i praktiken: "antes de que venga" mot "antes de que viniera".

        Franskan har ingen levande imperfektkonjunktiv — "qu'il vînt" är
        litterärt på samma sätt som passé simple — och tar därför alltid
        presens. Att paradigmet SAKNAR subj_imperf i fr är det som avgör,
        inte en regel här: språket får den stam vars celler finns.
        """
        if m.tid is Tidsreferens.FÖRFLUTEN and self.HAR_IMPERFEKTKONJUNKTIV:
            return "subj_imperf"
        return "subj"

    def frågecell(self, koncept: str, subjekt: bool) -> str:
        """Cellen i frågepronomenets paradigm. Franskans är kasusdelad."""
        return "nom" if subjekt else "obl"

    def frågedeterminantcell(self, genus: int, numerus: Numerus) -> str:
        """quel kongruerar som en artikel. Överskrivs där paradigmet är tunnare."""
        return self.artikelcell(genus, numerus, "", bestämd=True)

    def frågeord(self, m: Mening) -> list[str] | None:
        """Frågeordet, med preposition om slotten är prepositionsstyrd.

        Det indirekta objektet realiseras med à/a i de romanska språken, och
        prepositionen följer med frågan: "à qui a-t-elle donné le livre".
        Den läses ur samma MönsterKrav som styr påståendet.
        """
        if m.fråga_om is None:
            return None
        if m.fråga_om not in FRÅGESLOTTAR:
            return [self.u.form_för(m.fråga_om, "inv")]
        efterfrågat = {"subjekt": m.subjekt, "objekt": m.objekt, "io": m.io}[m.fråga_om]
        if efterfrågat is None:
            raise RenderingsFel(
                f"{self.SPRÅK}: fråga_om={m.fråga_om!r} men den slotten är tom")
        if efterfrågat.frågedeterminant is not None:
            ord = self.nominalfras(
                efterfrågat, "subjekt" if m.fråga_om == "subjekt" else "objekt")
        else:
            koncept = self.u.frågepronomen(efterfrågat.koncept)
            ord = [self.u.form_för(
                koncept, self.frågecell(koncept, m.fråga_om == "subjekt"))]
        prep = self.preposition_för(m.verb, m.fråga_om)
        if prep is not None:
            ord.insert(0, self.u.form_för(prep, "inv"))
        return ord

    def bisats(self, b: Bisats, styrande: Mening | None = None) -> list[str]:
        """Subjunktion plus sats, i det modus något ord styr fram.

        TVÅ ord kan styra modus, och båda måste frågas: subjunktionen som
        inleder satsen ("avant que", "benché") och — när satsen är ett
        ARGUMENT — verbet som tar den ("volere che", "esperar que"). Det
        senare är skälet till att den överordnade meningen skickas med:
        bisatsen kan inte veta vad som styr den.
        """
        modus = self.modusrektion(b.subjunktion, "komplement")
        if modus is None and styrande is not None:
            modus = self.modusrektion(styrande.verb, self.bisatsslot(styrande.verb))
        sats = (replace(b.sats, modus=Satsmodus.KONJUNKTIV)
                if modus == KONJUNKTIVBIT else b.sats)
        return [self.u.form_för(b.subjunktion, "inv"), *self.satsled(sats)]

    def bisatsslot(self, verb: str) -> str:
        """Vilken slot verbet har sin Bisatsfras på — objekt, kommunikat
        eller komplement. Ligger på det universella mönstret."""
        rad = self.conn.execute(
            """SELECT mk.slot FROM Mönster m
               JOIN Koncept k ON k.id = m.koncept_id
               JOIN MönsterKrav mk ON mk.mönster_id = m.id
               WHERE k.nyckel = ? AND m.språk IS NULL
                 AND (mk.frastyp & 32) = 32""", (verb,)).fetchone()
        return rad["slot"] if rad else "objekt"

    def rendera(self, m: Mening) -> str:
        ord = self.osammansmält = self.satsled(m)
        mening = " ".join(self.sandhi(ord))
        mening = mening[0].upper() + mening[1:]
        if m.fråga or m.fråga_om is not None:
            return self.FRÅGETECKEN_FÖRE + mening + "?"
        if m.modus is Satsmodus.IMPERATIV:
            # Spanskan sätter ut det inledande utropstecknet också.
            return self.UTROPSTECKEN_FÖRE + mening + "!"
        return mening + "."
