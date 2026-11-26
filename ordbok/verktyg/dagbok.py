"""Läs dagboken: hela situationen kring varje ställd mening.

Dagboken skrivs av `kort/dagbok.py` vid bokföringen, en JSON-rad per mening.
Den här filen gör raderna läsbara.

VAD DEN SVARAR PÅ, i den ordning Julius ställde frågorna:

    1  vilken mening som tränades          uppgift, facit och specen
    2  vilka kort som prövades             alla, inte bara de som fick betyg
    3  varför kortet var med               `härkomst`, och om det var infört
    4  vad som svarades och vad det gjorde  svar, dom, betyg, före → efter
    5  var kortet hamnade                   `hamnade`
    6  varför meningen valdes               poängen och om nödutgången togs

MARKERINGARNA ÄR DE FEL SOM FAKTISKT HÄNT, inte generella varningar:

    ⚠ oanmält ord     ett ORDKORT kom in genom en mening i stället för
                      glosläget — C5:s läcka, täppt tre gånger
    ⚠ före sitt ord   ett böjningskort prövades medan dess ord är oinfört (A4)
    ⚠ tomgång         meningen bokförde noll kort (C4)
    ⚠ nödfall         ordagrann upprepning, sista utvägen (B8)

Larmen är AVSIKTLIGT FÅ. Första versionen flaggade varje kort utan `sedd`
och passrad, men ett ordföljdskort införs aldrig i glosläget och står aldrig
i passet — larmet tjöt på var tredje mening. Ett larm som alltid tjuter lär
läsaren att bläddra förbi.

Kör:  python ordbok/verktyg/dagbok.py                  senaste dagboken
      python ordbok/verktyg/dagbok.py --lista          alla dagböcker
      python ordbok/verktyg/dagbok.py FIL --mening 3   en mening i detalj
      python ordbok/verktyg/dagbok.py FIL --problem    bara det som ser fel ut
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROT / "src"))

from sprakprog.kort.dagbok import KATALOG, dagböcker, läs   # noqa: E402

#: Härkomster som betyder "kortet stod i dagens plan".
PLANERADE = {"ny", "glosa", "förfallen", "igen"}


def _tid(post: dict) -> str:
    return post["tid"][11:19]


def _varningar(post: dict) -> list[str]:
    ut = []
    for k in post["kort"]:
        if k.get("oanmäld"):
            ut.append(f"oanmält ord: {k['facit']!r} kom in genom en mening "
                      f"i stället för glosläget")
        if k.get("före_sitt_ord"):
            ut.append(f"före sitt ord: {k['typ']}:{k['facit']!r} prövades "
                      f"medan ordet är oinfört (A4)")
    # NYINTRODUCERADE UTAN PLAN — en NOTIS och inte ett fel, eftersom Julius
    # avgjort att medföljande kort är gratis när de går rätt. Men de ska
    # SYNAS: han läste tre dagars dagbok och undrade varför kort dök upp som
    # inte introducerats, och svaret stod i datan utan att stå i sammandraget.
    utan_plan = [k for k in post["kort"] if k["härkomst"] == "medföljande-ny"
                 and k["bokförd"]]
    if utan_plan:
        ut.append("infördes av meningen, inte av planen: "
                  + ", ".join(f"{k['typ']}:{k['facit']!r}" for k in utan_plan))
    if not any(k["bokförd"] for k in post["kort"]):
        ut.append("tomgång: meningen bokförde noll kort")
    if post["urval"].get("nödfall"):
        ut.append("nödfall: ordagrann upprepning, sista utvägen")
    if post["urval"].get("reserv_släppt"):
        ut.append("reserv: okändgränsen släpptes, inga rena kandidater fanns")
    return ut


def sammanfatta(poster: list[dict]) -> None:
    """En rad per mening. Översikten man börjar i."""
    for i, p in enumerate(poster, 1):
        v = _varningar(p)
        bok = sum(1 for k in p["kort"] if k["bokförd"])
        fel = sum(1 for k in p["kort"] if k["dom"] is False)
        märke = "✗" if not p["korrekt"] else " "
        print(f"  {i:>3} {_tid(p)} {märke} {p['facit'][:38]:<38} "
              f"{len(p['kort']):>2} kort · {bok} bokförda · {fel} fel"
              + ("   ⚠ " + " · ".join(v) if v else ""))


def _pil(k: dict) -> str:
    """Förfallodagen före → efter. Det är här ett schemaläggningsfel syns."""
    f, e = k["före"], k["efter"]
    def d(x):
        return (x or {}).get("förfaller") or "—"
    return f"{d(f)[:10]} → {d(e)[:10]}"


def visa(post: dict, nr: int) -> None:
    """En mening i sin helhet."""
    print(f"\n{'═' * 78}")
    print(f"MENING {nr} · {_tid(post)} · kurs {post['kurs']['id']} "
          f"{post['kurs']['käll']}→{post['kurs']['mål']} "
          f"nivå {post['kurs']['nivå']}"
          + (f" · pass {post['pass']['id']} ({post['pass']['läge']})"
             if post["pass"] else " · UTAN PASS"))
    print(f"{'═' * 78}")
    print(f"  uppgift   {post['uppgift']}")
    print(f"  facit     {post['facit']}")
    print(f"  svar      {post['svar']}"
          + ("" if post["korrekt"] else "        ← FEL"))
    if post.get("millisekunder"):
        print(f"  tid       {post['millisekunder'] / 1000:.1f} s")

    d = post.get("dagsläge") or {}
    if d.get("före"):
        f, e = d["före"], d.get("efter") or {}
        rader = [f"{n} {f.get(n)}→{e.get(n)}" for n in
                 ("att_göra", "förfallna", "nya", "igen", "glosor")
                 if f.get(n) != e.get(n) or f.get(n)]
        print(f"  dagen     {' · '.join(rader)}")

    u = post["urval"]
    if u.get("poäng"):
        delar = " ".join(f"{k}={v:+.2f}" for k, v in sorted(u["poäng"].items())
                         if abs(v) > 0.005)
        print(f"  urval     förväntat {u.get('förväntat')} · {delar}")

    for v in _varningar(post):
        print(f"  ⚠ {v}")

    print(f"\n  {'kort':<26} {'härkomst':<12} {'dom':<4} {'läge':<14} "
          f"{'förfaller':<25} hamnade")
    print(f"  {'-' * 74}")
    for k in post["kort"]:
        namn = f"{k['typ']}:{k['facit']}"
        dom = "✓" if k["dom"] is True else "✗" if k["dom"] is False else "–"
        flagga = " ⚠" if k.get("oanmäld") or k.get("före_sitt_ord") else ""
        print(f"  {namn[:26]:<26} {k['härkomst']:<12} {dom:<4} "
              f"{str(k['läge'] or '—')[:14]:<14} {_pil(k):<25} "
              f"{k['hamnade']}{flagga}")
        f, e = k["före"] or {}, k["efter"] or {}
        if k["bokförd"] and (f.get("stabilitet") or e.get("stabilitet")):
            print(f"  {'':<26} S {f.get('stabilitet') or 0:.2f} → "
                  f"{e.get('stabilitet') or 0:.2f}   "
                  f"D {f.get('svårighet') or 0:.2f} → "
                  f"{e.get('svårighet') or 0:.2f}"
                  + (f"   R före {k['r_före']:.3f}" if k.get("r_före") else ""))

    if post["anmärkningar"]:
        print("\n  anmärkningar ur rättningen:")
        for a in post["anmärkningar"]:
            print(f"    {a}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fil", nargs="?", type=Path)
    p.add_argument("--lista", action="store_true", help="visa alla dagböcker")
    p.add_argument("--mening", type=int, help="visa EN mening i sin helhet")
    p.add_argument("--allt", action="store_true", help="visa alla i sin helhet")
    p.add_argument("--problem", action="store_true",
                   help="bara meningar med en varning")
    a = p.parse_args()

    böcker = dagböcker()
    if a.lista:
        if not böcker:
            print(f"Ingen dagbok än. De skrivs till {KATALOG}/ när du övar.")
            return 0
        for b in böcker:
            print(f"  {b.name:<34} {len(läs(b)):>3} meningar")
        return 0

    sökväg = a.fil or (böcker[-1] if böcker else None)
    if sökväg is None:
        print(f"Ingen dagbok än. De skrivs till {KATALOG}/ när du övar.",
              file=sys.stderr)
        return 1
    poster = läs(sökväg)
    if not poster:
        print(f"{sökväg} är tom.", file=sys.stderr)
        return 1

    print(f"{sökväg.name} — {len(poster)} meningar\n")
    if a.mening:
        if not 1 <= a.mening <= len(poster):
            print(f"Meningen finns inte; det är {len(poster)} i filen.",
                  file=sys.stderr)
            return 1
        visa(poster[a.mening - 1], a.mening)
        return 0
    if a.allt or a.problem:
        for i, post in enumerate(poster, 1):
            if a.problem and not _varningar(post):
                continue
            visa(post, i)
        return 0

    sammanfatta(poster)
    med_varning = sum(1 for post in poster if _varningar(post))
    print(f"\n  {med_varning} av {len(poster)} meningar har en varning."
          if med_varning else "\n  Inga varningar.")
    print("  --mening N för en i sin helhet, --problem för bara de flaggade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
