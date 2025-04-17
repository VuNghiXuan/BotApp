# custom_menubar.py
from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QAction, QIcon, QFont
from PySide6.QtCore import Signal
from config.config_menubar import create_menubar

# # Khai báo và định nghĩa các Menu
# class MenuActionTitle():
#     def __init__(self):
#         # Khởi tạo từ điển chứa tiêu đề menu và các hành động tương ứng
#         self.title_menu = {
#             "Nhập dữ liệu": ["Đổi dẻ", "Bán dẻ", "Mua dẻ"],
#             "Báo cáo": ["Đổi dẻ", "Bán dẻ", "Mua dẻ", "Công nợ", "Phiếu xuất", "Phiếu nhập"],
#             "Hướng dẫn": ["Nhập file Đổi dẻ", "Nhập file Bán dẻ", "Nhập file Mua dẻ", "Xuất báo Công nợ"],
#         }  

class WigetsMenuBar(QMenuBar):
    action_triggered = Signal(str)  # Tạo tín hiệu cho hành động

    def __init__(self, parent=None):
        # Khởi tạo thanh menu tùy chỉnh
        super().__init__(parent)
        # Thiết lập định dạng cho thanh menu
        self.set_config()
        # Tạo các menu từ tiêu đề đã định nghĩa
        self.create_menus()

    def create_menus(self):        
        # Tạo các menu cha và hành động con từ Menu_Bar        
        menubar = create_menubar()
        for menu in menubar.menus:
            self.create_parent_action(menu.name, menu.actions)


    def create_parent_action(self, parent_name, child_names):
        # Tạo menu cha và thêm các hành động con vào menu
        parent_menu = self.addMenu(parent_name)
        for child in child_names:
            child_action = QAction(child.name, self)
            # Kết nối hành động với phương thức xử lý
            child_action.triggered.connect(lambda checked, name=child.name: self.action_triggered.emit(name))
            # child_action.triggered.connect(lambda checked, name=child: self.handle_action(name))
            parent_menu.addAction(child_action)
    
    # # Xử lý các hành động khi người dùng chọn
    # def handle_action(self, action_name):
    #     if action_name == "Đổi dẻ":
    #         print("Thực hiện hành động Đổi dẻ")
    #     elif action_name == "Bán dẻ":
    #         print("Thực hiện hành động Bán dẻ")
    #     elif action_name == "Mua dẻ":
    #         print("Thực hiện hành động Mua dẻ")

    # Thiết lập định dạng cho thanh menu
    def set_config(self):    
        self.setStyleSheet("""
            QMenuBar {
                background-color: #006400; /* Màu xanh Excel*/
                color: white;
                font-size: 16px; 
            }
            QMenuBar::item {
                background-color: #006400;/* Màu xanh Excel*/
                padding: 5px;
            }
            QMenuBar::item:selected {
                background-color: #ffd700; /* Màu vàng gold*/
                color: #006400; 
            }
            QMenu {
                background-color: #006400;/* Màu xanh Excel*/
                color: white;
                font-size: 15px;
            }
            QMenu::item:selected {
                background-color: #006400;/* Màu xanh Excel*/
                color: #ffd700; /* Màu vàng gold*/
            }
        """)
