# -*- mode: python ; coding: utf-8 -*-

# Intel: 'x86_64', Apple Silicon: 'arm64'
app_arch = 'x86_64'

binary_name = 'swiftGuard.app'

# Major.Minor.Patch
app_version = '0.0.1'

# Year.BuildNumber
build_version = '2023.1'

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
            'CFBundleDevelopmentRegion': 'en',
            'CFBundleVersion': build_version,
            'NSHumanReadableCopyright': 'Copyright © 2023, Lennart Haack.',
            'LSApplicationCategoryType': 'public.app-category.utilities',
            'NSAppleEventsUsageDescription': 'swiftGuard is requesting access to System Events to provide the ability to shutdown and hibernate your Mac.\nThis permission will NEVER be used for any other purpose.',
            },
)
