# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['main.py'],
    pathex=['/SNS/users/ccd/analysiswork/esac_v1'],  # Include project directory
    binaries=[
        ('/SNS/users/ccd/.conda/envs/esac_env/lib/libssl.so.3', '.'),
        ('/SNS/users/ccd/.conda/envs/esac_env/lib/libcrypto.so.3', '.'),
    ],
    datas=[
        ('/SNS/users/ccd/.conda/envs/esac_env/lib/python3.8/site-packages/certifi/cacert.pem', 'certifi'),
        ('knowledge', 'knowledge'),  # Include knowledge base files
        ('gui', 'gui'),  # Include GUI modules
        ('services', 'services'),  # Include service modules
        ('config', 'config'),  # Include config files
        # Include tiktoken package data (encodings, registry files) so model encodings
        # like cl100k_base are available in frozen executables.
        *collect_data_files('tiktoken'),
    ],
    hiddenimports=[
        # PyQt5 core dependencies
        'sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        # Project dependencies
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.asymmetric',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.primitives.padding',
        'cryptography.hazmat.primitives.serialization',
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
        'urllib3.contrib.pyopenssl',
        'requests',
        'requests.adapters',
        'requests.packages.urllib3',
        'requests.packages.urllib3.util',
        'requests.packages.urllib3.util.ssl_',
        'certifi',
        'http.client',
        'socket',
        '_ssl',
        'OpenSSL',
        'OpenSSL.crypto',
        'OpenSSL.SSL',
        # Ensure tiktoken internals are available to the frozen app
        'tiktoken',
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
    console=True,  # Set to True for debugging if needed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

