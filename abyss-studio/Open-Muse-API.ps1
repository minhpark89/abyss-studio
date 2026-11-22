$ErrorActionPreference='Stop'
$electronPath=Join-Path $PSScriptRoot 'node_modules\electron\dist\electron.exe'
if (-not (Test-Path -LiteralPath $electronPath)) {
    $researchRoot=if ($env:VIRAL_RESEARCH_ROOT) {$env:VIRAL_RESEARCH_ROOT} else {'E:\DROPSHIP\SHARE LAPTOP\VIRAL RESEARCH'}
    $electronPath=Join-Path $researchRoot 'repo\node_modules\electron\dist\electron.exe'
}
if(-not (Test-Path -LiteralPath $electronPath)){throw 'Không tìm thấy bộ chạy Abyss Desktop.'}
# The visible window is requested by the owner. Services are started hidden by
# desktop/services.cjs; no URL or Chrome profile is launched by this entry point.
Start-Process -FilePath $electronPath -ArgumentList ('"'+(Join-Path $PSScriptRoot 'desktop\main.cjs')+'"') -WorkingDirectory $PSScriptRoot
