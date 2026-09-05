# Start the local workspace from any directory. Stop with Ctrl+C.
param(
    [ValidateRange(1024, 65535)][int]$Port = 8000,
    [ValidateSet('none', 'manual', 'ollama', 'anthropic', 'replay')]
    [string]$Provider = 'none'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install the project first. See README.md for setup.'
}
$env:LLM_PROVIDER = $Provider
Push-Location -LiteralPath $repoRoot
try {
    Write-Host "AI Act Companion: http://127.0.0.1:$Port" -ForegroundColor Cyan
    & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw "Server exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
