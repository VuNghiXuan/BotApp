from PySide6.QtWidgets import (
    QWidget, QMessageBox, QPushButton, QVBoxLayout, QLabel, QLineEdit,
    QScrollArea, QWidget, QGridLayout, QGroupBox, QHBoxLayout, QCheckBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtGui import Qt, QPalette, QColor
from PySide6.QtCore import Signal
from collections import defaultdict

# from vunghixuan.account.register.models import Roll, Permission, App
# from vunghixuan.account.register.user_controllers import (
#     DatabaseManager, UserManager, RollManager, PermissionManager, AppManager, GroupManager, InterfaceManager
# )
# from vunghixuan.account.register.user_controllers import UserController
from vunghixuan.gui.widgets import MyQLabel, MyQGridLayout, MyQLineEdit, MyQPushButton
from vunghixuan.settings import DATABASE_URL
import logging
import trace

from vunghixuan.account.register.user_manager import UserManager
from vunghixuan.account.register.group_manager import GroupManager
from vunghixuan.account.register.roll_manager import RollManager
from vunghixuan.account.register.permisson_manager import PermissionManager
from vunghixuan.account.register.interface_manager import InterfaceManager
from vunghixuan.account.register.app_manager import AppManager
from vunghixuan.account.register.db_manager import DatabaseManager
import traceback


class PermissionForm(QWidget):
    group_added = Signal(str)

    def __init__(self, register_form=None):
        super().__init__()
        self.db_manager = DatabaseManager(DATABASE_URL)
        self.user_manager = UserManager(self.db_manager.get_session())
        self.roll_manager = RollManager(self.db_manager.get_session())
        self.permission_manager = PermissionManager(self.db_manager.get_session())
        self.app_manager = AppManager(self.db_manager.get_session())
        self.group_manager = GroupManager(self.db_manager.get_session())
        self.interface_manager = InterfaceManager(self.db_manager.get_session())
        # self.default_setup = DefaultSetup(self.db_manager.get_session())
        self.register_form = register_form
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Cấp quyền")
        self.main_layout = QVBoxLayout()

        self.setLayout(self.main_layout)

        self.create_group_groupbox()
        self.create_roll_groupbox()

    def create_group_groupbox(self):
        self.group_groupbox = QGroupBox("Nhóm người dùng")
        group_layout = QGridLayout()
        self.group_groupbox.setLayout(group_layout)
        self.main_layout.addWidget(self.group_groupbox)

        self.group_name_input = self.create_input_row("Tên nhóm người dùng", "Nhập tên nhóm người dùng", group_layout, row=0)
        self.group_description_input = self.create_input_row("Mô tả nhóm", "Nhập mô tả nhóm", group_layout, row=1)  # Added description input
        self.roll_checkboxes_layout = QVBoxLayout()
        group_layout.addLayout(self.roll_checkboxes_layout, group_layout.rowCount(), 0, 1, 2)
        self.create_initial_roll_checkboxes(self.roll_checkboxes_layout)  # Tạo label và checkbox lần đầu tiên
        self.create_group_buttons(group_layout)

    def create_group_buttons(self, layout):
        button_layout = QHBoxLayout()
        self.add_group_button = MyQPushButton('Thêm nhóm người dùng')
        # self.add_group_button.set_size_font(12)
        # self.add_group_button.set_size(width=200, height=32)
        self.add_group_button.set_style_3D()
        self.add_group_button.clicked.connect(self.add_group_with_rolls)
        button_layout.addWidget(self.add_group_button)

        self.delete_group_button = MyQPushButton('Xóa nhóm quyền')
        # self.delete_group_button.set_size_font(12)
        # self.delete_group_button.set_size(width=200, height=32)
        self.delete_group_button.set_style_3D()
        self.delete_group_button.clicked.connect(self.delete_selected_rolls)
        button_layout.addWidget(self.delete_group_button)

        layout.addLayout(button_layout, layout.rowCount(), 0, 1, 2, alignment=Qt.AlignRight)

    def create_roll_groupbox(self):
        self.roll_groupbox = QGroupBox("Nhóm quyền")
        roll_layout = QGridLayout()
        self.roll_groupbox.setLayout(roll_layout)
        self.main_layout.addWidget(self.roll_groupbox)

        self.roll_name_input = self.create_input_row("Tên nhóm quyền", "Nhập tên nhóm quyền", roll_layout)
        self.permission_checkboxes = self.create_permission_checkboxes(roll_layout)
        self.add_permission_button = self.create_push_row(roll_layout)

    def create_input_row(self, label_text, placeholder_text, layout, row=None):
        label = MyQLabel(label_text)
        label.set_size_font(13)

        input_field = MyQLineEdit()
        input_field.set_size_font(13)
        input_field.set_placeholder(placeholder_text)
        if row is not None:
            layout.addWidget(label, row, 0)
            layout.addWidget(input_field, row, 1)
        else:
            layout.addWidget(label, layout.rowCount(), 0)
            layout.addWidget(input_field, layout.rowCount() - 1, 1)
        return input_field

    def create_initial_roll_checkboxes(self, layout):
        roll_group_box = QGroupBox("Các nhóm quyền:")
        roll_grid_layout = QGridLayout()
        roll_group_box.setLayout(roll_grid_layout)

        # Set background color
        palette = roll_group_box.palette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        roll_group_box.setPalette(palette)
        roll_group_box.setAutoFillBackground(True)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(roll_group_box)

        layout.addWidget(scroll_area)

        self.roll_checkboxes = {}
        rolls = self.roll_manager.get_rolls()
        row, col = 0, 0
        for roll in rolls:
            checkbox = QCheckBox(roll.name)
            self.roll_checkboxes[checkbox] = roll.id
            roll_grid_layout.addWidget(checkbox, row, col)
            col += 1
            if col == 4:
                col = 0
                row += 1

    def update_roll_checkboxes(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(item.widget(), QScrollArea):
                item.widget().deleteLater()
            layout.removeItem(item)
        self.create_initial_roll_checkboxes(layout)

    def create_permission_checkboxes(self, layout):
        # label = MyQLabel("Cấp quyền cho nhóm")
        # label.set_size_font(12)

        checkbox_widget = QWidget()
        checkbox_layout = QVBoxLayout()
        checkbox_widget.setLayout(checkbox_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(checkbox_widget)

        self.permission_checkboxes = {}

        grid_layout = QVBoxLayout()
        checkbox_layout.addLayout(grid_layout)

        interfaces = self.interface_manager.get_interfaces()

        permissions = self.permission_manager.get_all_permissions()

        # xem sau

        for interface in interfaces:
            interface_name = interface.name

            group_box = QGroupBox(interface_name)
            group_layout = QGridLayout()
            group_box.setLayout(group_layout)
            grid_layout.addWidget(group_box)

            row, col = 0, 0
            for permission in permissions:
                checkbox = QCheckBox(permission.name)
                self.permission_checkboxes[f"{interface_name}#{permission.name}"] = (
                    checkbox,
                    interface.id,
                )  # changed the self.permission_checkboxes
                # self.permission_checkboxes[permission.id] = (checkbox, permission.name, interface.name)   # Changed key to permission.id

                group_layout.addWidget(checkbox, row, col)
                col += 1
                if col == 4:
                    col = 0
                    row += 1

        self.all_permissions_checkbox = QCheckBox("Tất cả các quyền")
        self.permission_checkboxes["all"] = (self.all_permissions_checkbox, None)
        checkbox_layout.addWidget(self.all_permissions_checkbox)

        self.all_permissions_checkbox.stateChanged.connect(self.toggle_all_permissions)

        # layout.addWidget(label, layout.rowCount(), 0, 1, 2)
        layout.addWidget(scroll_area, layout.rowCount(), 0, 1, 2)
        return self.permission_checkboxes

    def toggle_all_permissions(self, state):
        if state == Qt.Checked.value:
            for permission_id, (checkbox, interface_id) in self.permission_checkboxes.items():  # changed the self.permission_checkboxes
                if permission_id != "all":
                    checkbox.setChecked(True)
        else:
            for permission_id, (checkbox, interface_id) in self.permission_checkboxes.items():  # changed the self.permission_checkboxes
                if permission_id != "all":
                    checkbox.setChecked(False)

    def create_push_row(self, layout):
        push = MyQPushButton("Thêm quyền")
        push.set_size_font(12)
        push.set_style_3D()
        push.clicked.connect(self.add_roll_with_permissions)

        layout.addWidget(push, layout.rowCount(), 0, 1, 2)
        return push

    def add_roll_with_permissions(self):
        """Thêm vai trò mới cùng với các quyền."""
        roll_name = self.roll_name_input.text().strip()
        selected_permissions_data = []  # Changed to store a list of tuples

        for permission_key, (checkbox, interface_id) in self.permission_checkboxes.items():  # changed self.permission_checkboxes
            if checkbox.isChecked() and permission_key != "all":
                interface_name, permission_name = permission_key.split("#")
                selected_permissions_data.append(
                    (permission_name, interface_id)
                )  # Store (permission_name, interface_id)

        if not roll_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên nhóm quyền.")
            return

        if not selected_permissions_data:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất một quyền.")
            return

        try:
            # Truyền cả self vào add_roll_with_permissions để có thể gọi các hàm của Manageroll nếu cần
            success = self.roll_manager.add_roll_with_permissions(
                roll_name, selected_permissions_data
            )  # Pass the list of tuples
            if success:
                QMessageBox.information(
                    self, "Thành công", "Nhóm quyền đã được tạo thành công."
                )
                self.roll_name_input.clear()
                self.all_permissions_checkbox.setChecked(False)
                for permission_id, (checkbox, interface_name) in self.permission_checkboxes.items():  # changed self.permission_checkboxes
                    checkbox.setChecked(False)
                self.update_roll_checkboxes(self.roll_checkboxes_layout)
            else:
                QMessageBox.warning(self, "Lỗi", "Tên nhóm quyền đã tồn tại.")
        except Exception as e:
            print(f"Lỗi: {e}")
            QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi: {e}")  # Hiển thị thông báo lỗi cho người dùng

    def add_group_with_rolls(self):
        """Thêm nhóm người dùng mới với các vai trò (roles) đã chọn."""
        group_name = self.group_name_input.text().strip()
        group_description = self.group_description_input.text().strip() # Get group description
        selected_role_ids = []

        for checkbox, role_id in self.roll_checkboxes.items():
            if checkbox.isChecked():
                selected_role_ids.append(role_id)

        if not group_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên nhóm người dùng.")
            return

        if not selected_role_ids:
            QMessageBox.warning(
                self, "Lỗi", "Vui lòng chọn ít nhất một nhóm quyền (vai trò)."
            )
            return

        try:
            success = self.group_manager.add_group_with_rolls(
                group_name, selected_role_ids, group_description
            )  # Pass group_description
            if success:
                self.group_added.emit(group_name)  # Phát tín hiệu với tên nhóm mới
                if self.register_form:
                    self.register_form.update_group_list()  # Cập nhật RegisterForm
                QMessageBox.information(
                    self, "Thành công", "Nhóm người dùng đã được tạo thành công."
                )
                self.group_name_input.clear()
                self.group_description_input.clear()
                for checkbox in self.roll_checkboxes.keys():
                    checkbox.setChecked(False)
            else:
                QMessageBox.warning(
                    self,
                    "Lỗi",
                    "Tên nhóm người dùng có thể đã tồn tại hoặc có lỗi cơ sở dữ liệu.",
                )

        except Exception as e:
            error_message = f"Lỗi khi thêm nhóm: {e}\n{traceback.format_exc()}"
            logging.error(error_message)
            QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi: {e}")

    def delete_selected_rolls(self):
        """Xóa vai trò và các bản ghi liên quan."""
        selected_roll_ids = []
        for checkbox, roll_id in self.roll_checkboxes.items():
            if checkbox.isChecked():
                selected_roll_ids.append(roll_id)
        if not selected_roll_ids:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn nhóm quyền để xóa.")
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc chắn muốn xóa nhóm quyền đã chọn?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                for roll_id in selected_roll_ids:
                    # Kiểm tra xem vai trò có đang được gán cho người dùng hoặc nhóm nào không
                    if (
                        self.roll_manager.is_roll_assigned_to_users(roll_id)
                        or self.roll_manager.is_roll_assigned_to_groups(roll_id)
                    ):
                        QMessageBox.warning(
                            self,
                            "Lỗi",
                            f"Không thể xóa nhóm quyền có ID {roll_id} vì nó đang được gán cho người dùng hoặc nhóm.",
                        )
                        return  # Dừng xóa nếu có vai trò đang được sử dụng

                for roll_id in selected_roll_ids:
                    # Trước tiên, xóa các bản ghi liên quan trong các bảng trung gian
                    # Lưu ý: Thứ tự xóa có thể quan trọng để tránh vi phạm ràng buộc khóa ngoại
                    # self.roll_manager.remove_roll_from_all_users(roll_id)   # Xóa khỏi bảng user_roll
                    # self.roll_manager.remove_roll_from_all_groups(roll_id) # Xóa khỏi bảng group_roll
                    # self.roll_manager.remove_roll_permissions(roll_id)       # Xóa khỏi bảng roll_permission
                    # self.roll_manager.remove_roll_apps(roll_id)             # Xóa khỏi bảng roll_app
                    # Sau khi đã xóa các bản ghi liên quan, xóa vai trò
                    self.roll_manager.delete_roll(roll_id)
                self.update_roll_checkboxes(self.roll_checkboxes_layout)
                QMessageBox.information(
                    self, "Thành công", "Đã xóa thành công các nhóm quyền đã chọn."
                )
            except Exception as e:
                self.db_manager.get_session().rollback()  # Rollback nếu có lỗi
                QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi khi xóa: {e}")
                print(f"Lỗi khi xóa vai trò: {e}")
            finally:
                self.db_manager.close()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    import time

    start_time = time.time()
    app = QApplication(sys.argv)
    window = PermissionForm(None)
    window.show()
    end_time = time.time()
    print(f"Thời gian chạy ứng dụng: {end_time - start_time:.4f} giây")
    sys.exit(app.exec())
