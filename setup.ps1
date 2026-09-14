$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectDir

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    python -m venv .venv
}
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed" }
& npm.cmd ci --omit=dev
if ($LASTEXITCODE -ne 0) { throw "Three.js installation failed" }
Write-Host "Setup complete. Run .\run-preview.ps1 first, then .\run-brain.ps1."
