# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['src\\main.py'],
    pathex=[r'C:\Robert\Coding\Python\Project\SkyblockTools'],
    binaries=[],
    datas=[
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\images\entity_img', r'entity_img'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\images\gui_img', r'gui_img'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\images\guns', r'guns'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\images\gun_parts', r'gun_parts'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\images\items', r'items'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\images\map', r'map'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\images\screen', r'screen'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\sounds\entity', r'entity'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\sounds\gui', r'gui'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\sounds\gun_reload', r'gun_reload'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\sounds\gun_repeat', r'gun_repeat'),
        (r'C:\Users\langh\AppData\Local\Programs\Python\Python310\Lib\DungeonShooter\src\sounds\gun_shot', r'gun_shot'),
    ],
    hiddenimports=[],
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
    name='SkyblockTools',
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
