# -*- coding: utf-8 -*-
# add_new_role_per_form.py

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMessageBox, QPushButton, QLabel, QLineEdit,
    QSpacerItem, QSizePolicy, QGroupBox, QHBoxLayout, QComboBox, QCheckBox, QScrollArea,
    QWidget, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import Qt, QFont
from PySide6.QtCore import Signal, Slot

from vunghixuan.account.register.models import User, Roll, Permission
# from vunghixuan.account.register.user_controllers import (
#     DatabaseManager, UserManager, RollManager, PermissionManager, AppManager
# )
from vunghixuan.gui.widgets_for_register import SearchTable
from vunghixuan.settings import DATABASE_URL

class UserPermissionsTable(QWidget):
    """
    A widget to display and manage user permissions.  It uses the SearchTable
    widget to display the data.
    """
    update_table_signal = Signal()

    def __init__(self,  db_manager, user_manager, roll_manager, permission_manager, parent=None): #Removed db managers
        super().__init__(parent)
        self.db_manager = db_manager # Removed
        self.user_manager = user_manager # Removed
        self.roll_manager = roll_manager # Removed
        self.permission_manager = permission_manager # Removed
        self.initUI()
        self._last_column_index = -1 # Lưu trữ index của cột cuối cùng
        self.load_data()  # Load data in showEvent, not in constructor.
        self.update_table_signal.connect(self.update_table_slot)
        self.user_list = []

    def initUI(self):
        """Initializes the user interface."""
        self.setWindowTitle("Danh sách người dùng và quyền")
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.searchable_table = SearchTable()
        

        self.main_layout.addWidget(self.searchable_table)
        # self.searchable_table.table_widget.user_deleted.connect(self.update_table_slot)
        self.searchable_table.table_widget.username_signal.connect(self.del_user_and_update_table)
        # self.received_user.username_deleted.conect(self.handle_received_action)

    
    def load_data(self):
        """Loads user data (including roles, apps, interfaces, and permissions) into the table."""
        # Simulate data loading
        users_data = self.user_manager.get_all_users_with_details()
        table_data = self.user_manager.convert_users_data_for_table(users_data)
        
        self.searchable_table.load_table_data(table_data)

        # Lấy chiều rộng khả dụng của searchable_table
        self.searchable_table.table_widget.load_data(table_data)
        # table_width = self.searchable_table.width()
        self.searchable_table.table_widget.set_column_widths([200, 200, 300, 400, 800])
        
    
    def delete_user(self, username):
        
            if username:
               
                reply = QMessageBox.question(
                    self,
                    "Xác nhận",
                    f'Bạn có chắc chắn muốn xóa người dùng "{username}"?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    # db_manager = DatabaseManager(DATABASE_URL)
                    # self.user_manager = UserManager(db_manager.get_session())
                    if self.user_manager.delete_user(username): #Removed user_manager
                        QMessageBox.information(self, "Thành công", f"Người dùng '{username}' đã được xóa.")
                        # self.load_user_roll_per_on_account_table()  # Refresh the table
                        # self.user_deleted.emit()
                    else:
                        QMessageBox.warning(self, "Lỗi", f"Không thể xóa người dùng '{username}'.")
                   
                
            else:
                QMessageBox.warning(self, "Error", "No user selected to delete.")


    @Slot()
    def update_table_slot(self):
        """Updates the table data."""
        self.load_data()
        self.searchable_table.table_widget.viewport().update()
        QApplication.processEvents()

    def update_table(self):
        """Emits the signal to update the table."""
        self.update_table_signal.emit()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data() # Load data when the widget is shown
    
    @Slot(str)
    def del_user_and_update_table(self, username):
        """Slot này sẽ nhận action từ form khác."""
        # print('Nhận tín hiệu', username)
        # Thực hiện xoá user
        self.delete_user(username)

        self.load_data()
        self.searchable_table.table_widget.viewport().update()
        QApplication.processEvents()

    def get_user_table_widget(self):
        return self.searchable_table.table_widget

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    # db_manager = DatabaseManager(DATABASE_URL) # Removed
    # user_manager = UserManager(db_manager.get_session()) # Removed
    # roll_manager = RollManager(db_manager.get_session()) # Removed
    # permission_manager = PermissionManager(db_manager.get_session()) # Removed

    # window = UserPermissionsTable(db_manager, user_manager, roll_manager, permission_manager) #Removed db managers
    window = UserPermissionsTable()
    window.show()
    sys.exit(app.exec())