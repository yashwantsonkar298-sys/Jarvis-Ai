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

datas += collect_data_files(
    "mediapipe",
    includes=[
        "modules/**/*.binarypb",
        "modules/**/*.tflite",
        "modules/**/*.txt",
    ],
)
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

icon_file = project_root / "app_icon.ico"
app_icon = str(icon_file) if icon_file.exists() else None

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
    a.binaries,
    a.datas,
    [],
    name="JARVIS_AI_Vision_Controller",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=app_icon,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
