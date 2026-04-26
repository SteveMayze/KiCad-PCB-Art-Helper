$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$srcDir = Join-Path $repoRoot "src"

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = "python"
}

$env:PYTHONPATH = if ($env:PYTHONPATH) { "$srcDir;$env:PYTHONPATH" } else { $srcDir }

& $pythonExe -m kicad_merge @args
exit $LASTEXITCODE