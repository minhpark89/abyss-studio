param([switch]$Headless)
$ErrorActionPreference = 'Stop'
$studio = Join-Path $PSScriptRoot 'abyss-studio'
if (-not (Test-Path -LiteralPath (Join-Path $studio 'data/channel-board.json'))) {
    & (Join-Path $PSScriptRoot 'Setup.ps1') -Headless
}
Push-Location $studio
try {
    if ($Headless) {
        Write-Host 'Abyss Studio: http://127.0.0.1:4320/fieldnotes'
        & node native-server.js
    } else {
        & (Join-Path $studio 'Open-Muse-API.ps1')
    }
} finally { Pop-Location }

