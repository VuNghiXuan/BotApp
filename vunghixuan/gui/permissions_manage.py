# PermissionManager.py
from vunghixuan.settings import PERMISSIONS
from vunghixuan.settings import TABS_INFO

class PermissionManager:
    def __init__(self, user_permissions, tab_widget):
        self.user_permissions = user_permissions
        self.tab_widget = tab_widget

    def apply_permissions(self):
        if self.user_permissions:
            self.apply_apps()
        else:
            print("Không có quyền nào được cấp.")

    def apply_apps(self):
        for app_name, permissions in self.user_permissions.items():
            if app_name in PERMISSIONS:
                print(f"App '{app_name}' được cấp quyền.")
                self.apply_app_permissions(app_name, permissions)
            else:
                print(f"App '{app_name}' không được cấp quyền.")
                # Ẩn hoặc vô hiệu hóa toàn bộ phần giao diện liên quan đến app này
                if app_name == "Tài khoản người dùng":
                    self.tab_widget.hide_user_tab()
                # ... (ẩn hoặc vô hiệu hóa các app khác) ...

    def apply_app_permissions(self, app_name, permissions):
        for permission in permissions:
            if permission in PERMISSIONS[app_name]:
                print(f"Quyền '{permission}' trong app '{app_name}' được cấp.")
                # Thực hiện hành động tương ứng với quyền được cấp
                if app_name == "app_sell":
                    if permission == "view":
                        # Hiển thị nút hoặc tab xem bán hàng
                        print("Hiển thị nút xem bán hàng")
                    elif permission == "add":
                        # Hiển thị nút hoặc tab thêm bán hàng
                        print("Hiển thị nút thêm bán hàng")
                    # ... (xử lý các quyền khác trong app_sell) ...
                elif app_name == "Tài khoản người dùng":
                    if permission == "view":
                        # Hiển thị tab quản lý người dùng
                        self.tab_widget.show_user_tab()
                    elif permission == "edit":
                        # Hiển thị nút chỉnh sửa người dùng
                        print("Hiển thị nút sửa người dùng")
                    # ... (xử lý các quyền khác trong Tài khoản người dùng) ...
                # ... (xử lý các app khác) ...
            else:
                print(f"Quyền '{permission}' trong app '{app_name}' không được cấp.")
                # Ẩn hoặc vô hiệu hóa các phần tử giao diện tương ứng
                if app_name == "Tài khoản người dùng":
                    if permission == "view":
                        self.tab_widget.hide_user_tab()
                # ... (ẩn hoặc vô hiệu hóa các quyền khác) ...