Sửa lại logic 2 file dưới:

# account_form.py
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
)
from vunghixuan.bot_station.table_data import TableData
from vunghixuan.bot_station.file_list_form import FileListForm
from PySide6.QtCore import Slot
import pandas as pd
import os
from vunghixuan.bot_station.load_gif_file import LoadingGifLabel

class CheckTicketsForm(QWidget):
    """
    Đây là Form chứa và sắp xếp toàn bộ giao diện: FileListForm (phải), PermissionManager (trái), UserPermissionsTable (dưới)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = 'Đối soát vé'
        self.file_data = {}
        self.loading_gif = LoadingGifLabel(self)
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        self.data_table = TableData(self)
        self.file_list_form = FileListForm(self)
        self.file_list_form.data_loaded.connect(self.handle_all_data_loaded)
        self.file_list_form.file_selected.connect(self.load_data_to_table)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.setSpacing(0)
        horizontal_layout.addWidget(self.file_list_form, 1)
        horizontal_layout.addWidget(self.data_table, 4)
        self.main_layout.addLayout(horizontal_layout)
        self.main_layout.addWidget(self.loading_gif) # Thêm loading gif vào layout chính
        self.loading_gif.hide() # Ẩn ban đầu
        self.setLayout(self.main_layout)

    @Slot(dict)
    def handle_all_data_loaded(self, all_data):
        self.file_data = all_data
        # Bạn có thể thực hiện xử lý dữ liệu ban đầu ở đây nếu cần
        pass

    @Slot(pd.DataFrame)
    def load_data_to_table(self, df):
        """
        Slot này nhận DataFrame và tải dữ liệu vào TableData.
        """
        self.loading_gif.show_gif()  # Hiển thị GIF trước khi tải dữ liệu

        if not df.empty:
            # Kiểm tra và xử lý các cột trùng lặp (nếu có)
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique():
                cols[df.columns == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(df.columns == dup))]
            df.columns = cols

            # Chuyển DataFrame thành list of dict để phù hợp với TableData
            data_for_table = df.to_dict('records')
            self.data_table.load_data(data_for_table)
            self.loading_gif.hide_gif()  # Ẩn GIF sau khi tải dữ liệu xong
        else:
            self.data_table.clear()
            self.loading_gif.hide_gif()  # Ẩn GIF nếu không có dữ liệu

    @Slot(str)
    def old_load_data_to_table(self, file_path):
        """
        Slot này nhận đường dẫn file và tải dữ liệu vào TableData (phiên bản cũ).
        """
        if file_path:
            self.loading_gif.show_gif()
            try:
                df = pd.read_excel(file_path, header=None)
                start_row_index = -1
                for index, row in df.iterrows():
                    for cell in row:
                        if isinstance(cell, str) and cell.lower() == 'stt':
                            start_row_index = index
                            break
                    if start_row_index != -1:
                        break

                if start_row_index != -1:
                    header = [str(h).strip() for h in df.iloc[start_row_index].tolist()]
                    data_rows = df.iloc[start_row_index + 1:].values.tolist()
                    processed_data = []
                    for row in data_rows:
                        row_dict = {}
                        for i, value in enumerate(row):
                            if i < len(header):
                                row_dict[header[i]] = value
                        processed_data.append(row_dict)
                    self.data_table.load_data(processed_data)
                else:
                    QMessageBox.warning(self, "Cảnh báo", f"Không tìm thấy cột 'STT' trong file: {os.path.basename(file_path)}")

            except FileNotFoundError:
                QMessageBox.critical(self, "Lỗi", f"Không tìm thấy file: {os.path.basename(file_path)}")
            except ImportError:
                QMessageBox.critical(self, "Lỗi", "Thư viện 'openpyxl' chưa được cài đặt.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi đọc file Excel {os.path.basename(file_path)}: {e}")
            finally:
                self.loading_gif.hide_gif()
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QListWidget, QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QDir, Slot, Signal
from PySide6.QtGui import QMovie
from vunghixuan.gui.widgets import MyQLabel, MyQLineEdit, MyQPushButton, MyQTableWidget

import csv
import os
import pandas as pd
from vunghixuan.settings import STATIC_DIR

# ... import các class khác ...
from vunghixuan.bot_station.thread_files import DataProcessorWorker, DataReaderWorker #mport worker thread
from vunghixuan.bot_station.load_gif_file import LoadingGifLabel  # Import worker thread




# ... import DataReaderWorker ...

class FileListForm(QWidget):
    data_loaded = Signal(dict) # Signal phát ra khi cả hai file FE và BE đã được đọc
    file_selected = Signal(pd.DataFrame) # Signal phát ra khi một file được chọn từ list

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_path = None
        self.file_paths = {"FE": None, "BE": None}
        self.file_data = {} # Lưu trữ dữ liệu của cả hai file sau khi đọc
        self.workers = []
        self.loading_gif = LoadingGifLabel(self)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # Chọn thư mục
        folder_layout = QHBoxLayout()
        self.folder_label = MyQLabel("Chọn thư mục:")
        self.folder_line_edit = MyQLineEdit()
        self.browse_folder_button = MyQPushButton("Duyệt...")
        self.browse_folder_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_line_edit)
        folder_layout.addWidget(self.browse_folder_button)
        main_layout.addLayout(folder_layout)

        # Danh sách file
        self.file_list_widget = QListWidget()
        self.file_list_widget.itemClicked.connect(self.handle_file_clicked)
        main_layout.addWidget(self.file_list_widget)

        # Nút xóa file
        self.delete_button = MyQPushButton("Xóa File")
        self.delete_button.clicked.connect(self.delete_selected_file)
        main_layout.addWidget(self.delete_button)

        # Label hiển thị GIF tải (đã là một widget riêng)
        main_layout.addWidget(self.loading_gif)

        self.setLayout(main_layout)

    @Slot()
    def browse_folder(self):
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(self, "Chọn thư mục chứa files Excel")
        if folder_path:
            self.folder_line_edit.setText(folder_path)
            self.folder_path = folder_path
            self.load_all_data_from_folder(folder_path)

    def load_all_data_from_folder(self, folder_path):
        self.file_list_widget.clear() # Clear list widget ở đây
        self.file_paths = {"FE": None, "BE": None}
        self.file_data = {}
        dir = QDir(folder_path)
        dir.setFilter(QDir.Files | QDir.NoDotAndDotDot)
        dir.setSorting(QDir.Name)
        entry_list = dir.entryList(["*.xlsx", "*.xls"])

        fe_path = None
        be_path = None
        for entry in entry_list:
            file_path = os.path.join(folder_path, entry)
            print(f"Tìm thấy file: {entry}, đường dẫn: {file_path}")
            if "FE" in entry and fe_path is None:
                fe_path = file_path
                self.file_paths["FE"] = file_path
            elif "BE" in entry and be_path is None:
                be_path = file_path
                self.file_paths["BE"] = file_path

        print(f"Đường dẫn file FE: {fe_path}")
        print(f"Đường dẫn file BE: {be_path}")

        files_to_load = []
        if fe_path:
            files_to_load.append(("FE", fe_path))
        if be_path:
            files_to_load.append(("BE", be_path))

        if files_to_load:
            self.loading_gif.show_gif()
            self.workers = []
            for name, path in files_to_load:
                worker = DataReaderWorker(path)
                worker.data_ready.connect(self.handle_data_ready_all)
                worker.error_occurred.connect(self.handle_read_error)
                self.workers.append(worker)
                worker.start()
        else:
            QMessageBox.warning(self, "Cảnh báo", "Không tìm thấy file FE hoặc BE trong thư mục.")


    @Slot(str, pd.DataFrame)
    def handle_data_ready_all(self, file_name, data):
        print(f"handle_data_ready_all được gọi với file: {file_name}")
        self.file_data[file_name] = data
        print(f"Dữ liệu đã đọc: {list(self.file_data.keys())}")
        loaded_files = list(self.file_data.keys())
        # Không clear file_list_widget ở đây nữa

        if "FE" in self.file_paths["FE"]:
            print(f"Thêm FE vào list: {os.path.basename(self.file_paths['FE'])}")
            # Kiểm tra xem item đã tồn tại chưa trước khi thêm (nếu cần)
            found = False
            for i in range(self.file_list_widget.count()):
                if self.file_list_widget.item(i).text().startswith("FE:"):
                    found = True
                    break
            if not found:
                self.file_list_widget.addItem(f"FE: {os.path.basename(self.file_paths['FE'])}")

        if "BE" in self.file_paths["BE"]:
            print(f"Thêm BE vào list: {os.path.basename(self.file_paths['BE'])}")
            # Kiểm tra xem item đã tồn tại chưa trước khi thêm (nếu cần)
            found = False
            for i in range(self.file_list_widget.count()):
                if self.file_list_widget.item(i).text().startswith("BE:"):
                    found = True
                    break
            if not found:
                self.file_list_widget.addItem(f"BE: {os.path.basename(self.file_paths['BE'])}")
        
        self.loading_gif.hide_gif()

        # if len(loaded_files) == 2 or (len(loaded_files) == 1 and (self.file_paths["FE"] is None or self.file_paths["BE"] is None)):
        #     self.loading_gif.hide_gif()
        #     # self.data_loaded.emit(self.file_data) # Phát tín hiệu khi cả hai (hoặc có thể một) file đã đọc xong
        #     self.loading_gif.hide_gif()

    @Slot(object)
    def handle_file_clicked(self, item):
        file_name_prefix = item.text().split(":")[1].strip()
        if file_name_prefix in self.file_data:
            self.loading_gif.show_gif()
            # Phát tín hiệu file_selected trực tiếp với dữ liệu đã có
            self.file_selected.emit(self.file_data[file_name_prefix])
            # self.loading_gif.hide_gif() # Loại bỏ dòng này, GIF sẽ ẩn khi dữ liệu được tải xong ở nơi nhận tín hiệu
        else:
            QMessageBox.warning(self, "Cảnh báo", f"Không tìm thấy dữ liệu cho file: {file_name_prefix}")

    # @Slot(object)
    # def handle_file_clicked(self, item):
    #     file_name_prefix = item.text().split(":")[1].strip()
    #     if file_name_prefix in self.file_data.keys():
    #         self.loading_gif.show_gif()
    #         # Dừng worker cũ nếu đang chạy
    #         for worker in self.workers[:]:
    #             if isinstance(worker, DataProcessorWorker) and worker.isRunning():
    #                 worker.quit()
    #                 worker.wait()
    #                 self.workers.remove(worker)
    #                 # worker.finished.connect(self.loading_gif.hide_gif)
                    

    #         # Tạo worker mới
    #         worker = DataProcessorWorker(self.file_data[file_name_prefix])
    #         worker.processed_data_ready.connect(self.emit_selected_data)
    #         worker.finished.connect(self.loading_gif.hide_gif)
    #         self.workers.append(worker)
    #         worker.start()

    
    # @Slot(pd.DataFrame)
    # def emit_selected_data(self, data):
    #     self.file_selected.emit(data)

    @Slot()
    def delete_selected_file(self):
        selected_item = self.file_list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            if text.startswith("FE:"):
                self.file_paths["FE"] = None
                if "FE" in self.file_data:
                    del self.file_data["FE"]
            elif text.startswith("BE:"):
                self.file_paths["BE"] = None
                if "BE" in self.file_data:
                    del self.file_data["BE"]
            self.file_list_widget.takeItem(self.file_list_widget.row(selected_item))

    @Slot(str)
    def handle_read_error(self, error_msg):
        QMessageBox.critical(self, "Lỗi đọc file", error_msg)
        self.loading_gif.hide_gif()

    def closeEvent(self, event):
        for worker in self.workers:
            worker.quit()
            worker.wait()
        event.accept()