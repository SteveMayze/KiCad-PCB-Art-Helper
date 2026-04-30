from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
import sys
from typing import Any

import yaml

from .merger import MergeInput, merge_footprints


LAYER_ALIASES = {
    "F.Cu": ["--f.cu"],
    "B.Cu": ["--b.cu"],
    "F.Mask": ["--f.mask"],
    "B.Mask": ["--b.mask"],
    "F.Paste": ["--f.paste"],
    "B.Paste": ["--b.paste"],
    "F.SilkS": ["--f.silk", "--f.silks"],
    "B.SilkS": ["--b.silk", "--b.silks"],
}


class LayerMappingAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        items = list(getattr(namespace, self.dest, []) or [])
        layer, path = _parse_layer_mapping(values)
        items.append(MergeInput(layer=layer, path=Path(path)))
        setattr(namespace, self.dest, items)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kicad-merge",
        description="Merge layer-specific KiCad footprint files into a single .kicad_mod footprint.",
    )
    parser.add_argument("--config", type=Path, help="Path to a YAML config file.")
    parser.add_argument("--output", type=Path, help="Path for the merged .kicad_mod file.")
    parser.add_argument("--name", help="Override the footprint name written into the merged file.")
    parser.add_argument(
        "--layer",
        action=LayerMappingAction,
        default=[],
        metavar="LAYER=FILE",
        help="Map any KiCad layer name to an input footprint file. Repeat as needed.",
    )

    for layer, flags in LAYER_ALIASES.items():
        parser.add_argument(
            *flags,
            dest="shorthand_inputs",
            action="append",
            default=[],
            metavar="FILE",
            type=Path,
            help=f"Source footprint file for {layer}.",
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = _load_config(parser, args.config)

    sources = _collect_config_sources(parser, config, args.config)
    sources.extend(args.layer)
    sources.extend(_collect_shorthand_sources(parser, argv if argv is not None else sys.argv[1:]))
    sources = _dedupe_sources_keep_last(sources)
    if not sources:
        parser.error("provide at least one layer input")

    output = args.output or _parse_optional_path(parser, config, "output", args.config)
    if output is None:
        parser.error("provide --output or set output in --config")

    name = args.name if args.name is not None else _parse_optional_string(parser, config, "name")

    merged = merge_footprints(sources, footprint_name=name)
    output.write_text(merged, encoding="utf-8")
    return 0


def _load_config(parser: argparse.ArgumentParser, config_path: Path | None) -> Mapping[str, Any]:
    if config_path is None:
        return {}

    if not config_path.exists():
        parser.error(f"config file not found: {config_path}")

    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        parser.error(f"invalid YAML config file: {config_path}: {exc}")

    if loaded is None:
        return {}
    if not isinstance(loaded, Mapping):
        parser.error("config root must be a mapping")
    return loaded


def _collect_config_sources(
    parser: argparse.ArgumentParser,
    config: Mapping[str, Any],
    config_path: Path | None,
) -> list[MergeInput]:
    layers = config.get("layers")
    if layers is None:
        return []
    if not isinstance(layers, Mapping):
        parser.error("config field 'layers' must be a mapping of LAYER: FILE")

    sources: list[MergeInput] = []
    for layer, file_path in layers.items():
        if not isinstance(layer, str) or not layer.strip():
            parser.error("config 'layers' keys must be non-empty strings")
        if not isinstance(file_path, str) or not file_path.strip():
            parser.error(f"config 'layers.{layer}' value must be a non-empty string")
        path = Path(file_path)
        if not path.is_absolute() and config_path is not None:
            path = config_path.parent / path
        sources.append(MergeInput(layer=layer.strip(), path=path))
    return sources


def _parse_optional_path(
    parser: argparse.ArgumentParser,
    config: Mapping[str, Any],
    key: str,
    config_path: Path | None,
) -> Path | None:
    value = config.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        parser.error(f"config field '{key}' must be a non-empty string")
    path = Path(value)
    if not path.is_absolute() and config_path is not None:
        path = config_path.parent / path
    return path


def _parse_optional_string(parser: argparse.ArgumentParser, config: Mapping[str, Any], key: str) -> str | None:
    value = config.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        parser.error(f"config field '{key}' must be a non-empty string")
    return value


def _dedupe_sources_keep_last(sources: list[MergeInput]) -> list[MergeInput]:
    deduped: dict[str, MergeInput] = {}
    for source in sources:
        deduped[source.layer] = source
    return list(deduped.values())


def _collect_shorthand_sources(parser: argparse.ArgumentParser, argv: list[str]) -> list[MergeInput]:
    known_flags: dict[str, str] = {}
    for layer, flags in LAYER_ALIASES.items():
        for flag in flags:
            known_flags[flag] = layer

    sources: list[MergeInput] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        layer = known_flags.get(token)
        if layer is None:
            index += 1
            continue
        if index + 1 >= len(argv):
            parser.error(f"{token} requires a file path")
        sources.append(MergeInput(layer=layer, path=Path(argv[index + 1])))
        index += 2
    return sources


def _parse_layer_mapping(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected LAYER=FILE")
    layer, path = value.split("=", 1)
    layer = layer.strip()
    path = path.strip()
    if not layer or not path:
        raise argparse.ArgumentTypeError("expected LAYER=FILE")
    return layer, path


if __name__ == "__main__":
    raise SystemExit(main())