$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot "game_env\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

Write-Host "Building single-file JARVIS AI Vision Controller..."
$FinalOutput = Join-Path $ProjectRoot "output\single"
$WorkPath = Join-Path $ProjectRoot "build_onefile"

& $Python -m PyInstaller --noconfirm --clean --distpath $FinalOutput --workpath $WorkPath app_onefile.spec
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$FinalExe = Join-Path $FinalOutput "JARVIS_AI_Vision_Controller.exe"
if (-not (Test-Path $FinalExe)) {
    throw "Build failed verification: single-file executable was not created."
}

Write-Host "Single-file build ready: output\single\JARVIS_AI_Vision_Controller.exe"
