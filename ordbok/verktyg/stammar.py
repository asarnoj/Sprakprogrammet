"""Härled varje ords stamuppsättning och varje klass ändelsetabell ur Former.

GENERATOR.md avgör att en form får eget kort först när den INTE går att
härleda ur det användaren redan har kort för. Den här filen räknar fram vad
"redan har kort för" betyder, per språk och ordklass:

    STAMMAR      fakta om ORDET      groß / größer / größt
    ÄNDELSER     fakta om SYSTEMET   svag m dat tar -en, delad av alla
    RESTER       former som inte går att härleda — egna formkort

Stammar och ändelser definierar varandra, så ordningen är:

  1. För varje cell: den längsta ändelse som en tröskelandel av orden delar,
     med ett TAK på ändelsens längd. Taket är avgörande, se _celländelse.

  2. Ord som tabellen förklarar bildar en klass och plockas bort. Resten får
     en egen omgång. En klass är alltså "de ord de tidigare tabellerna inte
     räckte till för", vilket är precis vad en böjningsklass är. Grupper
     under MINSTA_KLASS är undantag och inte regler, och löses upp.

  3. Stammen är formen minus cellens ändelse. Distinkta stammar per ord =
     ordets stamuppsättning. Former där ändelsen inte går att skala av är
     RESTER och får egna kort.

  4. Tröskeln och längdtaket söks fram per språk och ordklass genom att
     minimera antalet kort. Vilket värde som är rätt beror på hur mycket
     språket delar, och går inte att veta i förväg.

KVALITETSMÅTTET är var resterna hamnar. Sprids de jämnt över lexikonet är
analysen fel; samlas de hos de ord som faktiskt är oregelbundna är den rätt.
Utfallet: 33 av 560 tyska ord ger rester, och de fyra värsta är de tre
oböjliga färgadjektiven plus groß. Spanskans värsta är ser.

Metoden förutsätter KONKATENATIV morfologi. Det gör alla sju språken; ett
framtida språk med rot och mönster (arabiska) skulle mäta ut nästan bara
rester — vilket är rätt svar, eftersom per-cell-modellen är golvet.

Resultatet är en approximation och inte en morfologisk analys. Den söker ett
minimum i ett stort rum och hittar inte alltid det bästa: tyska adjektiv
landar på 898 kort där 813 troligen går. Skillnaden ligger i att alla celler
i en grad måste byta ändelselängd samtidigt, och sökningen rör en åt gången.

Kör: .venv/bin/python ordbok/verktyg/stammar.py [--skriv]
"""
from __future__ import annotations

import collections
import sqlite3
import sys

from sprakprog.rendering import Uppslag

SPRÅK = ("sv", "en", "de", "fr", "es", "it", "ja")
ORDKLASSER = ("Substantiv", "Verb", "Adjektiv", "Pronomen", "Possessiv",
              "Artikel", "Räkneord", "Demonstrativ", "Kvantifikator",
              "Frågepronomen", "Interrogativdeterminant", "Relativpronomen")

#: En klass med färre medlemmar än så är ingen regel utan ett undantag, och
#: löses upp så att materialet hamnar hos orden i stället för i tabellen.
MINSTA_KLASS = 5


def _lcp(strängar) -> str:
    """Längsta gemensamma prefix."""
    i = 0
    första = min(strängar, key=len)
    while i < len(första) and all(s[i] == första[i] for s in strängar):
        i += 1
    return första[:i]


def paradigm(conn, språk: str, ordklass: str) -> dict[int, tuple]:
    """lexem_id → (rad, {cell: form}) för alla ord med minst två former."""
    u = Uppslag(conn, språk)
    ut = {}
    for lex in conn.execute(
            """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id
               WHERE l.språk = ? AND k.ordklass = ?""", (språk, ordklass)):
        try:
            celler = {c: f for c, f in u._celler(lex).items() if f}
        except Exception:
            continue          # ordklass utan slot-fil
        if len(celler) >= 2:
            ut[lex["id"]] = (lex, celler)
    return ut


