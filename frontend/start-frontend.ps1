<#
Demarre le frontend Vite : installe les dependances npm si necessaire,
puis lance le serveur de dev (proxy /api vers http://127.0.0.1:8000).
#>

$ErrorActionPreference = 'Stop'
$frontendDir = $PSScriptRoot
Set-Location $frontendDir

if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host "Dependances npm absentes, installation..."
    npm install
}

npm run dev
