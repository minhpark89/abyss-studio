param([switch]$BuildMuse, [switch]$Headless)
$ErrorActionPreference = 'Stop'
$studio = Join-Path $PSScriptRoot 'abyss-studio'
$runtime = Join-Path $studio 'data'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $runtime 'channel-board.json'))) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'seeds/channel-board.json') -Destination $runtime
}
if (-not $Headless) {
    Push-Location $studio
    try {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
        & node -e "require('electron')"
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path 'node_modules/electron/dist/electron.exe')) { throw 'Electron download failed' }
    } finally { Pop-Location }
}
if ($BuildMuse) {
    $out = Join-Path $studio 'research/muse-backends-2026-11-16/bin'
    New-Item -ItemType Directory -Path $out -Force | Out-Null
    Push-Location (Join-Path $PSScriptRoot 'gateway')
    try {
        & go build -trimpath -o (Join-Path $out 'muse2api-gateway-recovery.exe') './cmd/muse2api'
        if ($LASTEXITCODE -ne 0) { throw 'Go build failed' }
    } finally { Pop-Location }
}
Write-Host 'Abyss Studio is ready. Run .\Start.ps1 or .\Start.ps1 -Headless.'

