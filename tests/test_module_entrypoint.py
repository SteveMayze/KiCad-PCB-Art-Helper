from pathlib import Path
import subprocess
import sys


FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parent.parent


def test_python_module_entrypoint_writes_output(tmp_path):
    output = tmp_path / "combined.kicad_mod"
    environment = {
        **__import__("os").environ,
        "PYTHONPATH": str(REPO_ROOT / "src"),
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "kicad_merge",
            "--output",
            str(output),
            "--f.silk",
            str(FIXTURES / "silk.kicad_mod"),
            "--f.mask",
            str(FIXTURES / "mask.kicad_mod"),
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.exists()