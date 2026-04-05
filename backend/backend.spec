# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for SubTranslate Backend."""
import sys
import os
from pathlib import Path

block_cipher = None

# Collect all hidden imports
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'faster_whisper',
    'faster_whisper.vad',
    'faster_whisper.utils',
    'faster_whisper.assets',
    'onnxruntime',
    'httpx',
    'aiofiles',
]

# Find faster_whisper package location for assets
import faster_whisper
faster_whisper_pkg = os.path.dirname(faster_whisper.__file__)

# Collect data files (ONNX models for Silero VAD)
datas = [
    (os.path.join(faster_whisper_pkg, 'assets'), 'faster_whisper/assets'),
]

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)