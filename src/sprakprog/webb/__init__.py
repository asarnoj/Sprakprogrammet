"""Lokal server för övningsgränssnittet.

INGA BEROENDEN, och det är ett beslut och inte en brist. Arbetslasten är en
användare på localhost med fyra rutter, vilket standardbiblioteket klarar;
och slutmålet är en Tauri-app där Python följer med som sidecar, där varje
paket som ska buntas är verkligt arbete. Behövs mer senare är rutterna
desamma och bytet litet.

GRÄNSSNITTET ÄR WEBB HELA VÄGEN. Tauri är ett skal av Rust runt systemets
webbvy, så innehållet ÄR en webbfrontend — att bygga sidan nu är att bygga
Tauri-appens frontend, inte en prototyp som ska kastas. Det som tillkommer
vid inramningen är paketeringen av Python-körtiden, och den rör ingenting
som skrivs här.

TILLSTÅND I MINNET. Ett `Förslag` bär `sqlite3.Row`-objekt och en `Mening`,
och går inte att serialisera. Servern håller därför de obesvarade förslagen
i en ordbok och skickar bara ett id till sidan. Ett obesvarat förslag som
aldrig kommer tillbaka är bara minne, inte ett hål i historiken: ingenting
loggas förrän användaren svarat.

ETT LÅS RUNT GENERATORN. `ThreadingHTTPServer` ger en tråd per anrop medan
sqlite3-anslutningar hör till sin egen tråd. Med en användare är ett lås
det enkla och ärliga svaret; en anslutningspool vore att lösa ett problem
som inte finns.
"""

from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from ..db import anslut
from ..generator import Generator
from ..kort import pass_ as passlager
from ..kort import (
    Schemaläggare, anslut_kort, befolka, dagsplan, dygnets_början,
    oövade_koncept,
    INFÖRBAR,
    redo_för_nivå,
    sekunder_per_repetition,
    upplåsningsläge,
)
from ..kort.db import STANDARD_KORT_DB
from ..kort.schemalaggning import kostnad
from .lektion import Lektioner
from .ordbok import Ordbok

SIDA = Path(__file__).parent / "sida.html"


