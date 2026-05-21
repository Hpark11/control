$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (!(Test-Path ".venv")) {
  python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
gate-control menu
