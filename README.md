# Gate Control CLI

Python 3.11 CLI for TCP access controllers.

## Windows Setup

Install Python 3.11 on Windows 10:

```powershell
winget install Python.Python.3.11
```

If `winget` is unavailable:

```powershell
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$env:TEMP\python-3.11.9-amd64.exe"
Start-Process "$env:TEMP\python-3.11.9-amd64.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" -Wait
```

## Run From Source

```powershell
cd control
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
gate-control setup
gate-control menu
```

## Common Commands

```powershell
gate-control status
gate-control monitor
gate-control open-door --door 0
gate-control add-card-1door --index 50000 --card-no 999998 --pin 1234 --tz 1 --expires 2027-05-21
gate-control clear-card-slot --index 50000 --confirm
```

Destructive commands require `--confirm`.

`add-card-1door` defaults to the captured 17-byte AddCard format:

```text
CardIndex 2 + CardNo 4 + PIN2 2 + TZ 4 + Expiry 5
```

In this format, PIN must be numeric and within `0-65535`.
`Card No` may still be larger, for example `999998`.

To match a captured frame that has explicit permission bytes such as `02 03 01 03`:

```powershell
gate-control add-card-1door --index 2 --card-no 6789842 --pin 8738 --permission-hex "02 03 01 03" --expires 2012-01-07 --rand 0x7B
```

To use the heartbeat `SystemOption` layout instead:

```powershell
gate-control add-card-1door --card-format heartbeat --index 50000 --card-no 999998 --pin 00001234 --tz 1 --expires 2027-05-21 --name A
```
