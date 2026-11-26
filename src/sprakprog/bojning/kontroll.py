"""Kör böjningsreglerna mot varje form i databasen.

    python -m sprakprog.bojning.kontroll sv

SÖKNINGEN FÖLJER KÄRNAN 3.4 BOKSTAVLIGT. För varje ord börjar den med bara
grundformen, förutsäger alla celler, och tar den första cellen i
införandeordning som inte stämmer som ett kort. Sedan förutsäger den igen, nu
med kortet känt, och fortsätter tills allt stämmer. Varje varv lägger till ett
kort, så sökningen tar alltid slut. Ett ord utan kort är regelbundet.

Det är principens "den första form som visar avvikelsen": för `köpa` blir
presens `köper` kortet, och när det är känt följer `köpte` och `köpt`.

KONTROLLEN AVGÖR INGENTING OM SPRÅKET. En form som reglerna inte ger är ett
äkta undantag, en regel som saknas, eller ett fel i datan. Bara det sista går
att känna igen mekaniskt, och bara där formen bryter mot en regel som saknar
undantag — en passiv som inte är den aktiva formen plus -s, en genitiv som inte
är grundformen plus -s. De sorteras ut som misstänkta datafel. Resten granskar
en människa.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..rendering.uppslag import Uppslag
from . import Spår, en, sv

SPRÅK = {"sv": sv, "en": en}
ROT = Path(__file__).resolve().parents[3]


@dataclass
class Utfall:
    ordklass: str
    koncept: str
    variant: str
    lemma: str
    kort: dict[str, str]
    datafel: dict[str, tuple[str, str]]          # cell -> (form i datan, skäl)
    regler: set[str] = field(default_factory=set)
    saknas: dict[str, str] = field(default_factory=dict)   # cell -> form reglerna ger


def huvudformer(ok, info: dict, prövas: dict) -> tuple[dict, Spår]:
    """Korten för ett ord: de former förutsägelsen inte når, i införandeordning."""
    kända: dict[str, str] = {}
    while True:
        spår = Spår()
        förutsagt = ok.förutsäg(info, kända, spår)
        avvikande = [c for c in ok.ordning
                     if c in prövas and c not in kända and förutsagt.get(c) != prövas[c]]
        if not avvikande:
            return kända, spår
        kända[avvikande[0]] = prövas[avvikande[0]]


def kör(språk: str, conn: sqlite3.Connection) -> list[Utfall]:
    regler = SPRÅK[språk]
    u = Uppslag(conn, språk)
    ut: list[Utfall] = []
    for ordklass, ok in regler.ORDKLASSER.items():
        rader = conn.execute(
            """SELECT l.*, k.ordklass, k.nyckel FROM Lexem l
               JOIN Koncept k ON k.id = l.koncept_id
               WHERE l.språk = ? AND k.ordklass = ? ORDER BY l.lemma, k.nyckel""",
            (språk, ordklass)).fetchall()
        for lex in rader:
            info, facit = ok.bas(u._celler(lex), lex)
            fel = ok.datafel(facit, info)
            prövas = {c: f for c, f in facit.items() if c in ok.ordning and c not in fel}
            kort, spår = huvudformer(ok, info, prövas)
            använda: set[str] = set()
            for cell, namn in spår.per_cell.items():
                if cell in prövas and cell not in kort:
                    använda |= namn
            förutsagt = ok.förutsäg(info, kort, Spår())
            saknas = {c: förutsagt[c] for c in ok.saknad
                      if förutsagt.get(c) and not facit.get(c) and c not in fel}
            ut.append(Utfall(ordklass, lex["nyckel"], lex["variant"] or "", lex["lemma"],
                             kort, {c: (facit[c], skäl) for c, skäl in fel.items()},
                             använda, saknas))
    return ut


def rapport(språk: str, utfall: list[Utfall]) -> str:
    regler = SPRÅK[språk]
    namn = lambda c: regler.CELLNAMN.get(c, c)
    lemmaantal = Counter(x.lemma for x in utfall)
    visa = lambda x: x.lemma if lemmaantal[x.lemma] == 1 else f"{x.lemma} ({x.koncept})"
    per = defaultdict(list)
    for x in utfall:
        per[x.ordklass].append(x)

    r = [f"# Regelkontroll: {regler.NAMN}", "",
         f"*Genererad av `python -m sprakprog.bojning.kontroll {språk}`. Ändra inte "
         f"för hand — ändra reglerna i `src/sprakprog/bojning/{språk}.py` och kör om.*", "",
         "Reglerna förutsäger varje ords former ur grundformen (KÄRNAN 3.4). Det "
         "reglerna inte når blir **undantagskort**, i införandeordning: den första "
         "avvikande formen först, och sedan förutsägs resten med den känd.", "",
         "Varje undantagskort nedan är antingen **ett äkta undantag**, **en regel som "
         "saknas** eller **ett fel i datan**. Former som bryter mot en regel utan "
         "undantag är redan utsorterade som misstänkta datafel.", "",
         "## Sammanfattning", "",
         "| ordklass | ord | regelbundna | med kort | undantagskort | misstänkta datafel |",
         "|---|---|---|---|---|---|"]
    for ok, lista in per.items():
        med = [x for x in lista if x.kort]
        r.append(f"| {ok} | {len(lista)} | {len(lista) - len(med)} | {len(med)} | "
                 f"{sum(len(x.kort) for x in lista)} | {sum(len(x.datafel) for x in lista)} |")

    r += ["", "## Ljudregler som används", "",
          "En ljudanpassning som beror på ljudet och inte på klassen är ett eget "
          "regelkort. Antal ord där regeln ger minst en form:", "",
          "| regel | ord | vad den gör |", "|---|---|---|"]
    använt = Counter(regel for x in utfall for regel in x.regler)
    for regel, beskrivning in regler.LJUDREGLER.items():
        r.append(f"| `{regel}` | {använt.get(regel, 0)} | {beskrivning} |")

    r += ["", "## Att granska", ""]
    r += [f"{i}. {punkt}" for i, punkt in enumerate(regler.GRANSKA, 1)]

    for ok, lista in per.items():
        med = [x for x in lista if x.kort]
        r += ["", f"## {ok}: ord med undantagskort ({len(med)})", "",
              "| ord | kort |", "|---|---|"]
        for x in med:
            kort = " · ".join(f"{namn(c)} **{f}**" for c, f in x.kort.items())
            r.append(f"| {visa(x)} | {kort} |")

    saknas = [(x, c, form) for x in utfall for c, form in x.saknas.items()]
    if saknas:
        r += ["", f"## Former som reglerna ger men datan saknar ({len(saknas)})", "",
              "Här betyder en saknad form något: ordet uttrycks med ett annat ord "
              "(`mer`, `more`) eller böjs inte så. Antingen avviker ordet från "
              "reglerna — och det är kunskap om ordet — eller så saknas formen i datan.",
              "", "| ord | cell | reglerna ger |", "|---|---|---|"]
        for x, c, form in saknas:
            r.append(f"| {visa(x)} | {namn(c)} | {form} |")

    fel = [(x, c, form, skäl) for x in utfall for c, (form, skäl) in x.datafel.items()]
    r += ["", f"## Misstänkta datafel ({len(fel)})", "",
          "| ord | cell | i datan | skäl |", "|---|---|---|---|"]
    for x, c, form, skäl in fel:
        r.append(f"| {visa(x)} | {namn(c)} | {form} | {skäl} |")
    return "\n".join(r) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Kör böjningsreglerna mot databasen.")
    p.add_argument("språk", choices=sorted(SPRÅK))
    p.add_argument("--db", default=str(ROT / "sprak.db"))
    a = p.parse_args(argv)

    utfall = kör(a.språk, sqlite3.connect(a.db))
    mapp = ROT / "ordbok" / "regelkontroll"
    mapp.mkdir(parents=True, exist_ok=True)
    (mapp / f"{a.språk}.md").write_text(rapport(a.språk, utfall), encoding="utf-8")
    with open(mapp / f"{a.språk}_kort.tsv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["ordklass", "koncept", "variant", "lemma", "cell", "form", "sort", "anmärkning"])
        for x in utfall:
            for c, form in x.kort.items():
                w.writerow([x.ordklass, x.koncept, x.variant, x.lemma, c, form, "undantag", ""])
            for c, (form, skäl) in x.datafel.items():
                w.writerow([x.ordklass, x.koncept, x.variant, x.lemma, c, form, "datafel", skäl])

    per = defaultdict(list)
    for x in utfall:
        per[x.ordklass].append(x)
    for ok, lista in per.items():
        print(f"{ok:<11} ord={len(lista):<4} regelbundna={sum(1 for x in lista if not x.kort):<4} "
              f"kort={sum(len(x.kort) for x in lista):<4} datafel={sum(len(x.datafel) for x in lista)}")
    print(f"skrev {mapp / (a.språk + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
