# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
)


project_root = Path(SPECPATH)

datas = [
    (str(project_root / "kiosk_demo.html"), "."),
    (str(project_root / "project_clone.html"), "."),
    (str(project_root / "project_clone_group.html"), "."),
]

known_faces_dir = project_root / "known_faces"
if known_faces_dir.exists():
    datas.append((str(known_faces_dir), "known_faces"))

# MediaPipe loads graph/model files at runtime from paths such as
# mediapipe/modules/hand_landmark/hand_landmark_tracking_cpu.binarypb.
# PyInstaller does not collect these resources automatically, so include every
# MediaPipe graph/model resource used by the solution APIs.
datas += collect_data_files(
    "mediapipe",
    includes=[
        "modules/**/*.binarypb",
        "modules/**/*.tflite",
        "modules/**/*.txt",
    ],
)

# Keep OpenCV Haar cascades available for Face ID / eye checks in the packaged app.
datas += collect_data_files("cv2", includes=["data/*.xml"])

binaries = collect_dynamic_libs("mediapipe")

hiddenimports = [
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
    "pythoncom",
    "pywintypes",
    "win32com",
    "win32com.client",
    "win32timezone",
]

a = Analysis(
    ["app.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Visiq",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / "app_icon.ico"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="app",
)
