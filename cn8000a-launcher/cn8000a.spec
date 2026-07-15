# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows portable .exe (built via Wine on Linux CI).

block_cipher = None

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("i18n/languages", "i18n/languages"),
        ("resources", "resources"),
    ],
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.font",
        "tkinter.messagebox",
    ],
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
    [],
    exclude_binaries=True,
    name="CN8000A-KVM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CN8000A-KVM",
)
