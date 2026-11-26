"""Prototyp för kartan (KÄRNAN 6.7), mätt 2026-09-13.

Mätning: hur stort är den svenska renderarens beslutsträd?

Renderaren körs med ett orakel som svarar på varje läsning av specen eller
lexikonet. Varje körning följer en väg genom trädet; nästa körning byter det
sista valet som har alternativ kvar (uttömmande djupet-först). Antalet
körningar är antalet löv.

Nominalfraser och bisatser utforskas som egna delar (faktorer): i satsens
träd ersätts de av en stubb som bara noterar att de finns.

Förenklingar i prototypen (inte i en riktig karta):
- en symbolisk forms cell antas finnas (form() förgrenar inte på datahål)
- identitetsjämförelser mot bestämda koncept (tilltal, reflexivpronomen)
  är lagade till orakelval
- tupler (attribut, adverbial) har längd högst 1
"""
from __future__ import annotations

import sqlite3
import sys
import time
from collections import Counter

ROT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.rendering import spec as S
from sprakprog.rendering import sv as svmod
from sprakprog.rendering.spec import RenderingsFel
from sprakprog.rendering.sv import SvenskRenderare
from sprakprog.rendering.uppslag import Uppslag

DB = str(ROT / "sprak.db")


class Orakel:
    def __init__(self, prefix):
        self.prefix = prefix
        self.valda = []          # (nyckel, antal alternativ, valt index)
        self.minne = {}

    def välj(self, nyckel, domän):
        if nyckel in self.minne:
            return self.minne[nyckel]
        i = len(self.valda)
        idx = self.prefix[i] if i < len(self.prefix) else 0
        self.valda.append((nyckel, len(domän), idx))
        v = domän[idx]
        self.minne[nyckel] = v
        return v


class SlumpOrakel:
    """Knuths skattare: slumpa en väg, vikten är produkten av grenantalen."""

    def __init__(self, rng):
        self.rng, self.vikt, self.minne, self.valda = rng, 1, {}, []

    def välj(self, nyckel, domän):
        if nyckel in self.minne:
            return self.minne[nyckel]
        self.vikt *= len(domän)
        v = domän[self.rng.randrange(len(domän))]
        self.minne[nyckel] = v
        self.valda.append(nyckel)
        return v


def uppskatta(kör, n, frö=1):
    import random
    rng = random.Random(frö)
    lyckade = vägrade = 0.0
    djup = 0
    for _ in range(n):
        o = SlumpOrakel(rng)
        try:
            kör(o)
            lyckade += o.vikt
        except RenderingsFel:
            vägrade += o.vikt
        except Exception:                                       # noqa: BLE001
            vägrade += o.vikt
        djup = max(djup, len(o.valda))
    return lyckade / n, vägrade / n, djup


def utforska(kör, tak=None, rapport=None):
    prefix, blad, vägrar, krascher = [], 0, 0, Counter()
    utfall = Counter()
    t0 = time.perf_counter()
    while True:
        if tak is not None and blad + vägrar >= tak:
            print(f"    tak nått vid {blad + vägrar} körningar", flush=True)
            break
        if rapport and (blad + vägrar) % rapport == 0 and blad + vägrar:
            dt = time.perf_counter() - t0
            print(f"    … {blad} löv, {vägrar} vägrar, {len(utfall)} utfall, "
                  f"{dt:.0f} s", flush=True)
        o = Orakel(prefix)
        try:
            poster = kör(o)
            blad += 1
            utfall[tuple(sorted(set(poster)))] += 1
        except RenderingsFel:
            vägrar += 1
        except Exception as e:                                  # noqa: BLE001
            krascher[f"{type(e).__name__}: {e}"[:90]] += 1
        v = o.valda
        j = len(v) - 1
        while j >= 0 and v[j][2] + 1 >= v[j][1]:
            j -= 1
        if j < 0:
            break
        prefix = [x[2] for x in v[:j]] + [v[j][2] + 1]
    return blad, vägrar, krascher, utfall


