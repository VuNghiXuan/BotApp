

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
    db_manager = DatabaseManager(DATABASE_URL)
    session = db_manager.get_session()

    default_setup = DefaultSetup(session)
    default_setup.setup_defaults()  # Tự động cập nhật cơ sở dữ liệu

    from vunghixuan.gui.main_window import show
    show()
    db_manager.close()

        
    # if os.path.exists('vunghixuan/settings.py'):
    #     db_manager = DatabaseManager(DATABASE_URL)
    #     session = db_manager.get_session()

    #     default_setup = DefaultSetup(session)
    #     default_setup.setup_defaults()  # Tự động cập nhật cơ sở dữ liệu

    #     from vunghixuan.gui.main_window import show
    #     show()

    #     db_manager.close()
    # else:
    #     print("""
    #         Cài gói 'vunghixuan' bằng câu lệnh : pip install vunghixuan
    #     """)

if __name__ == '__main__':
    main()

    """
    Build file ra exe
        1. Chạy trong môi trường ảo: venv/scripts/activate
        2. pyinstaller run_check_tickets.spec
    """
    # Build file ra exe: pyinstaller run_check_tickets.spec

    # 15H07010 dòng 14

    
