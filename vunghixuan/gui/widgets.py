from PySide6.QtWidgets import QWidget, QGridLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMenuBar, QMenu, QToolBar, QListWidget, QListWidgetItem, QTableWidget, QAbstractItemView, QTableWidgetItem, QTabWidget,  QWidgetAction, QSpacerItem, QSpacerItem, QSizePolicy, QScrollArea, QHeaderView
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QAction, QIcon, QStandardItemModel, QStandardItem, QPixmap
from PySide6.QtCore import Qt, QSize, QRegularExpression, Slot
# from config.settings import STATIC_DIR
from vunghixuan.settings import PERMISSIONS
import logging



# from functools import partial


class MyQVBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent) 
        # Các hàm cho MyQVBoxLayout

class MyQGridLayout(QGridLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_row = 0 
        self.current_col = 0 

        # self.coutinouns_row = 0 
        # self.current_col = 0 
       
        # self.grid_layout = QGridLayout()
        # self.central_widget = QWidget()
        # self.central_widget.setLayout(self.grid_layout)
        # self.setCentralWidget(self.central_widget)
        # self.endRow = 0

    def add_list_labels(self, list_labels, horizontal=None):
        
        for _, (label_text, line_edit, warning_label) in enumerate(list_labels):
            self.add_widget(label_text, self.current_row, 0, 1, 1)
            self.add_widget(line_edit, self.current_row, 1, 1, 1)
            if horizontal==True:
                self.add_widget(warning_label, self.current_row, 2, 1, 1)
                self.current_row += 1
            else:
                self.current_row += 1
                self.add_widget(warning_label, self.current_row, 1, 1, 1)
                self.current_row += 1
        
    def add_widget(self, widget, extentRow =None, extentCol =None):
        if extentRow !=None and extentCol!=None:
            self.addWidget(widget, self.current_row, self.current_col, extentRow, extentCol)
            self.current_col += extentCol
            self.current_row += extentRow
        else:
            self.addWidget(widget, self.current_row, self.current_col)
            self.current_col +=1
    
    def add_widgets_on_row(self, widgets, extentRow =None, extentCol =None):
        if extentRow !=None and extentCol!=None:
            for column, widget in enumerate(widgets):            
                self.add_widget(widget, extentRow, extentCol)
               
        else:
            for column, widget in enumerate(widgets):            
                self.add_widget(widget)
        
        # Thay đổi dòng mới
        self.current_row += 1 
        self.current_col = 0 
    
    # def add_empty_widget(self):
    #     spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
    #     self.addItem(spacer, self.current_row, self.current_col)
    #     # self.current_row += 1  # Chuyển xuống dòng tiếp theo

    # # Tìm đòng theo tên lable sau đó thêm widget vào cuối
    # def add_widget_to_last_column(self, label_text, widget):
    #     for row in range(self.current_row):
    #         item = self.itemAtPosition(row, 0)  # Giả sử label nằm ở cột 0
    #         if item and item.widget().text() == label_text:
    #             col_count = self.columnCount()  # Lấy số cột hiện tại
    #             self.add_widget(widget, row, col_count)  # Thêm widget vào cột cuối cùng
    #             break

    

    def set_column_stretch(self, row, col):
        self.setColumnStretch(row, col)
        # grid.setColumnStretch(0, 1)  # Kéo dài cột 0
        # grid.setColumnStretch(1, 2)  # Kéo dài cột 1

    def set_row_stretch(self, row, col):
        self.setRowStretch(row, col)
        # grid.setRowStretch(0, 1)  # Kéo dài dòng 0
        # grid.setRowStretch(1, 2)  # Kéo dài dòng 1

# Bố cục Menu chức năng
class MyMenuAction(QStandardItemModel): #Danh mục chức năng
    def __init__(self, options):
        super().__init__()
        self.options = options
        self.createItems()

    def createItems(self):
        # root_heading = QStandardItem("DANH MỤC CHỨC NĂNG")
        # self.appendRow(root_heading)

        for menu, actions in self.options.items():
            root_menu = QStandardItem(menu)
            root_menu.setForeground(QColor('blue'))  # Set the text color to blue
            # font = QFont("family", 15)  # Tạo một đối tượng QFont với font family là Arial và kích thước là 12
            # font.setBold(True)
            font = QFont()
            font.setPointSize(15)
            root_menu.setFont(font)  # Set the font to bold
            self.appendRow(root_menu)

            for action in actions:
                action_item = QStandardItem(action)
                action_item.setForeground(QColor('blue'))  # Set the text color here
                root_menu.appendRow(action_item)

# Đây là Action chỉ dành cho mneu
class MyQActionForMenu(QAction):
    """
    Class MyQActionForMenu kế thừa từ QAction, được sử dụng để tạo ra các hành động cho menu. Trong phương thức khởi tạo (__init__), nó nhận vào tiêu đề, đường dẫn biểu tượng và menu cha. Khi một hành động được kích hoạt, phương thức on_action_triggered sẽ in ra thông tin về hành động và menu hiện tại.
    """
    def __init__(self, title, icon_path=None, menu=None):
        super().__init__(title, menu)
        self.current_action = None
        self.current_menu = menu.current_menu
        

        if icon_path:
            self.setIcon(QIcon(icon_path))
        self.triggered.connect(self.on_action_triggered)

    def on_action_triggered(self):
        # Xác định action hiện tại
        action = self.sender()  # Lấy action đã được nhấp
        if action:
            # menu = action.parent()  # Lấy menu cha của action
            self.current_action = action
            print(f"Hành động '{self.current_action.text()}' từ menu '{self.current_menu.title()}' đã được nhấp!")

        


    
class MyActionForToolBar(QWidgetAction):
    """
    Lớp MyActionForToolBar tạo ra các nút bấm với biểu tượng và văn bản. 
    Khi nút được nhấn, phương thức on_triggered sẽ được gọi, cho phép thực hiện các hành động cụ thể
    Trong đó, parent: Chính là MyQToolBar
    """
    def __init__(self, title, icon_path=None, parent=None):
        super().__init__(parent)
        self.current_tab = parent.current_tab
        # self.tool_bar = parent
        
        # Tạo widget cho Action
        self.widget = QWidget()
        layout = QVBoxLayout()
        
        # Tạo nút với biểu tượng và văn bản
        self.button = QPushButton(title)
        if icon_path:
            self.button.setIcon(QIcon(icon_path))
            
        layout.addWidget(self.button)
        
        # Kết nối tín hiệu click
        # self.button.clicked.connect(self.on_triggered)
        
        self.widget.setLayout(layout) 
        self.setDefaultWidget(self.widget)

    def on_triggered(self):
        # Xử lý khi Action được kích hoạt
        print(f"Action {self.button.text()} được kích hoạt!")

        # Set lại current_action cho lớp cha
        # self.tool_bar.current_action = self.button.text()
        # self.tool_bar.tab.current_action = self.button.text()



class CustomLabel(QLabel):
    def __init__(self, text, font_size):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size, QFont.Bold))
        # self.setStyleSheet("color: gold; background-color: transparent;")
        self.setStyleSheet("color: #0b4f0d; ")  # Chỉnh sửa màu chữ và nền background-color: #0b4f0d
        self.setAlignment(Qt.AlignCenter)  # Căn giữa tiêu đề
        # self.setAutoFillBackground(True)
        # palette = self.palette()
        # palette.setColor(QPalette.Window, QColor(0, 0, 0, 0))  # Màu nền trong suốt
        # self.setPalette(palette)

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.Antialiasing)
    #     painter.setPen(QColor(255, 255, 255))  # Màu chữ
    #     painter.drawText(self.rect(), Qt.AlignCenter, self.text())
    #     # Thêm hiệu ứng bóng đổ
    #     painter.setPen(QColor(100, 100, 100, 150))
    #     painter.drawText(self.rect().translated(2, 2), Qt.AlignCenter, self.text())

