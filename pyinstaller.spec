# -*- mode: python ; coding: utf-8 -*-

########################################################################
#                PyInstaller spec File for swiftGuard                  #
#                        << Lennart Haack >>                           #
#                    << lennart-haack@mail.de >>                       #
#                 << https://github.com/Lennolium >>                   #
########################################################################

########################## Auto Configuration ##########################
import os
import re
import sys
from os.path import dirname as up

MAIN_FILE = sys.modules["__main__"].__file__
PROJECT_DIR = up(up(up(os.path.abspath(os.path.realpath(MAIN_FILE)))))
SRC_DIR = f"{PROJECT_DIR}/src/swiftguard"
USER_HOME = os.path.expanduser("~")

# Get app version from const.py (Major.Minor.Patch).
with open("src/swiftguard/const.py", "r") as file:
    content = file.read()
app_version = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content).group(1)

# Get the build version from const.py (Year.BuildNumber).
build_version = re.search(r'__build__\s*=\s*["\']([^"\']+)["\']', content).group(1)

# Extract all imported modules from project opt: ('__builtin__').
def extract_modules():
    excluded_folders = ('.', 'venv', 'env', 'tests', 'test',
                        'docs', 'doc', 'examples',
                        'example', 'build', 'dist',)

    folder_path = SRC_DIR

    def add_to_modules(modules, imp):
        if '.' in imp:
            modules.add(imp)
        else:
            modules.add(imp.split('.')[-1])

    modules = set()
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for excluded_folder in excluded_folders:
            if excluded_folder in dirnames:
                dirnames.remove(excluded_folder)

        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                with (open(file_path, 'r') as file):
                    content = file.read()
                    imports = re.findall(r'^import\s+(\S+)', content,
                                         re.MULTILINE
                                         )

                    for imp in imports:
                        if not imp.startswith('swiftguard'):
                            add_to_modules(modules, imp)
                    from_imports = re.findall(r'^from\s+(\S+)\s+import',
                                              content, re.MULTILINE
                                              )
                    for imp in from_imports:
                        if not imp.startswith('swiftguard') and (imp !=
                                                                 'PySide6'):
                            add_to_modules(modules, imp)

    return sorted(list(modules))

hidden_imports = extract_modules()

########################## User Configuration ##########################

# Intel: x86_64, Apple Silicon: arm64.
app_arch = 'x86_64'

# Name.
app_name = 'swiftGuard'
binary_name = app_name + '.app'

# Icon.
app_icon = 'src/swiftguard/resources/icons/app.icns'

# App entry point.
app_entry_point = 'src/swiftguard/app.py'

# List all extra files and directories here.
added_files = [
    ('src/swiftguard/install', 'install'),
    ('src/swiftguard/resources/ACKNOWLEDGMENTS', 'resources/'),
    ('src/swiftguard/resources/icons/app.icns', '.'),
    ('src/swiftguard/resources/resources_rc.py', 'resources/'),
    ('src/swiftguard/utils', 'utils'),
    ('src/swiftguard/__init__.py', '.'),
    ('src/swiftguard/__main__.py', '.'),
    ('src/swiftguard/cli.py', '.'),
    ('src/swiftguard/const.py', '.'),
    ('README.md', '.'),
    ('LICENSE', '.'),
    ('ACKNOWLEDGMENTS', '.'),
    ('/usr/local/bin/gpg', '.'),
    # ('/usr/local/lib/libgcrypt.20.dylib', '.'),
    # ('/usr/local/lib/libassuan.0.dylib', '.'),
    # ('/usr/local/lib/libnpth.0.dylib', '.'),
    # ('/usr/local/lib/libgpg-error.0.dylib', '.')
    ]

############################# PyInstaller ##############################

a = Analysis(
    [app_entry_point,],
    pathex=['./src/swiftguard'],
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
    icon=app_icon,
    bundle_identifier='dev.lennolium.swiftguard',
    version=app_version,
    info_plist={
            'NSPrincipalClass': 'NSApplication',
            'LSUIElement': True,
            'CFBundleDevelopmentRegion': 'en',
            'CFBundleVersion': build_version,
            'NSHumanReadableCopyright': 'Copyright © 2023, Lennart Haack',
            'LSApplicationCategoryType': 'public.app-category.utilities',
            'NSAppleEventsUsageDescription': 'swiftGuard is requesting access to System Events to provide the ability to shutdown and hibernate your Mac.\nThis permission will NEVER be used for any other purposes.',
            },
)
