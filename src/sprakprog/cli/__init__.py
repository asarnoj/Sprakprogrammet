"""CLI-router för ordbok-kommandot.

Användning:
    ordbok import <csv> [<csv> ...]
    ordbok lista [--språk sv]
    ordbok visa <koncept>
    ordbok lägg-till
    ordbok mappa-kaikki --språk sv --ordklass Verb --lemma tala
    ordbok generera --alla-språk --fortsätt
    ordbok exportera-former ordbok/former.tsv
    ordbok importera-former ordbok/former.tsv --ersätt
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ordbok",
        description="Ordbokshantering för språkprogrammet.",
    )
    sub = parser.add_subparsers(dest="kommando", required=True)

    # ── import ───────────────────────────────────────────────────────────
    p_import = sub.add_parser("import", help="Importera CSV-filer till sprak.db")
    p_import.add_argument("filer", nargs="+", help="CSV-filer att importera")
    p_import.add_argument(
        "--återinitiera",
        action="store_true",
        help="Radera och återskapa databasen innan import",
    )

    # ── lista ────────────────────────────────────────────────────────────
    p_lista = sub.add_parser("lista", help="Översikt av alla koncept")
    p_lista.add_argument("--språk", default="sv", help="Vilket språks lemma att visa")
    p_lista.add_argument("--källa", help="Filtrera på källa (t.ex. bas_kärna)")
    p_lista.add_argument("--ordklass", help="Filtrera på ordklass")

    # ── visa ─────────────────────────────────────────────────────────────
    p_visa = sub.add_parser("visa", help="Drill-down för ett koncept")
    p_visa.add_argument("koncept", help="Koncept-nyckel, t.ex. rör_gå")

    # ── lägg-till ────────────────────────────────────────────────────────
    sub.add_parser("lägg-till", help="Interaktivt lägga till nytt koncept")

    # ── mappa-kaikki ─────────────────────────────────────────────────────
    p_mappa = sub.add_parser(
        "mappa-kaikki",
        help="Slå upp ett lemma i kaikki-dumpen och matcha mot slot-filen",
    )
    p_mappa.add_argument("--språk",    required=True, help="sv (övriga ej implementerade)")
    p_mappa.add_argument("--ordklass", required=True, help="Verb / Substantiv / ...")
    p_mappa.add_argument("--lemma",    required=True, help="lemmaformen, t.ex. 'tala'")
    p_mappa.add_argument("--json",     action="store_true", help="JSON-output istället för text")

    # ── exportera-former / importera-former ──────────────────────────────
    p_exp = sub.add_parser(
        "exportera-former",
        help="Skriv Former-tabellen till en TSV-fil (för överföring/granskning)",
    )
    p_exp.add_argument("fil", help="Målfil, t.ex. ordbok/former.tsv")

    p_imp = sub.add_parser(
        "importera-former",
        help="Läs in en Former-TSV i sprak.db",
    )
    p_imp.add_argument("fil", help="TSV-fil från 'ordbok exportera-former'")
    p_imp.add_argument(
        "--ersätt",
        action="store_true",
        help="Radera befintliga Former-rader innan import",
    )

    # ── tagga-koncept / tagga-monster ────────────────────────────────────
    from .tagga import lägg_till_argument as _tagga_args
    _tagga_args(sub.add_parser(
        "tagga-koncept",
        help="Fyll gradbarhet, räknebar, valens och semantik på Koncept"), 25)
    _tagga_args(sub.add_parser(
        "tagga-lexem",
        help="Fyll genus (substantiv) och prenominal (adjektiv) på Lexem"), 30)
    _tagga_args(sub.add_parser(
        "tagga-monster",
        help="Bygg valensmönster (Mönster + MönsterKrav) för verben"), 10)

    # ── generera ─────────────────────────────────────────────────────────
    p_generera = sub.add_parser(
        "generera",
        help="Generera böjda former via Claude API och skriv till Former-tabellen",
    )
    from .generera import lägg_till_argument as _generera_args
    _generera_args(p_generera)

    # ── tillämpa-granskning ──────────────────────────────────────────────
    p_ratt = sub.add_parser(
        "tillämpa-granskning",
        help="Skriv in granskningens förslag i Former (inga LLM-anrop)")
    from .rattelse import lägg_till_argument as _ratt_args
    _ratt_args(p_ratt)

    # ── granska-former ───────────────────────────────────────────────────
    p_granska = sub.add_parser(
        "granska-former",
        help="Låt en starkare modell läsa igenom Former och rapportera avvikelser",
    )
    from .granska import lägg_till_argument as _granska_args
    _granska_args(p_granska)

    # ── rendera ──────────────────────────────────────────────────────────
    p_rendera = sub.add_parser(
        "rendera",
        help="Rendera en meningsspecifikation till ett språk")
    from .rendera import lägg_till_argument as _rendera_args
    _rendera_args(p_rendera)

    # ── kort och övning ──────────────────────────────────────────────────
    from .kort import lägg_till_parser as _kort_parser
    from .kurs import lägg_till_parser as _kurs_parser
    from .ova import lägg_till_parser as _ova_parser
    _kort_parser(sub)
    _ova_parser(sub)
    _kurs_parser(sub)

    args = parser.parse_args(argv)

    if args.kommando in ("kort", "öva", "kurs", "webb"):
        return args.func(args)


    # Lazy import för snabb startup på enskilda kommandon
    if args.kommando == "import":
        from .importera import kör as kör_import
        return kör_import(args)
    if args.kommando == "lista":
        from .lista import kör as kör_lista
        return kör_lista(args)
    if args.kommando == "visa":
        from .visa import kör as kör_visa
        return kör_visa(args)
    if args.kommando == "lägg-till":
        from .lägg_till import kör as kör_lägg_till
        return kör_lägg_till(args)
    if args.kommando == "mappa-kaikki":
        from .mappa_kaikki import kör as kör_mappa_kaikki
        return kör_mappa_kaikki(args)
    if args.kommando == "exportera-former":
        from .former import kör_export
        return kör_export(args)
    if args.kommando == "importera-former":
        from .former import kör_import
        return kör_import(args)
    if args.kommando == "generera":
        from .generera import kör as kör_generera
        return kör_generera(args)
    if args.kommando == "tagga-koncept":
        from .tagga import kör_koncept
        return kör_koncept(args)
    if args.kommando == "tagga-lexem":
        from .tagga import kör_lexem
        return kör_lexem(args)
    if args.kommando == "tagga-monster":
        from .tagga import kör_monster
        return kör_monster(args)
    if args.kommando == "tillämpa-granskning":
        from .rattelse import kör as kör_rattelse
        return kör_rattelse(args)
    if args.kommando == "granska-former":
        from .granska import kör as kör_granska
        return kör_granska(args)

    if args.kommando == "rendera":
        from .rendera import kör as kör_rendera
        return kör_rendera(args)

    parser.error(f"okänt kommando: {args.kommando}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
