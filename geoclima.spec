# -*- mode: python ; coding: utf-8 -*-
# Build: poetry run pyinstaller geoclima.spec  ->  dist/Geoclima.exe

a = Analysis(
    ['src/geoclima/__main__.py'],
    pathex=['src'],
    binaries=[],
    # The stylesheet points at the check mark SVG on disk.
    datas=[('src/geoclima/ui/assets', 'geoclima/ui/assets')],
    # Loaded by name at runtime, so the analysis does not see it: the Windows Credential Manager backend.
    hiddenimports=['keyring.backends.Windows'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Not used since the move to Qt; keeps them out even if some dependency imports them optionally.
    excludes=['tkinter', 'matplotlib'],
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
