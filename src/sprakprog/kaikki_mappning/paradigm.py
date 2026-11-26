"""Laddare för paradigm/_legend.yaml + paradigm/{språk}/{ordklass}.yaml.

Resolverar slot-filens namnkonstanter (Inf, Aktiv, ...) till heltal
enligt legend-filen. Returnerar en lista av celler där varje cell har
sina axlar uttryckta som int (för bitmask-axlar) eller None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import _yaml

PROJEKTROT = Path(__file__).resolve().parents[3]
PARADIGM_DIR = PROJEKTROT / "paradigm"
LEGEND_FIL = PARADIGM_DIR / "_legend.yaml"

# Axlar som är IntFlag (bitmask, kombinerbara) — alla andra är IntEnum
INTFLAG_AXLAR: frozenset[str] = frozenset({"tempus", "kasus"})

# Alla möjliga Former-axlar (matchar setup.sql Former-kolumner)
ALLA_AXLAR: tuple[str, ...] = (
    "tempus", "kasus", "numerus", "species", "genus", "grad", "person", "diates"
)


@dataclass(frozen=True, slots=True)
class Cell:
    """En cell ur en slot-fil med axlar resolverade till heltal."""
    id: str
    axlar: dict[str, int | None]
    not_kommentar: str | None = None


@dataclass
class Slot:
    """Ett laddat slot-fils-innehåll."""
    språk: str
    ordklass: str
    version: int
    beskrivning: str
    celler: list[Cell] = field(default_factory=list)


def ladda_legend() -> dict[str, dict[str, int]]:
    """Läs _legend.yaml och returnera dict[axel_namn][konstant_namn] = int."""
    raw = _yaml.lasa_fil(LEGEND_FIL)
    legend: dict[str, dict[str, int]] = {}
    for nyckel, värde in raw.items():
        if nyckel == "version":
            continue
        if isinstance(värde, dict):
            legend[nyckel] = {k: int(v) for k, v in värde.items()}
    return legend


def ladda_slot(språk: str, ordklass: str, legend: dict[str, dict[str, int]] | None = None) -> Slot:
    """Läs paradigm/{språk}/{ordklass}.yaml och resolva axelnamn till heltal.

    `ordklass` matchar Koncept.ordklass-värdet, t.ex. 'Verb', 'Substantiv'.
    Filnamnet är ordklassen i lowercase (verb.yaml, substantiv.yaml).
    """
    if legend is None:
        legend = ladda_legend()

    fil = PARADIGM_DIR / språk / f"{ordklass.lower()}.yaml"
    if not fil.exists():
        raise FileNotFoundError(f"Slot-fil saknas: {fil}")
    raw = _yaml.lasa_fil(fil)

    meta = raw.get("meta", {})
    rå_celler = raw.get("celler", []) or []

    celler: list[Cell] = []
    for c in rå_celler:
        cell_id = c.get("id")
        if not cell_id:
            raise ValueError(f"Cell utan id i {fil.name}: {c}")
        axlar: dict[str, int | None] = {a: None for a in ALLA_AXLAR}
        for axel in ALLA_AXLAR:
            v = c.get(axel)
            if v is None:
                continue
            axlar[axel] = _resolve_axelvärde(axel, v, legend, fil.name, cell_id)
        celler.append(Cell(id=cell_id, axlar=axlar, not_kommentar=c.get("not")))

    return Slot(
        språk=meta.get("språk", språk),
        ordklass=meta.get("ordklass", ordklass),
        version=int(meta.get("version", 0)),
        beskrivning=meta.get("beskrivning", ""),
        celler=celler,
    )


def _resolve_axelvärde(
    axel: str,
    värde: Any,
    legend: dict[str, dict[str, int]],
    filnamn: str,
    cell_id: str,
) -> int:
    """Översätt ett axel-värde (sträng eller lista) till heltal via legend."""
    if axel not in legend:
        raise ValueError(f"Okänd axel '{axel}' i {filnamn}/{cell_id}")
    namnmappning = legend[axel]

    def slå_upp(namn: str) -> int:
        if namn not in namnmappning:
            raise ValueError(
                f"Okänd konstant '{namn}' för axel '{axel}' i {filnamn}/{cell_id}. "
                f"Tillåtna: {sorted(namnmappning)}"
            )
        return namnmappning[namn]

    if axel in INTFLAG_AXLAR:
        if not isinstance(värde, list):
            raise ValueError(
                f"IntFlag-axel '{axel}' kräver lista i {filnamn}/{cell_id}, fick {värde!r}"
            )
        bits = 0
        for n in värde:
            bits |= slå_upp(n)
        return bits

    # IntEnum — enskilt namn
    if isinstance(värde, list):
        if len(värde) != 1:
            raise ValueError(
                f"IntEnum-axel '{axel}' kräver enskilt värde i {filnamn}/{cell_id}, fick {värde!r}"
            )
        return slå_upp(värde[0])
    return slå_upp(värde)
