#Requires -Version 5.1
<#
  Opens the catalog URL in the default browser (normal window).
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Url
)

Start-Process $Url
