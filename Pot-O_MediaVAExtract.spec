# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['Pot-O_MediaVAExtract_v1.0.3.6-beta.py'],
    pathex=['.'],
    binaries=[
        ('executables/ffmpeg.exe', 'executables/'),
        ('executables/ffprobe.exe', 'executables/'),
        ('executables/mkvextract.exe', 'executables/'),
        ('executables/mkvinfo.exe', 'executables/'),
        ('executables/mkvmerge.exe', 'executables/'),
        ('executables/mkvpropedit.exe', 'executables/')
    ],
    datas=[
        ('assets_rc.py', '.'), 
        ('PotO_UI.py', '.'), 
        ('AboutPotOui.py', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,
    name='Pot-O_MediaVAExtract',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want to see console output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Pot-O_MediaVAExtract'
)
