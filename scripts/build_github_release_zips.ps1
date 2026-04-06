#Requires -Version 5.1
<#
.SYNOPSIS
  Builds two ZIPs for GitHub Releases: FullScreen (default browser chrome fullscreen)
  and Windows (default browser windowed). Same tree as the repo except the Windows
  ZIP includes PICKER_VARIANT_Windows.txt so install/launch use windowed mode.

  Remote manuals and JSON caches follow the repo (LEMON Manuals — lemon-manuals.la).

.PARAMETER RepoRoot
  Path to the Open-Vehicle-Database repository root (folder containing catalog/).

.PARAMETER OutDir
  Output directory for staging folders and ZIP files (created if missing).

.PARAMETER Label
  Optional suffix for ZIP file names, e.g. "LEMON" -> Open-Vehicle-Database-FullScreen-LEMON.zip

.PARAMETER KeepStaging
  If set, leave timestamped staging-* folders under OutDir for debugging.

.PARAMETER FullScreenOnly
  Build only the FullScreen ZIP (skip Windows variant). Use this when you want to produce the fullscreen release first.
#>
param(
    [string]$RepoRoot = '',
    [string]$OutDir = '',
    [string]$Label = 'LEMON',
    [switch]$KeepStaging,
    [switch]$FullScreenOnly
)

$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
} else {
    $RepoRoot = (Resolve-Path $RepoRoot).Path
}

if (-not $OutDir) {
    $OutDir = Join-Path $RepoRoot 'release'
}
$null = New-Item -ItemType Directory -Force -Path $OutDir
$OutDir = (Resolve-Path -LiteralPath $OutDir).Path

$Catalog = Join-Path $RepoRoot 'catalog\index.html'
if (-not (Test-Path -LiteralPath $Catalog)) {
    Write-Error "catalog\index.html not found under RepoRoot: $RepoRoot"
}

$stamp = [DateTime]::UtcNow.ToString('yyyyMMddHHmmss')
$stageFull = Join-Path $OutDir "staging-fullscreen-$stamp"
$stageWin = $null
if (-not $FullScreenOnly) {
    $stageWin = Join-Path $OutDir "staging-windows-$stamp"
}

$null = New-Item -ItemType Directory -Force -Path $stageFull

# Directory names to exclude (matched under source root; robocopy /XD).
$xd = @('.git', '.github', 'release', '__pycache__', '.cursor', '.vs', 'node_modules')
$xdArgs = @()
foreach ($d in $xd) { $xdArgs += @('/XD', $d) }

Write-Host "[build_github_release_zips] RepoRoot: $RepoRoot"
Write-Host "[build_github_release_zips] Staging fullscreen -> $stageFull"

$robolog = Join-Path $OutDir 'robocopy-full.log'
$args = @($RepoRoot, $stageFull, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NC', '/NS') + $xdArgs
$rc = Start-Process -FilePath 'robocopy.exe' -ArgumentList $args -Wait -PassThru -NoNewWindow
# robocopy exit codes 0-7 are success
if ($rc.ExitCode -ge 8) {
    Write-Error "robocopy failed with exit code $($rc.ExitCode). See $robolog (re-run with tee if needed)."
}

$suffix = ''
if ($Label) { $suffix = "-$Label" }

# Unique names per run so a stuck process elsewhere does not lock the output file.
$zipFull = Join-Path $OutDir "Open-Vehicle-Database-FullScreen$suffix-$stamp.zip"
$zipWin = if (-not $FullScreenOnly) { Join-Path $OutDir "Open-Vehicle-Database-Windows$suffix-$stamp.zip" } else { $null }

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Write-ZipFromDirectory([string]$SourceDir, [string]$ZipPath) {
    if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
    # Faster than Compress-Archive for large trees (e.g. charm-vehicle-cache.json + manuals).
    try {
        [System.IO.Compression.ZipFile]::CreateFromDirectory(
            $SourceDir,
            $ZipPath,
            [System.IO.Compression.CompressionLevel]::Fastest,
            $false)
    } catch {
        [System.IO.Compression.ZipFile]::CreateFromDirectory($SourceDir, $ZipPath)
    }
}

Write-Host "[build_github_release_zips] Compressing FullScreen -> $zipFull"
Write-ZipFromDirectory -SourceDir $stageFull -ZipPath $zipFull

$gf = Get-Item $zipFull
Write-Host "[build_github_release_zips] FullScreen done: $($gf.FullName)  ($([math]::Round($gf.Length / 1MB, 2)) MB)"

if (-not $FullScreenOnly) {
    Write-Host "[build_github_release_zips] Copying staging -> Windows variant..."
    $null = New-Item -ItemType Directory -Force -Path $stageWin
    $rc2 = Start-Process -FilePath 'robocopy.exe' -ArgumentList @($stageFull, $stageWin, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NC', '/NS') -Wait -PassThru -NoNewWindow
    if ($rc2.ExitCode -ge 8) {
        Write-Error "robocopy mirror to Windows staging failed: $($rc2.ExitCode)"
    }

    $markerPath = Join-Path $stageWin 'PICKER_VARIANT_Windows.txt'
    $markerText = @"
Windows release package (windowed browser).

Remote service manuals open on LEMON Manuals: https://lemon-manuals.la/

Delete this file if you want fullscreen Edge/Chrome behavior like the FullScreen release;
then use the same install and launch scripts as that package.
"@
    Set-Content -LiteralPath $markerPath -Value $markerText -Encoding utf8

    Write-Host "[build_github_release_zips] Compressing Windows -> $zipWin"
    Write-ZipFromDirectory -SourceDir $stageWin -ZipPath $zipWin
    $gw = Get-Item $zipWin
    Write-Host "[build_github_release_zips] Windows done: $($gw.FullName)  ($([math]::Round($gw.Length / 1MB, 2)) MB)"
}

Write-Host "[build_github_release_zips] Done."
if ($FullScreenOnly) {
    Write-Host "FullScreen-only: upload that ZIP to the FullScreen GitHub Release; mention https://lemon-manuals.la/ in the notes."
} else {
    Write-Host "Upload both ZIPs to their GitHub Releases and describe LEMON Manuals (https://lemon-manuals.la/) in the release notes."
}

if (-not $KeepStaging) {
    $toRemove = @($stageFull)
    if ($stageWin) { $toRemove += $stageWin }
    foreach ($p in $toRemove) {
        try {
            Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop
        } catch {
            Write-Warning "Could not remove staging folder (close apps using files there): $p"
        }
    }
}
