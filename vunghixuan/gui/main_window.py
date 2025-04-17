import sys, os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QSizePolicy
)
from PySide6.QtGui import QFont
from vunghixuan.gui.login import LoginGroupBox
from vunghixuan.settings import COLOR_FONT_BACKGROUND, color_fnt_bg, label_name_change_color
from vunghixuan.gui.menu_tab import MainTab
from PySide6.QtCore import Signal, Slot
from vunghixuan.gui.models_manage import ModelsManager
# from vunghixuan.gui.permissions_manage import PermissionManager # Remove this import
from vunghixuan.gui.forms_manage import FormManager
# from vunghixuan.account.register.user_controllers import UserManager, DatabaseManager  # Import UserManager và DatabaseManager

from vunghixuan.settings import DATABASE_URL  # Import DATABASE_URL
from vunghixuan.account.register.user_manager import UserManager
# from vunghixuan.account.register.group_manager import GroupManager
# from vunghixuan.account.register.roll_manager import RollManager
from vunghixuan.account.register.permisson_manager import PermissionManager  # Corrected import
# from vunghixuan.account.register.interface_manager import InterfaceManager
# from vunghixuan.account.register.app_manager import AppManager
from vunghixuan.account.register.db_manager import DatabaseManager


class Header(QWidget):
    theme_changed = Signal(tuple)

    def __init__(self, form_manager, main_window):
        super().__init__()
        self.form_manager = form_manager
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        logo = QLabel('VuNghiXuan')
        logo.setFont(QFont('Brush Script MT', 20))
        logo.setStyleSheet("color: gold;")
        layout.addWidget(logo)
        layout.addStretch()

        self.theme_selector = QComboBox(self)
        self.theme_selector.addItems(['-- Chọn nền và màu chữ --'] + list(COLOR_FONT_BACKGROUND.keys()))
        self.theme_selector.currentIndexChanged.connect(self.on_theme_changed)
        layout.addWidget(self.theme_selector)

        # login = QPushButton('Đăng nhập')
        register = QPushButton('Đăng ký')
        close_bnt = QPushButton('Thoát')
        register.clicked.connect(self.show_register_form)
        close_bnt.clicked.connect(self.close_form)
        layout.addWidget(register)
        layout.addWidget(close_bnt)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setFixedHeight(50)

    def on_theme_changed(self, index):
        if index != 0:
            color_name = self.theme_selector.currentText()
            self.theme_changed.emit(COLOR_FONT_BACKGROUND[color_name])

    def show_register_form(self):
        print('Hiện tab đăng ký và quản lý tài khoản')
        self.form_manager.register_form

    def close_form(self):
        'Thực hiện đóng form'
        self.main_window.close()

    def set_background(self, color_fnt_bg):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color_fnt_bg[0])
        palette.setColor(self.foregroundRole(), color_fnt_bg[1])
        self.setAutoFillBackground(True)
        self.setPalette(palette)


class Footer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        logo = QLabel("@Copyright 2025 by VuNghiXuan")
        layout.addWidget(logo)
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.setFixedHeight(50)

    def set_background(self, color_fnt_bg):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color_fnt_bg[0])
        palette.setColor(self.foregroundRole(), color_fnt_bg[1])
        self.setAutoFillBackground(True)
        self.setPalette(palette)


