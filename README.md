# KiCad PCB Art Helper

`kicad-merge` combines layer-specific `.kicad_mod` footprint files into a single footprint that can be placed as PCB art.

## Running The Tool

You have three practical ways to run it.

### Option 1: Install The Command Once

From the repository root:

```bash
python -m pip install -e .
```

That installs the `kicad-merge` command exposed by [pyproject.toml](pyproject.toml). After that, you can run:

```bash
kicad-merge --output combined.kicad_mod --f.silk silk.kicad_mod --f.mask mask.kicad_mod --f.cu copper.kicad_mod
```

If you install into a virtual environment, that command is available whenever that environment is activated. If you want it available system-wide, install it into the Python environment that is already on your `PATH`, or use a tool like `pipx`.

### Option 2: Run It As A Python Module

After installing it with `python -m pip install -e .`, you can also run:

```bash
python -m kicad_merge --output combined.kicad_mod --f.silk silk.kicad_mod --f.mask mask.kicad_mod --f.cu copper.kicad_mod
```

This is useful if you prefer module-style invocation over console scripts.

### Option 3: Use The Repo Wrapper Scripts

If you do not want to install anything, wrapper scripts are included in [scripts/kicad-merge.cmd](scripts/kicad-merge.cmd), [scripts/kicad-merge.ps1](scripts/kicad-merge.ps1), and [scripts/kicad-merge.sh](scripts/kicad-merge.sh). They run the package directly from this checkout by pointing Python at the local `src` directory.

On Windows, prefer the `.cmd` wrapper from PowerShell because it does not depend on PowerShell execution policy.

Windows-safe wrapper from PowerShell:

```powershell
.\scripts\kicad-merge.cmd --output combined.kicad_mod --f.silk .\reference\SkeleKatze-Silk.kicad_mod --f.mask .\reference\SkeleKatze-Mask.kicad_mod --f.cu .\reference\SkeleKatze-Copper.kicad_mod
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\kicad-merge.ps1 --output combined.kicad_mod --f.silk .\reference\SkeleKatze-Silk.kicad_mod --f.mask .\reference\SkeleKatze-Mask.kicad_mod --f.cu .\reference\SkeleKatze-Copper.kicad_mod
```

Bash:

```bash
./scripts/kicad-merge.sh --output combined.kicad_mod --f.silk ./reference/SkeleKatze-Silk.kicad_mod --f.mask ./reference/SkeleKatze-Mask.kicad_mod --f.cu ./reference/SkeleKatze-Copper.kicad_mod
```

If you want to call one of those from anywhere, add the [scripts](scripts) directory to your shell `PATH`.

## Usage

```bash
kicad-merge --output combined.kicad_mod --f.silk silk.kicad_mod --f.mask mask.kicad_mod --f.cu copper.kicad_mod
```

Layer mapping flags are authoritative. The output remaps each merged item to the selected target layer even if the source file was generated for a different layer.

For example, passing `--b.cu some_front_layer_file.kicad_mod` will write that source content on `B.Cu` in the merged footprint.

The common front-layer flags are available directly:

- `--f.cu`
- `--f.mask`
- `--f.paste`
- `--f.silk`
- `--b.cu`
- `--b.mask`
- `--b.paste`
- `--b.silk`

For any other KiCad layer, use a generic mapping:

```bash
kicad-merge --output combined.kicad_mod --layer Dwgs.User=outline.kicad_mod --layer Eco1.User=notes.kicad_mod
```

## Development

```bash
python -m pip install -e .[dev]
pytest
```