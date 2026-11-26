"""Projektionen av den universella cellistan — håller den?

Fyra invarianter, och den tredje är den som bär hela idén: varje ändelse i
varje tabell ska läras ut EXAKT en gång. Lärs den ut två gånger är stegen
full av tomma moment; lärs den aldrig ut går den inte att lära sig.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

# MODULEN, inte namnen. `from … import projicera` binder funktionen vid
# import, och då når falsifieringens patch den aldrig — alla fyra proven höll
# med sabotaget påslaget första gången de kördes. Ett prov som inte kan
# fällas bevisar ingenting, och det gällde här hela filen.
import sprakprog.kort.dimensioner as d                       # noqa: E402

projicera = lambda *a, **kw: d.projicera(*a, **kw)            # noqa: E731
universella_celler = lambda *a, **kw: d.universella_celler(*a, **kw)  # noqa: E731
ändelsetabeller = lambda *a, **kw: d.ändelsetabeller(*a, **kw)        # noqa: E731


def prov_delmängd() -> list[str]:
    """Varje stege är en DELFÖLJD av den universella listan, i samma ordning.

    Det är vad "en universell lista, projicerad" betyder. Kan ett språk
    kasta om ordningen är listan inte längre delad utan sju listor.
    """
    fel, u = [], list(universella_celler())
    for språk, steg in projicera().items():
        index = [u.index(c) for c, _ in steg if c in u]
        if len(index) != len(steg):
            fel.append(f"{språk}: steg utanför den universella listan")
        elif index != sorted(index):
            fel.append(f"{språk}: stegen är omkastade mot listan")
    return fel


def prov_ingen_upprepning() -> list[str]:
    """Ingen klass lär ut samma ändelse två gånger. Det är hela urvalet."""
    fel = []
    tabeller = ändelsetabeller()
    for språk, steg in projicera().items():
        sedd: dict[str, set[str]] = {}
        for cell, klasser in steg:
            for klass in klasser:
                # `.get`, inte indexering: sabotaget släpper igenom celler
                # som klassen inte HAR, och en krasch är ett sämre besked än
                # ett fall — provet ska säga vad som är fel, inte dö av det.
                ändelse = tabeller[(språk, klass)].get(cell)
                if ändelse is None:
                    fel.append(f"{språk}/{klass}: {cell} finns inte i tabellen")
                    continue
                if ändelse in sedd.setdefault(klass, set()):
                    fel.append(f"{språk}/{klass}: {ändelse!r} lärs ut igen "
                               f"på {cell}")
                sedd[klass].add(ändelse)
    return fel


def prov_allt_lärs_ut() -> list[str]:
    """Varje ändelse som finns i en tabell ska läras ut någon gång.

    Motsatsen till provet ovan, och den farligare: en ändelse som ingen cell
    introducerar är omöjlig att lära sig, och det syns inte förrän någon
    skriver fel på den.
    """
    fel = []
    tabeller = ändelsetabeller()
    projektion = projicera()
    for (språk, klass), tabell in tabeller.items():
        lärda = {tabell[cell] for cell, klasser in projektion.get(språk, [])
                 if klass in klasser and cell in tabell}
        for saknad in set(tabell.values()) - lärda:
            fel.append(f"{språk}/{klass}: ändelsen {saknad!r} lärs aldrig ut")
    return fel


def prov_stegen_viks() -> list[str]:
    """Stegen ska bli OLIKA lång i olika språk — annars gör projektionen inget.

    Det här är provet mot att kriteriet tyst slutar diskriminera. Skulle
    `projicera` börja släppa igenom varje cell för varje språk blir alla
    stegar lika långa som listan, och ingenting hade sagt ifrån.
    """
    p = projicera()
    längder = {s: len(steg) for s, steg in p.items()}
    if len(set(längder.values())) < 2:
        return [f"alla språk fick lika många steg ({längder}) — projektionen "
                f"skiljer inte längre på språken"]
    if max(längder.values()) >= len(universella_celler()):
        return [f"ett språk fick hela listan ({max(längder.values())} steg) — "
                f"kriteriet filtrerar inte"]
    return []


PROV = [("stegen är en delföljd av listan", prov_delmängd),
        ("ingen ändelse lärs ut två gånger", prov_ingen_upprepning),
        ("varje ändelse lärs ut någon gång", prov_allt_lärs_ut),
        ("stegen viks olika per språk", prov_stegen_viks)]



# VARJE INVARIANT BEHÖVER SITT EGET SABOTAGE, och det lärde det här provet
# mig på det hårda sättet. Ett enda sabotage — "släpp igenom varje cell" —
# fällde bara två av fyra, och de andra två såg då stumma ut fast de var
# riktiga. De vaktar mot ANDRA fel: omkastning och för lite undervisning, och
# ett sabotage som lär ut för mycket kan inte bryta någon av dem.
#
# Ett prov som inte faller för sitt eget sabotage är stumt. Ett prov som inte
# faller för NÅGON ANNANS är bara ett annat prov.

def _sabotage_omkastad():
    """Stegen byggs i omvänd ordning mot listan."""
    äkta = d.projicera
    def bakvänt(celler=None, ordklass="Verb"):
        return {s: list(reversed(v)) for s, v in äkta(celler, ordklass).items()}
    d.projicera = bakvänt
    return lambda: setattr(d, "projicera", äkta)


def _sabotage_halva():
    """Varannan cell tappas — ändelser som ingen cell längre lär ut."""
    äkta = d.projicera
    def halvt(celler=None, ordklass="Verb"):
        return {s: v[::2] for s, v in äkta(celler, ordklass).items()}
    d.projicera = halvt
    return lambda: setattr(d, "projicera", äkta)


def _sabotage_utan_filter():
    """Före projektionen: varje cell blev ett steg i varje språk."""
    import sprakprog.kort.dimensioner as d
    äkta = d.projicera
    def allt(celler=None, ordklass="Verb"):
        celler = celler or d.universella_celler(ordklass)
        t = d.ändelsetabeller(ordklass)
        ut = {}
        for språk in sorted({s for s, _ in t}):
            klasser = {k for s, k in t if s == språk}
            ut[språk] = [(c, klasser) for c in celler]
        return ut
    d.projicera = allt
    return lambda: setattr(d, "projicera", äkta)

#: (sabotage, vilket prov det ska fälla).
SABOTAGE = [
    (_sabotage_omkastad, 0),
    (_sabotage_utan_filter, 1),
    (_sabotage_halva, 2),
    (_sabotage_utan_filter, 3),
]


def main() -> int:
    print("projektionen av den universella cellistan\n")
    p = d.projicera()
    print(f"  {len(d.universella_celler())} universella celler → "
          + ", ".join(f"{s}:{len(v)}" for s, v in sorted(p.items())) + "\n")
    fel = 0
    for namn, prov in PROV:
        rader = prov()
        fel += bool(rader)
        print(f"  {'✓' if not rader else '✗'} {namn}")
        for r in rader[:4]:
            print(f"      {r}")
        if len(rader) > 4:
            print(f"      … och {len(rader) - 4} till")

    print("\nfalsifiering — varje invariant mot sitt eget sabotage:")
    stumma = []
    for sabotera, i in SABOTAGE:
        namn, prov = PROV[i]
        ångra = sabotera()
        try:
            höll = not prov()
        finally:
            ångra()
        if höll:
            stumma.append(namn)
        print(f"  {'✗ STUM' if höll else '✓ föll'}  {namn}"
              f"  ← {sabotera.__doc__.splitlines()[0]}")

    print(f"\n{len(PROV)} invarianter, {fel} brott, {len(stumma)} stumma.")
    return 1 if fel or stumma else 0


if __name__ == "__main__":
    raise SystemExit(main())
