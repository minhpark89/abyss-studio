$ErrorActionPreference = 'Stop'
$studio = Join-Path $PSScriptRoot 'abyss-studio'
& (Join-Path $PSScriptRoot 'Setup.ps1') -Headless
$port = 4387
$env:NATIVE_STUDIO_PORT = [string]$port
$proc = Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList 'native-server.js' -WorkingDirectory $studio -WindowStyle Hidden -PassThru
try {
    $base = "http://127.0.0.1:$port"
    $ready = $false
    for ($i=0; $i -lt 25; $i++) {
        if ($proc.HasExited) { throw 'The test server exited' }
        try { $null = Invoke-RestMethod "$base/api/studio/runtime" -TimeoutSec 3; $ready=$true; break } catch { Start-Sleep -Milliseconds 300 }
    }
    if (-not $ready) { throw 'Startup timeout' }
    $board=Invoke-RestMethod "$base/api/studio/channels"
    if ('Second Bell Pictures' -notin $board.channels.name -or 'Abyss Fieldnotes' -notin $board.channels.name) { throw 'Missing channel' }
    $progress=Invoke-RestMethod "$base/api/studio/fieldnotes"
    if ('D007' -notin $progress.episodes.id) { throw 'D007 missing' }
    foreach ($path in @('/fieldnotes','/api/registry','/api/registry/episodes','/dashboard/dashboard.js','/production/episodes/D007/full-v1/delivery/review.html','/production/episodes/SB09/delivery/review.html')) {
        $response=Invoke-WebRequest -UseBasicParsing -Uri ($base+$path)
        if ($response.StatusCode -ne 200) { throw $path }
        Write-Host "OK $path"
    }
} finally {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id }
    Remove-Item Env:NATIVE_STUDIO_PORT -ErrorAction SilentlyContinue
}

