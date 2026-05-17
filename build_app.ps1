$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot "game_env\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

Write-Host "Building JARVIS AI Vision Controller..."
$StageOutput = Join-Path $ProjectRoot "output_fixed"
$FinalOutput = Join-Path $ProjectRoot "output\app"

& $Python -m PyInstaller --noconfirm --clean --distpath $StageOutput --workpath build app.spec
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$StageApp = Join-Path $StageOutput "app"
$RequiredMediaPipeGraph = Join-Path $StageApp "_internal\mediapipe\modules\hand_landmark\hand_landmark_tracking_cpu.binarypb"
if (-not (Test-Path $RequiredMediaPipeGraph)) {
    throw "Build failed verification: MediaPipe hand landmark graph was not bundled."
}

$RequiredPalmModel = Join-Path $StageApp "_internal\mediapipe\modules\palm_detection\palm_detection_lite.tflite"
if (-not (Test-Path $RequiredPalmModel)) {
    throw "Build failed verification: MediaPipe palm detection model was not bundled."
}

New-Item -ItemType Directory -Force -Path $FinalOutput | Out-Null
Copy-Item -Path (Join-Path $StageApp "*") -Destination $FinalOutput -Recurse -Force

$FinalMediaPipeGraph = Join-Path $FinalOutput "_internal\mediapipe\modules\hand_landmark\hand_landmark_tracking_cpu.binarypb"
if (-not (Test-Path $FinalMediaPipeGraph)) {
    throw "Copy failed verification: MediaPipe hand landmark graph is missing from output\app."
}

Write-Host "Build ready: output\app\app.exe"
