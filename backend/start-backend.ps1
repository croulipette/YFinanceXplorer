<#
Demarre le backend FastAPI : cree le venv et installe les dependances si
necessaire, regenere le bundle de certificats CA si absent, puis lance
uvicorn avec reload sur http://127.0.0.1:8000 (doc: /docs).
#>

$ErrorActionPreference = 'Stop'
$backendDir = $PSScriptRoot
Set-Location $backendDir

$venvPython = Join-Path $backendDir '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Write-Host "Environnement virtuel introuvable, creation..."
    py -m venv (Join-Path $backendDir '.venv')
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path $backendDir 'requirements.txt')
}

$bundlePath = Join-Path $backendDir 'certs\combined-ca-bundle.pem'
if (-not (Test-Path $bundlePath)) {
    Write-Host "Bundle de certificats absent, generation (scripts\build-ca-bundle.ps1)..."
    try {
        & (Join-Path $backendDir 'scripts\build-ca-bundle.ps1')
    } catch {
        Write-Warning "Generation du bundle impossible ($($_.Exception.Message)). On continue sans (utile seulement derriere un proxy qui inspecte le HTTPS)."
    }
}

if (Test-Path $bundlePath) {
    $env:SSL_CERT_FILE = $bundlePath
    $env:REQUESTS_CA_BUNDLE = $bundlePath
    $env:CURL_CA_BUNDLE = $bundlePath
}

& $venvPython -m uvicorn app.main:app --port 8000 --reload