# ── lata spec-objekt ────────────────────────────────────────────────────

def _o(self):
    return object.__getattribute__(self, "_o")


def _p(self):
    return object.__getattribute__(self, "_p")


def ny(klass, o, p, djup, **över):
    x = object.__new__(klass)
    object.__setattr__(x, "_o", o)
    object.__setattr__(x, "_p", p)
    object.__setattr__(x, "_d", djup)
    object.__setattr__(x, "_över", över)
    return x


MENING_FÄLT = {"verb", "subjekt", "objekt", "io", "predikativ", "adverbial",
               "komplement", "grad", "jämförelse", "diates", "fråga",
               "negerad", "tid", "aspekt", "bisats", "fråga_om", "modus"}


class LatMening(S.Mening):
    __slots__ = ("_o", "_p", "_d", "_över")

    def __getattribute__(self, namn):
        if namn not in MENING_FÄLT:
            return object.__getattribute__(self, namn)
        över = object.__getattribute__(self, "_över")
        if namn in över:
            return över[namn]
        o, p, d = _o(self), _p(self), object.__getattribute__(self, "_d")
        q = f"{p}.{namn}"
        dom = {
            "verb": [f"$verb:{p}"],
            "subjekt": [ny(LatNF, o, f"{q}", d)],
            "objekt": [None, ny(LatNF, o, q, d)],
            "io": [None, ny(LatNF, o, q, d)],
            "predikativ": [None, f"$predadj:{p}", ny(LatNF, o, q, d)],
            "adverbial": ([(), (f"$adv:{p}",), (ny(LatPrep, o, q, d),),
                           (ny(LatBisats, o, q, d + 1),)] if d == 0 else
                          [(), (f"$adv:{p}",), (ny(LatPrep, o, q, d),)]),
            "komplement": [None, f"$kompl:{p}"],
            "grad": list(S.Grad),
            "jämförelse": [None, ny(LatNF, o, q, d)],
            "diates": list(S.Diates),
            "fråga": [False, True],
            "negerad": [False, True],
            "tid": list(S.Tidsreferens),
            "aspekt": list(S.Aspekt),
            "bisats": [None, ny(LatBisats, o, q, d + 1)] if d == 0 else [None],
            "fråga_om": [None, "subjekt", "objekt", "io", f"$frågadv:{p}"],
            "modus": list(S.Satsmodus),
        }[namn]
        return o.välj(q, dom)


NF_FÄLT = {"koncept", "bestämdhet", "numerus", "attribut", "possessiv",
           "possessiv_koreferent", "referent", "frågedeterminant", "ägare"}


class LatNF(S.Nominalfras):
    __slots__ = ("_o", "_p", "_d", "_över")

    def __getattribute__(self, namn):
        if namn not in NF_FÄLT:
            return object.__getattribute__(self, namn)
        o, p, d = _o(self), _p(self), object.__getattribute__(self, "_d")
        q = f"{p}.{namn}"
        dom = {
            "koncept": [f"$nf:{p}"],
            "bestämdhet": list(S.Bestämdhet),
            "numerus": list(S.Numerus),
            "attribut": [(), (ny(LatAttr, o, q, d),)],
            "possessiv": [None, f"$poss:{p}"],
            "possessiv_koreferent": [False, True],
            "referent": [None, S.Referentgenus.MASKULIN, S.Referentgenus.FEMININ],
            "frågedeterminant": [None, f"$fdet:{p}"],
            "ägare": [None, ny(LatNF, o, q, d + 1)],
        }[namn]
        return o.välj(q, dom)


class LatAttr(S.Attribut):
    __slots__ = ("_o", "_p", "_d", "_över")

    def __getattribute__(self, namn):
        if namn == "koncept":
            return f"$attr:{_p(self)}"
        if namn == "grad":
            return _o(self).välj(f"{_p(self)}.grad", list(S.Grad))
        return object.__getattribute__(self, namn)


