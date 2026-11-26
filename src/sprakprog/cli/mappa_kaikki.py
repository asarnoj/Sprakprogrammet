"""ordbok mappa-kaikki — uppslag i kaikki-dump och matchning mot slot-fil.

Användning:
    ordbok mappa-kaikki --språk sv --ordklass Verb --lemma tala
    ordbok mappa-kaikki --språk sv --ordklass Substantiv --lemma flicka --json

Default: läsbar text-rapport. --json: maskinläsbar JSON.
"""

from __future__ import annotations

import argparse
import json
import sys

from ..kaikki_mappning import KaikkiAccess, Mappningsrapport, mappa_lemma_sv
from ..kaikki_mappning.data_access import SpråkSaknas


def kör(args: argparse.Namespace) -> int:
    if args.språk != "sv":
        print(
            f"FEL: kaikki-mappning är än så länge bara implementerad för sv. "
            f"Begärt språk: {args.språk}",
            file=sys.stderr,
        )
        return 1

    try:
        access = KaikkiAccess(args.språk)
    except SpråkSaknas as e:
        print(f"FEL: {e}", file=sys.stderr)
        return 2

    rapport = mappa_lemma_sv(args.lemma, args.ordklass, access=access)

    if args.json:
        print(json.dumps(rapport.som_dict(), ensure_ascii=False, indent=2))
    else:
        skriv_text_rapport(rapport)
    return 0


def skriv_text_rapport(r: Mappningsrapport) -> None:
    print(f"=== Mappning för {r.lemma!r} ({r.ordklass}, {r.språk}) ===\n")

    print(f"Fyllda celler ({len(r.celler_fyllda)}):")
    if not r.celler_fyllda:
        print("  (inga)")
    else:
        for c in r.celler_fyllda:
            ax = _format_axlar(c.axlar)
            tags = ", ".join(c.kaikki_tags)
            print(f"  {c.cell_id:18}  {c.form:18}  axlar={ax:30}  tags=[{tags}]")
    print()

    print(f"Saknade celler ({len(r.celler_saknade)}):")
    if not r.celler_saknade:
        print("  (inga)")
    else:
        for c in r.celler_saknade:
            ax = _format_axlar(c.förväntade_axlar)
            print(f"  {c.cell_id:18}  förväntade axlar={ax}")
    print()

    print(f"Skippade former ({len(r.former_skippade)}):")
    if not r.former_skippade:
        print("  (inga)")
    else:
        for f in r.former_skippade:
            tags = ", ".join(f.kaikki_tags)
            print(f"  {f.form:18}  skäl={f.skäl:30}  tags=[{tags}]")
    print()

    print(f"Varningar ({len(r.varningar)}):")
    if not r.varningar:
        print("  (inga)")
    else:
        for v in r.varningar:
            print(f"  • {v}")


def _format_axlar(axlar: dict[str, int | None]) -> str:
    """Formatera bara icke-NULL-axlar för läsbarhet."""
    aktiva = [(a, v) for a, v in axlar.items() if v is not None]
    return "{" + ", ".join(f"{a}={v}" for a, v in aktiva) + "}"
