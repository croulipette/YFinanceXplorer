<#
Demarre le backend et le frontend chacun dans sa propre fenetre PowerShell.
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

Start-Process powershell -ArgumentList '-NoExit', '-Command', "& '$root\backend\start-backend.ps1'"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "& '$root\frontend\start-frontend.ps1'"

Write-Host "Backend  : http://127.0.0.1:8000/docs"
Write-Host "Frontend : voir la fenetre Vite (URL affichee, ex http://localhost:5173)"
