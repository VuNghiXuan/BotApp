# login.py
from PySide6.QtWidgets import(
    
    QWidget,
    
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QGroupBox, 
    QSizePolicy

)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QShowEvent
# from vunghixuan.settings import color_fnt_bg
from vunghixuan.settings import color_fnt_bg, DATABASE_URL
# from vunghixuan.account.register import user_managers
from vunghixuan.account.register.db_manager import DatabaseManager
from vunghixuan.account.register.user_manager import UserManager


class LoginGroupBox(QWidget):
    def __init__(self, main_window, user_manager):#
        super().__init__()
        self.main_window = main_window
        self.user_manager = user_manager
        self.initUI()

    def set_background(self):
        # Tạo nền xanh
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color_fnt_bg[0])  # Màu xanh lục
        palette.setColor(self.backgroundRole(), color_fnt_bg[1])  # Màu xanh lục

        self.setAutoFillBackground(True)
        self.setPalette(palette)

    def initUI(self):
        # self.set_background()

        layout = QVBoxLayout()
        group_box = QGroupBox("") #Đăng Nhập
        
        lb_login = QLabel('ĐĂNG NHẬP HỆ THỐNG')
        # lb_login.setStyleSheet("font-size: 20px; color: white;") 
        lb_login.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lb_login.setFixedHeight(30)  # Thiết lập chiều cao cố định cho lb_login
        

        lb_login.setStyleSheet(f"background-color: {color_fnt_bg[0]}; color: {color_fnt_bg[1]}; font-size: 18px;")
        # lb_login.setStyleSheet('background-color: #007f8c; font-size: 20px; color: white;')
        # lb_login.setStyleSheet(f"background-color: {QColor(0, 127, 140).name()};")
        # '#007f8c'
        # print(QColor(0, 127, 140).name())

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên người dùng")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        login_button = QPushButton("Đăng Nhập")
        login_button.clicked.connect(self.handle_login)

        layout.addWidget(lb_login)        
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        group_box.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(group_box)
        self.setLayout(main_layout)

        # Thiết lập kích thước tối thiểu cho form
        self.setMaximumSize(350, 250)
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.username_input.returnPressed.connect(self.password_input.setFocus)

        # Kết nối sự kiện returnPressed và editingFinished của password_input
        self.password_input.returnPressed.connect(self.handle_login)
        

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        isUser = self.user_manager.verify_user(username, password)
        if isUser:
            self.hide()
            self.parent().tab_widget.setVisible(True)

            # Đảm bảo không có cờ toàn màn hình
            if self.main_window.windowState() & Qt.WindowFullScreen:
                self.main_window.setWindowState(self.main_window.windowState() & ~Qt.WindowFullScreen)

            # Hiển thị ở trạng thái phóng to
            self.main_window.showMaximized()

            self.main_window.handle_login_success(username)
        else:
            QMessageBox.warning(self, "Lỗi", "Tên người dùng hoặc mật khẩu không đúng.")


    def showEvent(self, event: QShowEvent):
        """Ghi đè phương thức showEvent để đặt focus sau khi form được hiển thị."""
        super().showEvent(event)
        self.username_input.setFocus()