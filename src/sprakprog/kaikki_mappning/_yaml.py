"""Minimal YAML-läsare för paradigm-/legend-filer.

INTE en allmän YAML-parser. Stöder enbart formatet som faktiskt används
i `paradigm/_legend.yaml` och `paradigm/{språk}/*.yaml`:

  • Topp-nivå mapping
  • Nestade mappings via 2-spaces-indent
  • Listor av mappings:  - key: value
                           key2: value2
  • Inline-listor:  [A, B, C]
  • Folded scalar:  > följt av indenterade rader
  • Hela-radens-kommentarer:   # ...
  • Inline-kommentarer:        key: value  # comment
  • Dokumentstart:  ---
  • Skalärer: int, str (citerad eller bare-ord), null, true/false

Höjer ValueError med radnummer vid syntaxfel. Räcker för slot-filerna —
om vi behöver mer komplex YAML, byter vi till PyYAML då (med dep).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def lasa_fil(sökväg: Path) -> dict[str, Any]:
    """Läs och parsa en YAML-fil. Returnerar en dict."""
    return parsa(sökväg.read_text(encoding="utf-8"))


def parsa(text: str) -> dict[str, Any]:
    """Parsa YAML-text och returnera en dict."""
    return _Parser(text).parse_top()


class _Parser:
    def __init__(self, text: str):
        self._lines: list[tuple[int, str]] = []
        for lineno, raw in enumerate(text.splitlines(), 1):
            # Strippa inline-kommentar (allt efter första #)
            content = raw.split("#", 1)[0].rstrip()
            if not content or content.strip() == "---":
                continue
            self._lines.append((lineno, content))
        self._pos = 0

    def parse_top(self) -> dict[str, Any]:
        return self._parse_mapping(0)

    def _peek(self) -> tuple[int, str] | None:
        if self._pos >= len(self._lines):
            return None
        return self._lines[self._pos]

    def _curr_indent(self) -> int:
        c = self._peek()
        if c is None:
            return -1
        return len(c[1]) - len(c[1].lstrip())

    def _parse_mapping(self, expected_indent: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        while True:
            c = self._peek()
            if c is None:
                break
            indent = self._curr_indent()
            if indent < expected_indent:
                break
            if indent > expected_indent:
                raise ValueError(
                    f"Oväntad indent på rad {c[0]}: '{c[1]}' (väntade {expected_indent})"
                )
            stripped = c[1].strip()
            if ":" not in stripped:
                raise ValueError(f"Förväntad 'key: value' på rad {c[0]}: '{stripped}'")
            key, _, val = stripped.partition(":")
            key, val = key.strip(), val.strip()
            self._pos += 1
            result[key] = self._parse_value_after_key(val, expected_indent)
        return result

    def _parse_value_after_key(self, val: str, key_indent: int) -> Any:
        if val == ">":
            return self._parse_folded(key_indent + 1)
        if val == "":
            # Block: nested mapping eller lista
            nxt = self._peek()
            if nxt is None:
                return None
            nxt_indent = self._curr_indent()
            if nxt_indent <= key_indent:
                return None
            nxt_stripped = nxt[1].strip()
            if nxt_stripped.startswith("- "):
                return self._parse_list(nxt_indent)
            return self._parse_mapping(nxt_indent)
        return self._parse_scalar(val)

    def _parse_list(self, expected_indent: int) -> list[Any]:
        items: list[Any] = []
        while True:
            c = self._peek()
            if c is None:
                break
            indent = self._curr_indent()
            if indent < expected_indent:
                break
            if indent > expected_indent:
                raise ValueError(f"Oväntad listindent på rad {c[0]}: '{c[1]}'")
            stripped = c[1].strip()
            if not stripped.startswith("- "):
                break
            after_dash = stripped[2:]
            self._pos += 1

            item: dict[str, Any] = {}
            child_indent = expected_indent + 2

            # Första nyckeln efter '- '
            if ":" in after_dash:
                k, _, v = after_dash.partition(":")
                k, v = k.strip(), v.strip()
                item[k] = self._parse_value_after_key(v, child_indent)

            # Resterande nycklar i samma listobjekt
            while True:
                c2 = self._peek()
                if c2 is None:
                    break
                ind2 = self._curr_indent()
                if ind2 != child_indent:
                    break
                s2 = c2[1].strip()
                if s2.startswith("- "):
                    break
                if ":" not in s2:
                    raise ValueError(f"Oväntad rad i listobjekt: '{s2}'")
                k, _, v = s2.partition(":")
                k, v = k.strip(), v.strip()
                self._pos += 1
                item[k] = self._parse_value_after_key(v, child_indent)

            items.append(item)
        return items

    def _parse_folded(self, min_indent: int) -> str:
        """Folded scalar — joina rader med mellanslag, blank rad = paragraf."""
        paragraphs: list[str] = []
        current: list[str] = []
        while True:
            c = self._peek()
            if c is None:
                break
            indent = self._curr_indent()
            if indent < min_indent:
                break
            content = c[1].lstrip()
            self._pos += 1
            if not content:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(content)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)

    def _parse_scalar(self, val: str) -> Any:
        val = val.strip()
        if not val:
            return None
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                return []
            return [self._parse_scalar(s.strip()) for s in inner.split(",")]
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            return val[1:-1]
        if val in ("null", "~"):
            return None
        if val == "true":
            return True
        if val == "false":
            return False
        try:
            return int(val)
        except ValueError:
            pass
        try:
            if "." in val:
                return float(val)
        except ValueError:
            pass
        return val
