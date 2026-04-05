#Requires -Version 5.1
<#
  Opens the catalog URL in Edge or Chrome in real fullscreen (F11-style).
  Uses a temp user-data-dir so a running default browser window does not swallow
  --start-fullscreen (common Chromium behavior on Windows).
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Url
)

$dataRoot = Join-Path $env:TEMP 'OpenVehicleDbPickerBrowser'
$edgeData = Join-Path $dataRoot 'Edge'
$chromeData = Join-Path $dataRoot 'Chrome'
$null = New-Item -ItemType Directory -Force -Path $edgeData, $chromeData -ErrorAction SilentlyContinue

$tryEdge = @(
    (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe')
)
foreach ($exe in $tryEdge) {
    if (Test-Path -LiteralPath $exe) {
        Start-Process -FilePath $exe -ArgumentList @(
            "--user-data-dir=$edgeData",
            '--no-first-run',
            '--new-window',
            '--start-fullscreen',
            $Url
        )
        exit 0
    }
}

$tryChrome = @(
    (Join-Path $env:LocalAppData 'Google\Chrome\Application\chrome.exe'),
    (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe')
)
foreach ($exe in $tryChrome) {
    if (Test-Path -LiteralPath $exe) {
        Start-Process -FilePath $exe -ArgumentList @(
            "--user-data-dir=$chromeData",
            '--no-first-run',
            '--new-window',
            '--start-fullscreen',
            $Url
        )
        exit 0
    }
}

Start-Process $Url
exit 0
