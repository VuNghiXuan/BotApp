# manage.py

import os

def print_otp():
    from vunghixuan import Otp
    Otp().otp_vunghixuan()

def show_gui():
    from vunghixuan import setting_controlls

def main():
    # from vunghixuan import Otp
    # print(Otp().otp_vunghixuan()) 
    if os.path.exists('settings/settings.py'):    
        from vunghixuan.gui.main_window import show
        show()
        
    else:
        # from vunghixuan.project import Project
        # from vunghixuan.gui_main import show

        # # Tạo ra dự án
        # Project().create_project()
        # # Hiển thì Gui
        # show()
        
        
        print("""
            Cài gói 'vunghixuan' bằng câu lệnh : pip install vunghixuan
        """)
    

if __name__ == '__main__':
    main()



"""
I. Sơ đồ cấu trúc dữ liệu:
        vunghixuan/
        ├── account/
        │   ├── account_form.py       # Form quản lý tài khoản
        │   ├── register/
        │   │   ├── register_form.py  # Form đăng ký người dùng
        │   │   ├── user_controllers.py # Điều khiển người dùng
        │   ├── roll_permissions/
        │   │   ├── acount_table.py   # Bảng quyền người dùng
        │   │   ├── permission_form.py # Form quản lý quyền
        ├── gui/
        │   ├── login.py              # Form đăng nhập
        │   ├── manage_permissions.py # Quản lý quyền người dùng
        │   ├── menu_tab.py           # Tab quản lý
        │   ├── widgets.py            # Các widget tùy chỉnh
        │   ├── main.py               # MyWindows (Hea)
        ├── manage.py                 # File chính điều khiển ứng dụng
        ├── settings.py               # Cài đặt ứng dụng

        
1. manage.py (File chính điều khiển ứng dụng)
2. main.py (chứa file gui chính)
Khởi động form chính:
show(): Hàm này tạo một instance của MyWindow và hiển thị nó.
MyWindow.__init__(): Khởi tạo AppManager và FormManager, thiết lập giao diện người dùng chính.
Quản lý dữ liệu ứng dụng:
AppManager:
Tương tác với UserController để kiểm tra sự tồn tại của người dùng.
Điều này ảnh hưởng đến việc hiển thị form đăng nhập hay tab quản lý.
FormManager:
Quản lý việc tạo và truy cập các form LoginGroupBox và AccountForm.
Đảm bảo rằng chỉ có một instance của mỗi form được tạo.
Giao diện người dùng chính:
MyWindow:
Chứa Header, ContentView và Footer.
Xử lý thay đổi theme từ Header và cập nhật giao diện.
Xử lý sự kiện đăng nhập thành công từ ContentView.
Header:
Cho phép người dùng chọn theme, hiển thị form đăng ký và đóng ứng dụng.
Phát tín hiệu theme_changed khi theme thay đổi.
ContentView:
Hiển thị form đăng nhập hoặc tab quản lý tùy thuộc vào sự tồn tại của người dùng.
Cập nhật các form liên quan khi có thay đổi dữ liệu từ các form con.
Áp dụng quyền người dùng dựa trên thông tin đăng nhập.
Footer:
Hiển thị thông tin bản quyền.
Luồng dữ liệu chính:
Dữ liệu người dùng từ LoginGroupBox được gửi đến UserController để xác thực.
Quyền người dùng từ UserController được gửi đến ContentView để áp dụng.
Dữ liệu từ các form con (đăng ký, quyền, v.v.) được gửi đến ContentView để cập nhật giao diện.
Thay đổi theme từ Header được gửi đến MyWindow và các widget khác để cập nhật giao diện.
3. gui/login.py (Form đăng nhập)

Luồng dữ liệu:
Dữ liệu người dùng (tên đăng nhập và mật khẩu) được nhập vào QLineEdit.
Khi người dùng nhấn nút "Đăng nhập", dữ liệu được gửi đến UserController để xác thực.
Kết quả xác thực được hiển thị bằng QMessageBox.
Nếu đăng nhập thành công, tín hiệu được phát ra để cập nhật giao diện chính.
4. gui/menu_tab.py (Tab quản lý)

Luồng dữ liệu:
Hiển thị các tab quản lý dựa trên quyền người dùng.
Tương tác với AccountForm để hiển thị và quản lý thông tin tài khoản.
5. account/register/user_controllers.py (Điều khiển người dùng)

Luồng dữ liệu:
Nhận dữ liệu người dùng từ các form (đăng nhập, đăng ký).
Tương tác với cơ sở dữ liệu để xác thực, tạo, cập nhật và xóa người dùng.
Trả về kết quả cho các form.
6. account/register/register_form.py (Form đăng ký)

Luồng dữ liệu:
Nhận dữ liệu người dùng từ QLineEdit và QListWidget.
Gửi dữ liệu đến UserController để tạo người dùng mới.
Hiển thị kết quả cho người dùng.
7. account/roll_permissions/acount_table.py (Bảng quyền người dùng)

Luồng dữ liệu:
Hiển thị dữ liệu quyền người dùng từ cơ sở dữ liệu.
Cho phép người dùng chỉnh sửa và cập nhật quyền.
8. account/roll_permissions/permission_form.py (Form quyền)

Luồng dữ liệu:
Cho phép người dùng tạo và chỉnh sửa quyền.
Gửi dữ liệu quyền đến UserController để cập nhật cơ sở dữ liệu.
9. account/account_form.py (Form tài khoản)

Luồng dữ liệu:
Quản lý các form đăng ký và quyền người dùng.
Tương tác với UserController để cập nhật thông tin tài khoản.
10. gui/manage_permissions.py (Quản lý quyền)

Luồng dữ liệu:
Nhận dữ liệu quyền người dùng từ ContentView.
Áp dụng quyền cho các widget trong tab quản lý.
11. settings.py (Cài đặt)

Luồng dữ liệu:
Chứa các biến cài đặt được sử dụng bởi các thành phần khác trong ứng dụng.
12. gui/widgets.py (Các widget tùy chỉnh)

Luồng dữ liệu:
Các widget tùy chỉnh này được sử dụng để hiển thị và nhập dữ liệu.
"""
