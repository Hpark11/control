$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
.\.venv\Scripts\Activate.ps1
python -m pip install pyinstaller
pyinstaller --onefile --name gate-control src\gate_control\cli.py
