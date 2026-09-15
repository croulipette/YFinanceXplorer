<#
Regenere backend/certs/combined-ca-bundle.pem : certificats publics (certifi)
+ la CA racine interne de l'entreprise (necessaire derriere le proxy qui
inspecte le HTTPS, sinon Ticker.info / funds_data echouent avec
CertificateVerifyError). Ce fichier n'est pas versionne (voir .gitignore)
car il depend du poste ; relance ce script apres un `git clone` ou si
`pip install` a recree le venv.
#>

$ErrorActionPreference = 'Stop'

$backendDir = Split-Path -Parent $PSScriptRoot
$certsDir = Join-Path $backendDir 'certs'
New-Item -ItemType Directory -Force -Path $certsDir | Out-Null

$rootCaSubject = "CN=LDC-DC03-CA, DC=cdbdx, DC=biz"
$cert = Get-ChildItem Cert:\LocalMachine\Root | Where-Object { $_.Subject -eq $rootCaSubject } | Select-Object -First 1
if (-not $cert) {
    throw "CA racine '$rootCaSubject' introuvable dans Cert:\LocalMachine\Root. Adapte `$rootCaSubject dans ce script si le poste utilise une autre CA de proxy."
}

$internalCaPem = Join-Path $certsDir 'internal-ca.tmp.pem'
$b64 = [System.Convert]::ToBase64String($cert.RawData, [System.Base64FormattingOptions]::InsertLineBreaks)
"-----BEGIN CERTIFICATE-----`r`n$b64`r`n-----END CERTIFICATE-----" | Out-File -FilePath $internalCaPem -Encoding ascii

$certifiPem = Join-Path $backendDir '.venv\Lib\site-packages\certifi\cacert.pem'
if (-not (Test-Path $certifiPem)) {
    throw "certifi introuvable ($certifiPem). Active le venv et installe les dependances (pip install -r requirements.txt) avant de lancer ce script."
}

$bundlePath = Join-Path $certsDir 'combined-ca-bundle.pem'
Get-Content $certifiPem, $internalCaPem | Set-Content -Path $bundlePath -Encoding ascii
Remove-Item $internalCaPem

Write-Host "Bundle genere : $bundlePath"
