from gui.widgets import MyQLabel, MyQLineEdit, QPushButton, QLineEdit
from PySide6.QtCore import QTimer

class UserRow:
    def __init__(self, layout):
        self.layout = layout
        self.username = self.create_user_row()

    def create_user_row(self):
        lb_user = MyQLabel('Tên đăng nhập')
        lb_user.set_size_font(13)
        
        username = MyQLineEdit()
        username.set_size_font(13)
        username.set_placeholder('Nhập mới tên người dùng')

        self.layout.add_widgets_on_row([lb_user, username])
        return username


class PasswordRow:
    def __init__(self, layout, isRePassWord=False):
        self.layout = layout
        self.label, self.password, self.toggle_button = self.create_pass_word_row(isRePassWord)
        #  = self.create_toggle_button()
        # self.re_password = self.create_re_pass_word_row()
        # self.toggle_button = self.create_toggle_button()

    # Create pass word
    def create_pass_word_row(self, isRePassWord):
        if not isRePassWord:
            lb_pw = MyQLabel('Mật khẩu')
        else:
            lb_pw = MyQLabel('Xác thực')

        lb_pw.set_size_font(13)
        
        pass_word = MyQLineEdit()
        pass_word.set_size_font(13)
        # self.pass_word.set_fixed_size(300, 27)
        if not isRePassWord:
            pass_word.set_placeholder('Nhập mật khẩu mới')
        else:
            pass_word.set_placeholder('Nhập lại mật khẩu, để xác thực')

        # Set kiểu password ****
        pass_word.set_pass_word()

        # View pass word        
        toggle_button = QPushButton('👁️') # Biểu tượng mắt đóng
        # self.toggle_button.set_size_font(8)
        # self.toggle_button.set_icon(f'{STATIC_DIR}/icon/close_eye.png')
        # self.toggle_button.set_icon_size(32,32)  # Thay đổi kích thước biểu tượng
        toggle_button.setStyleSheet("My {"
                        "background-color: white;"                        
                        "border-style: solid;"                       
                        
                        "}"
                        "QPushButton:hover {"
                        "background-color: gold;"
                        "}"
                        )
        # self.toggle_button.set_size_font(18)
        toggle_button.setCheckable(True)
        toggle_button.clicked.connect(self.toggle_password_visibility)


        self.layout.add_widgets_on_row([lb_pw, pass_word, toggle_button])
        
        # self.toggle_button.clicked.connect(self.abc)
        return lb_pw, pass_word, toggle_button
       

    def toggle_password_visibility(self):
        if self.toggle_button.isChecked():
            self.password.setEchoMode(QLineEdit.Normal)
            self.toggle_button.setText('👁️‍🗨️')  # Biểu tượng mắt mở
        else:
            self.password.setEchoMode(QLineEdit.Password)
            self.toggle_button.setText('👁️')  # Biểu tượng mắt đóng
    
   