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


SPRÅK = ("sv", "en", "de", "fr", "es", "it", "ja")


def prov_stegen_är_hel() -> list[str]:
    """Den flätade stegen innehåller ALLT, en gång var.

    Tappar flätningen en konstruktion går den aldrig att låsa upp; tappar den
    en böjningscell är ändelsen otillgänglig igen — samma fel som hela
    projektionen finns för att laga, återinfört ett steg senare.
    """
    from sprakprog.generator.urval import NIVÅ
    fel = []
    for språk in SPRÅK:
        s = d.stege(språk)
        k = [n for t, n in s if t == "konstruktion"]
        b = [n for t, n in s if t == "böjning"]
        väntad_b = [c for c, _ in d.projicera().get(språk, [])]
        if sorted(k) != sorted(NIVÅ.values()):
            fel.append(f"{språk}: konstruktionerna stämmer inte ({len(k)} av "
                       f"{len(NIVÅ)})")
        if sorted(b) != sorted(väntad_b):
            fel.append(f"{språk}: böjningsstegen stämmer inte ({len(b)} av "
                       f"{len(väntad_b)})")
        if len(set(k)) != len(k) or len(set(b)) != len(b):
            fel.append(f"{språk}: något steg förekommer två gånger")
    return fel


def prov_beroenden() -> list[str]:
    """En konstruktion får aldrig komma före den böjning den kräver.

    Utan det lägger den proportionella flätningen "tempus" på steg 9 medan
    preteritumändelserna kommer på steg 30 — och användaren möter dåtid
    trettio steg innan något kort lär ut hur den böjs.

    PROVET HAR SIN EGEN KOPIA AV KRAVEN, och det är inte dubbelarbete. Först
    läste det `d.BEROENDE`, alltså exakt det sabotaget tömmer — och då hade
    provet inget att kontrollera och gick igenom. Ett prov som läser sin egen
    förutsättning ur det som prövas kan aldrig falla.

    Kraven här är den grammatiska sanningen: dåtid kräver dåtidsformer,
    perfekt kräver participet, imperativ kräver imperativformer, passiv
    kräver passiva former. Skulle modulens tabell säga något annat är det
    HÄR som säger ifrån.
    """
    KRAV = {"tempus": ("Pret", "Imperf", "Fut"),
            "perfekt": ("Sup", "PresPer"),
            "imperativ": ("Imp",),
            "passiv": None}          # None = diates Passiv, inte en tempus
    from sprakprog.kaikki_mappning.paradigm import ladda_legend, ladda_slot
    legend = ladda_legend()
    tempusnamn = {v: k for k, v in legend.get("tempus", {}).items()}
    fel = []
    for språk in SPRÅK:
        s = d.stege(språk)
        plats = {namn: i for i, (_, namn) in enumerate(s)}
        try:
            axlar = {c.id: c.axlar
                     for c in ladda_slot(språk, "Verb", legend).celler}
        except FileNotFoundError:
            continue
        for konstruktion, tempus in KRAV.items():
            if konstruktion not in plats:
                continue
            celler = [n for t, n in s if t == "böjning" and (
                (axlar.get(n, {}).get("diates") == 2) if tempus is None
                else tempusnamn.get(axlar.get(n, {}).get("tempus")) in tempus)]
            if celler and plats[celler[-1]] > plats[konstruktion]:
                fel.append(f"{språk}: {konstruktion} på steg "
                           f"{plats[konstruktion] + 1} men {celler[-1]} först "
                           f"på {plats[celler[-1]] + 1}")
    return fel


def prov_varvas() -> list[str]:
    """De två sorterna ska VARVAS, inte ligga i två block.

    Ligger all böjning först och alla konstruktioner sedan är det två stegar
    efter varandra och inte en flätad, och då har flätningen slutat göra
    något utan att säga ifrån.
    """
    fel = []
    for språk in SPRÅK:
        typer = [t for t, _ in d.stege(språk)]
        if len(set(typer)) < 2:
            continue                       # bara en sort finns att varva
        byten = sum(a != b for a, b in zip(typer, typer[1:]))
        if byten < 4:
            fel.append(f"{språk}: bara {byten} byten mellan sorterna — "
                       f"stegen är block, inte flätad")
    return fel


PROV = [("stegen är en delföljd av listan", prov_delmängd),
        ("ingen ändelse lärs ut två gånger", prov_ingen_upprepning),
        ("varje ändelse lärs ut någon gång", prov_allt_lärs_ut),
        ("stegen viks olika per språk", prov_stegen_viks),
        ("den flätade stegen är hel", prov_stegen_är_hel),
        ("konstruktion aldrig före sin böjning", prov_beroenden),
        ("de två sorterna varvas", prov_varvas)]



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

def _sabotage_utan_beroenden():
    """Beroendetabellen tömd — ren proportionell flätning."""
    äkta = d.BEROENDE, d.PASSIVKONSTRUKTION
    d.BEROENDE, d.PASSIVKONSTRUKTION = {}, "\0"
    def ångra():
        d.BEROENDE, d.PASSIVKONSTRUKTION = äkta
    return ångra


def _sabotage_två_block():
    """All böjning först, alla konstruktioner sedan — två stegar, inte en."""
    äkta = d.stege
    def block(språk, ordklass="Verb"):
        s = äkta(språk, ordklass)
        return ([x for x in s if x[0] == "böjning"]
                + [x for x in s if x[0] == "konstruktion"])
    d.stege = block
    return lambda: setattr(d, "stege", äkta)


def _sabotage_tappa_steg():
    """Sista steget tappas — något går aldrig att låsa upp."""
    äkta = d.stege
    d.stege = lambda språk, ordklass="Verb": äkta(språk, ordklass)[:-1]
    return lambda: setattr(d, "stege", äkta)


#: (sabotage, vilket prov det ska fälla).
SABOTAGE = [
    (_sabotage_omkastad, 0),
    (_sabotage_utan_filter, 1),
    (_sabotage_halva, 2),
    (_sabotage_utan_filter, 3),
    (_sabotage_tappa_steg, 4),
    (_sabotage_utan_beroenden, 5),
    (_sabotage_två_block, 6),
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
