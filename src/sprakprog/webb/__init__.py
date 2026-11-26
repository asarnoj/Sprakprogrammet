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
from ..kort import anslut_kort, upplåsningsläge
from ..kort.db import STANDARD_KORT_DB

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
        self._nästa = 1

    def kurser(self) -> list[dict]:
        return [dict(r) for r in self.kort_db.execute(
            "SELECT * FROM Kurs ORDER BY målspråk")]

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
            return {"kurs": dict(kurs), "rader": rader, "summa": summa,
                    "nivå": kurs["nivå"], "nivåer": 21,
                    "krävs": u["krävs"], "kapacitet": u["kapacitet"],
                    "plats": u["klar"], "kort": u["totalt"]}

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
            idag = datetime.now(UTC).date().isoformat()
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
        if self.path != "/api/svar":
            return self._svara({"fel": "okänd väg"}, kod=404)
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        r = self.tjänst.svara(int(data.get("id", 0)), data.get("svar", ""))
        self._svara(r or {"fel": "uppgiften finns inte"}, kod=200 if r else 410)


def starta(port: int = 8765, *, kandidater: int = 800) -> None:
    # Anslutningarna delas mellan trådar och serialiseras av tjänstens lås.
    kort_db = anslut_kort(delad_mellan_trådar=True)
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
