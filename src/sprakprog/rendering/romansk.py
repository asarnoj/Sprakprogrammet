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
    Numerus, Referentgenus, attribut_med_grad, bestämd_fras,
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
        return rad["nyckel"] if rad else None

    # ── nominalfras ──────────────────────────────────────────────────

    def nominalfras(self, nf: Nominalfras, roll: str = "objekt") -> list[str]:
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

        genus = huvud["genus"]
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
            före.append(self.u.form_för(
                nf.possessiv, self.possessivcell(genus, nf.numerus)))
        else:
            bestämd = nf.bestämdhet is Bestämdhet.BESTÄMD
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

    def _subjektsform(self, nf: Nominalfras) -> tuple[int, str, int]:
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
            genus = self.u.lexem(nf.koncept)["genus"] or MASKULIN
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
            # Pluskvamperfekt: hjälpverbet i imperfekt. "elle avait lu".
            # I konjunktiv är det HJÄLPVERBET som byter modus: "qu'il ait
            # lu", "que haya leído", "che abbia letto". Participet är
            # oförändrat, precis som i indikativ.
            hjälpstam = (self.konjunktivstam(m) if m.modus is Satsmodus.KONJUNKTIV
                         else "imperf" if m.aspekt is Aspekt.PERFEKT
                         and m.tid is Tidsreferens.FÖRFLUTEN else "pres")
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
        """Elision och sammandragning mellan intilliggande ord."""
        ut: list[str] = []
        for o in ord:
            if ut:
                ersättning = self.SAMMANDRAG.get((ut[-1], o))
                if ersättning is not None:
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
            genus = self.u.lexem(nf.koncept)["genus"] or MASKULIN
        return genus, numerus

    # Tilltal → imperativcell. De tre språken skiljer sig på artigheten:
    # franskan lånar 2pl-formen (vouvoiement), spanskan och italienskan har
    # en egen tredjepersonsform (usted, Lei).
    IMPERATIVCELL: dict[str, str] = {}
    # Nekad imperativ är INTE alltid samma form som den jakande. Spanskan
    # byter till konjunktiv i hela paradigmet ("¡no leas!"), italienskan
    # bara i 2sg, och där till infinitiv ("non leggere!"). Tom = oförändrad.
    NEKAD_IMPERATIVCELL: dict[str, str] = {}
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
        if frågeord is not None:
            ord += frågeord
            if m.fråga_om != "subjekt" and self.FRÅGEINLEDNING:
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
        if coi is None and self.DUBBLERAR and m.io is not None:
            coi = self._dubblering(m.io)
        if (m.modus is Satsmodus.IMPERATIV and not m.negerad
                and (cod is not None or coi is not None)):
            # JAKANDE imperativ fäster klitikan EFTER verbet, och inte som
            # ett eget ord: "donne-le-moi", "¡dámelo!", "dammelo!". Enklisen
            # har egna regler i varje språk — bindestreck och moi/toi i
            # franskan, accentflytt i spanskan, konsonantfördubbling i
            # italienskan — och byggs inte av samma maskineri som proklisen.
            # Den NEKADE imperativen är proklitisk som alla andra satser
            # ("no me lo des") och går därför igenom här.
            raise RenderingsFel(
                f"{self.SPRÅK}: jakande imperativ med klitika kräver enklis "
                f"— inte byggd. Nekad imperativ fungerar.")

        före, efter = self.negation(m)
        ord += före
        ord += self.ordna_klitika(cod, coi)
        verb = self.verbdelar(m, self._objektskongruens(m.objekt) if cod else None)
        # Negationens efterled hamnar efter det FINITA verbet, inte efter
        # participet: "elle n'a pas donné", aldrig "elle n'a donné pas".
        ord.append(verb[0])
        ord += efter
        ord += verb[1:]
        if inverterar:
            ord += self.nominalfras(m.subjekt, "subjekt")

        if m.komplement is not None:
            markör = self.u.infinitivmarkör(m.verb)
            if markör is not None:
                ord.append(self.u.form_för(markör, "inv"))
            ord.append(self.u.form_för(m.komplement, "inf"))
        if m.predikativ is not None:
            ord += self.predikativ(m)
        if m.objekt is not None and cod is None and m.fråga_om != "objekt":
            ord += self.nominalfras(m.objekt, "objekt")
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
        ord = self.satsled(m)
        mening = " ".join(self.sandhi(ord))
        mening = mening[0].upper() + mening[1:]
        if m.fråga or m.fråga_om is not None:
            return self.FRÅGETECKEN_FÖRE + mening + "?"
        if m.modus is Satsmodus.IMPERATIV:
            # Spanskan sätter ut det inledande utropstecknet också.
            return self.UTROPSTECKEN_FÖRE + mening + "!"
        return mening + "."
