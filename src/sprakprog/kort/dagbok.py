"""Dagbok över varje ställd mening — situationen, inte bara utfallet.

VARFÖR DEN LIGGER I EN FIL OCH INTE I `kort.db`. Julius nollställer kursen
vid varje test, och `nollställ` bygger om kortleken från grunden. Kort-id:n
återanvänds för andra kort, och `Spår`-raderna pekar då på kort som inte
finns: en felsökning dagen efter läste `(kort borta)` på var och en. Ett
forensiskt spår som raderas av nästa RESET är inget spår.

Filen är därför **självbärande**: varje rad bär kortets nyckel, typ, facit
och hela dess tillstånd före och efter, så raden går att läsa utan att
databasen som skapade den finns kvar.

SYFTET STYR FORMEN. Julius: *"kunna kolla tillbaka och se exakt när det har
skett fel beslut i rättning sortering eller något annat. Så att jag slipper
återberätta."* Det ställer tre krav som en vanlig logg inte uppfyller:

    fullständighet   varje kort meningen rörde, inte bara de som fick betyg
    före OCH efter   ett felaktigt beslut syns i övergången, inte i utfallet
    härkomst         VARFÖR kortet var med — planerat, förfallet, eller med
                     på köpet

Den tredje är den som fällde flest fel hittills. Ett kort kan finnas i en
mening på fem sätt med helt olika innebörd, och utan `härkomst` går de inte
att skilja i efterhand.

DET SÄRSKILT VAKTADE FALLET, som Julius bad om uttryckligen: *"Var noggrann
med att se att korten faktiskt är aktiverade så att vi inte missar att ett
kort egentligen inte har introducerats (detta händer ibland)."* Fältet
`oanmäld` är sant när ett kort både saknar `sedd` och saknar passrad —
alltså kom in i meningen utan att någon planerat att införa det. Det är C5:s
läcka och den har täppts tre gånger; raden gör en fjärde gång synlig direkt.

Formatet är JSONL, en rad per mening, en fil per kurs och dygn. Rader läggs
bara till, aldrig ändras: en dagbok som skrivs om är inget vittne.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

#: Var dagböckerna hamnar. Rot bestäms av anroparen i drift; förvalet är
#: projektroten, samma katalog som `kort.db`.
KATALOG = Path(__file__).resolve().parents[3] / "loggar"


def fil_för(katalog: Path, kurs_id: int, språk: str, nu: datetime) -> Path:
    """En fil per kurs och DYGN, namngiven så att den går att hitta för hand."""
    return katalog / f"{nu.date().isoformat()}-{språk}-kurs{kurs_id}.jsonl"


def _kortrad(rad: sqlite3.Row) -> dict:
    """Kortets tillstånd, de fält FSRS och schemaläggningen faktiskt läser."""
    return {"sedd": rad["sedd"], "förfaller": rad["förfaller"],
            "stabilitet": rad["stabilitet"], "svårighet": rad["svårighet"],
            "tillstånd": rad["tillstånd"], "antal": rad["antal"],
            "fall": rad["fall"], "schemalagt": rad["schemalagt"]}


def _hämta(kort_db: sqlite3.Connection, idn: set[int]) -> dict[int, sqlite3.Row]:
    if not idn:
        return {}
    platser = ",".join("?" * len(idn))
    return {r["id"]: r for r in kort_db.execute(
        f"SELECT * FROM Kort WHERE id IN ({platser})", tuple(idn))}


def _passrader(kort_db: sqlite3.Connection, pass_id: int | None,
               idn: set[int]) -> dict[int, list[sqlite3.Row]]:
    """Kortets rader i DAGENS pass — rollen och statusen de har just nu."""
    if pass_id is None or not idn:
        return {}
    platser = ",".join("?" * len(idn))
    ut: dict[int, list] = {}
    for r in kort_db.execute(
            f"""SELECT kort_id, roll, status FROM Passkort
                WHERE pass_id = ? AND kort_id IN ({platser})
                ORDER BY ordning, id""", (pass_id, *idn)):
        ut.setdefault(r["kort_id"], []).append(dict(r))
    return ut


def _ordet_sett(kort_db: sqlite3.Connection,
                kort: dict[int, sqlite3.Row]) -> dict[int, bool | None]:
    """Är ORDET bakom kortet infört? None när kortet inte hör till ett ord.

    DET ÄR DEN RIKTIGA FRÅGAN, och min första version ställde en annan. Jag
    flaggade varje kort som saknade `sedd` och passrad — men ett
    ordföljdskort införs aldrig i glosläget och står aldrig i passet, så
    larmet tjöt på var tredje mening. Ett larm som alltid tjuter är sämre än
    inget: det lär läsaren att bläddra förbi.

    Regeln som faktiskt gäller är A4:s: ett böjningskort får inte mötas före
    sitt ord. Den frågan har ett svar för alla korttyper som HAR ett ord,
    och `None` för dem som inte har det.
    """
    behöver = {(r["språk"], r["koncept"], r["variant"])
               for r in kort.values() if r["koncept"]}
    if not behöver:
        return {k: None for k in kort}
    sett: dict[tuple, bool] = {}
    for språk, koncept, variant in behöver:
        rad = kort_db.execute(
            """SELECT sedd FROM Kort WHERE språk = ? AND koncept = ?
               AND typ = 'ord' AND variant IS ?""",
            (språk, koncept, variant)).fetchone()
        sett[(språk, koncept, variant)] = (
            None if rad is None else rad["sedd"] is not None)
    return {k: (sett.get((r["språk"], r["koncept"], r["variant"]))
                if r["koncept"] else None)
            for k, r in kort.items()}


def före(kort_db: sqlite3.Connection, pass_id: int | None,
         idn: set[int]) -> dict:
    """Ögonblicksbild INNAN bokföringen. Måste tas före `registrera`."""
    kort = _hämta(kort_db, idn)
    pass_ = _passrader(kort_db, pass_id, idn)
    ordet = _ordet_sett(kort_db, kort)
    return {"kort": {k: _kortrad(v) for k, v in kort.items()},
            "fast": {k: {"nyckel": v["nyckel"], "typ": v["typ"],
                         "koncept": v["koncept"], "variant": v["variant"],
                         "facit": v["facit"], "ordklass": v["ordklass"],
                         "klass": v["klass"], "cell": v["cell"],
                         "egenskap": v["egenskap"]}
                     for k, v in kort.items()},
            "pass": pass_, "ordet_sett": ordet}


def _härkomst(passrader: list | None, snapshot: dict | None) -> str:
    """VARFÖR kortet var med i meningen. Se modulens docstring.

    Ordningen är avsiktlig: en passrad säger vad dagen PLANERADE, och den
    vinner över kortets eget tillstånd. Ett kort utan passrad är med på
    köpet, och då är frågan i stället om det ens var infört.
    """
    if passrader:
        return passrader[0]["roll"]          # ny · glosa · förfallen · igen
    if snapshot is None:
        return "okänd"
    # `medföljande-ny` OCH INTE `oanmäld`: ordet `oanmäld` är reserverat för
    # det smalare fältet med samma namn, och två namn för olika saker i
    # samma rad är precis vad en dagbok inte får ha.
    return "medföljande" if snapshot["sedd"] else "medföljande-ny"


def _hamnade(efter: dict | None, betyg: int | None, skäl: str | None,
             passrader_efter: list | None, läge: str | None) -> str:
    """Var kortet tog vägen. Ett ord, för att raderna ska gå att sortera.

    ETT OBOKFÖRT KORT SÄGER VARFÖR. Att bara skriva "obedömd" gör de fem
    orsakerna omöjliga att skilja i efterhand, och det är precis vad
    dagboken finns för att inte göra: `redan_bedömd` (E2) är ett riktigt
    beslut, `undanhållen` (D3) är ett medgivande om okunskap, och `skyddad`
    (A4/E5) är ett tredje. De ser likadana ut i kortets tillstånd.
    """
    if efter is None:
        return "borta"
    if passrader_efter and any(p["status"] == "onåbar" for p in passrader_efter):
        return "onåbar"
    if betyg is None:
        return f"obokförd:{skäl or läge or 'okänd'}"
    if passrader_efter and any(p["roll"] == "igen" for p in passrader_efter):
        return "again"
    if efter["sedd"] is None:
        return "ny"
    return "schemalagd"


def rad(*, nu: datetime, kurs: sqlite3.Row, pass_rad: sqlite3.Row | None,
        förslag, svar: str, korrekt: bool, utfall: dict[int, bool],
        lägen: dict[int, str], anmärkningar: list,
        ögonblick: dict, kort_db: sqlite3.Connection,
        mening_id: int | None, dagsläge: dict | None = None,
        millisekunder: int | None = None) -> dict:
    """Hela situationen kring EN mening, som en självbärande post."""
    from .schemalaggning import spec_json
    spec = json.loads(spec_json(förslag.mening))
    idn = set(ögonblick["fast"])
    efter_kort = _hämta(kort_db, idn)
    pass_id = pass_rad["id"] if pass_rad is not None else None
    pass_efter = _passrader(kort_db, pass_id, idn)

    # Betygen som faktiskt skrevs för PRECIS den här meningen. Läses ur
    # `Repetition` och inte ur `utfall`: `utfall` är rättningens dom, men
    # vad som BOKFÖRDES avgörs av E2, skyddet och undanhållandet — och det
    # är skillnaden mellan dem som felsökningen handlar om.
    betyg: dict[int, sqlite3.Row] = {}
    if mening_id is not None:
        betyg = {r["kort_id"]: r for r in kort_db.execute(
            "SELECT * FROM Repetition WHERE mening_id = ?", (mening_id,))}

    kort = []
    for kid in sorted(idn):
        f = ögonblick["fast"][kid]
        f_före = ögonblick["kort"].get(kid)
        f_efter = _kortrad(efter_kort[kid]) if kid in efter_kort else None
        b = betyg.get(kid)
        p_före = ögonblick["pass"].get(kid)
        kort.append({
            **f,
            "id": kid,
            "härkomst": _härkomst(p_före, f_före),
            "planerad": bool(p_före),
            "passroller": p_före or [],
            # Julius uttryckliga krav: gick kortet att möta ÖVERHUVUDTAGET?
            "introducerad": bool(f_före and f_före["sedd"]),
            "aktiverad": bool(f_före and (f_före["schemalagt"]
                                          or f["typ"] == "ord")),
            # Är ORDET bakom kortet infört? None = kortet hör inte till ett.
            "ordet_infört": ögonblick.get("ordet_sett", {}).get(kid),
            # DE TVÅ FEL SOM FAKTISKT KAN HÄNDA, och inga andra:
            #   ett ORDKORT som kom in genom en mening i stället för glosan
            #   ett BÖJNINGSKORT som möttes före sitt ord (A4)
            "oanmäld": bool(
                f_före and not f_före["sedd"] and not p_före
                and f["typ"] == "ord"),
            "före_sitt_ord": (f["typ"] != "ord"
                              and ögonblick.get("ordet_sett", {}).get(kid)
                              is False),
            "dom": utfall.get(kid),
            "läge": lägen.get(kid),
            "betyg": b["betyg"] if b else None,
            "skäl": b["skäl"] if b else None,
            "r_före": b["r_före"] if b else None,
            "bokförd": b is not None and b["betyg"] is not None,
            "före": f_före,
            "efter": f_efter,
            "hamnade": _hamnade(f_efter, b["betyg"] if b else None,
                                b["skäl"] if b else None, pass_efter.get(kid),
                                lägen.get(kid)),
        })

    return {
        "tid": nu.isoformat(),
        "mening_id": mening_id,
        "kurs": {"id": kurs["id"], "käll": kurs["källspråk"],
                 "mål": kurs["målspråk"], "nivå": kurs["nivå"],
                 "cefr": kurs["cefr"]},
        "pass": ({"id": pass_rad["id"], "datum": pass_rad["datum"],
                  "läge": pass_rad["läge"]} if pass_rad is not None else None),
        "uppgift": förslag.uppgift,
        "facit": förslag.text,
        "svar": svar,
        "korrekt": korrekt,
        "millisekunder": millisekunder,
        # VARFÖR just den här meningen valdes. Utan det går ett dåligt val
        # inte att skilja från ett dåligt utfall.
        "urval": {"nödfall": getattr(förslag, "nödfall", None),
                  "reserv_släppt": getattr(förslag, "reserv_släppt", None),
                  "poäng": (dict(förslag.poäng.delar)
                            if getattr(förslag, "poäng", None) else None),
                  "förväntat": (round(förslag.poäng.förväntat, 3)
                                if getattr(förslag, "poäng", None) else None)},
        "dagsläge": dagsläge,
        # SPECEN, alltså vad meningen skulle UTTRYCKA. Utan den går det inte
        # att avgöra om renderaren gjorde rätt — bara om texten ser rimlig ut.
        "spec": spec,
        "anmärkningar": anmärkningar,
        "kort": kort,
    }


def skriv(post: dict, katalog: Path | None = None) -> Path:
    """Lägg posten sist i dygnets fil. Skapar katalogen vid behov."""
    katalog = katalog or KATALOG
    katalog.mkdir(parents=True, exist_ok=True)
    nu = datetime.fromisoformat(post["tid"])
    sökväg = fil_för(katalog, post["kurs"]["id"], post["kurs"]["mål"], nu)
    with sökväg.open("a", encoding="utf-8") as f:
        f.write(json.dumps(post, ensure_ascii=False) + "\n")
    return sökväg


def läs(sökväg: Path) -> list[dict]:
    """Alla poster i en dagbok, i den ordning de skrevs."""
    if not sökväg.exists():
        return []
    return [json.loads(r) for r in
            sökväg.read_text(encoding="utf-8").splitlines() if r.strip()]


def dagböcker(katalog: Path | None = None) -> list[Path]:
    """Alla dagböcker, nyast sist."""
    katalog = katalog or KATALOG
    return sorted(katalog.glob("*.jsonl")) if katalog.exists() else []


def nu_utc() -> datetime:
    return datetime.now(UTC)
