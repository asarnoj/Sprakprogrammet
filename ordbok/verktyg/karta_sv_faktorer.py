"""Mätning 2: blir träden små om satsen delas i sina frasfunktioner?

Varje del utforskas för sig, med de andra delarna ersatta av stubbar. Stubbar
som påverkar ordföljden (verbfrasens längd, om ett reflexivt pronomen finns)
förgrenar på just det, och inget annat.
"""
from __future__ import annotations

import sqlite3
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import karta_sv as K                                              # noqa: E402

from sprakprog.rendering import sv as svmod                       # noqa: E402
from sprakprog.rendering.sv import SvenskRenderare                # noqa: E402
from sprakprog.rendering.uppslag import Uppslag                   # noqa: E402

conn = sqlite3.connect(K.DB)
verklig = Uppslag(conn, "sv")


def med_patchar(kör):
    def inre(o):
        svmod.tilltal, svmod.replace = K.lat_tilltal(o), K.lat_replace(o)
        poster = []
        r = K.renderare(o, poster, conn, verklig)
        kör(o, r, poster)
        return poster
    return inre


def verbfras(o, r, poster):
    SvenskRenderare.verbfras(r, K.ny(K.LatMening, o, "m", 0))


def ordföljd(o, r, poster):
    def verb_stubb(m):
        poster.append(("VERB",))
        return o.välj("verbfrasens längd", [["<v>"], ["<v1>", "<v2>"]])
    r.verbfras = verb_stubb
    r.reflexivpronomen = lambda m: o.välj("reflexiv finns", [None, "<refl>"])
    for namn in ("predikativ", "komplement"):
        setattr(r, namn, (lambda n: lambda m: (poster.append((n.upper(),)),
                                                ["<x>"])[1])(namn))
    r.adverbial = lambda a: (poster.append(("ADVERBIAL",)), ["<adv>"])[1]
    SvenskRenderare.satsled(r, K.ny(K.LatMening, o, "m", 0), bisats=False)


def ordföljd_bisats(o, r, poster):
    def verb_stubb(m):
        poster.append(("VERB",))
        return o.välj("verbfrasens längd", [["<v>"], ["<v1>", "<v2>"]])
    r.verbfras = verb_stubb
    r.reflexivpronomen = lambda m: o.välj("reflexiv finns", [None, "<refl>"])
    for namn in ("predikativ", "komplement"):
        setattr(r, namn, (lambda n: lambda m: (poster.append((n.upper(),)),
                                                ["<x>"])[1])(namn))
    r.adverbial = lambda a: (poster.append(("ADVERBIAL",)), ["<adv>"])[1]
    SvenskRenderare.satsled(r, K.ny(K.LatMening, o, "s", 1), bisats=True)


def predikativ(o, r, poster):
    val = o.välj("predikativets sort",
                 ["$predadj:m", K.ny(K.LatNF, o, "m.predikativ", 0)])
    SvenskRenderare.predikativ(r, K.ny(K.LatMening, o, "m", 0, predikativ=val))


def komplement(o, r, poster):
    SvenskRenderare.komplement(
        r, K.ny(K.LatMening, o, "m", 0, komplement="$kompl:m"))


def adverbial(o, r, poster):
    a = o.välj("adverbialets sort",
               ["$adv:m", K.ny(K.LatPrep, o, "m.adv", 0),
                K.ny(K.LatBisats, o, "m.adv", 1)])
    SvenskRenderare.adverbial(r, a)


def main():
    delar = [("verbfras", verbfras), ("ordföljd huvudsats", ordföljd),
             ("ordföljd bisats", ordföljd_bisats), ("predikativ", predikativ),
             ("komplement", komplement), ("adverbial", adverbial)]
    for namn, f in delar:
        kör = med_patchar(f)
        lyckade, vägrade, djup = K.uppskatta(kör, 5000)
        t = time.perf_counter()
        blad, vägrar, krascher, utfall = K.utforska(kör, tak=2_000_000)
        dt = time.perf_counter() - t
        print(f"{namn:20} skattat ≈{lyckade:>10,.0f}  uttömmande: löv {blad:>7} "
              f"vägrar {vägrar:>6} olika utfall {len(utfall):>5}  "
              f"längsta väg {djup:>2} val  {dt:5.1f} s", flush=True)
        for k, n in krascher.most_common(3):
            print(f"    KRASCH ×{n}: {k}", flush=True)


if __name__ == "__main__":
    main()
