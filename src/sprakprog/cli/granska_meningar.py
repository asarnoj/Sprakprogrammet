"""ordbok granska-meningar — läs igenom renderade meningar och rapportera fel.

Exempel:
  ordbok granska-meningar --struktur                    # utan modell
  ordbok granska-meningar --svep --språk fr
  ordbok granska-meningar --logg --språk de --fortsätt
  ordbok granska-meningar --sammanställ                 # rapporten som arbetslista

Granskningen ändrar aldrig databasen — den skriver en TSV med anmärkningar.
Att tillämpa dem är ett separat beslut, samma regel som `granska-former`.

`--struktur` kör kontrollerna som klarar sig utan modell och returnerar 1 när
den hittar något, så att den går att köra som ett regressionstest.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from ..db import anslut
from ..generering.meningsgranskning import (
    RAPPORT_KOLUMNER, STANDARD_MODELL, bygg_prompt, korpus_ur_loggen,
    korpus_ur_svep, parsa_svar, sammanställ, strukturkontroller,
    _vägra_i_claude_code,
)
from ..kort.db import anslut_kort

STANDARD_RAPPORT = "ordbok/meningsgranskning.tsv"

#: Meningar per anrop. Fler ger färre anrop men gör ett parsfel dyrare, och
#: granskaren tappar noggrannhet på långa listor. Samma storleksordning som
#: formgranskningens batchar.
BATCH = 25


def lägg_till_argument(p: argparse.ArgumentParser) -> None:
    källa = p.add_mutually_exclusive_group()
    källa.add_argument("--logg", action="store_true",
                       help="Granska meningar som FAKTISKT ställts (kort.db)")
    källa.add_argument("--svep", action="store_true",
                       help="Granska den designade korpusen, 57 konstruktioner")
    källa.add_argument("--struktur", action="store_true",
                       help="Bara kontrollerna som inte behöver någon modell")
    källa.add_argument("--sammanställ", action="store_true",
                       help="Visa rapporten som en arbetslista")
    p.add_argument("--språk", help="Begränsa till ett språk")
    p.add_argument("--gräns", type=int, help="Högst så här många meningar")
    p.add_argument("--rapport", default=STANDARD_RAPPORT)
    p.add_argument("--modell", default=STANDARD_MODELL)
    p.add_argument("--fortsätt", action="store_true",
                   help="Hoppa över källor som redan står i rapporten")
    p.add_argument("--verbose", action="store_true")


def _skriv(rapport: Path, rader: list[dict], nytt: bool) -> None:
    rapport.parent.mkdir(parents=True, exist_ok=True)
    with rapport.open("a" if not nytt else "w", newline="",
                      encoding="utf-8") as f:
        s = csv.writer(f, delimiter="\t", lineterminator="\n")
        if nytt:
            s.writerow(RAPPORT_KOLUMNER)
        for r in rader:
            s.writerow([str(r.get(k, "")).replace("\t", " ")
                        for k in RAPPORT_KOLUMNER])


def kör(args: argparse.Namespace) -> int:
    rapport = Path(args.rapport)

    if args.sammanställ:
        print(sammanställ(rapport))
        return 0

    poster = []
    if args.logg or args.struktur:
        poster += korpus_ur_loggen(anslut_kort(), args.språk, args.gräns)
    if args.svep or args.struktur:
        poster += korpus_ur_svep(anslut(), args.språk)
    if not poster:
        print("ingen korpus vald — se --logg, --svep, --struktur", file=sys.stderr)
        return 2

    if args.struktur:
        fynd = strukturkontroller(poster)
        for f in fynd:
            print(f"{f['språk']}  {f['feltyp']:16s} {f['text'][:44]!r}\n"
                  f"      {f['motivering']}")
        print(f"\n{len(poster)} meningar, {len(fynd)} strukturfynd")
        # Returnerar 1 vid fynd, så att den går att köra som regressionstest.
        return 1 if fynd else 0

    # ── modellgranskningen ───────────────────────────────────────────
    if (v := _vägra_i_claude_code()):
        print(v, file=sys.stderr)
        return 2
    import subprocess

    redan: set[str] = set()
    if args.fortsätt and rapport.exists():
        redan = {r.split("\t")[0] for r in
                 rapport.read_text(encoding="utf-8").splitlines()[1:] if r}
    poster = [p for p in poster if p.källa not in redan]

    # STRUKTURFYNDEN SKRIVS FÖRST, gratis och utan modell. En mening som
    # redan fallit på dem behöver ingen granskare.
    nytt = not (args.fortsätt and rapport.exists())
    fynd = strukturkontroller(poster)
    if fynd:
        _skriv(rapport, fynd, nytt)
        nytt = False

    per_språk: dict[str, list] = {}
    for p in poster:
        per_språk.setdefault(p.språk, []).append(p)

    totalt = 0
    for språk, grupp in sorted(per_språk.items()):
        for i in range(0, len(grupp), BATCH):
            batch = grupp[i:i + BATCH]
            if args.verbose:
                print(f"{språk}: {i + 1}–{i + len(batch)} av {len(grupp)}",
                      file=sys.stderr)
            svar = subprocess.run(
                ["claude", "--model", args.modell, "-p",
                 bygg_prompt(batch, språk)],
                capture_output=True, text=True, timeout=600)
            if svar.returncode:
                print(f"  anropet misslyckades: {svar.stderr[:200]}",
                      file=sys.stderr)
                continue
            try:
                rader = parsa_svar(svar.stdout, batch)
            except ValueError as e:
                print(f"  kunde inte tolka svaret: {e}", file=sys.stderr)
                continue
            _skriv(rapport, rader, nytt)
            nytt = False
            totalt += len(rader)

    print(f"{len(poster)} meningar granskade, "
          f"{totalt + len(fynd)} anmärkningar → {rapport}")
    print(sammanställ(rapport))
    return 0
