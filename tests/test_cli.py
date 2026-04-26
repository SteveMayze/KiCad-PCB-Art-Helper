from pathlib import Path

from kicad_merge.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_writes_output_for_shorthand_and_generic_layers(tmp_path):
    output = tmp_path / "combined.kicad_mod"

    exit_code = main(
        [
            "--output",
            str(output),
            "--f.silk",
            str(FIXTURES / "silk.kicad_mod"),
            "--layer",
            f'Dwgs.User={FIXTURES / "user-text.kicad_mod"}',
        ]
    )

    merged = output.read_text(encoding="utf-8")
    assert exit_code == 0
    assert '(layer "F.SilkS")' in merged
    assert '(layer "Dwgs.User")' in merged
    assert merged.count('(fp_text reference "G***"') == 1