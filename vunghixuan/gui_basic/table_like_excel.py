import sys
from PySide6.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QLineEdit, QComboBox

class ExcelLikeApp(QWidget):
    def __init__(self):
        super().__init__()
        # self.main_window = main_window
        # Tạo một QTableWidget với 5 hàng và 5 cột
        self.tableWidget = QTableWidget(5, 5)
        self.tableWidget.setHorizontalHeaderLabels(['A', 'B', 'C', 'D', 'E'])
        self.tableWidget.setVerticalHeaderLabels(['1', '2', '3', '4', '5'])

        # Tạo một danh sách các lựa chọn cho ComboBox
        self.options = ["Option 1", "Option 2", "Option 3"]

        # Tùy chỉnh các ô: xen kẽ QLineEdit và QComboBox
        for row in range(self.tableWidget.rowCount()):
            for col in range(self.tableWidget.columnCount()):
                if col % 2 == 0:  # Cột chẵn: QLineEdit
                    line_edit = QLineEdit()
                    self.tableWidget.setCellWidget(row, col, line_edit)
                else:  # Cột lẻ: QComboBox
                    combo_box = QComboBox()
                    combo_box.addItems(self.options)
                    self.tableWidget.setCellWidget(row, col, combo_box)

        # Tạo layout và thêm vào widget chính
        layout = QVBoxLayout()
        layout.addWidget(self.tableWidget)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExcelLikeApp()
    window.show()
    sys.exit(app.exec())