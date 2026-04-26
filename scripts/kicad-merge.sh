#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
src_dir="${repo_root}/src"

if [[ -x "${repo_root}/.venv/Scripts/python.exe" ]]; then
  python_cmd="${repo_root}/.venv/Scripts/python.exe"
elif [[ -x "${repo_root}/.venv/bin/python" ]]; then
  python_cmd="${repo_root}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
else
  python_cmd="python"
fi

if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="${src_dir}:${PYTHONPATH}"
else
  export PYTHONPATH="${src_dir}"
fi

exec "${python_cmd}" -m kicad_merge "$@"