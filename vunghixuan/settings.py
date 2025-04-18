# coding=utf-8

from pathlib import Path
import os
import sys

"1. Khai báo chung dự án"
BASE_DIR = str(Path(__file__).parent.parent)
DATABASE_URL = 'sqlite:///data.db'  # Thay đổi nếu sử dụng DB khác

STATIC_DIR_RELATIVE = 'vunghixuan/static'

def get_resource_path(relative_path):
    """Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cả khi chạy từ source và khi đóng gói."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

STATIC_DIR = get_resource_path(STATIC_DIR_RELATIVE)

'2. Khai báo cho Header của basic_gui'

# Cặp màu nền và chữ
COLOR = {
    'Trắng': '#FFFFFF',
    'Đen': '#000000',
    'Đỏ': 'F70000',
    'Xanh lục': '#007f8c',
    'Xanh lục tối': '#29465B',
    'Xanh lá cây': '#006400',
    'Vàng gold': '#FFD700',
}

COLOR_FONT_BACKGROUND = {
    'Nền xanh lục, chữ trắng': ['#007f8c', '#FFFFFF'],  # xanh lục tối
    'Nền xanh xám, chữ vàng Gold': ['#29465B', '#FFD700'],  # Gold (W3C)
    'Nền xanh xám, chữ trắng': ['#29465B', '#FFFFFF'],  # xanh lục tối #29465B
    'Nền đen, chữ trắng': ['#000000', '#FFFFFF'],
    'Nền đen, chữ vàng': ['#000000', '#FFD700'],
}

# Danh mục thay đổi màu cho label
label_name_change_color = ['ĐĂNG NHẬP HỆ THỐNG',
                           'ĐĂNG KÝ',
                           ]
# Set màu nền và chữ toàn bộ gui
color_fnt_bg = COLOR_FONT_BACKGROUND['Nền xanh xám, chữ trắng']

MENUS_INFO = {
    "File": {
        "New": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icons8-file-64.png'),
        "Open": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icons8-opened-folder-50.png'),
        "Save": None,
    },
    "Edit": {
        "Cut": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icons8-file-64.png'),
        "Copy": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icons8-opened-folder-50.png'),
        "Paste": None,
    },
    "Help": {
        "About": None,
        "Documentation": None
    }
}

# Danh mục cấp quyền:
PERMISSIONS = ['Thêm', 'Xoá', 'Sửa', 'Xem']

# Hệ thống MainTab và SubTab
TABS_INFO = {
    "Hệ thống": {
        "Quản lý tài khoản": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icon_user_64.png'),
        "Cài đặt": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icon_sys.png'),
        "Hướng dẫn": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icons8-bookmark.gif'),
    },
    "Đối soát vé BOT": {
        "Đối soát files": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icons8-calculate-64.png'),
        "Hướng dẫn": get_resource_path(f'{STATIC_DIR_RELATIVE}/icon/icons8-bookmark.gif'),
    },
}
FILES_URL = os.path.abspath(".")  # Lưu file Excel trong thư mục chứa file .exe

ICON = {
    'eye_open': '👁️',
    'eye_closed': '👁️‍🗨️',
    'smile': '😀',
    'party': '🎉',
    'rocket': '🚀',
    'star': '🌟',
    'heart': '❤️',
    'thumbs_up': '👍',
    'fire': '🔥',
    'check_mark': '✔️',
    'clap': '👏',
    'sun': '☀️',
    'moon': '🌙',
    'sparkles': '✨',
    'gift': '🎁',
    'music': '🎵',
    'folder': '📁',
    'file': '📄',
    'add_button': '➕',
    'remove_button': '➖',
    'edit_button': '✏️',
    'open_folder': '📂',
    'close_folder': '📁',
    'user': '👤',
    'sys': '🖥️',
    'lock': '🔒',
    'unlock': '🔓',
    'search': '🔍',
    'settings': '⚙️',
    'warning': '⚠️',
}

if __name__ == "__main__":
    print(f"Base Directory: {BASE_DIR}")
    print(f"Static Directory (Resolved): {STATIC_DIR}")
    print(f"Icon Path (New): {MENUS_INFO['File']['New']}")
    print(f"FILES_URL (for output): {FILES_URL}")