# -*- mode: python ; coding: utf-8 -*-

app_arch = 'x86_64'

binary_name = 'swiftGuard.app'

app_version = '0.0.1'

added_files = [
    ('src/swiftguard/resources', 'resources'),
    ('src/swiftguard/helpers.py', '.'),
    ('src/swiftguard/worker.py', '.')]

hidden_imports = [
    '__builtin__',
    'configparser',
    'datetime',
    'os',
    'signal',
    'sys',
    'webbrowser',
    'plistlib',
    're',
    'subprocess',
    'datetime.datetime',
    'ast.literal_eval',
    'collections.Counter',
    'copy.deepcopy',
    'functools.partial',
    'time.sleep',
    'darkdetect',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

a = Analysis(
    ['src/swiftguard/swiftguard.py', 'src/swiftguard/helpers.py', 'src/swiftguard/worker.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='swiftGuard',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=app_arch,
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
    name='swiftGuard',
)
app = BUNDLE(
    coll,
    name=binary_name,
    icon='src/swiftguard/resources/logo-macos@2x.icns',
    bundle_identifier='dev.lennolium.swiftguard',
    version=app_version,
    info_plist={
            'NSPrincipalClass': 'NSApplication',
            'LSUIElement': True,
            'CFBundleDevelopmentRegion': 'English',
            },
)
