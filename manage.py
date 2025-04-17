"""

# Xem cách bố trí đường dẫn:   https://gemini.google.com/app/1f0b9b2cf2469c53

# from config.settings import register_apps, get_model

# # Đăng ký các ứng dụng
# register_apps()

# Ví dụ: Lấy mô hình từ ứng dụng users
# UserModel = get_model(apps.)#('apps.users', 'User')
# Bây giờ bạn có thể sử dụng UserModel để tương tác với cơ sở dữ liệu

from config import *
import sys
from PySide6.QtWidgets import QApplication
from apps.register.views import RegisterForm
# from controllers.user_controllers import UserController
# from app_login.views.login import LoginForm
# from config import *


# from apps.app_mainGui.main import GuiExcel

from gui.window_menuTabTool import BaseWindow

from apps.login.views import LoginForm
if __name__ == "__main__":
    app = QApplication(sys.argv)
    

    "1. Hiện form Login"
    login_form = LoginForm()
    login_form.show()

    

    "2. Giao diện chính"
    base_window = BaseWindow()
    base_window.show()

    "3. Giao diện Phân Kim"
    # user_form = UserRegistrationForm()
    # user_form.show()

    

    sys.exit(app.exec())

"""

import os
from sqlalchemy import create_engine
from vunghixuan.settings import DATABASE_URL
from vunghixuan.account.register.models import Base  # Import Base từ models của bạn
# from vunghixuan.account.register.user_controllers import  DatabaseManager
from vunghixuan.account.register.db_manager import DefaultSetup, DatabaseManager
# from vunghixuan.gui.main_window import show
import os



def print_otp():
    from vunghixuan import Otp
    Otp().otp_vunghixuan()

# def show_gui():
#     from vunghixuan import setting_controlls

def main():
    if os.path.exists('vunghixuan/settings.py'):
        db_manager = DatabaseManager(DATABASE_URL)
        session = db_manager.get_session()

        default_setup = DefaultSetup(session)
        default_setup.setup_defaults()  # Tự động cập nhật cơ sở dữ liệu

        from vunghixuan.gui.main_window import show
        show()

        db_manager.close()
    else:
        print("""
            Cài gói 'vunghixuan' bằng câu lệnh : pip install vunghixuan
        """)

if __name__ == '__main__':
    main()


    
