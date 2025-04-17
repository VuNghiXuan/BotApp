from PySide6.QtWidgets import (
    QApplication, QWidget, QMessageBox, QPushButton, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpacerItem, QSizePolicy, QGroupBox,
    QHBoxLayout, QListWidget, QListWidgetItem
)
from PySide6.QtGui import Qt, QShowEvent
from PySide6.QtCore import QSize, Signal, Slot

# from vunghixuan.account.register.user_controllers import (
#     DatabaseManager,  UserManager, RollManager,
#     PermissionManager, AppManager, GroupManager, InterfaceManager
# )
from vunghixuan.settings import STATIC_DIR, ICON, DATABASE_URL
from vunghixuan.gui.widgets import MyQLabel, MyQGridLayout, MyQLineEdit, MyQComboBox, MyQPushButton
# from vunghixuan.account.register.user_controllers import UserController

from vunghixuan.account.register.user_manager import UserManager
from vunghixuan.account.register.group_manager import GroupManager
from vunghixuan.account.register.roll_manager import RollManager
# from vunghixuan.account.register.permisson_manager import PermissionManager
# from vunghixuan.account.register.interface_manager import InterfaceManager
from vunghixuan.account.register.app_manager import AppManager
from vunghixuan.account.register.db_manager import DatabaseManager


