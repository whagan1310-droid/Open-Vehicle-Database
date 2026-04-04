# Stage everything except catalog/charm-section-toc-cache.json (safe while the TOC scan is running).
# Usage:
#   .\scripts\commit-without-charm-toc-cache.ps1
#   .\scripts\commit-without-charm-toc-cache.ps1 -Message "your commit message"
param(
    [string] $Message = ""
)
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot/..")
git add -- . ":(exclude)catalog/charm-section-toc-cache.json"
git status --short
if ($Message) {
    git commit -m $Message
}