class MyQLabel(QLabel):
    def __init__(self, parent=None, ):
        super().__init__(parent)
        
        # self.default_config()

    def default_config(self):
        # self.setFont(QFont("Arial", 10))
        self.set_color('blue')
        self.set_size_font(13)
        # self.set_alignLeft()

    def set_text(self, text):
        self.setText(text)
    
    def set_color(self, color):
        self.setStyleSheet(f"color: {color};")

    # def set_size_font(self, size):
    #     self.setFont(QFont("Arial", size))
    def set_size_font(self, size):
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)
    def acsign_icon(self, icon_path):
        self.setPixmap(QIcon(icon_path).pixmap(16, 16))

    def set_font(self, font_type=None, font_size=None, is_bold=False, is_italic=False, color=None):
        font = QFont()
        if font_type:
            font.setFamily(font_type)  # Thiết lập loại font nếu có
        
        if font_size:
            font.setPointSize(font_size)  # Thiết lập kích thước font nếu có
        
        if is_bold:
            font.setBold(True)
        if is_italic:
            font.setItalic(True)
        self.setFont(font)
        
        if color:
            self.setStyleSheet(f"color: {color};")

    # Canh lề giữa
    def set_alignCenter(self):
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    # Canh lề trái
    def set_alignLeft(self):
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
    # Canh lề phải
    def set_alignRight(self):
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
    # Canh lề top
    def set_alignTop(self):
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
    def icon(self, path):
        self.acsign_icon(path)
    def set_font_3D(self, icon_path = None):
        self.setStyleSheet("QLabel {"
                        "background-color: gray;"
                        "color: gold;"
                        "border-style: solid;"
                        "border-width: 2px;"
                        "border-color: gold;"##808080
                        "border-radius: 10px;"
                        "padding: 5px;"
                        # "font-size: 15px;"
                        # "text-align: center;"  # Thêm thuộc tính canh giữa văn bản
                        "}"
                        # "QLabel:hover {"
                        # "background-color: darkgreen;"
                        # "color: white;"
                        # "}"
                        # "QLabel:pressed {"
                        # "background-color: darkgold;"
                        # "}"
                        )    
        if icon_path:
            self.acsign_icon(icon_path)
        self.set_alignCenter()

    def set_title_dialog(self):       
        
        self.setStyleSheet("QLabel {"
                    "background-color: darkgreen;"
                    "color: white;"
                    "border-style: solid;"
                    "border-width: 2px;"
                    "border-color: gold;"
                    "border-radius: 10px;"
                    "padding: 5px;"
                    "}")
        self.set_size_font(15)
    
    def set_multi_text_color(self, texts, colors, sizes):
        html_text = "<div style='text-align: center;'>"
        for i in range(len(texts)):
            html_text += f"<span style='color:{colors[i]}; font-size:{sizes[i]}pt;'>{texts[i]}</span><br>"
        html_text += "</div>"
        self.setText(html_text)

class MyQListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_config()

    def default_config(self):
        self.set_size_font(12)
        self.setWordWrap(True)

    def set_size_font(self, size):
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)

    def add_list(self, items):
        self.clear()
        for row, item in enumerate(items):
            QListWidgetItem(item, self)

    def currentText(self):
        return self.currentItem().text()

    def setText(self, text):
        self.setText(text)

    def setColorBackGround(self, color):
        self.setStyleSheet(f"background-color: {color};")

    # def setVisible(self, isHide):
    #     self.setVisible(isHide)

    def height(self):
        return self.height()

class MyQPushButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.create_3D()

    def set_style_3D(self):
        self.setStyleSheet("QPushButton {"
                        "background-color: gold;"
                        "color: black;"

                        "border-style: solid;"
                        
                        "border-width: 2px;"
                        "border-color: #808080;"
                        "border-radius: 10px;"
                        "padding: 5px;"
                        "font-size: 16px;"
                        "}"
                        "QPushButton:hover {"
                        "background-color: darkgreen;"
                        "color: white;"
                        "}"
                        "QPushButton:pressed {"
                        "background-color: darkgold;"
                        "}"
                        )
    # def event(self, event):
    #     if event.type() == QEvent.Type.Enter:
    #         self.setStyleSheet("background-color: gold;")
    #     elif event.type() == QEvent.Type.Leave:
    #         self.create_3D()
    #     return super().event(event)
    def set_icon(self, path_icon):
        icon = QIcon(path_icon)
        self.setIcon(icon)
    
    def set_icon_size(self, width, height):
        self.setIconSize(QSize(width, height))  # Thay đổi kích thước biểu tượng

    def set_size_font(self, size):
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)

    def get_text(self):
        return self.text()

    def set_text(self, text):
        self.setText(text)

    def setColorBackGround(self, color):
        self.setStyleSheet(f"background-color: {color};")

    # def setVisible(self, isHide):
    #     self.setVisible(isHide)

    def set_size(self, width, height):
        self.setFixedSize(width, height)
        
    def height(self):
        return self.height()

