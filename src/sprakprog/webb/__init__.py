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
import sqlite3
import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from ..db import anslut
from ..generator import Generator
from ..kort import anslut_kort, befolka, upplåsningsläge
from ..kort.db import STANDARD_KORT_DB
from .lektion import Lektioner
from .ordbok import Ordbok

SIDA = Path(__file__).parent / "sida.html"


def _dygnets_början() -> str:
    """När det nuvarande dygnet började, som UTC-tidsstämpel.

    LOKAL midnatt, inte UTC. UTC-midnatt är 02:00 i Sverige, så ett pass
    klockan 00:30 skulle räknas till gårdagen — vilket är fel för den som
    övar. Gränsen härleds ur systemets tidszon och innehåller därför inget
    valt tal.

    (Anki lägger gränsen några timmar efter midnatt, för att ett sent pass
    ska höra till kvällen man började. Det är en inställning och inte en
    härledning, och den läggs till om användningen visar att den behövs.)
    """
    lokal = datetime.now().astimezone()
    midnatt = lokal.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnatt.astimezone(UTC).isoformat()


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
        self._nästa = 1
        self.ordbok = Ordbok(språk_db, kort_db)
        self.lektioner = Lektioner(språk_db, kort_db)

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
        """Kurserna, den senast öppnade först."""
        return [dict(r) | {"källnamn": self.SPRÅKNAMN.get(r["källspråk"], ""),
                           "målnamn": self.SPRÅKNAMN.get(r["målspråk"], "")}
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
            ny = kurs["nivå"] + 1
            self.kort_db.execute("UPDATE Kurs SET nivå = ? WHERE id = ?",
                                 (ny, kurs_id))
            self.kort_db.commit()
            r = befolka(self.kort_db, self.språk_db, {kurs["målspråk"]},
                        nivå=ny, cefr=kurs["cefr"])
            # Generatorn cachas per (källa, mål, nivå, budget) — den gamla
            # är låst vid förra nivån och måste kastas.
            self._generatorer.clear()
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
            self._generatorer.clear()
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

    def uppgift(self, kurs_id: int) -> dict | None:
        with self.lås:
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            if kurs is None:
                return None
            g = self._generator(kurs)
            f = g.föreslå(kandidater=self.kandidater)
            if f is None:
                return None
            id_ = self._nästa
            self._nästa += 1
            self._öppna[id_] = (kurs["id"], f)
            return {"id": id_, "uppgift": f.uppgift, "källspråk": kurs["källspråk"],
                    "målspråk": kurs["målspråk"], "kort": len(f.kort),
                    "nya": f.poäng.nya, "förväntat": round(f.poäng.förväntat, 2)}

    def svara(self, id_: int, svar: str) -> dict | None:
        with self.lås:
            post = self._öppna.pop(id_, None)
            if post is None:
                return None
            kurs_id, f = post
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            g = self._generator(kurs)
            r = g.svara(f, svar)
            return {"korrekt": r.korrekt, "facit": f.text, "igen": g.passkö(),
                    "anmärkningar": [{"skrev": a.skrev, "väntat": a.väntat,
                                      "slutsats": a.slutsats, "osäker": a.osäker}
                                     for a in r.anmärkningar]}

    #: Korttyperna som de heter för en inlärare. Ordningen är den kort
    #: introduceras i (Schemaläggare.INTRODUKTIONSORDNING) — den är
    #: pedagogisk och inte alfabetisk: ordet först, ändelsen sedan.
    TYPNAMN = (("ord", "Words"), ("egenskap", "Properties"), ("stam", "Stems"),
               ("form", "Irregular forms"), ("system", "Endings"),
               ("rektion", "Government"), ("ordföljd", "Word order"))

    def hem(self, kurs_id: int) -> dict | None:
        """Allt hemvyn behöver: räknarna per korttyp, nivån, kapaciteten."""
        with self.lås:
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            if kurs is None:
                return None
            språk, nu = kurs["målspråk"], datetime.now(UTC).isoformat()
            # Passkön ligger i generatorn och bara om ett pass har börjat.
            g = self._generatorer.get(
                (kurs["källspråk"], språk, kurs["nivå"], kurs["budget"]))
            igen = set(g._passkö) if g else set()
            per_typ = {t: {"nya": 0, "förfallna": 0, "igen": 0}
                       for t, _ in self.TYPNAMN}
            for r in self.kort_db.execute(
                    """SELECT id, typ, sedd, förfaller FROM Kort
                       WHERE språk = ? AND schemalagt = 1""", (språk,)):
                rad = per_typ.get(r["typ"])
                if rad is None:
                    continue
                if r["id"] in igen:
                    rad["igen"] += 1
                elif r["sedd"] is None:
                    rad["nya"] += 1
                elif r["förfaller"] and r["förfaller"] <= nu:
                    rad["förfallna"] += 1
            rader = [{"typ": t, "namn": namn, **per_typ[t]}
                     for t, namn in self.TYPNAMN if any(per_typ[t].values())]
            summa = {k: sum(r[k] for r in rader)
                     for k in ("nya", "förfallna", "igen")}
            u = upplåsningsläge(self.kort_db, språk, kurs["meningar_per_dag"])
            idag = self.kort_db.execute(
                "SELECT COUNT(*) FROM Mening WHERE språk = ? AND tidpunkt >= ?",
                (språk, _dygnets_början())).fetchone()[0]
            return {"kurs": dict(kurs), "rader": rader, "summa": summa,
                    "idag": idag, "mål": kurs["meningar_per_dag"],
                    "nästa_ord": self._nästa_ord(språk),
                    "nivå": kurs["nivå"], "nivåer": 21,
                    "krävs": u["krävs"], "kapacitet": u["kapacitet"],
                    "plats": u["klar"], "kort": u["totalt"]}

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

    def _nästa_ord(self, språk: str, antal: int = 8) -> list[dict]:
        """Orden som står näst på tur, med de former kursen når just nu.

        Julius: "det borde vara en bild med de nästkommande upplåsta orden som
        man snabbt kan få en överblick över, samt deras böjningar." Ordningen
        är schemaläggarens INTRODUKTIONSORDNING — ordet först, sedan dess
        former — så listan är inte en gissning utan exakt vad som kommer.
        """
        sedda = {r[0] for r in self.kort_db.execute(
            "SELECT DISTINCT koncept FROM Kort WHERE språk=? AND sedd IS NOT NULL",
            (språk,))}
        ut: list[dict] = []
        for r in self.kort_db.execute(
                """SELECT koncept, ordklass FROM Kort
                   WHERE språk = ? AND typ = 'ord' AND sedd IS NULL
                     AND schemalagt = 1 AND koncept IS NOT NULL
                   ORDER BY räckvidd DESC, id""", (språk,)):
            if r["koncept"] in sedda:
                continue
            lemma = self.språk_db.execute(
                """SELECT l.lemma FROM Lexem l JOIN Koncept k ON k.id=l.koncept_id
                   WHERE l.språk = ? AND k.nyckel = ?""",
                (språk, r["koncept"])).fetchone()
            if lemma is None:
                continue
            former = [x[0] for x in self.kort_db.execute(
                """SELECT DISTINCT c.cell FROM Cellkort c
                   WHERE c.språk = ? AND c.koncept = ? ORDER BY c.cell""",
                (språk, r["koncept"]))]
            ut.append({"koncept": r["koncept"], "lemma": lemma["lemma"],
                       "ordklass": r["ordklass"] or "", "former": len(former)})
            if len(ut) >= antal:
                break
        return ut

    def nytt_pass(self, kurs_id: int) -> None:
        with self.lås:
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            if kurs:
                self._generator(kurs).nytt_pass()

    def läge(self, kurs_id: int) -> dict:
        with self.lås:
            kurs = self.kort_db.execute(
                "SELECT * FROM Kurs WHERE id = ?", (kurs_id,)).fetchone()
            idag = _dygnets_början()
            rad = self.kort_db.execute(
                """SELECT COUNT(*) AS meningar,
                          COALESCE(SUM(fel), 0) AS fel,
                          COALESCE(SUM(förväntat), 0) AS förväntat
                   FROM Mening WHERE språk = ? AND tidpunkt >= ?""",
                (kurs["målspråk"], idag)).fetchone()
            u = upplåsningsläge(self.kort_db, kurs["målspråk"],
                                kurs["meningar_per_dag"])
            return {"idag": rad["meningar"], "mål": kurs["meningar_per_dag"],
                    "fel": rad["fel"], "förväntat": round(rad["förväntat"], 1),
                    "nivå": kurs["nivå"], "kort": u["totalt"],
                    "osedda": u["osedda"], "krävs": u["krävs"],
                    "kapacitet": u["kapacitet"], "plats": u["klar"]}


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
        if väg.startswith("/api/hem/"):
            h = self.tjänst.hem(int(väg.rsplit("/", 1)[1]))
            return self._svara(h or {"fel": "kursen finns inte"},
                               kod=200 if h else 404)
        if väg.startswith("/api/nytt-pass/"):
            self.tjänst.nytt_pass(int(väg.rsplit("/", 1)[1]))
            return self._svara({"ok": True})
        if väg.startswith("/api/läge/"):
            return self._svara(self.tjänst.läge(int(väg.rsplit("/", 1)[1])))
        if väg.startswith("/api/uppgift/"):
            u = self.tjänst.uppgift(int(väg.rsplit("/", 1)[1]))
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
        if väg == "/api/kurs":
            r = self.tjänst.ny_kurs(data.get("källspråk", ""),
                                    data.get("målspråk", ""))
            return self._svara(r or {"fel": "ogiltigt språkpar"},
                               kod=200 if r else 400)
        if väg.startswith("/api/välj/"):
            r = self.tjänst.välj(int(väg.rsplit("/", 1)[1]))
            return self._svara(r or {"fel": "okänd kurs"}, kod=200 if r else 404)
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
