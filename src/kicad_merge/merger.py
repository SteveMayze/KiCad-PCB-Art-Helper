from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


KEEP_FROM_BASE = {
    "version",
    "generator",
    "generator_version",
    "layer",
    "attr",
    "descr",
    "tags",
    "property",
    "model",
    "tedit",
    "solder_mask_margin",
    "solder_paste_margin",
    "solder_paste_ratio",
    "clearance",
    "zone_connect",
    "net_tie_pad_groups",
}

MERGEABLE_HEADS = {
    "fp_line",
    "fp_rect",
    "fp_circle",
    "fp_arc",
    "fp_poly",
    "fp_curve",
    "fp_text",
}

UUID_PATTERN = re.compile(r"\s*\(uuid\s+[^()]+\)")
LAYER_PATTERN = re.compile(r"\(layer\s+\"[^\"]+\"\)")


@dataclass(frozen=True)
class MergeInput:
    layer: str
    path: Path


@dataclass(frozen=True)
class Footprint:
    name: str
    forms: tuple[str, ...]


def merge_footprints(sources: list[MergeInput], footprint_name: str | None = None) -> str:
    if not sources:
        raise ValueError("at least one source footprint is required")

    parsed = [_parse_footprint(source.path.read_text(encoding="utf-8")) for source in sources]
    base = parsed[0]
    name = footprint_name or _unquote_atom(base.name)

    target_footprint_layer = sources[0].layer
    kept_forms = [
        _retarget_base_form(form, target_footprint_layer)
        for form in base.forms
        if _keep_from_base(form)
    ]
    merged_items: list[str] = []
    for source, footprint in zip(sources, parsed, strict=True):
        merged_items.extend(_retarget_item(form, source.layer) for form in footprint.forms if _is_mergeable_item(form))

    all_forms = [*kept_forms, *merged_items]
    body = "\n".join(_indent(form, 2) for form in all_forms)
    return f'(footprint "{name}"\n{body}\n)\n'


def _parse_footprint(content: str) -> Footprint:
    text = content.strip()
    if not text.startswith("("):
        raise ValueError("footprint file must start with '('")

    end_index = _scan_form(text, 0)
    if end_index != len(text):
        raise ValueError("expected a single top-level footprint form")

    inner = text[1:-1].strip()
    index = 0
    head, index = _read_atom(inner, index)
    if head != "footprint":
        raise ValueError("top-level form must be a footprint")

    name, index = _read_atom(inner, index)
    forms: list[str] = []
    while True:
        index = _skip_ws(inner, index)
        if index >= len(inner):
            break
        if inner[index] != "(":
            raise ValueError("unexpected token in footprint body")
        form_end = _scan_form(inner, index)
        forms.append(inner[index:form_end])
        index = form_end

    return Footprint(name=name, forms=tuple(forms))


def _keep_from_base(form: str) -> bool:
    head = _form_head(form)
    if head in KEEP_FROM_BASE:
        return True
    if head == "fp_text":
        subtype = _fp_text_subtype(form)
        return subtype in {"reference", "value"}
    return False


def _is_mergeable_item(form: str) -> bool:
    head = _form_head(form)
    if head not in MERGEABLE_HEADS:
        return False
    if head == "fp_text":
        return _fp_text_subtype(form) not in {"reference", "value"}
    return True


def _retarget_item(form: str, layer: str) -> str:
    without_uuid = UUID_PATTERN.sub("", form)
    return LAYER_PATTERN.sub(f'(layer "{layer}")', without_uuid)


def _retarget_base_form(form: str, layer: str) -> str:
    if _form_head(form) != "layer":
        return form
    return f'(layer "{layer}")'


def _form_head(form: str) -> str:
    inner = form[1:-1]
    head, _ = _read_atom(inner, 0)
    return head


def _fp_text_subtype(form: str) -> str:
    inner = form[1:-1]
    _, index = _read_atom(inner, 0)
    subtype, _ = _read_atom(inner, index)
    return subtype


def _indent(block: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else line for line in block.splitlines())


def _skip_ws(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _read_atom(text: str, index: int) -> tuple[str, int]:
    index = _skip_ws(text, index)
    if index >= len(text):
        raise ValueError("unexpected end of input")

    if text[index] == '"':
        start = index
        index += 1
        while index < len(text):
            char = text[index]
            if char == '"' and text[index - 1] != "\\":
                return text[start : index + 1], index + 1
            index += 1
        raise ValueError("unterminated string")

    start = index
    while index < len(text) and not text[index].isspace() and text[index] not in "()":
        index += 1
    if start == index:
        raise ValueError("expected atom")
    return text[start:index], index


def _scan_form(text: str, start: int) -> int:
    if text[start] != "(":
        raise ValueError("expected form")

    depth = 0
    in_string = False
    index = start
    while index < len(text):
        char = text[index]
        if char == '"' and (index == start or text[index - 1] != "\\"):
            in_string = not in_string
        elif not in_string:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return index + 1
        index += 1
    raise ValueError("unterminated form")


def _unquote_atom(atom: str) -> str:
    if len(atom) >= 2 and atom[0] == '"' and atom[-1] == '"':
        return atom[1:-1]
    return atom