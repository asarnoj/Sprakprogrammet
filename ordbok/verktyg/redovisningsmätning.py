"""Steg 1:s prov: håller attributionen när varje beslut redovisas?

KÄRNAN 9: «När renderarna redovisar går det att mäta hur många regler en mening
faktiskt använder, och alltså om attributionen fungerar.» Verktyget spårar en
fast mängd meningar (samma specar som `renderarfacit.py`) och mäter:

  kort per mening       ordkort och formkort per ord, plus varje beslut som syns
  täthet                hur många kort som delar varje plats (ord eller lucka)
  högst samtidigt svaga det största antal kort i meningen som kan vara svaga
                        samtidigt utan att två delar plats (KÄRNAN 6.2) — ett
                        ord och dess formkort får dela
  förväxlingsbara       beslut vars alternativ ger exakt samma mening som ett
                        annat besluts alternativ; ett fel där går inte att knyta
                        till ett enda kort (villkor 7 i KÄRNAN 6.1)
  kortbestånd           hur många olika regelkort meningarna rör

Kör:  python ordbok/verktyg/redovisningsmätning.py sv [ANTAL]
"""
from __future__ import annotations

import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from renderarfacit import specar                                    # noqa: E402
from sprakprog.rendering import RENDERARE, RenderingsFel, spåra    # noqa: E402


def kort_i(ut) -> list[tuple[tuple, frozenset, tuple | None]]:
    """(kort, platser, undantaget) för varje kort i meningen.

    Undantaget är ordkortet ett formkort får dela plats med.
    """
    ut_kort = []
    for i, o in enumerate(ut.ord):
        ord_kort = ("ord", o.koncept)
        ut_kort.append((ord_kort, frozenset({("ord", i)}), None))
        ut_kort.append((("form", o.koncept, o.cell), frozenset({("ord", i)}),
                        ord_kort))
    for b in ut.beslut:
        if not b.syns:
            continue
        if b.sort in ("regel",):
            nyckel = ("regel", b.id[2], b.utfall)
        elif b.sort == "ordning":
            nyckel = ("ordning", b.id[2])
        else:
            nyckel = (b.sort, *b.id[2:-1], b.utfall)
        platser = {("ord", i) for i in b.positioner} | {("lucka", g) for g in b.luckor}
        ut_kort.append((nyckel, frozenset(platser), None))
    return ut_kort


def högst_samtidigt_svaga(kort) -> int:
    """Största mängd kort utan två som delar plats (ord och eget formkort undantagna)."""
    n = len(kort)
    krock = [0] * n
    for a in range(n):
        for b in range(a + 1, n):
            ka, pa, ua = kort[a]
            kb, pb, ub = kort[b]
            if pa & pb and not (ua == kb or ub == ka):
                krock[a] |= 1 << b
                krock[b] |= 1 << a
    bäst = 0

    def sök(kvar: int, storlek: int) -> None:
        nonlocal bäst
        if kvar == 0:
            bäst = max(bäst, storlek)
            return
        if storlek + bin(kvar).count("1") <= bäst:
            return
        v = (kvar & -kvar).bit_length() - 1
        sök(kvar & ~(1 << v) & ~krock[v], storlek + 1)
        sök(kvar & ~(1 << v), storlek)

    sök((1 << n) - 1, 0)
    return bäst


def main() -> None:
    språk = sys.argv[1]
    antal = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    conn = sqlite3.connect(ROT / "sprak.db")
    renderare = RENDERARE[språk](conn)
    t = time.perf_counter()
    s = Counter()
    fördelning = {"ord": Counter(), "kort": Counter(), "svaga": Counter(),
                  "täthet": Counter()}
    regelkort: Counter = Counter()
    förväxlade: Counter = Counter()
    for m in specar(conn, språk):
        if s["meningar"] >= antal:
            break
        try:
            ut = spåra(renderare, m)
        except RenderingsFel:
            continue
        s["meningar"] += 1
        kort = kort_i(ut)
        s["ord"] += len(ut.ord)
        s["kort"] += len(kort)
        fördelning["ord"][len(ut.ord)] += 1
        fördelning["kort"][len(kort)] += 1
        platser = Counter(p for _, ps, _ in kort for p in ps)
        for antal_kort in platser.values():
            fördelning["täthet"][antal_kort] += 1
        svaga = högst_samtidigt_svaga(kort)
        s["högst samtidigt svaga"] += svaga
        fördelning["svaga"][svaga] += 1
        for nyckel, _, _ in kort:
            if nyckel[0] in ("regel", "ordning", "rektion"):
                regelkort[nyckel] += 1
            elif nyckel[0] == "egenskap":
                regelkort[("egenskap", nyckel[2])] += 1
        # Förväxlingsbara: samma alternativa mening från två olika beslut.
        # Ett alternativ som ger samma text som meningen själv visar bara att
        # beslutet inte syns just där ("trasiga" är både plural och svag form),
        # och räknas inte.
        texter: dict[tuple, set] = {}
        for b in ut.beslut:
            if not b.syns or b.sort == "ordning":
                continue
            for utfall, alt in b.alternativ.items():
                if tuple(alt) != tuple(ut.ord):
                    texter.setdefault(tuple(alt), set()).add((b.id, utfall))
        for b in ut.beslut:
            if not b.syns or b.sort == "ordning":
                continue
            s["beslut som syns"] += 1
            if any(len({x[0] for x in texter[tuple(alt)]}) > 1
                   for alt in b.alternativ.values() if tuple(alt) != tuple(ut.ord)):
                s["förväxlingsbara beslut"] += 1
                förväxlade[(b.sort, b.id[2])] += 1
    dt = time.perf_counter() - t
    n = s["meningar"]
    print(f"{språk}: {n} meningar spårade på {dt:.1f} s\n")
    print(f"  ord per mening                 {s['ord'] / n:5.1f}")
    print(f"  kort per mening                {s['kort'] / n:5.1f}")
    print(f"  högst samtidigt svaga kort     {s['högst samtidigt svaga'] / n:5.1f}")
    print(f"  förväxlingsbara beslut         {s['förväxlingsbara beslut']} av "
          f"{s['beslut som syns']} "
          f"({100 * s['förväxlingsbara beslut'] / max(1, s['beslut som syns']):.1f} %)")
    for namn in ("svaga", "täthet"):
        rad = "  ".join(f"{k}:{v}" for k, v in sorted(fördelning[namn].items()))
        print(f"\n  fördelning {namn}: {rad}")
    typer = Counter(k[0] for k in regelkort)
    print(f"\n  olika regelkort som rörs: {dict(typer)}")
    for k, v in regelkort.most_common():
        if k[0] in ("regel", "ordning", "rektion"):
            print(f"    {v:>6}  {' · '.join(map(str, k))}")
    if förväxlade:
        print("\n  förväxlingsbara, per beslut:")
        for k, v in förväxlade.most_common(15):
            print(f"    {v:>6}  {' · '.join(map(str, k))}")


if __name__ == "__main__":
    main()