# Show hide pass
class ShowHidePassWord():
    def __init__(self) -> None:
        pass

    




class MyQComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.default_configuration()

    def set_edit_value(self):
        self.setEditable(True)
        
    def default_configuration(self):
        self.set_size_font(10)
        self.set_fixed_size(200,27)
    
    def set_size_font(self, size):
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)
    
    def set_fixed_size(self, width, height):
        self.setFixedSize(width, height)
    
    def get_list_values(self):
        items = []
        for index in range(self.count()):
            items.append(self.itemText(index))
        return items
    
    def add_item(self, list_values):
        for val in list_values:
            self.addItem(val)
    
    def setColorBackGround(self, color):
        self.setStyleSheet(f"background-color: {color};")

    def setFontColor(self, color):
        self.setStyleSheet(f"QComboBox {{ color: {color}; }}")

    def lock(self):
        self.setEnabled(False)

    def unlock(self):
        self.setEnabled(True)
    def clear_items(self):
        self.clear()
    
class MyQLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.locked = False
        # self.default_configuration()
        self.mouseDoubleClickEvent = self.handle_double_click

    def handle_double_click(self, event):
        self.selectAll()

    def default_configuration(self):
        self.set_size_font(12)
        self.set_fixed_size(200,27)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
    
    def set_fixed_size(self, width, height):
        self.setFixedSize(width, height)
    
    def set_size_font(self, size):
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)

    def setReadOnly(self):
        self.setReadOnly(True)

    def lock(self):
        self.setEnabled(False)
        self.locked = True

    def unlock(self):
        self.setEnabled(True)
        self.locked = False

    def set_pass_word(self):
        self.setEchoMode(self.EchoMode.Password)

    def set_placeholder(self, placeholder):
        self.setPlaceholderText(placeholder)
       
class MyQTableWidget(QTableWidget):
    def __init__(self, user_controller, parent=None):
        super().__init__(parent)
        self.user_controller = user_controller
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.external_actions = []

    def showContextMenu(self, pos):
        contextMenu = QMenu(self)
        actions = [
            QAction("Xóa dòng", self),
            QAction("Thêm dòng", self)
        ]
        actions[0].triggered.connect(self.deleteRow)
        actions[1].triggered.connect(self.insertRow)
        contextMenu.addActions(actions + self.external_actions)
        contextMenu.exec(self.mapToGlobal(pos))

    def updateContextMenuActions(self, actions):
        self.external_actions = actions

    def deleteRow(self):
        selectedRanges = self.selectedRanges()
        rows_to_delete = []
        for selectedRange in selectedRanges:
            rows_to_delete.extend(range(selectedRange.bottomRow(), selectedRange.topRow() - 1, -1))
        for row in sorted(set(rows_to_delete), reverse=True):
            self.removeRow(row)

    def setEditTable(self, locked=None):
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers if locked else
                             QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked)

    def setEditColumnTable(self, id_column):
        for column in range(self.columnCount()):
            flags = Qt.ItemIsEditable if column == id_column else Qt.ItemIsEnabled | Qt.ItemIsSelectable
            self.horizontalHeaderItem(column).setFlags(flags)

    def insertRow(self):
        self.insertRow(self.currentRow())

    def load_user_roll_per_on_account_table(self, data):
        self.upload_contents(data)
        self.upload_headings(["Tên người dùng", "Quyền", "Phân quyền", "Chi tiết"])
        self.auto_resize_columns()

    def upload_headings(self, list_colname):
        self.setHorizontalHeaderLabels(list_colname)

    def upload_contents(self, data):
        self.setRowCount(len(data))
        self.setColumnCount(len(data[0]))
        for row, rowData in enumerate(data):
            self.setRowHidden(row, False)
            for col, value in enumerate(rowData):
                item = QTableWidgetItem(str(value))
                self.setItem(row, col, item)
                self.setColorItem(row, item)

    def setColorItem(self, row, item):
        if row % 2 == 0:
            item.setBackground(QColor(253, 252, 219))

    def addRow_on_table(self, ir, rowData):
        for col, value in enumerate(rowData):
            item = QTableWidgetItem(str(value))
            self.setItem(ir, col, item)

    def default_config(self):
        self.set_size_font(13)
        self.setHeaderFont(15)

    def setHeaderFont(self, size):
        header = self.horizontalHeader()
        font = header.font()
        font.setPointSize(size)
        header.setFont(font)
        header.setStyleSheet("QHeaderView::section { background-color: darkgreen; color: white; border: 1px solid gray;}")

    def auto_resize_columns(self):
        self.resizeColumnsToContents()

    def set_size_font(self, size):
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)

    def read_data(self):
        values = []
        for row in range(self.rowCount()):
            rowData = [self.item(row, col).text() if self.item(row, col) else "" for col in range(self.columnCount())]
            values.append(rowData)
        return values
    def unhideAllRows(self):
        row_count = self.rowCount()
        for row in range(row_count):
            self.setRowHidden(row, False)




    
