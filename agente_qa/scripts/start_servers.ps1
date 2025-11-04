param(
    [switch]$Watch = $false
)

if (-not (Test-Path "$PSScriptRoot/../../.venv/Scripts/python.exe")) {
    Write-Host "[ERRO] .venv não encontrado." -ForegroundColor Red
    exit 1
}

$python = "$PSScriptRoot/../../.venv/Scripts/python.exe"
$projectRoot = "$PSScriptRoot/.."

Write-Host "[INFO] Usando Python: $python" -ForegroundColor Cyan

$env:PYTHONIOENCODING = "utf-8"
Set-Location $projectRoot

if ($Watch) {
    & $python scripts/start_servers.py
}
else {
    & $python backend/api.py
}
