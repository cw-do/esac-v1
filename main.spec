# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['/SNS/users/ccd/analysiswork/esac_v1'],  # Include project directory
    binaries=[],
    datas=[('/SNS/users/ccd/.conda/envs/esac_env/lib/python3.8/site-packages/certifi/cacert.pem', 'certifi')],
    hiddenimports=[
        # PyQt5 core dependencies
        'sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        # Project dependencies
        'cryptography',
        'cryptography.fernet',
        'dotenv',
        'PyPDF2',
        # Standard library modules that might need explicit inclusion
        'ast',
        're',
        'subprocess',
        'tempfile',
        'os',
        'sys',
        'select',
        'json',
        'hashlib',
        # SSL and HTTPS support for requests
        'ssl',
        'urllib3',
        'urllib3.util.ssl_',
        'requests',
        'certifi',
        'http.client',
        'socket',
        '_ssl',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging if needed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

