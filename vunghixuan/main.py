# src/vunghixuan/main.py
import sys
from .api_and_otp import APIKey, Otp
from .project import Project
# from . import gui_main
# from PySide6.QtWidgets import QApplication
def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        print("Help message")
    else:
        key = args[1] if len(args) > 1 else None
        if key:
            if '-api' in args:
                obj = APIKey(key)
                obj.get_api()
            if '-otp' in args or '-totp' in args:
                obj = Otp(key)
                obj.get_otp()
            if '-create_project' in args :
                Project().create_project()
            if '-create_app' in args :
                Project().create_app()
        else:
            print("Missing API key")
    
    # Tạo giao diên chính
    # create_gui.create_gui()


if __name__ == '__main__':
    main()
    # app = QApplication(sys.argv)
    # window = MyWindow()
    # window.show()
    # sys.exit(app.exec())