class RegisterForm(QWidget):
    user_added = Signal()

    def __init__(self, user_permissions_table, permission_form=None):
        super().__init__()
        self.is_visible = False
        self.group_box = QGroupBox("Thông tin đăng ký")
        self.layout_groupbox = QVBoxLayout()
        self.group_box.setLayout(self.layout_groupbox)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.group_box)
        self.setLayout(self.main_layout)
        self.layout = MyQGridLayout()
        self.layout_groupbox.addLayout(self.layout)
        self.layout.current_row = 0
        self.db_manager = DatabaseManager(DATABASE_URL)
        self.user_manager = UserManager(self.db_manager.get_session())
        # self.roll_manager = RollManager(self.db_manager.get_session())
        self.groups_manager = GroupManager(self.db_manager.get_session())
        self.app_manager = AppManager(self.db_manager.get_session())
        # self.default_setup = DefaultSetup(self.db_manager.get_session())
        self.user_permissions_table = user_permissions_table
        self.permission_form = permission_form
        


        if self.permission_form:
            self.permission_form.group_added.connect(self.update_group_list) # Đổi tên hàm

        self.user = None
        self.create_ui_elements()
        self.main_layout.addLayout(self.create_horizontal_layout())

    def create_ui_elements(self):
        # self.create_title_row()
        self.username = self.create_input_row('Tên người dùng', 'Nhập tên người dùng')
        self.password = self.create_password_row('Mật khẩu', 'Nhập mật khẩu')
        self.re_password = self.create_password_row('Xác thực', 'Nhập lại mật khẩu')
        self.group_list = self.create_group_list("Nhóm người dùng", self.groups_manager.get_groups(), "name", "id") # Đổi tên biến
        self.app_list = self.app_manager.get_all_app_names()
        # self.register_push = self.create_push_row()
        # self.delete_group_button = self.create_delete_group_button() # Đổi tên biến
        self.create_delete_group_button()
        # self.add_group_button = self.create_add_group_button()  # Thêm nút Add Group
        self.layout.update()

        self.username.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self.re_password.setFocus)

    def create_group_list(self, label_text, items, display_attr, data_attr):  # Đổi tên hàm và biến
        grbox = QGroupBox('Nhóm người dùng') # Create groupbox
        layout = QVBoxLayout() # Create layout for groupbox

        # label = MyQLabel(label_text)
        # label.set_size_font(13)
        group_list = QListWidget()
        group_list.setStyleSheet("background-color: #f0f0f0;")  # Set background color
        for item in items:
            list_item = QListWidgetItem(getattr(item, display_attr))
            list_item.setData(Qt.UserRole, getattr(item, data_attr))
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Unchecked)
            group_list.addItem(list_item)

        # layout.addWidget(label) # add label and list widget to the layout
        layout.addWidget(group_list)
        grbox.setLayout(layout) # set the layout to the groupbox

        self.layout.addWidget(grbox, self.layout.rowCount(), 0, 1, 2)  # Span 2 columns
        return group_list


    def create_input_row(self, label_text, placeholder_text):
        label = MyQLabel(label_text)
        label.set_size_font(13)
        input_field = MyQLineEdit()
        input_field.set_size_font(13)
        input_field.set_placeholder(placeholder_text)
        self.layout.add_widgets_on_row([label, input_field])
        return input_field

    def create_password_row(self, label_text, placeholder_text):
        label = MyQLabel(label_text)
        label.set_size_font(13)
        password_field = MyQLineEdit()
        password_field.set_size_font(13)
        password_field.set_placeholder(placeholder_text)
        password_field.set_pass_word()
        show_button = self.create_show_password_button(password_field)
        show_button.set_size_font(18)
        show_button.setStyleSheet("QPushButton { background-color: white; border-style: solid; }"
                                    "QPushButton:hover { border-width: 2px; border-color: gold; }")
        self.layout.add_widgets_on_row([label, password_field, show_button])
        return password_field

    def create_show_password_button(self, password_field):
        button = MyQPushButton('️👁️')
        button.setCheckable(True)
        button.clicked.connect(lambda: self.toggle_password_visibility(password_field, button))
        return button

    def toggle_password_visibility(self, password_field, button):
        if button.isChecked():
            password_field.setEchoMode(QLineEdit.Normal)
            button.setText('️👁️‍🗨️')
        else:
            password_field.setEchoMode(QLineEdit.Password)
            button.setText('️👁️')
    

    def create_delete_group_button(self): # Đổi tên hàm
        button_layout = QHBoxLayout()
        empty = QWidget()
        button_layout.addWidget(empty)

        self.register_push = MyQPushButton('Thêm người dùng')   # Reduced width
        # self.register_push.set_size_font(10)
        # self.register_push.set_size(width=200, height=32)
        self.register_push.set_style_3D()
        self.register_push.clicked.connect(self.add_user)
        
        button_layout.addWidget(self.register_push)

        self.delete_group_button = MyQPushButton('Xóa nhóm')   # Reduced width
        # self.delete_group_button.set_size_font(10)
        # self.delete_group_button.set_size(width=200, height=32)
        self.delete_group_button.set_style_3D()
        self.delete_group_button.clicked.connect(self.delete_selected_groups)
        button_layout.addWidget(self.delete_group_button)

        self.layout.addLayout(button_layout, self.layout.rowCount(), 0, 1, 2)

    def delete_selected_groups(self):  # Đổi tên hàm
        """Xóa các nhóm người dùng đã chọn."""
        selected_group_ids = []  # Đổi tên biến
        for i in range(self.group_list.count()):  # Đổi tên biến
            item = self.group_list.item(i)  # Đổi tên biến
            if item.checkState() == Qt.Checked:
                selected_group_ids.append(item.data(Qt.UserRole))  # Đổi tên biến

        if not selected_group_ids:  # Đổi tên biến
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn nhóm người dùng để xóa.")
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc chắn muốn xóa nhóm người dùng đã chọn?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            groups_not_removed = [] # Đổi tên biến số cho rõ ràng
            for group_id in selected_group_ids:  # Đổi tên biến
                # group_name = self.groups_manager.get(group_id)
                group_name = self.groups_manager.delete_group(group_id)
                if not group_name:
                    groups_not_removed.append(group_id)
                else :
                    # users = self.user_manager.get_users_with_group(group_id)
                    QMessageBox.information(self, "Thành công", f"Nhóm người dùng {group_name} đã xoá thành công.")
            if groups_not_removed:
                users_not_removed_messages = ["Không thể xoá nhóm, trừ khi xoá đồng loạt các Users dưới đây:\n"]
                for group_id in groups_not_removed:
                    users = self.user_manager.get_users_with_group(group_id)
                    if users: #Kiểm tra xem có user nào trong group không.
                        user_names = [user.username for user in users]                       
                       
                        users_not_removed_messages.extend(user_names)
                        message = ", ".join(users_not_removed_messages)
                        QMessageBox.warning(self, "Lỗi", message) # Không thể xoá Users có gắn với Groups vì liên quan đến Rolls 
            else:
                self.update_group_list()  # Đổi tên hàm

    def add_user(self):
        username = self.username.text().strip()
        password = self.password.text().strip()
        re_password = self.re_password.text().strip()
        group_ids = []
        role_ids = []  # Danh sách để lưu trữ ID của các vai trò đã chọn

        # Lấy ID của các nhóm đã chọn
        for i in range(self.group_list.count()):
            item = self.group_list.item(i)
            if item.checkState() == Qt.Checked:
                group_id = item.data(Qt.UserRole)
                if group_id not in group_ids: # Tránh việc trùng lặp dữ liệu
                    group_ids.append(group_id)
                

                # Lấy ID của rolls
                rolls_list = self.groups_manager.get_rolls_in_group(group_id)
                for roll in rolls_list:
                    if roll.id not in role_ids: # Tránh việc trùng lặp dữ liệu
                        role_ids.append(roll.id)                


        if not username:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập.")
            return

        if not password or not re_password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mật khẩu và xác nhận mật khẩu.")
            return

        if password != re_password:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu và xác nhận mật khẩu không khớp.")
            return

        
        if len(role_ids) == 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất 1 nhóm người dùng.")
            return
        
        session = self.db_manager.get_session()
        try:
            # Truyền cả group_ids và role_ids vào hàm add_user
            success = self.user_manager.add_user(username, password, re_password, group_ids, role_ids)
            if success:
                # Phát tín hiệu cho user_permissions_table nhận
                self.user_added.emit()
                if self.user_permissions_table:
                    QMessageBox.information(self, "Thành công", "Người dùng đã được thêm thành công.")
                    self.clear_input_fields()
                    self.user_permissions_table.update_table()
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể thêm người dùng. Vui lòng kiểm tra lại thông tin.")
        except Exception as e:
            session.rollback()
            QMessageBox.warning(self, "Lỗi", f"Lỗi: {str(e)}")
        finally:
            session.close()


    def clear_input_fields(self):
        self.username.clear()
        self.password.clear()
        self.re_password.clear()
        for i in range(self.group_list.count()): # Đổi tên biến
            item = self.group_list.item(i) # Đổi tên biến
            item.setCheckState(Qt.Unchecked)

    def update_group_list(self): # Đổi tên hàm
        self.group_list.clear() # Đổi tên biến
        # fsdfs
        groups = self.groups_manager.get_groups()
        for group in groups:
            list_item = QListWidgetItem(group.name)
            # Hãy lưu trữ dữ liệu này, và tôi sẽ truy xuất nó sau này bằng 'khóa' này (là Qt.UserRoll)"
            list_item.setData(Qt.UserRole, group.id)
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Unchecked)
            self.group_list.addItem(list_item) # Đổi tên biến

    def create_title_row(self):
        title_label = MyQLabel('Đăng Ký Người Dùng')
        title_label.set_size_font(18)
        self.layout.add_widgets_on_row([title_label])

    def create_horizontal_layout(self):
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.group_box)
        return horizontal_layout

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        if not self.is_visible:
            self.is_visible = True
            self.update_group_list() # Đổi tên hàm

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    import time

    start_time = time.time()
    app = QApplication(sys.argv)
    window = RegisterForm(None, None)
    window.show()
    end_time = time.time()