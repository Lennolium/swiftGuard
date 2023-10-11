# -*- mode: python ; coding: utf-8 -*-

########################################################################
#                PyInstaller spec File for swiftGuard                  #
#                        << Lennart Haack >>                           #
#                    << lennart-haack@mail.de >>                       #
#                 << https://github.com/Lennolium >>                   #
########################################################################

########################## Auto Configuration ##########################

# Get app version from const.py (Major.Minor.Patch).
import re
with open("src/swiftguard/const.py", "r") as file:
    content = file.read()
app_version = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content).group(1)

# Get the build version from const.py (Year.BuildNumber).
build_version = re.search(r'__build__\s*=\s*["\']([^"\']+)["\']', content).group(1)

########################## User Configuration ##########################

# Intel: 'x86_64', Apple Silicon: 'arm64'
app_arch = 'x86_64'

# Name.
app_name = 'swiftGuard'
binary_name = app_name + '.app'

# App entry point.
app_entry_point = 'src/swiftguard/app.py'

# List all extra files and directories here.
added_files = [
    ('src/swiftguard/install', 'install'),
    ('src/swiftguard/resources/ACKNOWLEDGMENTS', 'resources/'),
    ('src/swiftguard/resources/logo-macos@2x.icns', 'resources/'),
    ('src/swiftguard/resources/resources_rc.py', 'resources/'),
    ('src/swiftguard/utils', 'utils'),
    ('src/swiftguard/__main__.py', '.'),
    ('src/swiftguard/cli.py', '.'),
    ('src/swiftguard/const.py', '.'),
    ('README.md', '.'),
    ('LICENSE', '.'),
    ('ACKNOWLEDGMENTS', '.'),
    ]

added_files_old = [
    ('src/swiftguard/install', 'install'),
    ('src/swiftguard/resources', 'resources'),
    ('src/swiftguard/utils', 'utils'),
    ('src/swiftguard/__main__.py', '.'),
    ('src/swiftguard/cli.py', '.'),
    ('src/swiftguard/const.py', '.'),
    ('README.md', '.'),
    ('LICENSE', '.'),
    ('ACKNOWLEDGMENTS', '.'),
    ]

# List all imports here (built-in and external). opt: ('__builtin__',).
hidden_imports = [
    'argparse',
    'ast',
    'collections',
    'configparser',
    'copy',
    'darkdetect',
    'datetime',
    'functools',
    'logging',
    'logging.handlers',
    'os',
    'plistlib',
    'platform',
    'pyoslog',
    're',
    'requests',
    'shutil',
    'signal',
    'subprocess',
    'sys',
    'time',
    'webbrowser',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

############################# PyInstaller ##############################

a = Analysis(
    [app_entry_point,],
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
    name=app_name,
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
    name=app_name,
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
