# account_form.py
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)
# from vunghixuan.account.register.user_controllers import (
#     DatabaseManager, UserManager, RollManager, PermissionManager, AppManager
# )
from vunghixuan.account.register.db_manager import DefaultSetup, DatabaseManager
from vunghixuan.account.roll_permissions.acount_table import UserPermissionsTable
from vunghixuan.account.roll_permissions.permission_form import PermissionForm
from vunghixuan.account.register.register_form import RegisterForm
from vunghixuan.settings import DATABASE_URL
from vunghixuan.account.register.user_manager import UserManager
from vunghixuan.account.register.roll_manager import RollManager
from vunghixuan.account.register.permisson_manager import PermissionManager
from vunghixuan.account.register.app_manager import AppManager


class AccountForm(QWidget):
    """
    Đây là Form chứa và sắp xếp toàn bộ giao diện: RegisterForm (phải), PermissionManager (trái), UserPermissionsTable (dưới)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = 'Quản lý tài khoản'
        self.db_manager = DatabaseManager(DATABASE_URL)
        self.user_manager = UserManager(self.db_manager.get_session())
        self.roll_manager = RollManager(self.db_manager.get_session())
        self.permission_manager = PermissionManager(self.db_manager.get_session())
        self.app_manager = AppManager(self.db_manager.get_session())
        self.default_setup = DefaultSetup(self.db_manager.get_session())

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Account Form")
        self.main_layout = QVBoxLayout(self)

        # Initialize UserPermissionsTable
        self.user_permissions_table = UserPermissionsTable(self.db_manager, self.user_manager, self.roll_manager, self.permission_manager)

        # Initialize PermissionForm
        self.permission_form = PermissionForm(self.user_permissions_table)

        # Initialize RegisterForm, passing user_permissions_table and permission_form
        self.register_form = RegisterForm(self.user_permissions_table, self.permission_form)

        # Update register_form for permission_form
        self.permission_form.register_form = self.register_form

        # Create horizontal layout for RegisterForm and PermissionForm
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setSpacing(0)  # Loại bỏ khoảng cách giữa register_form và permission_form
        horizontal_layout.addWidget(self.register_form)
        horizontal_layout.addWidget(self.permission_form)

        # Set stretch factors to make RegisterForm occupy 1/3 of the width
        horizontal_layout.setStretch(0, 1)  # RegisterForm stretch factor: 1
        horizontal_layout.setStretch(1, 2)  # PermissionForm stretch factor: 2

        # Add horizontal layout and UserPermissionsTable to main layout
        self.main_layout.addLayout(horizontal_layout)
        self.main_layout.addWidget(self.user_permissions_table)

        # Thiết lập stretch factor cho main_layout
        # Giả sử PermissionForm (và RegisterForm đi kèm) chiếm 2 phần và UserPermissionsTable chiếm 1 phần
        self.main_layout.setStretchFactor(horizontal_layout, 1)
        self.main_layout.setStretchFactor(self.user_permissions_table, 1)