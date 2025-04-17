# show_data_form.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTableWidget, QHeaderView
)
from PySide6.QtCore import Qt, Slot

from vunghixuan.gui.widgets_for_register import SearchTable

class TableData(QWidget):
    """
    A widget that displays data in a table with a search bar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.searchable_table = SearchTable()
        self.main_layout.addWidget(self.searchable_table)
        self.searchable_table.set_group_box_title('Hiển thị dữ liệu')
        self.setWindowTitle("Hiển thị dữ liệu") # Set window title (can be removed if embedded)

    @Slot(list)
    def receive_data(self, data):
        """
        Slot này nhận tín hiệu chứa dữ liệu và gọi hàm load_data.
        """
        print('Đẫ nhận tín hiệu')
        self.load_data(data)

    def load_data(self, data):
        """Loads data into the table.

        Args:
            data (list of lists): The data to display in the table.
                The first list should be the header row.
        """
        self.searchable_table.load_table_data(data)

    def set_column_widths(self, widths):
        """Sets the widths of the columns in the table.

        Args:
            widths (list of int): A list of integers representing the width
                for each column.
        """
        self.searchable_table.table_widget.set_column_widths(widths)

    def upload_contents(self, contents):
        """Uploads the main content data to the table.

        Args:
            contents (list of lists): The data rows to be displayed.
        """
        self.searchable_table.table_widget.upload_contents(contents)

    def upload_headings(self, headings):
        """Uploads the header row for the table.

        Args:
            headings (list of str): A list of strings representing the
                column headers.
        """
        self.searchable_table.table_widget.upload_headings(headings)

    def auto_resize_columns(self):
        """Automatically resizes the columns to fit their content."""
        self.searchable_table.table_widget.auto_resize_columns()

    def get_table_widget(self):
        """Returns the underlying QTableWidget instance."""
        return self.searchable_table.table_widget

if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = TableData()  # Use the correct class name
    # Example data
    data = [
        ["ID", "Name", "Description"],
        ["1", "Item A", "This is item A"],
        ["2", "Item B", "Another item"],
        ["3", "Item C", "A third item"]
    ]
    window.load_data(data)
    window.set_column_widths([50, 150, 200])
    window.show()
    sys.exit(app.exec())