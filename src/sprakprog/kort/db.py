"""Anslutning till inlärardatabasen.

Egen fil, eget schema, ingen delad anslutning med sprak.db. Att hålla dem
isär är hela poängen — se kort.sql.
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

PROJEKTROT = Path(__file__).resolve().parents[3]
KORTSCHEMA = PROJEKTROT / "kort.sql"
STANDARD_KORT_DB = PROJEKTROT / "kort.db"
SÄKERHETSKOPIOR = PROJEKTROT / "säkerhetskopior"

#: Så många dagliga kopior som sparas.
#:
#: Talet är inte hämtat ur luften utan ur projektets egen historia: den
#: längsta TYSTA felfunktionen hittills var `Cellkort`-tömningen, som gick
#: oupptäckt i en månad. En kortare fönstring hade inte hjälpt då. Trettio
#: kopior à ~1,6 MB är omkring 50 MB, vilket är billigt mot att förlora
#: repetitionshistoriken.
KOPIOR_ATT_SPARA = 30


#: Kolumner som tillkommit efter att schemat först skrevs, som (tabell, namn,
#: definition). Inlärardatabasen kan aldrig byggas om — den innehåller
#: repetitionshistoriken — så schemaändringar måste vara ADDITIVA och gå att
#: köra om. Därför bara nya kolumner med förvalt värde, aldrig ändrade eller
#: borttagna. Behövs något annat är det en riktig migrering med datakopiering,
#: och den ska skrivas för hand och köras medvetet.
TILLÄGG = (
    ("Repetition", "r_före", "REAL"),
    ("Mening", "sedda", "INTEGER"),
    ("Mening", "nya", "INTEGER"),
    ("Kurs", "cefr", "TEXT NOT NULL DEFAULT 'C2'"),
    ("Kurs", "senast_öppnad", "TEXT"),
    # Tidsloggningen. Rena tillägg, så de hör hemma här — till skillnad från
    # `Repetition.skäl`, som krävde att NOT NULL lättades på `betyg` och
    # därför måste vara en handkörd tabellombyggnad
    # (`ordbok/migrationer/kort_betyglos_rad.sql`).
    ("Mening", "millisekunder", "INTEGER"),
    ("Repetition", "millisekunder", "INTEGER"),
    # B4: användarens val är MINUTER, inte meningar.
    #
    # `meningar_per_dag` stod kvar här med motiveringen "en kolumn som ingen
    # längre läser skadar ingen". Den var fel: `exponeringsgräns` läste den,
    # och talet 20 avgjorde i en månad vilka kort som fick spacing. Kolumnen
    # är borta sedan 2026-09-04 — se `kurs_utan_meningar_per_dag.sql`.
    ("Kurs", "minuter_per_dag", "INTEGER NOT NULL DEFAULT 20"),
    # Dagens tilldelning, BESLUTAD en gång per dygn. Se `dagsplan`.
    ("Kurs", "tak_datum", "TEXT"),
    ("Kurs", "tak_kort", "INTEGER"),
)


def säkerhetskopiera(conn: sqlite3.Connection, *, katalog: Path | None = None,
                     idag: date | None = None) -> Path | None:
    """En kopia per dygn, verifierad, med de äldsta gallrade.

    VARFÖR INTE `cp`. Databasen körs i WAL-läge: skrivningar hamnar i
    `kort.db-wal` och flyttas till huvudfilen först vid en checkpoint. En
    kopia gjord med cp, Finder eller rsync tappar allt som ligger där — och
    det är precis det NYASTE, alltså det dyraste att förlora. Mätt vid
    upptäckten: 129 repetitioner med WAL, 108 utan. Kopian öppnas utan fel
    och ser fullt frisk ut; ingenting säger ifrån. `Connection.backup` läser
    genom WAL och är därför det enda rätta sättet.

    KOPIAN VERIFIERAS INNAN DEN FÅR STÅ KVAR. En trasig säkerhetskopia är
    värre än ingen, eftersom den ger falsk trygghet — samma feltyp som resten
    av det här projektet handlar om. Både `integrity_check` och radantalen
    prövas, och håller de inte tas filen bort igen.

    ETT MISSLYCKANDE FÅR ALDRIG HINDRA ANVÄNDNING. Full disk ska inte låsa
    användaren ute ur sitt eget program. Men det får inte heller ske TYST:
    varningen går till stderr.
    """
    katalog = katalog or SÄKERHETSKOPIOR
    mål = katalog / f"kort.db.{(idag or date.today()).isoformat()}"
    if mål.exists():
        return mål                      # dygnets kopia är redan tagen
    try:
        katalog.mkdir(exist_ok=True)
        ut = sqlite3.connect(mål)
        with ut:
            conn.backup(ut)
        tabeller = [r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")]
        if ut.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise sqlite3.DatabaseError("integritetskontrollen underkände kopian")
        for tabell in tabeller:
            a = conn.execute(f"SELECT COUNT(*) FROM {tabell}").fetchone()[0]
            b = ut.execute(f"SELECT COUNT(*) FROM {tabell}").fetchone()[0]
            if a != b:
                raise sqlite3.DatabaseError(
                    f"{tabell}: {a} rader i original, {b} i kopia")
        ut.close()
    except Exception as fel:              # noqa: BLE001 — se docstringen
        mål.unlink(missing_ok=True)
        print(f"VARNING: säkerhetskopian misslyckades ({fel}). "
              f"Inlärardatabasen är oskyddad idag.", file=sys.stderr)
        return None
    # GALLRINGEN RÖR BARA DE DAGLIGA KOPIORNA. Mönstret är avsiktligt strikt:
    # `kort.db.20*` hade också matchat `kort.db.2026-08-24.före-nollställning`,
    # alltså precis den kopia som aldrig får försvinna. Namngivna kopior —
    # före en migrering, före en nollställning — gallras aldrig automatiskt.
    dagliga = sorted(katalog.glob("kort.db.20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]"))
    for gammal in dagliga[:-KOPIOR_ATT_SPARA]:
        gammal.unlink(missing_ok=True)
    return mål


#: Tabeller som skapas om de saknas. Skilt från `TILLÄGG`, som lägger till
#: KOLUMNER: en ny tabell kan skrivas som ren SQL och behöver ingen
#: kolumninspektion. `CREATE TABLE IF NOT EXISTS` gör steget idempotent.
NYA_TABELLER = ("pass.sql", "spar.sql")

#: Tabellombyggnader — SQL som bara ska köras EN gång, och som därför måste
#: kunna se om den redan är gjord. SQLite kan inte ändra en främmandenyckel
#: med ALTER, så en ändrad regel kräver en ny tabell och en kopiering.
#: Villkoret läser SCHEMAT och inte en versionsräknare: det som avgör om
#: migreringen behövs är hur tabellen ser ut, inte vad någon skrivit ner.
#:
#: VILLKORET LÄSER SCHEMATS INNEBÖRD, INTE DESS TEXT. Det gjorde det inte
#: förut, och det var en riktig defekt: mönstret `sql LIKE
#: '%ON DELETE CASCADE%kort_id%'` matchade `pass_id`-radens CASCADE följd av
#: ordet `kort_id` längre ner, och det gör den FÄRDIGMIGRERADE tabellen
#: också. Villkoret var därmed sant för alltid, och `anslut_kort` körde
#: DROP TABLE Passkort plus en kopiering — med `foreign_keys = OFF` — vid
#: VARJE anslutning. Mätt: tabellens rootpage flyttade sig på varenda
#: uppkoppling (398 → 367 → 394 → 391), alltså byggdes användarens pass om
#: varje gång programmet startade.
#:
#: `pragma_foreign_key_list` svarar på den faktiska frågan — vilken
#: ON DELETE-regel `kort_id` har — och kan inte råka matcha en annan kolumns
#: regel. En textmatchning på ett schema är en gissning; det här är en
#: avläsning.
OMBYGGNADER = (
    ("passkort_bevara_bevis.sql",
     """SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'Passkort'
          AND EXISTS (SELECT 1 FROM pragma_foreign_key_list('Passkort')
                      WHERE "table" = 'Kort' AND "from" = 'kort_id'
                        AND "on_delete" <> 'SET NULL')"""),
    # FEMTE ROLLEN. CHECK-villkor går inte att ändra med ALTER i SQLite, så
    # tabellen byggs om. Villkoret läses ur `sql` och inte ur en versionsrad:
    # frågan "tillåter tabellen rollen" besvaras då av tabellen själv.
    ("passkort_overvakad.sql",
     """SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'Passkort'
          AND sql NOT LIKE '%övervakad%'"""),
    # Kolumnen som ingen satte men som styrde vilka kort som schemalades.
    # Måste ligga i OMBYGGNADER och inte bara som en borttagen TILLÄGG-rad:
    # en befintlig databas har kolumnen kvar tills något faktiskt släpper den.
    ("kurs_utan_meningar_per_dag.sql",
     """SELECT 1 FROM pragma_table_info('Kurs')
        WHERE name = 'meningar_per_dag'"""),
)


def _migrera(conn: sqlite3.Connection) -> None:
    from pathlib import Path as _P
    katalog = _P(__file__).resolve().parents[3] / "ordbok" / "migrationer"
    for fil in NYA_TABELLER:
        sökväg = katalog / fil
        if sökväg.exists():
            conn.executescript(sökväg.read_text(encoding="utf-8"))
            conn.commit()
    for fil, behövs in OMBYGGNADER:
        sökväg = katalog / fil
        if sökväg.exists() and conn.execute(behövs).fetchone():
            # Kaskaden måste vara AV under ombyggnaden, annars river
            # `DROP TABLE` de rader som just kopierats.
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.executescript(sökväg.read_text(encoding="utf-8"))
            conn.commit()
            conn.execute("PRAGMA foreign_keys = ON")
    for tabell, kolumn, definition in TILLÄGG:
        if not conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (tabell,)).fetchone():
            continue
        finns = {r["name"] for r in conn.execute(f"PRAGMA table_info({tabell})")}
        if kolumn not in finns:
            conn.execute(f"ALTER TABLE {tabell} ADD COLUMN {kolumn} {definition}")
            conn.commit()


def anslut_kort(sökväg: Path | None = None, *,
                delad_mellan_trådar: bool = False) -> sqlite3.Connection:
    """Se `sprakprog.db.anslut` för vad `delad_mellan_trådar` innebär."""
    conn = sqlite3.connect(sökväg or STANDARD_KORT_DB, timeout=60,
                           check_same_thread=not delad_mellan_trådar)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 60000")
    _migrera(conn)
    # BARA DEN RIKTIGA DATABASEN. Prov och tillfälliga kopior öppnas ofta och
    # ska inte fylla katalogen; det är repetitionshistoriken som är
    # oersättlig, inte en testfil.
    if Path(sökväg or STANDARD_KORT_DB) == STANDARD_KORT_DB:
        säkerhetskopiera(conn)
    return conn


def skapa_kortdatabas(sökväg: Path | None = None) -> sqlite3.Connection:
    """Ny, tom inlärardatabas. Raderar en befintlig fil.

    Anroparen ansvarar för att fråga användaren först — det här kastar bort
    repetitionshistorik, det enda i systemet som inte går att återskapa.
    """
    mål = sökväg or STANDARD_KORT_DB
    # DEN FARLIGASTE FUNKTIONEN I KODBASEN. Kopian tas FÖRE raderingen och
    # under dagens datum plus en räknare, så att den inte skriver över en
    # kopia som redan finns — annars vore skyddet borta just när det behövs.
    if mål.exists() and Path(mål) == STANDARD_KORT_DB:
        conn = sqlite3.connect(mål)
        conn.row_factory = sqlite3.Row
        SÄKERHETSKOPIOR.mkdir(exist_ok=True)
        n = 0
        while (SÄKERHETSKOPIOR / f"kort.db.{date.today()}.före-nollställning{n or ''}").exists():
            n += 1
        kopia = SÄKERHETSKOPIOR / f"kort.db.{date.today()}.före-nollställning{n or ''}"
        ut = sqlite3.connect(kopia)
        with ut:
            conn.backup(ut)
        ut.close(); conn.close()
        print(f"Säkerhetskopia före nollställning: {kopia}", file=sys.stderr)
    mål.unlink(missing_ok=True)
    Path(str(mål) + "-wal").unlink(missing_ok=True)
    Path(str(mål) + "-shm").unlink(missing_ok=True)
    conn = anslut_kort(mål)
    conn.executescript(KORTSCHEMA.read_text(encoding="utf-8"))
    conn.commit()
    return conn
