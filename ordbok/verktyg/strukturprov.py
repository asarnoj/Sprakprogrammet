"""Strukturkontrollerna som ett nät — de fel som syns UTAN att kunna språket.

`granska-meningar --struktur` byggdes för att köras som ett regressionstest
och stod ändå utanför sviten. Det här nätet kör den, över hela svepkorpusen
och över de meningar som faktiskt ställts.

VARFÖR DEN HÖR HEMMA HÄR. Julius invändning: *"Det är inte svårt att fixa en
bugg MEN det är svårt att verifiera vad som är trasigt. Jag kan inte
verifiera eftersom det tar för mycket tid och eftersom jag inte är expert på
grammatik."* De här kontrollerna kräver ingen expert och ingen modell — de
läser strukturen, inte språket:

    saknat_led        renderingen kraschade, eller gav färre än två led
    överflödigt_led   samma ord två gånger i rad
    lexikalt          en intern nyckel läckte ut som ett ord
    kongruens         TVÅ OLIKA SPECAR RENDERAR IDENTISKT

Den sista är den starkaste, och den går inte att se genom att läsa en mening
i taget: skiljer sig specarna men inte texten har renderaren tappat en
distinktion. Singular och plural som blir samma sträng betyder att numerus
inte realiseras — ett fel som annars bara märks när någon råkar bli rättad
fel på det.

MODELLGRANSKNINGEN ÄR EN ANNAN SAK och kan inte ligga här: den ringer ut till
en språkmodell, kostar pengar och tid, och kräver ett vanligt terminalfönster
(se `_vägra_i_claude_code`). Den körs för hand med `ordbok granska-meningar
--svep` respektive `--logg`. Det här nätet är den del som får vara gratis.
"""

from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.db import anslut                                    # noqa: E402
from sprakprog.generering.meningsgranskning import (               # noqa: E402
    korpus_ur_loggen, korpus_ur_svep, strukturkontroller,
)
from sprakprog.kort.db import STANDARD_KORT_DB                     # noqa: E402


def _falsifiering(poster) -> list[str]:
    """Varje kontroll ska gå att fälla. Ett nät som inte kan fälla är inget nät.

    Sabotaget är data och inte en kodändring: en mening som BÄR felet matas in,
    och kontrollen ska hitta den. Går den förbi är kontrollen stum.
    """
    from sprakprog.generering.meningsgranskning import Post
    fel = []
    prov = [
        ("saknat_led",      Post("sabotage", "fr", "KRASCH: inget att rendera", "{}")),
        ("överflödigt_led", Post("sabotage", "de", "Sie sie sie liest.", "{}")),
        ("lexikalt",        Post("sabotage", "en", "She reads pers_flicka.", "{}")),
    ]
    for väntad, post in prov:
        funna = {f["feltyp"] for f in strukturkontroller([post])}
        if väntad not in funna:
            fel.append(f"sabotaget {väntad!r} gick förbi — kontrollen är stum")
    # Två specar, en text: kongruenskontrollen ska säga ifrån.
    par = [Post("sab_sg", "sv", "Hon läser.", '{"numerus": "sg"}'),
           Post("sab_pl", "sv", "Hon läser.", '{"numerus": "pl"}')]
    if "kongruens" not in {f["feltyp"] for f in strukturkontroller(par)}:
        fel.append("sabotaget 'kongruens' gick förbi — kontrollen är stum")
    return fel


def main() -> int:
    print("strukturkontroller — fel som syns utan att kunna språket\n")
    språk_db = anslut()
    poster = list(korpus_ur_svep(språk_db))
    källa = ["svepkorpusen"]
    if STANDARD_KORT_DB.exists():
        # ENDAST LÄSNING, och inte via `anslut_kort`. Den kör migrationer och
        # skriver alltså till inlärardatabasen — ett prov får aldrig röra
        # användarens kurs, allra minst för att läsa ur den.
        kort_db = sqlite3.connect(f"file:{STANDARD_KORT_DB}?mode=ro", uri=True)
        kort_db.row_factory = sqlite3.Row
        ställda = list(korpus_ur_loggen(kort_db))
        poster += ställda
        källa.append(f"{len(ställda)} ställda meningar")
        kort_db.close()

    fynd = strukturkontroller(poster)
    print(f"  {len(poster)} meningar ({', '.join(källa)})")
    if fynd:
        for typ, n in Counter(f["feltyp"] for f in fynd).most_common():
            print(f"    ✗ {typ:<18} {n}")
        for f in fynd[:12]:
            print(f"        [{f['språk']}] {f['text'][:44]:<44} {f['motivering'][:52]}")
        if len(fynd) > 12:
            print(f"        … och {len(fynd) - 12} till")
    else:
        print("    ✓ inga strukturfel")

    print("\nfalsifiering — varje kontroll ska gå att fälla:")
    stumma = _falsifiering(poster)
    for s in stumma:
        print(f"    ✗ {s}")
    if not stumma:
        print("    ✓ alla fyra kontrollerna fäller sitt sabotage")

    print(f"\n{len(fynd)} strukturfynd, {len(stumma)} stumma kontroller.")
    return 1 if fynd or stumma else 0


if __name__ == "__main__":
    raise SystemExit(main())
