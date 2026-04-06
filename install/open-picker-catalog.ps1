#Requires -Version 5.1
<#
  Opens the picker URL either fullscreen (Edge/Chrome temp profile) or in the
  default browser, depending on PICKER_VARIANT_Windows.txt at the repo root.
  That marker file is added only to the "Windows" GitHub release ZIP by
  scripts/build_github_release_zips.ps1.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Url
)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$marker = Join-Path $RepoRoot 'PICKER_VARIANT_Windows.txt'
$windowed = Test-Path -LiteralPath $marker

if ($windowed) {
    $ws = Join-Path $PSScriptRoot 'open-picker-windowed.ps1'
    if (-not (Test-Path -LiteralPath $ws)) {
        Start-Process $Url
        exit 0
    }
    & $ws -Url $Url
    exit 0
}

$fs = Join-Path $PSScriptRoot 'open-picker-fullscreen.ps1'
if (-not (Test-Path -LiteralPath $fs)) {
    Start-Process $Url
    exit 0
}
& $fs -Url $Url
