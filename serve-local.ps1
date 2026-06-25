# serve-local.ps1 — run AI Act Companion for LAN / Tailscale access (e.g. from your phone).
# Usage (locally or over SSH):  powershell -ExecutionPolicy Bypass -File serve-local.ps1
# Stop it with Ctrl+C. Saved assessments persist in the repo's data\ folder.

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath "C:\Users\Jesse\Projects\ai-act-companion"

# AI assist mode: "manual" = paste-into-your-own-LLM (no keys); "ollama" = local Ollama; "none" = rule engine only.
$env:LLM_PROVIDER = "manual"

$tsIp   = "100.94.23.120"
$tsName = "desktop-jvcsc8a"
Write-Host ""
Write-Host "AI Act Companion — starting on http://0.0.0.0:8000" -ForegroundColor Cyan
Write-Host "On this PC:        http://localhost:8000"
Write-Host "On your phone (Tailscale):  http://$tsIp`:8000   or   http://$tsName`:8000"
Write-Host "(Both devices must be on your tailnet. Ctrl+C to stop.)"
Write-Host ""

& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