class Övningstjänst:
    """Generatorerna och deras tillstånd, en per kurs."""

    def __init__(self, kort_db: sqlite3.Connection, språk_db: sqlite3.Connection,
                 *, kandidater: int = 800) -> None:
        self.kort_db = kort_db
        self.språk_db = språk_db
        self.kandidater = kandidater
        self.lås = threading.Lock()
        self._generatorer: dict[tuple, Generator] = {}
        self._öppna: dict[int, tuple] = {}
        #: (kurs, extraläge) → id på den uppgift som lämnats ut men ännu inte
        #: besvarats. Se `uppgift`.
        self._pågående: dict[tuple[int, bool], int] = {}
        # Rättade men ännu inte bokförda meningar — självrättningens
        # fönster. Ett obokfört svar som aldrig går vidare är bara minne,
        # precis som ett obesvarat förslag: ingenting loggas förrän
        # användaren lämnat meningen bakom sig.
        self._obokförda: dict[int, tuple] = {}
        #: När förra glosan besvarades, per kurs. Glosläget delar ut tio ord
        #: på en gång och drillar dem sedan ett i taget, så det finns ingen
        #: utdelningstidpunkt per ord — men tiden MELLAN två svar är den tid
        #: det andra ordet tog. Första ordet i en portion får därför ingen
        #: tid, vilket är riktigt: den går inte att mäta.
        self._glosklocka: dict[int, float] = {}
        self._nästa = 1
        self.ordbok = Ordbok(språk_db, kort_db)
        self.lektioner = Lektioner(språk_db, kort_db)
        # Vad nästa nivå skulle lägga till i kort. Svaret kräver en befolkning
        # i en kopia av databasen (en sekund), och det ändras bara när nivån
        # gör det — alltså cachas det per (språk, nivå, cefr) och inte per
        # sidladdning. Nyckeln bär nivån, så en upplåsning ogiltigförklarar
        # posten av sig själv.
        self._nästa_nivå_kostnad: dict[tuple, int] = {}
        self._byggbarheter: dict[tuple, float | None] = {}

    #: Språknamn i gränssnittet. Programmets språk är inte kursens — en
    #: svensk som lär sig tyska kan vilja ha engelskt gränssnitt.
    SPRÅKNAMN = {"sv": "Swedish", "en": "English", "de": "German",
                 "fr": "French", "es": "Spanish", "it": "Italian",
                 "ja": "Japanese"}

    #: Kurspar som mätts som svaga, med skälet. Italienskan misslyckas på
    #: 32 % av alla meningar, nästan alla på obestämd artikel i plural som
    #: språket inte har (mätt 2026-08-15, se uppgiften om partitiven).
    #: Varningen gäller italienskan som käll- ELLER målspråk och försvinner
    #: när den är löst.
    SVAGA = {"it": "Italian is missing indefinite plurals — about a third of "
                   "sentences cannot be built yet."}

    def språk(self) -> list[dict]:
        return [{"kod": k, "namn": n, "varning": self.SVAGA.get(k)}
                for k, n in self.SPRÅKNAMN.items()]

    def kurser(self) -> list[dict]:
        """Kurserna, den senast öppnade först.

        `sek_per_rep` är None tills tillräckligt många pass tidtagits. Talet
        följer med hit för att minutinställningen ska kunna SÄGA om den verkar
        ännu — ett fält som inte gör något och inte förklarar varför är värre
        än inget fält.
        """
        return [dict(r) | {"källnamn": self.SPRÅKNAMN.get(r["källspråk"], ""),
                           "målnamn": self.SPRÅKNAMN.get(r["målspråk"], ""),
                           "sek_per_rep": sekunder_per_repetition(
                               self.kort_db, r["målspråk"]),
                           **self._prognos(r)}
                for r in self.kort_db.execute(
                    """SELECT * FROM Kurs
                       ORDER BY senast_öppnad IS NULL, senast_öppnad DESC,
                                målspråk""")]

    def ny_kurs(self, källspråk: str, målspråk: str, nivå: int = 1,
                cefr: str = "A1") -> dict | None:
        if källspråk == målspråk or källspråk not in self.SPRÅKNAMN \
                or målspråk not in self.SPRÅKNAMN:
            return None
        with self.lås:
            nu = datetime.now(UTC).isoformat()
            self.kort_db.execute(
                """INSERT INTO Kurs (källspråk, målspråk, nivå, cefr, budget,
                                     meningar_per_dag, startad, senast_öppnad)
                   VALUES (?,?,?,?,1.5,20,?,?)
                   ON CONFLICT (källspråk, målspråk) DO UPDATE SET
                       senast_öppnad = excluded.senast_öppnad""",
                (källspråk, målspråk, nivå, cefr, nu, nu))
            self.kort_db.commit()
            befolka(self.kort_db, self.språk_db, {målspråk},
                    nivå=nivå, cefr=cefr)
            rad = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE källspråk=? AND målspråk=?",
                (källspråk, målspråk)).fetchone()
            return dict(rad)

    def välj(self, kurs_id: int) -> dict | None:
        with self.lås:
            self.kort_db.execute(
                "UPDATE Kurs SET senast_öppnad = ? WHERE id = ?",
                (datetime.now(UTC).isoformat(), kurs_id))
            self.kort_db.commit()
            rad = self._kurs(kurs_id)
            return dict(rad) if rad else None

    def lås_upp(self, kurs_id: int) -> dict | None:
        """Öppna nästa steg. ANVÄNDAREN klickar; systemet säger bara när det
        finns plats (schemalaggning.upplåsningsläge)."""
        with self.lås:
            kurs = self._kurs(kurs_id)
            if kurs is None or kurs["nivå"] >= 21:
                return None
            # SAMMA VILLKOR SOM KNAPPEN VISAS PÅ. Annars kan en gammal
            # sidladdning låsa upp en nivå som inte går att öva.
            if not redo_för_nivå(self._byggbarhet(kurs), self.kandidater):
                return None
            ny = kurs["nivå"] + 1
            self.kort_db.execute("UPDATE Kurs SET nivå = ? WHERE id = ?",
                                 (ny, kurs_id))
            self.kort_db.commit()
            # DAGENS TAK RÄKNAS OM NÄR ANVÄNDAREN VÄLJER OM. Att frysa det
            # per dygn finns för att BRÅDSKA inte ska belönas — svarar man
            # snabbt sjunker sekunder-per-repetition, vilket annars höjde
            # målet mitt i ett pass. Ett uttryckligt val är något annat än en
            # mätning som driver, och ska synas direkt.
            self.kort_db.execute(
                "UPDATE Kurs SET tak_datum = NULL WHERE målspråk = ?",
                (kurs["målspråk"],))
            r = befolka(self.kort_db, self.språk_db, {kurs["målspråk"]},
                        nivå=ny, cefr=kurs["cefr"])
            # Generatorn cachas per (källa, mål, nivå, budget) — den gamla
            # är låst vid förra nivån och måste kastas.
            self._generatorer.clear()
            # OCH DAGENS PASS UTÖKAS. Det byggs inte om — det som är gjort
            # ska stå kvar, och det som avskrivits som onåbart ska inte
            # prövas igen samma dag — men de nya korten ska kunna komma in
            # redan idag, upp till samma tak som förut. Annars gjorde
            # upplåsningen ingenting förrän imorgon, utan att säga det.
            kurs = self._kurs(kurs_id)
            passlager.utöka(self.kort_db, kurs, self._dagsplan(kurs))
            return {"nivå": ny, "nya_kort": r["nya"]}

    def nollställ(self, kurs_id: int, bekräftelse: str) -> dict | None:
        """Radera kursens historik. DEN ENDA OÅTERKALLELIGA KNAPPEN.

        Allt annat i systemet går att bygga om ur former.tsv; repetitions-
        historiken gör det inte. Därför krävs ett skrivet ord och inte ett
        klick — samma spärr som `ordbok kort --återinitiera` har.
        """
        if bekräftelse != "RESET":
            return None
        with self.lås:
            kurs = self._kurs(kurs_id)
            if kurs is None:
                return None
            språk = kurs["målspråk"]
            self.kort_db.execute(
                """DELETE FROM Repetition WHERE kort_id IN
                   (SELECT id FROM Kort WHERE språk = ?)""", (språk,))
            self.kort_db.execute("DELETE FROM Mening WHERE språk = ?", (språk,))
            # Korten tas BORT och byggs om, inte bara nollställs. En kurs som
            # stod på nivå 21 har kort som inte går att möta på nivå 1, och
            # att lämna kvar dem vore att återskapa precis de spökkort
            # nivåspärren finns för att förhindra. Här är det tryggt: all
            # historik för språket är just raderad, så inget går förlorat.
            self.kort_db.execute("DELETE FROM Kort WHERE språk = ?", (språk,))
            self.kort_db.execute("UPDATE Kurs SET nivå = 1 WHERE id = ?",
                                 (kurs_id,))
            self.kort_db.commit()
            befolka(self.kort_db, self.språk_db, {språk},
                    nivå=1, cefr=kurs["cefr"])
            self._glöm()
            return {"nollställd": språk}

    def _generator(self, kurs: sqlite3.Row) -> Generator:
        nyckel = (kurs["källspråk"], kurs["målspråk"], kurs["nivå"], kurs["budget"])
        if nyckel not in self._generatorer:
            # Dyr att bygga — läser hela kortbeståndet — så en per kurs och
            # inte en per mening. Den bär också poängsättarens minne av förra
            # meningen, vilket upprepningstermen behöver.
            self._generatorer[nyckel] = Generator(
                self.språk_db, self.kort_db, kurs["målspråk"],
                källspråk=kurs["källspråk"], nivå=kurs["nivå"],
                cefr=kurs["cefr"],
                budget=kurs["budget"])
        return self._generatorer[nyckel]

    def uppgift(self, kurs_id: int, *, extra: bool = False) -> dict | None:
        """Nästa mening, med dagsplanens tak på hur mycket nytt som får in.

        Taket räknas om HÄR och inte en gång per pass: ett kort som just
        introducerats är sett, ligger redan i belastningen med sitt korta
        intervall, och har därmed ätit sin plats. Talet sjunker alltså av sig
        självt medan passet går — och stiger igen när extraövningen flyttar
        fram förfallodagar. Det är samma mekanism sedd från två håll.
        """
        with self.lås:
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            if kurs is None:
                return None
            # EN OBESVARAD UPPGIFT ÖVERLEVER ATT MAN LÄMNAR VYN. Förut byggdes
            # en ny mening vid varje återkomst, och den gamla låg kvar i
            # `_öppna` obesvarad — så ett klick på "Home" och tillbaka bytte
            # ut frågan man höll på med. Det är inte bara onödigt arbete: den
            # mening som byggdes valdes för att den täckte något, och att
            # kasta den och lotta en ny gör vilket kort som övas till en
            # funktion av hur man klickar.
            #
            # Klockan fortsätter gå, och det ska den: en lång frånvaro räknas
            # som ett avbrott (`AVBROTTSGRÄNS_MS`) och tiden kastas, precis
            # som när man går ifrån mitt i en mening utan att lämna vyn.
            öppen = self._pågående.get((kurs_id, extra))
            if öppen in self._öppna:
                return self._uppgiftssvar(öppen, kurs, self._öppna[öppen][1])
            p = self._dagsplan(kurs)
            if extra:
                e = self._extrapass(kurs)
                p = ({**p, **passlager.läget(self.kort_db, e["id"])}
                     if e is not None else {**p, "att_göra": 0})
            if not p["att_göra"]:
                # Ingenting köat. Det är ett SVAR och inte ett fel, och det
                # skiljs från "sökningen misslyckades" just här — nedanför
                # betyder None att generatorn inte kunde bygga något.
                return {"tomt": True}
            g = self._generator(kurs)
            f = g.föreslå(kandidater=self.kandidater, extra=extra,
                          nya_tillåtna=0 if extra else p["nya"],
                          passkö=passlager.väntande_ider(
                              self.kort_db, p["pass_id"], "igen"),
                          # DAGENS NYA KORT KOMMER UR PASSET, inte ur en ny
                          # fråga till `osedda`. Passet valde dem och silade
                          # dem genom nåbarheten; generatorn räknade fram sin
                          # egen lista och fick en HELT DISJUNKT mängd — mätt
                          # noll gemensamma kort, varje varv. Se `föreslå`.
                          nya=None if extra else passlager.väntande_ider(
                              self.kort_db, p["pass_id"], "ny"),
                          oövade=None if extra else oövade_koncept(
                              self.kort_db, kurs["målspråk"]))
            if f is None:
                return None
            # INGEN TÄCKNING BETYDER ATT DET INTE GÅR ATT KOMMA LÄNGRE. Kön är
            # inte tom, men den bästa av flera hundra kandidater rör inget av
            # det som står i den — alltså går de kvarvarande korten inte att
            # bygga en mening kring just nu.
            #
            # Signalen är stark: poängsättaren straffar en mening utan täckning
            # med −40 (tomgång), så en sådan vinner bara när ingen annan finns.
            #
            # Det här ersätter det gamla meningsmålet som passets nödutgång.
            # Utan det skulle dagen aldrig ta slut när ett förfallet kort är
            # onåbart — och att i stället avsluta efter N meningar var att
            # låta transporten bestämma över arbetet.
            #
            # VILLKORET KRÄVDE FÖRFALLNA KORT, och det var fel. Onåbarheten
            # gäller KÖN, och kön är förfallna PLUS passkön PLUS dagens nya.
            # Med noll förfallna men sju nya böjningskort som alla krävde ord
            # kursen inte hade, föll nödutgången aldrig ut: passet gav fyra
            # meningar i rundgång med täckning noll, dygnet ut. Vad kön består
            # av spelar ingen roll för slutsatsen — går ingenting i den att
            # röra går det inte att komma längre.
            if self._onåbar(f, p):
                # SKRIV NER DET I PASSET. Förut minnesnoterades onåbarheten i
                # ett lexikon på tjänsten, med ett fingeravtryck som skulle
                # avgöra när noteringen var gammal — en konstruktion som var
                # svår att lita på och dessutom död vid omstart. Nu får de
                # kort som inte går att nå status `onåbar` i `Passkort`:
                # räknade som gjorda för dagen, betygsatta inte alls (D3),
                # och frågan behöver aldrig ställas igen.
                n = passlager.avskriv(self.kort_db, p["pass_id"])
                return {"tomt": True, "oåtkomliga": n, "onåbart_nytt": n}
            id_ = self._nästa
            self._nästa += 1
            # KLOCKAN STARTAR NÄR UPPGIFTEN LÄMNAS UT. Tiden mäts på
            # servern och inte i webbläsaren: den ska inte gå att påverka,
            # och den ska överleva att sidan laddas om.
            self._öppna[id_] = (kurs["id"], f, time.monotonic())
            self._pågående[(kurs["id"], extra)] = id_
            return self._uppgiftssvar(id_, kurs, f)

    @staticmethod
    def _onåbar(f, p: dict) -> bool:
        """Går det inte att komma längre? Passets nödutgång, som en egen regel.

        Villkoret bor i en metod för att gå att SABOTERA i `tjänsteprov` utan
        att skriva i källfilen — den vägen är en fälla, se
        `Generator._duglig`.
        """
        return f.poäng is not None and f.poäng.täckta == 0

    def _uppgiftssvar(self, id_: int, kurs: sqlite3.Row, f) -> dict:
        return {"id": id_, "uppgift": f.uppgift, "källspråk": kurs["källspråk"],
                "målspråk": kurs["målspråk"], "kort": len(f.kort),
                "nya": f.poäng.nya, "förväntat": round(f.poäng.förväntat, 2),
                # BARA TYPER OCH ANTAL, aldrig facit: korten ÄR svaret.
                # Att visa att meningen prövar formkortet `lies down` vore
                # att skriva ut lösningen bredvid frågan. Detaljen kommer
                # efter svaret, i `svara`.
                # SANT NÄR MENINGEN ÄR EN UPPREPNING SOM INTE GICK ATT
                # UNDVIKA. Ett litet ordförråd har inte fler meningar än det
                # har, och då är en upprepning ärligare än ett oanmält ord
                # (C5). Flaggan finns för att skillnaden ska gå att MÄTA —
                # utan den kan ett prov inte skilja "sökningen hade inget
                # val" från "meningsminnet är trasigt".
                "nödfall": f.nödfall,
                "typer": self._typfördelning(f.kort)}

    def _typfördelning(self, kort: list) -> list[dict]:
        """Korttyperna en mening rör, i introduktionsordning."""
        antal: dict[str, int] = {}
        for r in kort:
            antal[r["typ"]] = antal.get(r["typ"], 0) + 1
        return [{"typ": t, "namn": namn, "antal": antal[t]}
                for t, namn in self.TYPNAMN if antal.get(t)]

    def svara(self, id_: int, svar: str) -> dict | None:
        """Rätta meningen — men BOKFÖR den inte än.

        Betygsättningen skjuts upp till `bokför`, som sidan anropar när
        användaren går vidare. Skälet är att FSRS är en tillståndsmaskin:
        en Again som redan lagts kan inte tas tillbaka, och en kompenserande
        Good samma minut är nästan verkningslös (mätt: S 0,61 → 0,66). Ska
        självrättningen kunna rätta något måste den alltså komma FÖRE
        betyget, inte efter.

        Fönstret är exakt så länge facit står på skärmen, och kostar inget
        extra klick i det normala fallet.
        """
        with self.lås:
            post = self._öppna.pop(id_, None)
            if post is None:
                return None
            kurs_id, f, start = post
            for nyckel, v in list(self._pågående.items()):
                if v == id_:
                    del self._pågående[nyckel]
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            g = self._generator(kurs)
            r = g.rätta(f, svar)
            self._obokförda[id_] = (kurs_id, f, dict(r.utfall), set(), start)
            namn = dict(self.TYPNAMN)
            # SKYDDADE KORT FÅR INGET BETYG, och listan ska säga det. Faller
            # ordkortet testades formen aldrig — kan man inte hämta fram ordet
            # alls säger stavningen av dess ändelse ingenting — så
            # `registrera_mening` tar dem ur betygsättningen. Utan det här
            # visade listan ✓ på kort som aldrig bokfördes, alltså ett annat
            # utfall än det som hamnar i historiken.
            skyddade = g.schemaläggare._skyddade(r.utfall)
            dom = {k: (None if k in skyddade else v) for k, v in r.utfall.items()}
            return {"id": id_, "korrekt": r.korrekt, "facit": f.text,
                    "igen": self._igen_efter(g, r.utfall),
                    # HELA UTFALLET, kort för kort. Nu är svaret givet, så
                    # facit får visas — och det är först här man kan se vad
                    # meningen faktiskt mätte. `dom` är None för kort som
                    # hölls utanför betygsättningen (oattribuerat fel).
                    "kort": sorted(
                        ({"typ": k["typ"], "namn": namn.get(k["typ"], k["typ"]),
                          "facit": k["facit"], "koncept": k["koncept"],
                          # REGELNS NYCKEL för ordföljdskort. Deras `facit` är
                          # svensk prosa i databasen — "finita verbet på plats
                          # två i huvudsats" — och stod som kortets namn i ett
                          # engelskt gränssnitt bredvid rena språkdata som
                          # `haben` och `∅`. `egenskap` är den stabila nyckeln
                          # (`v2`, `satsklammer`), och texten hör hemma i `T`.
                          "regel": k["egenskap"] if k["typ"] == "ordföljd"
                                   else None,
                          "dom": dom.get(k["id"]),
                          # Förfallodagen FÖRE prövningen — den nya räknas ut
                          # först vid bokföringen. `null` = kortet är nytt och
                          # har ingen ännu.
                          "förfaller": k["förfaller"], "sedd": k["sedd"]}
                         for k in f.kort),
                        key=lambda x: ([t for t, _ in self.TYPNAMN].index(x["typ"])
                                       if x["typ"] in dict(self.TYPNAMN) else 99,
                                       str(x["facit"]))),
                    "anmärkningar": [
                        {"nr": n, "skrev": a.skrev, "väntat": a.väntat,
                         # NYCKELN, inte prosan. `slutsats` är svensk text —
                         # "fel stam — skrev formen för pres_3sg" — och gick
                         # rakt ut i ett engelskt gränssnitt. Texten bor i `T`
                         # i sida.html tillsammans med all annan
                         # gränssnittstext; hit skickas bara vad slutsatsen
                         # VAR och vad den handlade om.
                         #
                         # `slutsats` följer med som reserv: en nyckel som
                         # `T` inte känner igen ska visa något begripligt och
                         # inte ett tomt fält. Ett gränssnitt som tiger om ett
                         # fel är värre än ett som säger det på fel språk.
                         "nyckel": a.nyckel, "arg": a.arg,
                         "slutsats": a.slutsats, "osäker": a.osäker,
                         # KORTET RAPPORTERAS BARA OM DET FAKTISKT FICK EN
                         # DOM. En anmärkning kan namnge ett kort som sedan
                         # hålls utanför betygsättningen — hela meningen kan
                         # hållas inne när felet inte går att knyta till
                         # något (se `Rättare.rätta`). Att ändå skicka
                         # `kort_id` gav en räknare som sa att kort fällts
                         # när inget gjort det: mätt 2 kort mot räknarens 0.
                         "kort_id": (a.kort_id if a.kort_id in r.utfall
                                     else None),
                         # Rätt ord på fel plats. Får inte ritas som ett
                         # felskrivet ord — det var korrekt skrivet.
                         "ordföljd": a.ordföljd,
                         # Sammansmältning: felet är verkligt men har inget
                         # kort. Ska visas som en upplysning, inte som ett
                         # felskrivet ord.
                         "sandhi": a.sandhi}
                        for n, a in enumerate(r.anmärkningar)]}

    def självrätta(self, id_: int, *, hela: bool = False,
                   kort_id: int | None = None) -> dict | None:
        """Användaren överprövar rättningen, före bokföringen.

        `hela` betyder "mitt svar var också rätt" — det dyraste felet av alla,
        eftersom ett rätt svar som registreras som fel sänker stabiliteten på
        kort som mår bra. Det är den enda feltypen som FÖRDÄRVAR data i
        stället för att bara sakna den.

        `kort_id` vänder ett enskilt korts dom. Överprövningen bokförs som
        `Repetition.självrättad = 1` och blir därmed mätbar: överprövas en
        viss sorts anmärkning ofta är det rättningen som har fel.
        """
        with self.lås:
            post = self._obokförda.get(id_)
            if post is None:
                return None
            kurs_id, f, utfall, rättade, _ = post
            if hela:
                for kid in utfall:
                    if utfall[kid] is not True:
                        rättade.add(kid)
                    utfall[kid] = True
            elif kort_id is not None and kort_id in utfall:
                utfall[kort_id] = not utfall[kort_id]
                rättade.add(kort_id)
            return {"utfall": {str(k): v for k, v in utfall.items()},
                    "självrättade": sorted(rättade)}

    def bokför(self, id_: int) -> dict | None:
        """Skriv in betygen. Anropas när användaren går vidare."""
        with self.lås:
            post = self._obokförda.pop(id_, None)
            if post is None:
                return None
            kurs_id, f, utfall, rättade, start = post
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            g = self._generator(kurs)
            # BYGGBARHETEN ÄNDRAS NÄR ORD LÄRS IN, så cachen töms här. Utan
            # det kunde upplåsningsknappen dröja kvar dold en hel session
            # efter att nivån faktiskt blivit övningsbar.
            self._byggbarheter.clear()
            g.uppdatera_passkö(utfall)
            # OCH I PASSET, som är det som räknas. Generatorns egen kö är
            # en sökhjälp — den styr vilket kort meningen byggs kring — men
            # TALET som visas och frågan om dagen är klar kommer ur
            # `Passkort`. Två källor till samma sanning var precis vad som
            # gav "1 kvar" bredvid "klart för idag".
            rad = passlager.nuvarande(self.kort_db, kurs_id)
            if rad is not None:
                passlager.registrera(self.kort_db, rad["id"], utfall)
            # HELA CYKELN, inte bara skrivandet: att läsa rättelsen är också
            # tid uppgiften kostade, och kostnadsmodellen frågar hur mycket
            # av dygnet en repetition förbrukar. Råtiden sparas OKAPAD —
            # kapningen är ett analysval (`AVBROTTSGRÄNS_MS`) och görs när
            # talet används, annars går den verkliga fördelningen förlorad.
            g.registrera(f, utfall, självrättade=rättade,
                         millisekunder=int((time.monotonic() - start) * 1000))
            return {"bokförd": True, "självrättade": len(rättade),
                    "igen": self._dagsplan(
                        self.kort_db.execute("SELECT * FROM Kurs WHERE id = ?",
                                             (kurs_id,)).fetchone())["igen"]}

    def hem(self, kurs_id: int) -> dict | None:
        """Hemvyns två kolumner: dagens övning, och vägen till nästa nivå."""
        with self.lås:
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            if kurs is None:
                return None
            språk = kurs["målspråk"]
            p = self._dagsplan(kurs)
            nästa = self._nästa_nivå(kurs)
            u = upplåsningsläge(self.kort_db, språk, nästa,
                                byggbarhet=self._byggbarhet(kurs),
                                kandidater=self.kandidater,
                                inflödestak=p["inflödestak"])
            return {
                "kurs": dict(kurs),
                "idag": {"att_göra": p["att_göra"], "förfallna": p["förfallna"],
                         "igen": p["igen"], "nya": p["nya"],
                         "gjort": p["gjort"], "mål": p["mål"], "klar": p["klar"],
                         "finns": p["att_göra"],
                         # UPPDELNINGEN, färdigräknad. Sidan ska inte
                         # härleda den — se `pass_.läget`.
                         "delar": p["delar"],
                         # Nya ORD väntar på glosläget; övriga nya kort
                         # (böjning) introduceras i meningarna.
                         # B4: användarens val är minuter. Antalet meningar
                         # är en konsekvens och inte ett tak.
                         "minuter": p["minuter_per_dag"],
                         "tid_kvar": p["tid_kvar"], "tid_idag": p["tid_idag"],
                         "nya_obestämt": p["nya_obestämt"],
                         # UPPSKATTAD TID FÖR DAGEN, ur den egna takten.
                         # Minuter är användarens enhet (B4), så dagens
                         # arbete ska gå att läsa i minuter och inte bara i
                         # kort. None när takten inte är mätt — en gissad
                         # tidsangivelse vore värre än ingen.
                         #
                         # PER RAD, inte per repetition. `att_göra` räknar
                         # passrader; `sekunder_per_repetition` har bedömda
                         # kort i nämnaren. En mening betygsätter fler kort
                         # än den stänger rader, så produkten underskattade
                         # genomgående med omkring hälften — mätt över en
                         # vecka: lovat 1/2/3/4 min mot verkliga
                         # 1,5/3,4/4,4/5,7. Se `sekunder_per_rad`.
                         "minuter_kvar": (
                             round(p["att_göra"] * p["sekunder_per_rad"] / 60)
                             if p["sekunder_per_rad"] else None),
                         # VÄXER DAGEN ÄNNU? Tio minuter är ett JÄMVIKTSMÅL
                         # och inte ett löfte om dag ett. B2 styr inflödet så
                         # att dygnets arbete konvergerar mot målet; de
                         # första dagarna har helt enkelt inga repetitioner
                         # att göra ännu. Mätt på en ny franskkurs med tio
                         # minuter inställt: 1,5 min dag 1, 3,4 dag 3, 4,4
                         # dag 5, 5,7 dag 7.
                         #
                         # Utan det här beskedet ser en kort dag ut som en
                         # trasig inställning. Villkoret är MÄTT och inte
                         # antaget: dagen ligger under halva målet OCH det
                         # finns osett material kvar att växa med.
                         "växer": bool(
                             p["sekunder_per_rad"] and p["osedda"]
                             and p["att_göra"] * p["sekunder_per_rad"]
                                 < p["minuter_per_dag"] * 60 / 2),
                         "per_läge": p["kostnad_per_läge"],
                         "sek_per_rep": p["sekunder_per_repetition"],
                         # Den växelkurs `minuter_kvar` faktiskt vilar på.
                         # Skickas så att gränssnittets tal går att pröva mot
                         # sin egen källa — se `indikatorprov`.
                         "sek_per_rad": p["sekunder_per_rad"],
                         "inflödestak": p["inflödestak"],
                         "oövade": p["oövade"],
                         "glosor": min(
                             p["glosor"], self.kort_db.execute(
                             """SELECT COUNT(*) FROM Kort WHERE språk = ?
                                AND typ = 'ord'
                                AND sedd IS NULL""", (språk,)).fetchone()[0])},
                "extra": self._extraläge(p),
                # `rum`, `saknas`, `krävs`, `kapacitet` och `plats` skickas
                # INTE. De räknas med det gamla `per_kort`, som är fem till
                # trettio gånger för högt, och de grindar ingenting efter F1.
                # Att skicka ett tal som är både fel och oanvänt är att bjuda
                # in att det används igen — vilket det just hade blivit, i
                # underraden som visade `krävs` mot `kapacitet`.
                "nivå": {"nu": kurs["nivå"], "av": 21,
                         "osedda": u["osedda"], "totalt": u["totalt"],
                         # ORDFÖRRÅDET SOM ÅTERSTÅR, ur SAMMA räkning som
                         # kursvyn visar. De två sa olika saker om samma sak:
                         # hemvyn ritade `osedda` under etiketten "Words in
                         # this level's vocabulary", men `osedda` är OSEDDA
                         # KORT av alla sju typer och för hela språket.
                         #
                         # Mätt 2026-08-26 på tyskan: etiketten sa 1 058 ord.
                         # De 1 058 var 428 genuskort, 373 stammar, 202
                         # ordkort, 27 ändelser, 18 former, 6 rektioner och 4
                         # ordföljdsregler. Antalet ord var 205. Kursvyn sa
                         # samtidigt 217 — `_prognos`, som delar korten på
                         # kort-per-koncept och därför svarar på den fråga
                         # etiketten ställde.
                         #
                         # Att låta båda vyerna läsa `_prognos` är inte bara
                         # en rättelse av talet: det gör att de inte KAN gå
                         # isär igen, vilket etiketterna ensamma aldrig kunde
                         # garantera.
                         **{k: v for k, v in self._prognos(kurs, p).items()
                            if k in ("ord_kvar", "dygn_till_klart")},
                         # GRINDEN ÄR BYGGBARHETEN, inte kapaciteten (F1).
                         # `plats` står kvar som upplysning.
                         "redo": u["redo"], "byggbarhet": u["byggbarhet"],
                         "dygn": u["dygn_till_klart"],
                         # `plats`, `saknas` och `rum` skickas INTE längre.
                         # De räknas med det gamla `per_kort`, som är fem till
                         # trettio gånger för högt, och de grindar ingenting
                         # efter B2. Att skicka ett tal som är både fel och
                         # oanvänt är att bjuda in att det används igen.
                         "nästa_kort": u["nästa_nivå_kort"]},
                "typer": self._per_typ(kurs, p),
            }

    #: Korttyperna som de heter för en inlärare, i introduktionsordning —
    #: ordet först, sedan dess egenskaper, sedan böjningen.
    TYPNAMN = (("ord", "Words"), ("egenskap", "Genders"), ("stam", "Stems"),
               ("form", "Irregular forms"), ("system", "Endings"),
               ("rektion", "Government"), ("ordföljd", "Word order"))

    def _per_typ(self, kurs: sqlite3.Row, plan: dict) -> list[dict]:
        """Uppdelningen bakom de tre talen — RÄKNAD I PASSET.

        Den räknade förut ur kortbeståndet och kapade mot dagsplanens tak.
        Det gav tal som såg rimliga ut och inte var dagens: rutan sa
        "Genders 6" på en dag vars pass innehöll noll genuskort, eftersom
        inget substantiv var drillat och nåbarhetssilen därför lämnat dem
        utanför. Julius trodde att genus inte gick att pröva på nivån — det
        gör det (`un`/`une` skiljer sig i genus, 124 av 143 genuskort har
        exponering), det var uppdelningen som beskrev något annat.

        Nu är varje rad en räkning i `Passkort`, precis som `att_göra`. Två
        tal om samma sak kan då inte säga olika saker, för det finns bara ett.
        """
        per = {t: {"nya": 0, "förfallna": 0, "igen": 0} for t, _ in self.TYPNAMN}
        for r in self.kort_db.execute(
                """SELECT k.typ, pk.roll, COUNT(*) AS n
                   FROM Passkort pk JOIN Kort k ON k.id = pk.kort_id
                   WHERE pk.pass_id = ? AND pk.status = 'väntar'
                   GROUP BY k.typ, pk.roll""", (plan["pass_id"],)):
            rad = per.get(r["typ"])
            if rad is None:
                continue
            if r["roll"] == "igen":
                rad["igen"] += r["n"]
            elif r["roll"] == "förfallen":
                rad["förfallna"] += r["n"]
            else:
                rad["nya"] += r["n"]
        return [{"typ": t, "namn": namn, **per[t]}
                for t, namn in self.TYPNAMN if any(per[t].values())]

    def igenkön(self, kurs_id: int) -> list[dict] | None:
        """VAD som ligger i återförsöken, inte bara hur många.

        Julius: "det kommer vara lättare att felsöka ifall jag kan se vad som
        ligger i again". Talet ensamt säger att något gick fel men inte vad,
        och ett återförsök som inte verkar komma tillbaka går inte att skilja
        från ett som redan är gjort.

        Rollen `igen` finns i `Passkort` sedan passlagret, så listan är en
        fråga och ingen ny bokföring.
        """
        with self.lås:
            kurs = self._kurs(kurs_id)
            if kurs is None:
                return None
            rad = passlager.nuvarande(self.kort_db, kurs_id)
            if rad is None:
                return []
            namn = dict(self.TYPNAMN)
            return [{"typ": r["typ"], "namn": namn.get(r["typ"], r["typ"]),
                     "koncept": r["koncept"], "cell": r["cell"],
                     "facit": r["facit"], "status": r["status"]}
                    for r in self.kort_db.execute(
                        """SELECT k.typ, k.koncept, k.cell, k.facit, pk.status
                           FROM Passkort pk JOIN Kort k ON k.id = pk.kort_id
                           WHERE pk.pass_id = ? AND pk.roll = 'igen'
                           ORDER BY pk.ordning""", (rad["id"],))]

    #: Hur många glosor som visas i taget. Julius: "denna överblick kommer
    #: 10 ord i taget typ." Ett VAL om hur mycket text som ryms på en skärm
    #: utan att bli en lista att skrolla i — inte en härledning, och det ska
    #: det inte låtsas vara.
    GLOSPORTION = 10

    def glosor(self, kurs_id: int, antal: int | None = None) -> dict | None:
        """Nästa portion nya ord — läsvyn INNAN de ska kunna produceras.

        Ordkort introduceras inte längre inne i meningar. Ett ordkort frågar
        vad ordet betyder, och den frågan går inte att besvara ur en mening
        man inte kan läsa: en ny fransk kurs inledde med `Hon tittar.` →
        `Elle regarde.` där båda orden var osedda.

        Portionen visas först som en LISTA — bägge språken bredvid varandra,
        att läsa igenom — och drillas sedan ord för ord. Att presentera före
        prövningen är hela poängen: det första betyget blir då ett verkligt
        hämtningsförsök och inte en gissning.
        """
        with self.lås:
            kurs = self._kurs(kurs_id)
            if kurs is None:
                return None
            # PORTIONEN FÅR ALDRIG ÖVERSTIGA DAGENS SALDO. Utan den här
            # raden delade vyn ut tio nya ord varje gång den öppnades, utan
            # att något räknade — hela inflödesstyrningen (B2) gick att gå
            # förbi genom att lämna vyn och komma tillbaka. Mätt när felet
            # hittades: 44 införda kort mot ett tak på 34.
            #
            # Hemskärmen räknade redan rätt tal. Det var ÄNDPUNKTEN som inte
            # frågade, alltså två åsikter om samma sak — precis det som
            # `dagsplan` finns till för att förhindra.
            p = self._dagsplan(kurs)
            # F4:S ORDNINGSREGEL BEHÖVS INTE LÄNGRE HÄR, och att den låg kvar
            # var skadligt. Den fanns för att drillen annars fyllde hela dagen
            # med portion efter portion. Nu delas dagens omgång ut EN gång, så
            # den kan inte fylla dagen — och blockeringen kunde i stället låsa
            # ute användaren: ETT oövat ord från ett tidigare pass hindrade
            # hela dagens lektion.
            #
            # `oövade` finns kvar, men gör numera sitt arbete på två andra
            # ställen där det hör hemma: de räknas som dagens arbete
            # (`finns_idag`), och de blir MÅLORD så att meningarna faktiskt
            # övar det som just införts.
            # EN LEKTION PER DAG. Dagens hela ordtilldelning delas ut i EN
            # omgång, inte tio i taget — annars startar varje besök i vyn vad
            # som ser ut som en ny lektion, och den som lämnar och kommer
            # tillbaka får nya ord i stället för att fortsätta på de sina.
            #
            # `GLOSPORTION` är därmed en SIDBRYTNING och inte ett dagstak: den
            # styr hur många som visas åt gången i listan, inte hur många
            # dagen innehåller.
            #
            # Att lämna och återvända ger nu det som ÅTERSTÅR av dagens
            # omgång, eftersom `nya` är ett saldo — är omgången gjord är den
            # noll.
            # `kvar` ÄR ETT FAKTUM OM KURSEN, inte om dagens portion, och
            # måste därför räknas före den tidiga returen. Den svarade `0` när
            # dagen inte hade några glosor kvar att dela ut — alltså "inga ord
            # återstår att lära sig" för en kurs med tvåhundra kvar. Samma tal
            # visas numera i hemvyn och kursvyn (`_prognos.ord_kvar`), och där
            # hade nollan synts.
            kvar = self.kort_db.execute(
                """SELECT COUNT(*) FROM Kort WHERE språk = ? AND typ = 'ord'
                   AND sedd IS NULL""",
                (kurs["målspråk"],)).fetchone()[0]
            n = antal or p["glosor"]
            if n <= 0:
                return {"ord": [], "kvar": kvar, "saldo": 0}
            self._glosklocka.pop(kurs_id, None)
            rader = Schemaläggare(self.kort_db).oglosade(kurs["målspråk"], n)
            ut = []
            for r in rader:
                källa = self.språk_db.execute(
                    """SELECT l.lemma FROM Lexem l JOIN Koncept k ON k.id=l.koncept_id
                       WHERE l.språk = ? AND k.nyckel = ?""",
                    (kurs["källspråk"], r["koncept"])).fetchone()
                ut.append({"kort_id": r["id"], "mål": r["facit"],
                           "källa": källa["lemma"] if källa else None,
                           "ordklass": r["ordklass"], "koncept": r["koncept"]})
            return {"ord": [o for o in ut if o["källa"]], "kvar": kvar,
                    "portion": n}

    def glossvar(self, kurs_id: int, kort_id: int, rätt: bool) -> dict | None:
        """Bokför en glosa. Ett kort, inget meningslogg.

        Går förbi `registrera_mening` med flit: en glosa ÄR ingen mening, och
        att logga en sådan skulle förorena `Mening`-tabellen som nollmodellen
        och budgetmätningen läser. Dygnsregeln gäller ändå — samma kort får
        ett betyg om dagen, och ett fel väger tyngre än ett rätt.
        """
        with self.lås:
            kurs = self._kurs(kurs_id)
            if kurs is None:
                return None
            s = Schemaläggare(self.kort_db)
            nu = time.monotonic()
            förra = self._glosklocka.get(kurs_id)
            self._glosklocka[kurs_id] = nu
            rad = passlager.nuvarande(self.kort_db, kurs_id)
            graderade, fällda = s._redan_idag({kort_id: rätt})
            if (rätt and kort_id in graderade) or (not rätt and kort_id in fällda):
                # REDAN BEDÖMD IDAG (E2) — men glosraden är ändå AVKLARAD.
                # Utan det här ledet stod raden kvar som `väntar` medan
                # betyget vägrades, och drillen delade ut samma ord i
                # evighet: mätt trettio varv i rad med oförändrade tal.
                if rad is not None:
                    passlager.registrera(self.kort_db, rad["id"], {kort_id: rätt})
                return {"bokförd": False, "skäl": "redan bedömd idag"}
            self._byggbarheter.clear()
            s.repetera(kort_id, rätt,
                       millisekunder=None if förra is None
                       else int((nu - förra) * 1000))
            # EN FELSVARAD GLOSA SKA TILLBAKA, precis som ett fällt kort i en
            # mening (B7). `registrera` lägger raden med roll `igen`, och
            # drillen tar den i samma pass.
            if rad is not None:
                passlager.registrera(self.kort_db, rad["id"], {kort_id: rätt})
            self.kort_db.commit()
            return {"bokförd": True}

    def sätt_minuter(self, kurs_id: int, minuter: int) -> dict | None:
        """Hur många minuter om dagen användaren vill öva.

        DET ENDA VALDA TALET i hela arbetsbörderäkningen (B4). Allt annat
        räknas fram ur FSRS intervall eller ur den egna loggen; det här går
        inte att räkna fram, för det är ett faktum om användarens dygn.

        Talet sätter INGET tak på dagens arbete — förfallna kort ska göras,
        hur många de än är (B5). Det styr hur mycket NYTT som förs in, vilket
        är den enda ratt som påverkar framtida arbetsmängd.
        """
        with self.lås:
            if not 1 <= minuter <= 600:
                return None
            n = self.kort_db.execute(
                "UPDATE Kurs SET minuter_per_dag = ? WHERE id = ?",
                (minuter, kurs_id)).rowcount
            if not n:
                return None
            # OCH DAGENS TAK RÄKNAS OM. Taket fryses per dygn för att BRÅDSKA
            # inte ska belönas: svarar man snabbt sjunker sekunder-per-
            # repetition, vilket annars höjde målet mitt i ett pass — mätt
            # växte taket från 50 till 57 under en genomgång.
            #
            # Men ett UTTRYCKLIGT VAL är något annat än en mätning som
            # driver, och frysningen gällde båda. Följden var att ratten inte
            # gjorde något förrän nästa dygn, utan att skärmen sa det. Ratten
            # FUNGERAR — mätt linjärt, 5 min ger 12 nya kort och 40 ger 103 —
            # den syntes bara aldrig.
            # PER MÅLSPRÅK OCH INTE PER KURS. `dagsplan` läser taket med
            # `WHERE målspråk = ?`, alltså den FÖRSTA kursen mot språket —
            # två kurser mot franska delar både kort och tak. Att nollställa
            # på `id` rensade då fel rad, och minutratten syntes inte i den
            # andra kursen. Samma sorts fel som gjorde att en nollställning
            # tömde grannkursens pass: tillstånd per SPRÅK bokfört per KURS.
            self.kort_db.execute(
                "UPDATE Kurs SET tak_datum = NULL WHERE målspråk = ?",
                (self._kurs(kurs_id)["målspråk"],))
            self.kort_db.commit()
            kurs = self._kurs(kurs_id)
            lagt_till = passlager.utöka(self.kort_db, kurs, self._dagsplan(kurs))
            return {"minuter": minuter, "tillagda": lagt_till}

    @staticmethod
    def _igen_efter(g, utfall: dict[int, bool]) -> int:
        """Passkön SOM DEN BLIR när den här meningen bokförts.

        `svara` körs före `bokför`, som är där kön faktiskt uppdateras. Att
        läsa den råa kön gav ett tal som alltid låg en mening efter, vilket
        såg ut som att fel "ibland" inte hamnade i återförsöken.

        Egen metod för att regeln ska gå att BRYTA i `tjänsteprov.py`. En
        invariant som inte går att falsifiera bevisar ingenting.
        """
        fällda = {k for k, v in utfall.items() if not v}
        klarade = {k for k, v in utfall.items() if v}
        return len((g.passkö_ider() | fällda) - klarade)

    @staticmethod
    def _extraläge(p: dict) -> dict:
        """Vad extraövningen har att ta av — noll tills dagen är gjord.

        Att öva extra före de förfallna korten är att välja bort det FSRS
        garanti vilar på, rätt kort i tid, till förmån för tidiga
        repetitioner, som ger mindre (B6).
        """
        # ETT LÅST LÄGE VISAR INGA TAL. `finns` nollades redan, men `nya`
        # och `tidiga` skickades ändå — och ett tal som ingen knapp kan lösa
        # in är precis den sortens indikator som ser sann ut och inte är det.
        # Talen kommer tillbaka i samma sekund som dagen är gjord.
        if not p["klar"]:
            return {"nya": 0, "tidiga": 0, "finns": 0, "låst": True}
        return {"nya": 0, "tidiga": p["tidiga"], "finns": p["tidiga"],
                "låst": False}

    def _glöm(self) -> None:
        """Kasta ALLT härlett tillstånd. Anropas när kortleken bytts ut.

        Nollställningen rensade tidigare bara `_generatorer`, och de andra
        cacharna överlevde med tal från kortleken som just raderats. Mätt:
        efter en nollställning rapporterade byggbarheten 0,113 med NOLL sedda
        kort, så upplåsningsknappen till nivå 2 stod öppen på en kurs där
        användaren inte mött ett enda ord.

        Regeln är enklare än att räkna upp vad som ska rensas: byts kortleken
        ut är ingenting härlett giltigt. En cache som överlever sitt underlag
        är en lögn som håller sig färsk.
        """
        self._generatorer.clear()
        self._byggbarheter.clear()
        self._nästa_nivå_kostnad.clear()
        self._öppna.clear()
        self._pågående.clear()
        self._obokförda.clear()
        self._glosklocka.clear()

    def _dagsplan(self, kurs: sqlite3.Row) -> dict:
        """Dagens PLAN och dagens PASS, i ett svar.

        DE ÄR OLIKA SAKER, och att blanda ihop dem var grundfelet i hela det
        här lagret. `dagsplan` är POLITIK: hur mycket som får göras, räknat
        ur takten, taket och tiden. Den ska räknas om vid varje anrop, för
        den är en styrning som korrigerar sig varje dygn (B2).

        `Pass` är TILLSTÅND: vad dagen faktiskt innehåller. Det bestäms EN
        gång, ur planens tal, och står sedan kvar. Passets siffror vinner
        därför över planens i sammanslagningen nedan — planen säger vad som
        fick tas in, passet vad som är kvar att göra.

        Före uppdelningen räknades innehållet om vid varje anrop, och kunde
        alltså krympa under användaren mitt i ett pass. Tre lager lappar
        hade byggts ovanpå det: ett minne av onåbarhet, en sil på oövade ord
        och en omräkning av taket. Alla tre är borta — passet vet vad det
        innehåller, och det som är onåbart står skrivet i tabellen.
        """
        p = dagsplan(self.kort_db, kurs["målspråk"], kurs["meningar_per_dag"],
                     minuter_per_dag=kurs["minuter_per_dag"])
        # NÅBARHETEN MÄTS BARA NÄR ETT PASS FAKTISKT SKA BYGGAS. Den kostar
        # några hundra renderingar; att göra det vid varje läsning av dagen
        # vore att betala en dagskostnad per knapptryck. Finns passet redan
        # och är helt behövs den inte alls.
        befintligt = passlager.nuvarande(self.kort_db, kurs["id"])
        nåbara = None
        if befintligt is None or passlager.behöver_fyllas(
                self.kort_db, befintligt["id"]):
            g = self._generator(kurs)
            nåbara = lambda dagens_ord: g.nåbara_kort(plus=dagens_ord)  # noqa: E731
        rad = passlager.starta(self.kort_db, kurs, p, nåbara=nåbara)
        return {**p, **passlager.läget(self.kort_db, rad["id"]),
                # Planens tal om NYTT byter namn i stället för att försvinna:
                # `nya` är hädanefter passets kvarvarande, och taket behövs
                # ändå av upplåsningsvyn.
                "tak_nya": p["nya"], "finns_idag": 0,
                # `oövade` FÖRSVINNER UR RÄKNINGEN. Talet fanns för att hålla
                # dagen öppen tills drillade ord mötts i en mening — en
                # konstruktion som behövdes när dagen inte hade något minne.
                # Nu HAR den ett: ordets böjningskort står som `ny` i passet
                # och dagen är inte klar förrän de är gjorda eller avskrivna.
                # Att räkna oövade vid sidan av dem vore att räkna samma
                # arbete två gånger, och det var precis vad som gjorde
                # `att_göra` större än summan av sina delar.
                "oövade": 0}

    def _extrapass(self, kurs: sqlite3.Row):
        """Extrapasset — eget pass, egen kö (B6). None tills dagen är gjord."""
        p = self._dagsplan(kurs)
        if not p["klar"]:
            return None
        plan = dagsplan(self.kort_db, kurs["målspråk"], kurs["meningar_per_dag"],
                        minuter_per_dag=kurs["minuter_per_dag"])
        return passlager.starta(self.kort_db, kurs, plan, läge="extra")

    def _prognos(self, kurs: sqlite3.Row, plan: dict | None = None) -> dict:
        """Hur långt minuterna räcker — i ord och i dagar.

        Räknas ur samma två tal som styr inflödet: den hållbara takten
        (kort per dygn) och hur många kort ett koncept drar med sig. Inget
        nytt antagande tillkommer, och därför kan kurvan inte säga något
        annat än vad systemet faktiskt gör.

        None när takten inte är mätt. En prognos utan mätning vore en
        gissning presenterad som en utfästelse, vilket är värre än tomt.

        `plan` FINNS FÖR ATT DAGEN INTE SKA RÄKNAS TVÅ GÅNGER. `_dagsplan`
        är inte en ren läsning: den anropar `passlager.starta`, alltså kan
        den skapa dagens pass. Anropar man den två gånger i samma svar går
        det bra — `starta` är idempotent — men det är två omgångar arbete
        för samma tal, och `hem` gjorde precis det när prognosen kopplades
        in där.

        Att det märktes alls var passprovets förtjänst. Sabotaget som låter
        `nuvarande` svara None (det gamla lagret, som byggde om passet vid
        varje anrop) fick den andra omgången att krocka med den första på
        `UNIQUE (kurs_id, datum, läge)`. Ett dubbelanrop som bara är
        slöseri i drift blev synligt som ett fel under falsifieringen — och
        det är ungefär vad ett falsifieringspass är till för.
        """
        språk = kurs["målspråk"]
        p = plan if plan is not None else self._dagsplan(kurs)
        takt = p["inflödestak"]
        rad = self.kort_db.execute(
            """SELECT COUNT(DISTINCT koncept) AS koncept, COUNT(*) AS kort,
                      SUM(sedd IS NOT NULL) AS sedda
               FROM Kort WHERE språk = ? AND schemalagt = 1
                 AND koncept IS NOT NULL""", (språk,)).fetchone()
        if not takt or not rad["koncept"]:
            return {"takt": takt, "ord_kvar": None, "dygn_till_klart": None}
        per_koncept = rad["kort"] / rad["koncept"]
        kvar = rad["kort"] - (rad["sedda"] or 0)
        # ORDEN RÄKNAS, DE SKATTAS INTE. Talet var `kvar / per_koncept` —
        # osedda KORT delat på kort-per-koncept — alltså en kvot som SKATTAR
        # hur många ord som återstår. Men frågan har ett exakt svar: ett ord
        # återstår när dess ordkort är osett, och det går att räkna.
        #
        # Skillnaden var synlig för användaren. Mätt 2026-08-26 på tyskan sa
        # kvoten 217 medan glosvyn — som räknar — sa 205, och de stod på var
        # sin skärm under etiketter som båda handlade om ord som återstår.
        # Det är samma sorts fel som `nya − glosor`: en härledning där en
        # räkning fanns att göra.
        #
        # SAMMA FRÅGA SOM `glosor` STÄLLER, ordagrant, så att de två inte kan
        # gå isär. `schemalagt` utelämnas med flit: ett ordkort införs oavsett
        # exponering (INFÖRBAR), så ett ord som lyfts ur schemat återstår
        # fortfarande att lära sig.
        ord_kvar = self.kort_db.execute(
            """SELECT COUNT(*) FROM Kort
               WHERE språk = ? AND typ = 'ord' AND sedd IS NULL""",
            (språk,)).fetchone()[0]
        return {"takt": takt,
                "ord_per_dygn": round(takt / per_koncept, 1),
                "ord_kvar": ord_kvar,
                "dygn_till_klart": math.ceil(kvar / takt)}

    def dagsläge(self, kurs_id: int) -> dict | None:
        """Bara dagens räknare. Övningsskärmens anrop mellan varje mening.

        `hem` räknar också NIVÅN, och den kostar: byggbarheten kräver en kopia
        av inlärardatabasen och tvåhundra renderingar. Cachen töms vid varje
        bokförd mening, så övningsskärmen betalade ~600 ms per mening för ett
        tal den inte visar. Det var fördröjningen mellan meningarna.
        """
        with self.lås:
            kurs = self._kurs(kurs_id)
            if kurs is None:
                return None
            p = self._dagsplan(kurs)
            return {"idag": {"att_göra": p["att_göra"],
                             "förfallna": p["förfallna"], "igen": p["igen"],
                             "nya": p["nya"], "gjort": p["gjort"],
                             "glosor": p["glosor"], "delar": p["delar"],
                             "klar": p["klar"], "finns": p["att_göra"]},
                    "typer": self._per_typ(kurs, p)}

    def _byggbarhet(self, kurs: sqlite3.Row) -> float | None:
        """Nästa nivås byggbarhet, cachad per (språk, nivå, cefr).

        Måttet ändras när användaren lär sig nya ord, så cachen töms vid varje
        bokförd mening — se `bokför`. Att räkna om det för varje hemanrop vore
        en och en halv sekund per sidladdning.
        """
        if kurs["nivå"] >= 21:
            return None
        nyckel = (kurs["målspråk"], kurs["nivå"] + 1, kurs["cefr"])
        if nyckel not in self._byggbarheter:
            self._byggbarheter[nyckel] = kostnad(
                self.kort_db, self.språk_db, kurs["målspråk"],
                kurs["nivå"] + 1, kurs["cefr"])["byggbarhet"]
        return self._byggbarheter[nyckel]

    def _nästa_nivå(self, kurs: sqlite3.Row) -> int | None:
        """Hur många kort nivån efter den här skulle lägga till.

        None på sista nivån — det finns ingen nästa att räkna på.
        """
        if kurs["nivå"] >= 21:
            return None
        nyckel = (kurs["målspråk"], kurs["nivå"] + 1, kurs["cefr"])
        if nyckel not in self._nästa_nivå_kostnad:
            r = kostnad(self.kort_db, self.språk_db, kurs["målspråk"],
                        kurs["nivå"] + 1, kurs["cefr"])
            self._nästa_nivå_kostnad[nyckel] = r["nya_kort"]
        return self._nästa_nivå_kostnad[nyckel]

    def ordlista(self, kurs_id: int) -> list | None:
        with self.lås:
            k = self.kort_db.execute(
                "SELECT målspråk FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            return self.ordbok.lista(k["målspråk"]) if k else None

    def ordet(self, kurs_id: int, koncept: str) -> dict | None:
        with self.lås:
            k = self.kort_db.execute(
                "SELECT målspråk FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            return self.ordbok.ord(k["målspråk"], koncept) if k else None

    def _kurs(self, kurs_id: int):
        return self.kort_db.execute(
            "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()

    def lektionslista(self, kurs_id: int) -> list | None:
        with self.lås:
            k = self._kurs(kurs_id)
            return (self.lektioner.lista(k["målspråk"], k["nivå"], k["cefr"])
                    if k else None)

    def lektionen(self, kurs_id: int, nivå: int) -> dict | None:
        with self.lås:
            k = self._kurs(kurs_id)
            if k is None or not 1 <= nivå <= 21:
                return None
            return self.lektioner.lektion(k["målspråk"], k["källspråk"],
                                          nivå, k["cefr"])

    def nytt_pass(self, kurs_id: int) -> None:
        with self.lås:
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            if kurs:
                self._generator(kurs).nytt_pass()


class Hanterare(BaseHTTPRequestHandler):
    tjänst: Övningstjänst = None  # sätts av starta()

    def log_message(self, *a) -> None:      # tyst — sidan är inte en webbplats
        pass

    def _svara(self, kropp, typ="application/json", kod=200) -> None:
        data = (json.dumps(kropp, ensure_ascii=False).encode()
                if typ == "application/json" else kropp.encode())
        self.send_response(kod)
        self.send_header("Content-Type", f"{typ}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_one_request(self) -> None:
        """Fånga fel och svara i stället för att stänga tyst.

        BaseHTTPRequestHandler låter undantag bubbla, och klienten ser bara
        "empty reply". Under utveckling är det värsta möjliga svar.
        """
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                self._svara({"fel": f"{type(e).__name__}: {e}"}, kod=500)
            except Exception:
                pass

    def do_GET(self) -> None:
        # Avkodas först: rutterna har svenska namn, och varje klient som
        # följer specen skickar "läge" som "l%C3%A4ge".
        väg = unquote(self.path.split("?")[0])
        if väg in ("/", "/index.html"):
            return self._svara(SIDA.read_text(encoding="utf-8"), "text/html")
        if väg == "/api/kurser":
            return self._svara(self.tjänst.kurser())
        if väg == "/api/språk":
            return self._svara(self.tjänst.språk())
        if väg.startswith("/api/lektioner/"):
            l = self.tjänst.lektionslista(int(väg.rsplit("/", 1)[1]))
            return self._svara(l if l is not None else {"fel": "okänd kurs"},
                               kod=200 if l is not None else 404)
        if väg.startswith("/api/lektion/"):
            kurs_id, _, nivå = väg[len("/api/lektion/"):].partition("/")
            d = self.tjänst.lektionen(int(kurs_id), int(nivå))
            return self._svara(d or {"fel": "okänd lektion"}, kod=200 if d else 404)
        if väg.startswith("/api/ordlista/"):
            l = self.tjänst.ordlista(int(väg.rsplit("/", 1)[1]))
            return self._svara(l if l is not None else {"fel": "okänd kurs"},
                               kod=200 if l is not None else 404)
        if väg.startswith("/api/ord/"):
            _, kurs_id, koncept = väg[len("/api/ord/"):].partition("/")[0], *\
                (väg[len("/api/ord/"):].split("/", 1) + [""])[:2]
            d = self.tjänst.ordet(int(kurs_id), koncept)
            return self._svara(d or {"fel": "okänt ord"}, kod=200 if d else 404)
        if väg.startswith("/api/dag/"):
            r = self.tjänst.dagsläge(int(väg.rsplit("/", 1)[1]))
            return self._svara(r or {"fel": "okänd kurs"}, kod=200 if r else 404)
        if väg.startswith("/api/igen/"):
            return self._svara(self.tjänst.igenkön(
                int(väg[len("/api/igen/"):])))
        if väg.startswith("/api/hem/"):
            h = self.tjänst.hem(int(väg.rsplit("/", 1)[1]))
            return self._svara(h or {"fel": "kursen finns inte"},
                               kod=200 if h else 404)
        if väg.startswith("/api/glosor/"):
            g = self.tjänst.glosor(int(väg.rsplit("/", 1)[1]))
            return self._svara(g or {"fel": "okänd kurs"}, kod=200 if g else 404)
        if väg.startswith("/api/nytt-pass/"):
            self.tjänst.nytt_pass(int(väg.rsplit("/", 1)[1]))
            return self._svara({"ok": True})
        if väg.startswith("/api/uppgift/"):
            extra = "extra=1" in self.path.partition("?")[2]
            u = self.tjänst.uppgift(int(väg.rsplit("/", 1)[1]), extra=extra)
            # Tom kö är ett svar (200, `tomt`); att sökningen misslyckades är
            # ett fel (503). De såg likadana ut förut och gav samma text.
            return self._svara(u or {"fel": "ingen mening gick att bygga"},
                               kod=200 if u else 503)
        self._svara({"fel": "okänd väg"}, kod=404)

    def do_POST(self) -> None:
        väg = unquote(self.path.split("?")[0])
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if väg == "/api/svar":
            r = self.tjänst.svara(int(data.get("id", 0)), data.get("svar", ""))
            return self._svara(r or {"fel": "uppgiften finns inte"},
                               kod=200 if r else 410)
        if väg == "/api/glossvar":
            r = self.tjänst.glossvar(int(data.get("kurs", 0)),
                                     int(data.get("kort_id", 0)),
                                     bool(data.get("rätt")))
            return self._svara(r or {"fel": "okänd kurs"}, kod=200 if r else 404)
        if väg == "/api/självrätta":
            r = self.tjänst.självrätta(
                int(data.get("id", 0)), hela=bool(data.get("hela")),
                kort_id=data.get("kort_id"))
            return self._svara(r or {"fel": "meningen är redan bokförd"},
                               kod=200 if r else 410)
        if väg == "/api/bokför":
            r = self.tjänst.bokför(int(data.get("id", 0)))
            return self._svara(r or {"bokförd": False})
        if väg == "/api/kurs":
            r = self.tjänst.ny_kurs(data.get("källspråk", ""),
                                    data.get("målspråk", ""))
            return self._svara(r or {"fel": "ogiltigt språkpar"},
                               kod=200 if r else 400)
        if väg.startswith("/api/välj/"):
            r = self.tjänst.välj(int(väg.rsplit("/", 1)[1]))
            return self._svara(r or {"fel": "okänd kurs"}, kod=200 if r else 404)
        if väg.startswith("/api/minuter/"):
            r = self.tjänst.sätt_minuter(int(väg.rsplit("/", 1)[1]),
                                         int(data.get("minuter", 0)))
            return self._svara(r or {"fel": "ogiltigt värde"},
                               kod=200 if r else 400)
        if väg.startswith("/api/lås-upp/"):
            r = self.tjänst.lås_upp(int(väg.rsplit("/", 1)[1]))
            return self._svara(r or {"fel": "kan inte låsa upp"},
                               kod=200 if r else 400)
        if väg.startswith("/api/nollställ/"):
            r = self.tjänst.nollställ(int(väg.rsplit("/", 1)[1]),
                                      data.get("bekräftelse", ""))
            return self._svara(r or {"fel": "bekräftelsen saknas"},
                               kod=200 if r else 400)
        self._svara({"fel": "okänd väg"}, kod=404)


def starta(port: int = 8765, *, kandidater: int = 800,
           kort_sökväg=None) -> None:
    # Anslutningarna delas mellan trådar och serialiseras av tjänstens lås.
    kort_db = anslut_kort(kort_sökväg, delad_mellan_trådar=True)
    språk_db = anslut(delad_mellan_trådar=True)
    språk_db.row_factory = sqlite3.Row
    Hanterare.tjänst = Övningstjänst(kort_db, språk_db, kandidater=kandidater)
    # Bara loopback. Inlärardatabasen är personlig och servern har ingen
    # autentisering; att lyssna brett vore att dela den med nätverket.
    server = ThreadingHTTPServer(("127.0.0.1", port), Hanterare)
    print(f"Övning på http://127.0.0.1:{port}   (avsluta med Ctrl-C)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAvslutad.")