class LatPrep(S.Prepositionsfras):
    __slots__ = ("_o", "_p", "_d", "_över")

    def __getattribute__(self, namn):
        if namn == "preposition":
            return f"$prep:{_p(self)}"
        if namn == "komplement":
            return _o(self).välj(f"{_p(self)}.komplement",
                                 [ny(LatNF, _o(self), f"{_p(self)}.k",
                                     object.__getattribute__(self, "_d"))])
        return object.__getattribute__(self, namn)


class LatBisats(S.Bisats):
    __slots__ = ("_o", "_p", "_d", "_över")

    def __getattribute__(self, namn):
        if namn == "subjunktion":
            return f"$subjunktion:{_p(self)}"
        if namn == "sats":
            return _o(self).välj(f"{_p(self)}.sats",
                                 [ny(LatMening, _o(self), f"{_p(self)}.s",
                                     object.__getattribute__(self, "_d"))])
        return object.__getattribute__(self, namn)


# ── lexikonet ───────────────────────────────────────────────────────────

class Celler:
    def __init__(self, k, o):
        self.k, self.o = k, o

    def get(self, cell):
        return "x" if self.o.välj(("har", self.k, cell), [True, False]) else None


class SymLexem:
    def __init__(self, k, o):
        self.k, self.o = k, o

    def __getitem__(self, namn):
        if namn in ("nyckel", "id"):
            return self.k
        if namn == "variant":
            return None
        if namn == "ordklass":
            dom = (["Substantiv", "Pronomen"] if self.k.startswith("$nf:")
                   else ["?"])
            return self.o.välj(("ordklass", self.k), dom)
        if namn == "genus":
            return self.o.välj(("genus", self.k), [1, 2])
        if namn == "lemma":
            return "x sig" if self.o.välj(("refl", self.k), [False, True]) else "x"
        raise KeyError(namn)


class FalsktUppslag:
    def __init__(self, o, verklig, poster):
        self.o, self.v, self.poster = o, verklig, poster

    def lexem(self, koncept, variant=None):
        if isinstance(koncept, str) and koncept.startswith("$"):
            return SymLexem(koncept, self.o)
        return self.v.lexem(koncept, variant)

    def _celler(self, lexem):
        if isinstance(lexem, SymLexem):
            return Celler(lexem.k, self.o)
        return self.v._celler(lexem)

    def form(self, lexem, cell):
        self.poster.append(("form", lexem["nyckel"].split(":")[0], cell))
        if isinstance(lexem, SymLexem):
            return f"<{cell}>"
        return self.v.form(lexem, cell)

    def form_för(self, koncept, cell, variant=None):
        return self.form(self.lexem(koncept, variant), cell)

    def egenskap(self, lexem, namn):
        self.poster.append(("egenskap", namn))
        return lexem[namn]

    def ordföljd(self, regel):
        self.poster.append(("regel", regel))

    def rektion(self, koncept, slot, namn, värde):
        self.poster.append(("rektion", slot, namn))
        return värde

    def infinitivmarkör(self, verb):
        return self.o.välj(("markör", verb), [None, "$markör"])

    def kontrollera_naken(self, nf):
        if nf.bestämdhet in S.NAKEN and nf.numerus is S.Numerus.SG:
            if self.o.välj(("räknebar", nf.koncept), [False, True]):
                raise RenderingsFel("naken räknebar")

    def frågepronomen(self, koncept):
        return ("frågepronomen_person"
                if self.o.välj(("mänsklig", koncept), [False, True])
                else "frågepronomen_sak")


