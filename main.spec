# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # 这里填写你的主Python文件名
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),          # 将 assets 文件夹复制到 exe 内部的 assets 路径
        ('ew_desktop.ico', '.'),   # 将图标复制到 exe 内部根路径
        ('events.json', '.')           # 将 events.json 复制到 exe 内部根路径
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
    name='ewDesktop',  # 生成的 exe 文件名 (可以是中文，如 '关羽桌宠')
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,            # False = 隐藏黑框控制台，True = 显示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ew_desktop.ico', # exe 文件外观图标
)