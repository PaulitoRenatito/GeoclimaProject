# -*- mode: python ; coding: utf-8 -*-
# Build: poetry run pyinstaller geoclima.spec  ->  dist/Geoclima.exe
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['src/geoclima/__main__.py'],
    pathex=['src'],
    binaries=[],
    # customtkinter loads its theme .json files at runtime, so they must be bundled.
    datas=collect_data_files('customtkinter'),
    hiddenimports=[],
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
    name='Geoclima',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['res\\geoclima.ico'],
)
