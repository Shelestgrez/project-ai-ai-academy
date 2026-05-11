$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetBat = Join-Path $projectDir "start_ai_academy.bat"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "AI Academy.lnk"

if (-not (Test-Path $targetBat)) {
    throw "Launcher file not found: $targetBat"
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $projectDir
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$shortcut.Description = "Run AI Academy launcher"
$shortcut.Save()

Write-Host "Shortcut created: $shortcutPath"
