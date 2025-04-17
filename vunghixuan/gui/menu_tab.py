from PySide6.QtWidgets import (
    QApplication, QTabWidget, QWidget, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy,
    QTabBar, QPushButton, QHBoxLayout, QMenu, QTableWidget
)
from vunghixuan.gui.widgets import MyQTableWidget
from PySide6.QtGui import QIcon, QDrag, QAction, QColor, QPalette
from PySide6.QtCore import Qt, QSize, QMimeData, QPoint

# from vunghixuan.gui.login import LoginGroupBox
# from vunghixuan.account.register.register_form import RegisterForm
# from vunghixuan.account.roll_permissions.permission_form import PermissionForm
from vunghixuan.account.roll_permissions.acount_table import UserPermissionsTable
from vunghixuan.settings import TABS_INFO
# from vunghixuan.account.register.user_controllers import UserController
from vunghixuan.bot_station.check_tick_form import CheckTicketsForm




class SubTab(QWidget):
    def __init__(self, tab_name, account_form, interface_permissions=None):
        super().__init__()
        self.layout = QVBoxLayout()
        self.account_form = account_form
        self.interface_permissions = interface_permissions if interface_permissions else []
        self.content_widget = self.create_content_widget(tab_name)
        self.layout.addWidget(self.content_widget)
        self.setLayout(self.layout)

    def create_content_widget(self, tab_name):
        if tab_name == "Quản lý tài khoản":
            widget = self.account_form
            has_delete_permission = False
            for interface in self.interface_permissions:
                if interface['name'] == tab_name:
                    pers = [per.lower() for per in interface['permissions']]
                    print(f"Danh sách quyền (pers) cho '{tab_name}': {pers}")
                    if 'xóa' in pers or 'xoá' in pers:
                        has_delete_permission = True
                    break

            # Xử lý QPushButton
            for child in widget.findChildren(QPushButton):
                if "xóa" in child.text().lower():
                    if not has_delete_permission:
                        child.setEnabled(False)
                        disabled_bg_color = QColor(200, 200, 200).name()
                        disabled_text_color = QColor(100, 100, 100).name()
                        current_stylesheet = child.styleSheet()
                        new_stylesheet = current_stylesheet + f"""
                            QPushButton:disabled {{
                                background-color: {disabled_bg_color};
                                color: {disabled_text_color};
                            }}
                        """
                        child.setStyleSheet(new_stylesheet)

            # Tìm UserPermissionsTable và xử lý QAction
            user_permissions_table = None
            for child in widget.findChildren(UserPermissionsTable):
                user_permissions_table = child
                break

            if user_permissions_table:
                user_table_widget = user_permissions_table.get_user_table_widget()
                if user_table_widget:
                    user_table_widget.set_delete_action_enabled(has_delete_permission)

                        

            return widget
        elif tab_name == "Đối soát files":
            return CheckTicketsForm()
        
        else: #Đối soát vé BOT
            label = QLabel(f'Tab con {tab_name}')
            return label
        
class ClosableTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)

    def close_tab(self, index):
        self.parent().close_tab(index)

class MainTab(QTabWidget):
    def __init__(self, account_form):
        super().__init__()
        self.account_form = account_form
        self.setTabBar(ClosableTabBar(self))
        # self.add_main_tabs() # Chuyển việc thêm tab vào hàm apply_permissions
        self.setAcceptDrops(True)
        self.closed_tabs = []
        self.create_context_menu()

    def create_context_menu(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        if self.closed_tabs:
            restore_menu = menu.addMenu("Khôi phục tab")
            for tab_data in self.closed_tabs:
                action = QAction(tab_data["text"], self)
                action.triggered.connect(lambda checked, data=tab_data: self.restore_tab(data))
                restore_menu.addAction(action)
        menu.exec(self.mapToGlobal(pos))

    def restore_tab(self, tab_data):
        self.insertTab(tab_data["index"], tab_data["widget"], tab_data["icon"], tab_data["text"])
        self.setCurrentIndex(tab_data["index"])
        self.closed_tabs.remove(tab_data)

    def close_tab(self, index):
        widget = self.widget(index)
        text = self.tabText(index)
        icon = self.tabIcon(index)
        self.closed_tabs.append({"index": index, "widget": widget, "text": text, "icon": icon})
        self.removeTab(index)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-tab"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasFormat("application/x-tab"):
            source_index = int(mime_data.text())
            target_index = self.tabBar().tabAt(event.pos())
            if target_index == -1:
                target_index = self.count() - 1

            if source_index != target_index:
                widget = self.widget(source_index)
                text = self.tabText(source_index)
                icon = self.tabIcon(source_index)

                self.removeTab(source_index)
                self.insertTab(target_index, widget, icon, text)
                self.setCurrentIndex(target_index)

    

    def apply_permissions(self, user_access_info):   
        """Áp dụng quyền dựa trên user_access_info."""
        self.clear() # Xóa các tab hiện có
        allowed_apps = user_access_info.get('apps', [])
        allowed_interfaces = user_access_info.get('interfaces', [])
        self.add_main_tabs(allowed_apps, allowed_interfaces) # Gọi hàm thêm tab có kiểm tra quyền
        

    def add_main_tabs(self, allowed_apps, allowed_interfaces):
        for main_tab_name, sub_tabs_info in TABS_INFO.items():
            if main_tab_name in allowed_apps:
                main_tab = QWidget()
                main_layout = QVBoxLayout()
                main_tab.setLayout(main_layout)
                sub_tab_widget = QTabWidget()

                for tab_name, icon_path in sub_tabs_info.items():
                    # Kiểm tra quyền truy cập interface
                    # if any(iface['name'] == tab_name for iface in allowed_interfaces):
                    sub_tab = SubTab(tab_name, account_form=self.account_form, interface_permissions = allowed_interfaces)
                    sub_tab_widget.addTab(sub_tab, QIcon(icon_path), tab_name)

                if sub_tab_widget.count() > 0: # Chỉ thêm main tab nếu có ít nhất một sub tab được phép
                    main_layout.addWidget(sub_tab_widget)
                    self.addTab(main_tab, main_tab_name)
            

    def setVisible(self, visible: bool):
        super().setVisible(visible)
        for i in range(self.count()):
            self.widget(i).setVisible(visible)

    def set_style_sheet(self):
        self.setStyleSheet("""
            QTabWidget {
                background-color: #006400;
                font-family: Arial;
                font-size: 13px;
            }
            QTabBar::tab {
                background: #d9d9d9;
                padding: 10px;
                border: 1px solid #a0a0a0;
            }
            QTabBar::tab:selected {
                background: gold;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #c0c0c0;
            }
        """)

    # Cấp quyền cho MainTab
    def show_user_tab(self):
        self.setTabVisible(0, True)

    def hide_user_tab(self):
        self.setTabVisible(0, False)

    def enable_report_button(self):
        # Thêm logic cho nút report
        pass

    def disable_report_button(self):
        # Thêm logic cho nút report
        pass

if __name__ == "__main__":
    pass