def _celländelse(former: list[str], tröskel: float, maxlängd: int) -> str:
    """Längsta suffix på högst `maxlängd` tecken som `tröskel` av formerna delar.

    Längdtaket är metodens kärna, och det tog tre försök att hitta. Utan tak
    väljs `-sten` för tyskans superlativ — ett suffix som mycket riktigt
    återkommer, men som bakar in gradmarkören och gör varje oregelbunden
    superlativ till en rest: `groß` → `größte` slutar inte på `-sten`. Med
    taket blir ändelsen `-en`, stammen `größt`, och alla fem superlativceller
    delar den.

    Att optimera cellvis fungerar INTE, vilket var andra försöket: att byta
    en ensam cell från `-sten` till `-en` byter en rest mot en stam och
    ändrar ingenting. Hela graden måste flytta samtidigt, och det är precis
    vad ett gemensamt längdtak gör.
    """
    räknare: collections.Counter = collections.Counter()
    for form in former:
        for i in range(1, min(len(form), maxlängd + 1)):
            räknare[form[-i:]] += 1
    krav = tröskel * len(former)
    kandidater = [s for s, n in räknare.items() if n >= krav]
    return max(kandidater, key=len) if kandidater else ""


def ändelsetabeller(par: dict[int, tuple], tröskel: float = 0.6,
                    maxlängd: int = 3, max_klasser: int = 8) -> tuple[dict, dict]:
    """(klassnamn → {cell: ändelse}, lexem_id → klassnamn).

    Klasserna upptäcks iterativt i stället för att antas: den första
    tabellen härleds ur alla ord, orden den förklarar plockas bort, och
    resten får en egen omgång. Varje klass är alltså "de ord de tidigare
    tabellerna inte räckte till för" — vilket är precis vad en böjningsklass
    är. Iterationen stannar när ingen grupp är stor nog att vara en regel.
    """
    kvar = set(par)
    tabeller: dict[str, dict[str, str]] = {}
    tillhör: dict[int, str] = {}
    while kvar and len(tabeller) < max_klasser:
        celler: dict[str, list[str]] = collections.defaultdict(list)
        for lid in kvar:
            for cell, form in par[lid][1].items():
                celler[cell].append(form)
        tabell = {cell: _celländelse(former, tröskel, maxlängd)
                  for cell, former in celler.items()
                  if len(former) >= MINSTA_KLASS}
        if not tabell:
            break
        medlemmar = {lid for lid in kvar
                     if sum(1 for c, f in par[lid][1].items()
                            if c in tabell and f.endswith(tabell[c]))
                     >= tröskel * len(par[lid][1])}
        if len(medlemmar) < MINSTA_KLASS:
            break
        namn = f"K{len(tabeller)}"
        tabeller[namn] = tabell
        for lid in medlemmar:
            tillhör[lid] = namn
        kvar -= medlemmar
    return tabeller, tillhör


def _kortantal(par, tabeller, tillhör) -> int:
    """Stammar + ändelser + rester — måttet sökningen minimerar."""
    stammar = rester = 0
    for lid, (_, celler) in par.items():
        klass = tillhör.get(lid) or bästa_klass(celler, tabeller)
        if klass is None:
            continue
        a, b = dela_upp(celler, tabeller[klass])
        stammar += len(a)
        rester += len(b)
    return stammar + sum(len(t) for t in tabeller.values()) + rester


def bästa_klass(celler: dict, tabeller: dict) -> str | None:
    """Klassen vars ändelsetabell förklarar flest av ordets former."""
    bäst, poäng = None, 0
    for namn, tabell in tabeller.items():
        n = sum(1 for c, f in celler.items()
                if c in tabell and f.endswith(tabell[c]))
        if n > poäng:
            bäst, poäng = namn, n
    return bäst


def dela_upp(celler: dict, tabell: dict) -> tuple[dict[str, list[str]], list[str]]:
    """(stam → celler den täcker, celler som inte går att härleda)."""
    stammar: dict[str, list[str]] = collections.defaultdict(list)
    rester: list[str] = []
    for cell, form in sorted(celler.items()):
        ändelse = tabell.get(cell)
        if ändelse is None or not form.endswith(ändelse):
            rester.append(cell)
            continue
        stam = form[:len(form) - len(ändelse)] if ändelse else form
        stammar[stam].append(cell)
    return dict(stammar), rester


#: Trösklar att pröva. Vilken som är rätt går inte att veta i förväg — den
#: beror på hur mycket språket delar — så den söks fram genom att minimera
#: det vi faktiskt bryr oss om: antalet kort. En för girig tröskel tar
#: längsta gemensamma suffix och överanpassar ("-ren" i stället för "-en");
#: en för snål ger tomma ändelser och gör varje form till sin egen stam.
TRÖSKLAR = (0.5, 0.7, 0.9)
LÄNGDER = (1, 2, 3, 4, 5, 6)


