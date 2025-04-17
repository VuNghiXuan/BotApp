# Hướng dẫn cài đặt và sử dụng gói vunghixuan
1. Cài đặt: pip install vunghixuan
2. Tạo file manage.py và chép đoạn mã sau 
    ```python
    import os


    def main():
        # from vunghixuan import Otp
        # print(Otp().otp_vunghixuan()) 
        if not os.path.exists('settings/settings.py'):    
            from vunghixuan import show
            show()
            
        else:
            
            from vunghixuan.project import Project
            from vunghixuan.gui_main import show

            # Tạo ra dự án
            Project().create_project()
            # Hiển thì Gui
            show()
        

    if __name__ == '__main__':
        main()