def renderare(o, poster, conn, verklig, stubba_nf=True, stubba_bisats=True):
    r = SvenskRenderare.__new__(SvenskRenderare)
    r.u = FalsktUppslag(o, verklig, poster)
    if stubba_nf:
        def nf_stubb(nf, subjekt=False, genitiv=False):
            poster.append(("NF", subjekt, genitiv))
            return ["<NF>"]
        r.nominalfras = nf_stubb
    if stubba_bisats:
        def bisats_stubb(b):
            poster.append(("BISATS",))
            return ["<BISATS>"]
        r.bisats = bisats_stubb

    def refl(m):
        if not r.u.lexem(m.verb, None)["lemma"].endswith(" sig"):
            return None
        _ = m.subjekt.numerus
        val = o.välj(("reflpron", _p(m)), [
            "pronomen_1sg", "pronomen_2sg", "pronomen_1pl", "pronomen_2pl",
            "pronomen_2sg_formal", "pronomen_reflexiv"])
        return r.u.form_för(val, "ack_dat")
    r.reflexivpronomen = refl
    return r


def lat_tilltal(o):
    def tilltal(m, språk, stöds):
        tal = o.välj(("tilltal", _p(m)), ["2sg", "2pl", "artig", "1pl", None])
        if tal is None or tal not in stöds:
            raise RenderingsFel("inget tilltal")
        return tal
    return tilltal


def lat_replace(o):
    def replace(m, **över):
        gamla = object.__getattribute__(m, "_över")
        return ny(LatMening, o, _p(m), object.__getattribute__(m, "_d"),
                  **{**gamla, **över})
    return replace


def main():
    conn = sqlite3.connect(DB)
    verklig = Uppslag(conn, "sv")
    original_tilltal, original_replace = svmod.tilltal, svmod.replace

    def kör_sats(o):
        poster = []
        svmod.tilltal, svmod.replace = lat_tilltal(o), lat_replace(o)
        r = renderare(o, poster, conn, verklig)
        m = ny(LatMening, o, "m", 0)
        r.rendera(m)
        return poster

    def kör_nf(subjekt, genitiv):
        def kör(o):
            poster = []
            r = renderare(o, poster, conn, verklig)
            nf = ny(LatNF, o, "nf", 0)
            SvenskRenderare.nominalfras(r, nf, subjekt=subjekt, genitiv=genitiv)
            return poster
        return kör

    def kör_bisats(o):
        poster = []
        svmod.tilltal, svmod.replace = lat_tilltal(o), lat_replace(o)
        r = renderare(o, poster, conn, verklig)
        b = ny(LatBisats, o, "b", 1)
        SvenskRenderare.bisats.__wrapped__ if False else None
        poster.append(("form", "$subjunktion", "inv"))
        SvenskRenderare.satsled(r, b.sats, bisats=True)
        return poster

    delar = [("nf subjekt", kör_nf(True, False)),
             ("nf övrig", kör_nf(False, False)),
             ("nf genitiv", kör_nf(False, True)),
             ("bisats", kör_bisats),
             ("sats (huvudsats)", kör_sats)]
    try:
        print("SKATTNING (Knuth, 20 000 slumpvägar per del)", flush=True)
        for namn, kör in delar:
            t = time.perf_counter()
            lyckade, vägrade, djup = uppskatta(kör, 20000)
            dt = time.perf_counter() - t
            print(f"  {namn:18} ≈ {lyckade:>14,.0f} lyckade löv  "
                  f"≈ {vägrade:>14,.0f} vägrade  längsta väg {djup:>3} val  "
                  f"({20000 / dt:,.0f} körningar/s)", flush=True)
        print("\nUTTÖMMANDE (tak 300 000 körningar per del)", flush=True)
        for namn, kör in delar:
            t = time.perf_counter()
            blad, vägrar, krascher, utfall = utforska(kör, tak=300000,
                                                      rapport=50000)
            dt = time.perf_counter() - t
            print(f"  {namn:18} löv {blad:>8}  vägrar {vägrar:>7}  "
                  f"olika utfall {len(utfall):>6}  {dt:6.1f} s", flush=True)
            for k, n in krascher.most_common(5):
                print(f"    KRASCH ×{n}: {k}", flush=True)
    finally:
        svmod.tilltal, svmod.replace = original_tilltal, original_replace


if __name__ == "__main__":
    main()
