from pathlib import Path

from kicad_merge.merger import MergeInput, merge_footprints


FIXTURES = Path(__file__).parent / "fixtures"


def test_merge_footprints_combines_graphics_and_keeps_single_metadata_block():
    merged = merge_footprints(
        [
            MergeInput(layer="F.SilkS", path=FIXTURES / "silk.kicad_mod"),
            MergeInput(layer="F.Mask", path=FIXTURES / "mask.kicad_mod"),
        ],
        footprint_name="COMBINED_ART",
    )

    assert '(footprint "COMBINED_ART"' in merged
    assert merged.count('(fp_text reference "G***"') == 1
    assert merged.count('(fp_text value "ART"') == 1
    assert merged.count('(fp_poly') == 2
    assert '(layer "F.Cu")' not in merged
    assert '(layer "F.SilkS")' in merged
    assert '(layer "F.Mask")' in merged
    assert 'uuid silk-poly' not in merged
    assert 'uuid mask-poly' not in merged


def test_merge_footprints_keeps_non_reference_text_items():
    merged = merge_footprints(
        [MergeInput(layer="Dwgs.User", path=FIXTURES / "user-text.kicad_mod")]
    )

    assert '(fp_text user "LABEL"' in merged
    assert '(layer "Dwgs.User")' in merged


def test_merge_footprints_retargets_footprint_top_level_layer():
    merged = merge_footprints(
        [MergeInput(layer="B.Cu", path=FIXTURES / "silk.kicad_mod")]
    )

    assert '(layer "B.Cu")' in merged
    assert '(layer "F.Cu")' not in merged