$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectDir
& ".venv\Scripts\python.exe" server3d.py --preview
