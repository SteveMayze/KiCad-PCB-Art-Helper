from __future__ import annotations

import argparse
from pathlib import Path
import sys

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
    parser.add_argument("--output", required=True, type=Path, help="Path for the merged .kicad_mod file.")
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

    sources = list(args.layer)
    sources.extend(_collect_shorthand_sources(parser, argv if argv is not None else sys.argv[1:]))
    if not sources:
        parser.error("provide at least one layer input")

    merged = merge_footprints(sources, footprint_name=args.name)
    args.output.write_text(merged, encoding="utf-8")
    return 0


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