class ContentView(QWidget):
    data_changed = Signal(str)

    def __init__(self, form_manager, app_manager, main_window):
        super().__init__()
        self.form_manager = form_manager
        self.models_manager = app_manager
        self.main_window = main_window

        self.user_access_info = self.main_window.user_access_info # Khởi tạo user_permissions
        self.permission_manager = None # Initialize PermissionManager
        self.initUI()

    def initUI(self):
        self.tab_widget = MainTab(self.form_manager.account_form) # Truyền account_form
        layout = QVBoxLayout()
        layout.setSpacing(0)

        if self.models_manager.check_any_user_exists():
            # Nếu đã có người dùng, hiển thị form đăng nhập
            self.login_widget = self.form_manager.login_form
            layout.addWidget(self.login_widget)
            self.tab_widget.setVisible(False)
            # Không thêm account_form trực tiếp ở đây
        else:
            # Nếu chưa có người dùng, có thể hiển thị một form đăng ký ban đầu
            layout.addWidget(self.form_manager.account_form) # Giả sử bạn có register_form riêng
            if hasattr(self, 'login_widget'):
                self.login_widget.setVisible(False)
            self.tab_widget.setVisible(False)

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        self.form_manager.account_form.permission_form.group_added.connect(self.data_changed.emit)
        self.form_manager.account_form.register_form.user_added.connect(lambda: self.data_changed.emit("user_added"))
        self.data_changed.connect(self.update_all_forms)

    @Slot(str)
    def update_all_forms(self, data):
        """Slot nhận chuỗi và xử lý."""
        self.form_manager.account_form.register_form.update_group_list()
        self.form_manager.account_form.user_permissions_table.update_table()
        print(f"Data changed: {data}")

    def set_background(self, color_fnt_bg):
        for grbox in self.findChildren(QGroupBox):
            for label in grbox.findChildren(QLabel):
                if label.text() in label_name_change_color:
                    label.setStyleSheet(
                        f"background-color: {color_fnt_bg[0]}; color: {color_fnt_bg[1]}; font-size: 18px;")

    
    def update_user_interface(self, user_access_info):
        self.tab_widget.apply_permissions(user_access_info)
        self.tab_widget.setVisible(True)
        # Không ẩn account_form ở đây nữa, MainTab sẽ quản lý nó
        if hasattr(self, 'login_widget'):
            self.login_widget.setVisible(False)

class BackgroundManager:
    def __init__(self, widgets):
        self.widgets = widgets

    def set_background(self, color_fnt_bg):
        for widget in self.widgets:
            widget.set_background(color_fnt_bg)


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Tạo một đối tượng DatabaseManager và UserManager
        self.db_manager = DatabaseManager(DATABASE_URL)
        self.user_manager = UserManager(self.db_manager.get_session())
        self.models_manager = ModelsManager(self.user_manager)  # Truyền user_manager vào ModelsManager
        self.form_manager = FormManager(self.models_manager, self)
        self.user_access_info = None
        self.initUI()

    def initUI(self):
        # self.setGeometry(100, 100, 800, 600)
        self.showMaximized()
        self.setWindowTitle('Phần mềm VuNghiXuan')

        center_layout = QWidget()
        main_layout = QVBoxLayout()

        self.header = Header(self.form_manager, self)
        self.header.theme_changed.connect(self.change_theme)
        main_layout.addWidget(self.header)

        self.content = ContentView(self.form_manager, self.models_manager, self)
        main_layout.addWidget(self.content)

        self.footer = Footer()
        main_layout.addWidget(self.footer)

        center_layout.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(center_layout)

        self.background_manager = BackgroundManager(
            [self.header, self.footer, self.content])        
        
        self.change_theme(color_fnt_bg)

    def change_theme(self, color_fnt_bg):        
            self.background_manager.set_background(color_fnt_bg)
            self.update_color_theme()

    def update_color_theme(self):
        if self.header.theme_selector.currentIndex() !=0:
            from vunghixuan import setting_controlls

            color_fnt_bg = self.header.theme_selector.currentText()
            setting_controlls.update_theme(color_fnt_bg)

    def closeEvent(self, event):
        event.accept()

    # Sau khi login thì lấy quyền người dùng
    def handle_login_success(self, username):
        # self.content.update_user_permissions(user_permissions)
        self.user_access_info = self.user_manager.get_user_access_info(username)       
        print('Thông tin User truy cập', self.user_access_info)
        self.content.update_user_interface(self.user_access_info)



def show():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    show()