def analysera(conn, språk: str, ordklass: str):
    par = paradigm(conn, språk, ordklass)
    if len(par) < MINSTA_KLASS:
        return None
    bäst = None
    for tröskel in TRÖSKLAR:
        for maxlängd in LÄNGDER:
            tabeller, tillhör = ändelsetabeller(par, tröskel, maxlängd)
            if not tabeller:
                continue
            kort = _kortantal(par, tabeller, tillhör)
            if bäst is None or kort < bäst[0]:
                bäst = (kort, (tröskel, maxlängd), tabeller, tillhör)
    if bäst is None:
        return None
    _, tröskel, tabeller, tillhör = bäst
    rader, alla_rester, stamantal = [], 0, collections.Counter()
    for lid, (lex, celler) in par.items():
        klass = tillhör.get(lid) or bästa_klass(celler, tabeller)
        if klass is None:
            continue
        stammar, rester = dela_upp(celler, tabeller[klass])
        stamantal[len(stammar)] += 1
        alla_rester += len(rester)
        for i, (stam, täcker) in enumerate(sorted(stammar.items())):
            rader.append((språk, lex["nyckel"], lex["variant"] or "", ordklass,
                          klass, i, stam, len(täcker)))
        for cell in rester:
            rader.append((språk, lex["nyckel"], lex["variant"] or "", ordklass,
                          klass, -1, celler[cell], 1))
    former = sum(len(c) for _, c in par.values())
    return {"ord": len(par), "former": former, "klasser": len(tabeller),
            "tröskel": tröskel,
            "ändelser": sum(len(t) for t in tabeller.values()),
            "stammar": sum(k * v for k, v in stamantal.items()),
            "median": sorted(stamantal.elements())[sum(stamantal.values()) // 2],
            "rester": alla_rester, "rader": rader, "tabeller": tabeller}


def main() -> None:
    conn = sqlite3.connect("sprak.db")
    conn.row_factory = sqlite3.Row
    alla_rader, alla_tabeller = [], []
    print(f"{'':22}{'ord':>6}{'former':>8}{'klass':>6}{'ändels':>7}"
          f"{'stam':>7}{'med':>5}{'rest':>6}{'kort':>7}{'trsk':>6}{'län':>4}")
    summa = collections.Counter()
    for språk in SPRÅK:
        for ordklass in ORDKLASSER:
            r = analysera(conn, språk, ordklass)
            if r is None:
                continue
            kort = r["stammar"] + r["ändelser"] + r["rester"]
            print(f"{språk}/{ordklass:<19}{r['ord']:6}{r['former']:8}"
                  f"{r['klasser']:6}{r['ändelser']:7}{r['stammar']:7}"
                  f"{r['median']:5}{r['rester']:6}{kort:7}"
                  f"{r['tröskel'][0]:6.1f}{r['tröskel'][1]:4}")
            alla_rader += r["rader"]
            for namn, tabell in r["tabeller"].items():
                for cell, ändelse in sorted(tabell.items()):
                    alla_tabeller.append((språk, ordklass, namn, cell, ändelse))
            for nyckel in ("former", "stammar", "ändelser", "rester"):
                summa[nyckel] += r[nyckel]
    print(f"\n{'SUMMA':22}{'':6}{summa['former']:8}{'':6}{summa['ändelser']:7}"
          f"{summa['stammar']:7}{'':5}{summa['rester']:6}"
          f"{summa['stammar'] + summa['ändelser'] + summa['rester']:7}")
    print(f"\n{summa['former']} former → "
          f"{summa['stammar'] + summa['ändelser'] + summa['rester']} kort "
          f"({summa['former'] / (summa['stammar'] + summa['ändelser'] + summa['rester']):.1f}×)")

    if "--skriv" in sys.argv:
        with open("ordbok/stammar.tsv", "w") as f:
            f.write("språk\tkoncept\tvariant\tordklass\tklass\tstamgrupp\tform\tceller\n")
            for rad in alla_rader:
                f.write("\t".join(str(x) for x in rad) + "\n")
        with open("ordbok/ändelser.tsv", "w") as f:
            f.write("språk\tordklass\tklass\tcell\tändelse\n")
            for rad in alla_tabeller:
                f.write("\t".join(rad) + "\n")
        print(f"\n✓ {len(alla_rader)} rader → ordbok/stammar.tsv")
        print(f"✓ {len(alla_tabeller)} rader → ordbok/ändelser.tsv")


if __name__ == "__main__":
    main()
