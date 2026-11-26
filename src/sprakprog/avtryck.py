"""Avtryck av det artefakterna byggs ur — KÄRNAN 3.10.

> Kontrollen körs varje gång något kan ha ändrats. Ett infört kort kan bli
> oprövbart på två sätt: ett nytt kort införs, eller koden eller datan ändras —
> en ny renderare, en rättad böjning. När en ny version tas i bruk kontrolleras
> alla införda kort innan passet startar.

FELET SOM GAV DEN HÄR FILEN. Kartan (`kartor/en.pkl`) var byggd 2026-09-20
00:16 och `sprak.db` ändrad 23:29 samma dygn, alltså tjugotre timmar senare,
plus två ändringar i renderaren dagen därpå. Ingenting sa det. Kraven (4.2) är
lästa ur kartan, så de beskrev meningar grammatiken inte längre byggde: elva av
dag fyras trettiotvå köade kort hade ett falskt krav, grinden (4.4) släppte upp
dem ändå, och passet betalade en uttömmande nej-sökning för var och en — sex
sekunder med bara kravet tillåtet, 82 med de sjuttio införda, 821 med dagens
valda inräknade. Dag fyras plan blev aldrig klar.

Ett avtryck kostar en tiondels sekund att räkna och gör felet omöjligt att inte
märka: artefakten bär avtrycket av sina källor, och passet vägrar starta när de
inte stämmer.

VAD SOM RÄKNAS MED är grammatiken och koden som bygger meningar ur den:
`sprak.db` och renderaren. Sammansättningen och nivåbygget läser bara kartan och
databasen; ändras de utan att något annat gör det ändras inte vad som går att
bygga. Att ta med hela `src/` skulle göra varje ändring var som helst till en
timmes ombyggnad, och det gör avtrycket till något man stänger av.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]

#: Renderarens filer. Kartan går igenom varje del av dem uttömmande (6.7), så en
#: ändring här kan ändra vad kartan innehåller.
RENDERING = ROT / "src" / "sprakprog" / "rendering"


def _kort(data: bytes) -> str:
    """Sexton tecken sha256. Tillräckligt för att skilja versioner åt, kort nog
    att läsa i ett felmeddelande."""
    return hashlib.sha256(data).hexdigest()[:16]


def avtryck(rot: Path | None = None) -> dict[str, str]:
    """Grammatikens och renderarens avtryck, som artefakterna bär med sig."""
    rot = rot or ROT
    filer = sorted((rot / "src" / "sprakprog" / "rendering").glob("*.py"))
    kod = b"".join(f.read_bytes() for f in filer)
    return {"sprak.db": _kort((rot / "sprak.db").read_bytes()),
            "renderare": _kort(kod)}


def skiljer(sparat: dict | None, nu: dict[str, str]) -> list[str]:
    """Vilka källor som inte stämmer. Tom lista betyder att artefakten gäller."""
    if not sparat:
        return ["inget avtryck alls — artefakten är byggd före avtrycken fanns"]
    return [f"{namn}: byggd ur {sparat.get(namn, '—')}, nu {värde}"
            for namn, värde in nu.items() if sparat.get(namn) != värde]
