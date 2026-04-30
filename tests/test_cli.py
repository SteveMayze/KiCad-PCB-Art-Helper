from pathlib import Path

import yaml

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


def test_cli_reads_config_yaml_for_output_name_and_layers(tmp_path):
    output = tmp_path / "from-config.kicad_mod"
    config = tmp_path / "config.yaml"
    config_data = {
        "output": output.name,
        "name": "CFG_ART",
        "layers": {
            "F.SilkS": str(FIXTURES / "silk.kicad_mod"),
            "Dwgs.User": str(FIXTURES / "user-text.kicad_mod"),
        },
    }
    config.write_text(yaml.safe_dump(config_data), encoding="utf-8")

    exit_code = main(["--config", str(config)])

    merged = output.read_text(encoding="utf-8")
    assert exit_code == 0
    assert '(footprint "CFG_ART"' in merged
    assert '(layer "F.SilkS")' in merged
    assert '(layer "Dwgs.User")' in merged


def test_cli_overrides_config_with_explicit_flags(tmp_path):
    output_from_config = tmp_path / "from-config.kicad_mod"
    output_from_cli = tmp_path / "from-cli.kicad_mod"
    config = tmp_path / "config.yaml"
    config_data = {
        "output": output_from_config.name,
        "name": "FROM_CONFIG",
        "layers": {
            "F.SilkS": str(FIXTURES / "silk.kicad_mod"),
        },
    }
    config.write_text(yaml.safe_dump(config_data), encoding="utf-8")

    exit_code = main(
        [
            "--config",
            str(config),
            "--output",
            str(output_from_cli),
            "--name",
            "FROM_CLI",
            "--layer",
            f'F.SilkS={FIXTURES / "user-text.kicad_mod"}',
        ]
    )

    merged = output_from_cli.read_text(encoding="utf-8")
    assert exit_code == 0
    assert not output_from_config.exists()
    assert '(footprint "FROM_CLI"' in merged
    assert '(fp_text user "LABEL"' in merged