# Gui check infor input user
class InputCheckGui:
    """
    Class InputCheckGui là một công cụ hữu ích trong việc quản lý và kiểm tra đầu vào của người dùng trong ứng dụng GUI. Nó cho phép người dùng nhập dữ liệu và tự động kiểm tra tính hợp lệ của dữ liệu đó dựa trên các điều kiện đã được định nghĩa.

    Khi khởi tạo, bạn có thể chỉ định các tham số như isUpperString, isLowerString, isCapitalString để xác định cách thức biến đổi chuỗi. Class này cũng hỗ trợ kiểm tra xem đầu vào có phải là số nguyên hay số thực thông qua các phương thức is_interger và is_float.

    Khi người dùng nhập dữ liệu, phương thức check_input sẽ được gọi để kiểm tra và xử lý đầu vào. Nếu đầu vào không hợp lệ, thông báo cảnh báo sẽ được hiển thị qua label_warning.
    Class InputCheckGui bao gồm nhiều phương thức để xử lý và kiểm tra đầu vào của người dùng. Dưới đây là mô tả chi tiết về các hàm chính:

    *** Cụ thể như sau:
    __init__: Khởi tạo class với các tham số như tiêu đề, kiểu dữ liệu cần kiểm tra (chuỗi, số nguyên, số thực) và danh sách tên. Nó cũng tạo các label và line edit cần thiết cho giao diện.

    check_input: Kiểm tra đầu vào khi người dùng thay đổi nội dung trong line edit. Nếu đầu vào không rỗng, nó sẽ gọi hàm check_string_input_and_return_string_match.

    check_string_input_and_return_string_match: Kiểm tra đầu vào dựa trên các điều kiện đã được thiết lập (chuỗi, số nguyên, số thực) và trả về giá trị phù hợp hoặc thông báo lỗi.

    covert_string_match: Chuyển đổi chuỗi đầu vào theo các quy tắc đã định và kiểm tra xem tên đã tồn tại trong danh sách hay chưa.

    show_label_warning: Hiển thị thông báo cảnh báo trên giao diện người dùng.

    covert_strings: Chuyển đổi chuỗi thành chữ hoa, chữ thường hoặc chữ cái đầu tiên viết hoa dựa trên các tham số đã được thiết lập.

    is_string, is_interger, is_float: Các hàm kiểm tra kiểu dữ liệu đầu vào, xác định xem nó có phải là chuỗi, số nguyên hay số thực hay không.

    create_label_title, create_line_edit, create_warning_label: Các hàm tạo các thành phần giao diện người dùng như label và line edit với các thuộc tính cụ thể.

    Class này rất hữu ích trong việc xây dựng các ứng dụng GUI cần kiểm tra và xác thực dữ liệu đầu vào từ người dùng một cách hiệu quả.


    """
    def __init__(self, title, isUpperString=None, isLowerString=None, isCapitalString=None, acceptOldName = None, list_name=None,  isInt=None,  isFloat=None):
        self.title = title
        # self.isString = isString
        self.isUpperString = isUpperString
        self.isLowerString = isLowerString
        self.isCapitalString = isCapitalString
        self.acceptOldName = acceptOldName
        self.list_name = list_name

        self.isInt = isInt
        self.isFloat = isFloat
        self.label_title = self.create_label_title(title)
        self.line_edit_input = self.create_line_edit()
        self.label_warning = self.create_warning_label()
        self.text_result = ''
        # Kết nối sự kiện kiểm tra thông tin người nhập
        self.line_edit_input.textChanged.connect(self.check_input)

    def check_input(self):
        # print('======================')
        
        text = self.line_edit_input.text().strip()
        if text !='':
            self.text_result = self.check_string_input_and_return_string_match(text)
            
        else:
            self.label_warning.setText('')

    # Kiểm tra chuỗi từ người nhập và biến đổi chuỗi mới phù hợp
    def check_string_input_and_return_string_match(self, text):
        if self.isLowerString or self.isUpperString or self.isCapitalString:  # Kiểm tra chuỗi
            # if self.is_string(text):
            text = self.covert_string_match(text)
            if text != '':
                return text
            else:
                return ''

        elif self.isInt:  # Kiểm tra số nguyên
            if self.is_interger(text):
                # self.show_label_warning('Nhập đúng')
                self.show_label_warning('')
                return text
            else:
                self.show_label_warning('Nhập sai (Nhập vào số nguyên)')
                return ''
        elif self.isFloat:  # Kiểm tra số thực
            if self.is_float(text):
                # self.show_label_warning('Nhập đúng')
                self.show_label_warning('')
                return text
            else:
                self.show_label_warning('Nhập sai (Nhập vào số thực)')
                return ''

    # Biến đổi chuỗi thành chuỗi phù hợp
    def covert_string_match(self, text):
        text = self.covert_strings(text)
        if self.acceptOldName != None:
            self.list_name.remove(self.acceptOldName)

        if text in self.list_name:
            self.show_label_warning('Tên đã tồn tại')
            return ''
        else:
            self.label_warning.setText('')
            # self.label_warning.setText('Tên phù hợp')
            return text

    # Hiển thị thông báo cho label_warning
    def show_label_warning(self, text_warning):
        if text_warning !='':
            self.label_warning.setText(text_warning)
        else:
            self.label_warning.setText('')

    def covert_strings(self, text):
        if self.isUpperString:
            text = text.upper()
        if self.isLowerString:
            text = text.lower()
        if self.isCapitalString:
            text = text.capitalize()
        return text

    def is_string(self, value):
        try:
            if int(value) or float(value):
                return False
        except ValueError:
            return True

    def is_interger(self, num):  # Kiểm tra price phải là số nguyên không
        try:
            num = int(num)
            # return True
        except:
            return False
        if isinstance(num, int):
            return True
        
    def is_float(self, num):
        try:
            if '%' in num:
                num = num.replace('%','')
            num = float(num)
        except:
            return False
        if isinstance(num, float):#or '%' in num
            return True
        return False
    
    # def is_float(self, num):
    #     try:
    #         num = float(num)
    #     except:
    #         return False
    #     if isinstance(num, float):#and not num.is_integer()
    #         return True
    #     return False

    def create_label_title(self, text):
        label = MyQLabel(text)
        label.set_size_font(13)
        return label

    def create_line_edit(self):
        line_edit = MyQLineEdit()
        line_edit.set_size_font(13)
        line_edit.setStyleSheet("color: black;")#background-color: yellow; 
        return line_edit

    def create_warning_label(self):
        warning_label = MyQLabel()
        warning_label.set_color('red')
        warning_label.set_size_font(8)
        return warning_label
