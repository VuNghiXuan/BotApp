# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Lấy đường dẫn tuyệt đối đến thư mục chứa file .spec
spec_file_path = os.path.abspath('run_check_tickets.spec')
root_dir = Path(os.path.dirname(spec_file_path))

# Lấy đường dẫn thư mục static
static_dir = root_dir / 'vunghixuan' / 'static'

# Lấy đường dẫn thư mục files
files_dir = root_dir / 'files'

block_cipher = None

a = Analysis(
    ['run_check_tickets.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(static_dir), 'vunghixuan/static'),
        (str(files_dir), 'files') if os.path.exists(files_dir) else None,
        ('vunghixuan/settings.py', 'vunghixuan'),
        # Thêm các file dữ liệu khác bạn cần
    ],
    hiddenimports=[
        'et_xmlfile',
        'greenlet',
        'numpy',
        'openpyxl',
        'pandas',
        'pyotp',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6_Addons',
        'PySide6_Essentials',
        'dateutil',
        'pytz',
        'win32com.client',
        'shiboken6',
        'six',
        'sqlalchemy',
        'typing_extensions',
        'tzdata',
        'xlwings',
        # Thêm các hidden import khác nếu cần
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
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='run_check_tickets',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='run_check_tickets')