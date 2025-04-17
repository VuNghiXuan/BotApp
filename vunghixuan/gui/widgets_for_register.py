from PySide6.QtWidgets import (
    QWidget, QGridLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMenuBar, QMenu, QToolBar, QListWidget, QListWidgetItem,
    QTableWidget, QAbstractItemView, QTableWidgetItem, QTabWidget, QWidgetAction,
    QSpacerItem, QSizePolicy, QScrollArea, QHeaderView, QMessageBox
)
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QAction, QIcon, QStandardItemModel, QStandardItem, QPixmap
from PySide6.QtCore import Qt, QSize, QRegularExpression, Slot, Signal
import logging

# from vunghixuan.settings import PERMISSIONS  # Assuming this is not used
# from vunghixuan.gui.widgets import MyQLineEdit # Assuming this is correctly implemented and available
# from vunghixuan.account.register.user_controllers import (
#     DatabaseManager, UserManager, RollManager, PermissionManager, AppManager, DefaultSetup
# ) #Commented out since they are not available
from vunghixuan.settings import DATABASE_URL # Assuming this is available
from vunghixuan.account.register.user_manager import UserManager
from vunghixuan.account.register.db_manager import DatabaseManager



class MyQLineEditSearch(QLineEdit):  # Changed base class
    """
    A custom QLineEdit for search functionality.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_configuration()

    def default_configuration(self):
        """Sets the default configuration for the search line edit."""
        self.setFixedSize(800, 30)
        self.setStyleSheet(
            "QLineEdit {border: 1px solid gray; border-radius: 10px; padding: 4px; background-color: white;} "
            "QLineEdit:focus {border: 2px solid blue;}"
        )
        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def set_read_only(self):  # Corrected method name to follow PEP 8
        """Sets the line edit to read-only."""
        self.setReadOnly(True)

    def lock(self):
        """Disables the line edit."""
        self.setEnabled(False)

    def unlock(self):
        """Enables the line edit."""
        self.setEnabled(True)



class MyQTableWidget(QTableWidget):
    """
    A custom QTableWidget that automatically populates from a list of dictionaries.
    """

    user_deleted = Signal()
    username_signal = Signal(str)    

    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_menu = None
        self.delete_user_action = QAction("Xóa người dùng", self) # Khởi tạo ở đây
        self.delete_user_action.triggered.connect(self.get_username_from_signal)

        self.setContextMenuPolicy(Qt.CustomContextMenu)  # Enable context menu
        self.customContextMenuRequested.connect(
            self.showContextMenu
        )  # Connect to handler
        self.selected_row = -1
        
        
    def load_data(self, data: list[dict]):
        """
        Loads data into the table widget from a list of dictionaries.

        Args:
            data: A list of dictionaries, where each dictionary represents a row.
                The keys of the dictionaries are used as column headers.  If the dictionaries have
                different sets of keys, the union of the keys will be used.  Missing values will
                be displayed as empty strings.
        """
        if not data:
            self.clear()
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        # Get all unique keys to use as headers, without using set
        all_keys = []
        for row in data:
            for key in row.keys():
                if key not in all_keys:
                    all_keys.append(key)
        header_labels = all_keys

        self.clear()
        self.setColumnCount(len(header_labels))
        self.setHorizontalHeaderLabels(header_labels)
        self.setRowCount(len(data))

        for row_index, row_data in enumerate(data):
            for col_index, key in enumerate(header_labels):
                value = row_data.get(key, "")  # Use "" for missing values
                item = QTableWidgetItem(str(value))
                self.setItem(row_index, col_index, item)
            # Alternate row colors for better readability
            if row_index % 2 == 0:
                for col_index in range(self.columnCount()):
                    item = self.item(row_index, col_index)
                    if item:
                        item.setBackground(
                            QColor(240, 240, 240)
                        )  # Light gray
            else:
                for col_index in range(self.columnCount()):
                    item = self.item(row_index, col_index)
                    if item:
                        item.setBackground(QColor(255, 255, 255))  # White

        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resizeRowsToContents() # Tự động điều chỉnh chiều cao hàng theo nội dung
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def unhide_all_rows(self):  # Corrected method name to follow PEP 8
        """Displays all rows in the table."""
        for row in range(self.rowCount()):
            self.setRowHidden(row, False)

    def showContextMenu(self, position):
        """Displays the context menu when the user right-clicks."""
        if self.context_menu is None:
            self.context_menu = QMenu(self)
            self.delete_user_action = QAction("Xóa người dùng", self)
            
            self.delete_user_action.triggered.connect(self.get_username_from_signal)
            self.context_menu.addAction(self.delete_user_action)

        # Get the item at the clicked position.  If no item, don't show menu.
        item = self.itemAt(position)
        if item is None:
            return

        # Get the row of the selected item.
        row = self.row(item)
        if row >= 0:
            self.selected_row = row
            # Việc vô hiệu hóa/kích hoạt action nên được thực hiện từ bên ngoài (SubTab)
            self.context_menu.exec_(self.mapToGlobal(position))

    def set_delete_action_enabled(self, enabled):
        """Sets the enabled state of the delete user action."""
        if hasattr(self, 'delete_user_action') and self.delete_user_action is not None:
            self.delete_user_action.setEnabled(enabled)

    def get_username_from_signal(self):
        if hasattr(self, 'selected_row') and self.selected_row >= 0:
            username_item = self.item(
                self.selected_row, 0
            )  # Username is assumed to be in the first column
            if username_item:
                username = username_item.text()
                self.username_signal.emit(username) # Phát signal khi action được tạo
        
    def set_column_width(self, column_index: int, width: int):
        """
        Sets the width of a specific column.

        Args:
            column_index: The index of the column to set the width for (0-based).
            width: The desired width of the column in pixels.
        """
        if 0 <= column_index < self.columnCount():
            self.setColumnWidth(column_index, width)
        else:
            print(f"Error: Invalid column index {column_index}")
    
    def set_column_widths(self, width_list):
        """
        Distributes the column widths based on the specified requirements.

        Args:
            total_width: The total width available for the table widget.
        """
        column_count = self.columnCount()
        if column_count < 2:
            # Not enough columns to apply the specific width rules
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            return
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        count = 0
        for wth in width_list:
            self.set_column_width(count, wth)
            count +=1


class SearchTable(QWidget):
    """
    A widget that combines a search bar and a table widget for displaying data.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        self.group_box = QGroupBox("Danh mục tài khoản")
        group_layout = QVBoxLayout()
        self.group_box.setLayout(group_layout)

        search_layout = QHBoxLayout()
        search_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        search_label = QLabel("Tìm kiếm")
        search_label.setStyleSheet("color: blue; font-size: 15px; font-weight: bold;")
        search_layout.addWidget(search_label)
        self.search_line = MyQLineEditSearch()
        self.search_line.setPlaceholderText("Nhập từ khóa tìm kiếm...")
        self.search_line.textChanged.connect(self.search_data)
        search_layout.addWidget(self.search_line)
        search_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        search_layout.setAlignment(Qt.AlignCenter)
        group_layout.addLayout(search_layout)

        self.table_widget = MyQTableWidget()
        self.table_widget.setFont(QFont("Arial", 13))
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table_widget)
        group_layout.addWidget(scroll_area)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group_box)

    @Slot(str)
    def search_data(self, search_text):
        """
        Filters the table data based on the search text.

        Args:
            search_text: The text to search for.
        """
        self.table_widget.unhide_all_rows()
        if search_text:
            search_text = search_text.lower()
            for row in range(self.table_widget.rowCount()):
                found = False
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        text = item.text().lower()
                        if search_text in text:
                            found = True
                            break
                if not found:
                    self.table_widget.setRowHidden(row, True)

    def load_table_data(self, data: list[dict]):
        """Loads data into the table widget."""
        self.table_widget.load_data(data)

    def set_font(self, font):
        """Sets the font for the table."""
        self.table_widget.setFont(font)

    def set_header_font(self, font):
        """Sets the font for the table header."""
        self.table_widget.horizontalHeader().setFont(font)

    def set_column_width(self, column, width):
        """Sets the width of a column."""
        self.table_widget.setColumnWidth(column, width)

    def set_row_height(self, row, height):
        """Sets the height of a row."""
        self.table_widget.setRowHeight(row, height)

    def get_username_from_signal(self):
        self.table_widget.get_username_from_signal()

    def set_group_box_title(self, title):
        """Sets the title of the group box."""
        self.group_box.setTitle(title)
    
    def set_column_width(self, column_index: int, width: int):
        self.table_widget.set_column_width(column_index, width)

