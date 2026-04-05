#Requires -Version 5.1
<#
.SYNOPSIS
  Installs Python 3.12, Node.js LTS (optional but default), pip requirements, then starts the catalog picker.
  Intended for Windows after extracting the GitHub ZIP.
#>
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ReqFile = Join-Path $RepoRoot 'requirements.txt'
$CatalogIndex = Join-Path $RepoRoot 'catalog\index.html'

function Write-Info([string]$Message) {
    Write-Host "[Open-Vehicle-Database-Picker] $Message"
}

function Refresh-EnvPath {
    $machine = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Test-Winget {
    $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
}

function Install-WithWinget {
    param([string]$PackageId, [string]$Label)
    if (-not (Test-Winget)) {
        Write-Info "winget not found. Install $Label manually, then run this installer again."
        return $false
    }
    Write-Info "Installing $Label via winget (you may see a UAC prompt)..."
    $p = Start-Process -FilePath 'winget' -ArgumentList @(
        'install', '-e', '--id', $PackageId,
        '--accept-package-agreements', '--accept-source-agreements'
    ) -Wait -PassThru -NoNewWindow
    if ($p.ExitCode -ne 0) {
        Write-Info "winget finished with exit code $($p.ExitCode) (often OK if the app was already installed)."
    }
    Refresh-EnvPath
    return $true
}

function Get-PythonExe {
    Refresh-EnvPath
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $v = & py -3 -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0) {
            try {
                if ([version]$v -ge [version]'3.10') { return @{ Launcher = 'py'; Args = @('-3') } }
            } catch { }
        }
    }
    foreach ($name in @('python', 'python3')) {
        if (Get-Command $name -ErrorAction SilentlyContinue) {
            $v = & $name -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0) {
                try {
                    if ([version]$v -ge [version]'3.10') { return @{ Launcher = $name; Args = @() } }
                } catch { }
            }
        }
    }
    return $null
}

function Open-PickerInBrowserFullscreen {
    param([string]$Url)
    $candidates = @(
        @{ Path = Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe' },
        @{ Path = Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe' },
        @{ Path = Join-Path $env:LocalAppData 'Google\Chrome\Application\chrome.exe' },
        @{ Path = Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe' }
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c.Path) {
            Start-Process -FilePath $c.Path -ArgumentList @('--start-fullscreen', $Url)
            return
        }
    }
    Start-Process $Url
}

function Invoke-PythonPip {
    param($Python, [string[]]$PipArgs)
    $all = $Python.Args + @('-m', 'pip') + $PipArgs
    # Avoid treating pip stdout/stderr as function return values (breaks $LASTEXITCODE checks).
    & $Python.Launcher @all 2>&1 | ForEach-Object { Write-Host $_ }
    return [int]$LASTEXITCODE
}

# --- Validate repo ---
if (-not (Test-Path -LiteralPath $CatalogIndex)) {
    Write-Info "Could not find catalog\index.html under: $RepoRoot"
    Write-Info "Extract the full repository ZIP so this folder contains the catalog folder."
    exit 1
}

if (-not (Test-Path -LiteralPath $ReqFile)) {
    Write-Info "Could not find requirements.txt at repo root."
    exit 1
}

# --- Python ---
Write-Info "Checking Python 3.10+..."
$py = Get-PythonExe
if (-not $py) {
    if ($env:OVDB_SKIP_PYTHON_INSTALL -eq '1') {
        Write-Info "Python not found and OVDB_SKIP_PYTHON_INSTALL=1. Install Python 3.10+ and re-run."
        exit 1
    }
    Write-Info "Python 3.10+ not found. Attempting install..."
    Install-WithWinget -PackageId 'Python.Python.3.12' -Label 'Python 3.12' | Out-Null
    Refresh-EnvPath
    $py = Get-PythonExe
}
if (-not $py) {
    Write-Info "Python 3.10+ is still not on PATH."
    Write-Info "Install from https://www.python.org/downloads/ (check 'Add python.exe to PATH'), then run this installer again."
    exit 1
}
Write-Info "Using Python: $($py.Launcher) $($py.Args -join ' ')"

# --- pip + requirements.txt ---
Write-Info "Upgrading pip..."
$pipUp = Invoke-PythonPip -Python $py -PipArgs @('install', '--upgrade', 'pip')
if ($pipUp -ne 0) { Write-Info "pip upgrade returned $pipUp (continuing)." }
Write-Info "Installing packages from requirements.txt..."
$pipExit = Invoke-PythonPip -Python $py -PipArgs @('install', '-r', $ReqFile)
if ($pipExit -ne 0) {
    Write-Info "pip install reported an error (exit $pipExit). Check messages above."
    exit $pipExit
}

# --- Node.js (requested for ecosystem parity; picker server uses Python) ---
if ($env:OVDB_SKIP_NODE -ne '1') {
    Write-Info "Checking Node.js..."
    Refresh-EnvPath
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Info "Node.js not found. Attempting install..."
        Install-WithWinget -PackageId 'OpenJS.NodeJS.LTS' -Label 'Node.js LTS' | Out-Null
        Refresh-EnvPath
    }
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nv = & node -v
        Write-Info "Node.js OK: $nv"
    } else {
        Write-Info "Node.js is not on PATH (optional for the picker). Install from https://nodejs.org/ if you need it."
    }
} else {
    Write-Info "Skipping Node.js (OVDB_SKIP_NODE=1)."
}

# --- Start HTTP server + browser ---
$serverCmd = Join-Path $PSScriptRoot 'start-picker-server.cmd'
if (-not (Test-Path -LiteralPath $serverCmd)) {
    Write-Info "Missing install\start-picker-server.cmd"
    exit 1
}

Write-Info "Starting local web server on http://127.0.0.1:8080/ ..."
Start-Process -FilePath 'cmd.exe' -ArgumentList @('/k', 'call', $serverCmd) -WindowStyle Minimized

Start-Sleep -Seconds 2
$url = 'http://127.0.0.1:8080/catalog/'
Write-Info "Opening catalog in your browser (fullscreen when Edge/Chrome is found): $url"
Open-PickerInBrowserFullscreen -Url $url

Write-Info "Done. A small window is running the server; close it when you are finished browsing the picker."
