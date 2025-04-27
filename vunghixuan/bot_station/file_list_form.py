

# antagonize, BaoCaoTongHopDoanhThu đưa vào DataReaderWorker
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



class FileListForm(QWidget):
    data_loaded = Signal(dict) # Signal phát ra khi các file cần thiết đã được đọc
    file_selected = Signal(pd.DataFrame) # Signal phát ra khi một file được chọn từ list

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_path = None
        self.file_paths = {"FE": None, "BE": None, "antagonize": None, "BaoCaoTongHopDoanhThu": None}
        self.file_data = {} # Lưu trữ dữ liệu của các file sau khi đọc
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
        self.delete_button.set_style_3D()
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
        self.file_paths = {"FE": None, "BE": None, "antagonize": None, "BaoCaoTongHopDoanhThu": None}
        self.file_data = {}
        dir = QDir(folder_path)
        dir.setFilter(QDir.Files | QDir.NoDotAndDotDot)
        dir.setSorting(QDir.Name)
        entry_list = dir.entryList(["*.xlsx", "*.xls"])

        files_to_load = []
        for entry in entry_list:
            file_path = os.path.join(folder_path, entry)
            print(f"Tìm thấy file: {entry}, đường dẫn: {file_path}")
            if "FE" in entry and self.file_paths["FE"] is None:
                self.file_paths["FE"] = file_path
                files_to_load.append(("FE", file_path))
            elif "BE" in entry and self.file_paths["BE"] is None:
                self.file_paths["BE"] = file_path
                files_to_load.append(("BE", file_path))
            elif "antagonize" in entry and self.file_paths["antagonize"] is None:
                self.file_paths["antagonize"] = file_path
                files_to_load.append(("antagonize", file_path))
            elif "BaoCaoTongHopDoanhThu" in entry and self.file_paths["BaoCaoTongHopDoanhThu"] is None:
                self.file_paths["BaoCaoTongHopDoanhThu"] = file_path
                files_to_load.append(("BaoCaoTongHopDoanhThu", file_path))

        print(f"Đường dẫn file FE: {self.file_paths['FE']}")
        print(f"Đường dẫn file BE: {self.file_paths['BE']}")
        print(f"Đường dẫn file antagonize: {self.file_paths['antagonize']}")
        print(f"Đường dẫn file BaoCaoTongHopDoanhThu: {self.file_paths['BaoCaoTongHopDoanhThu']}")

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
        # Sử dụng tên file gốc (ví dụ: "FE_...", "antagonize_...") làm key
        base_name = os.path.basename(file_name)
        self.file_data[base_name] = data
        print(f"Dữ liệu đã đọc: {list(self.file_data.keys())}")
        loaded_files = list(self.file_data.keys())

        for key, path in self.file_paths.items():
            if path and os.path.basename(path) in self.file_data:
                found = False
                display_name = key if key not in ["FE", "BE"] else f"{key}:"
                display_text = f"{display_name} {os.path.basename(path)}"
                for i in range(self.file_list_widget.count()):
                    if self.file_list_widget.item(i).text().startswith(f"{display_name}"):
                        found = True
                        break
                if not found:
                    self.file_list_widget.addItem(display_text)

        # Phát tín hiệu khi đã đọc xong dữ liệu của tất cả các file có đường dẫn
        all_loaded = True
        for path in self.file_paths.values():
            if path is not None and os.path.basename(path) not in self.file_data:
                all_loaded = False
                break
        if all_loaded and self.workers:  # Đảm bảo có worker đã chạy xong
            self.loading_gif.hide_gif()
            self.data_loaded.emit(self.file_data) # Phát tín hiệu với toàn bộ self.file_data

    @Slot(object)
    def handle_file_clicked(self, item):
        file_name_prefix = item.text().split(":")[0].strip()
        # Tìm key tương ứng trong self.file_paths để lấy đúng tên file gốc
        selected_file_base_name = None
        for key, path in self.file_paths.items():
            if key == file_name_prefix or (key in ["FE", "BE"] and file_name_prefix == key):
                if path and os.path.basename(path) in self.file_data:
                    selected_file_base_name = os.path.basename(path)
                    break
        if selected_file_base_name in self.file_data:
            self.file_selected.emit(self.file_data[selected_file_base_name])
        else:
            QMessageBox.warning(self, "Cảnh báo", f"Không tìm thấy dữ liệu cho file: {item.text()}")

    @Slot()
    def delete_selected_file(self):
        selected_item = self.file_list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            file_type = text.split(":")[0].strip()
            for key, path in self.file_paths.items():
                if key == file_type or (key in ["FE", "BE"] and file_type == key):
                    if path and os.path.basename(path) in self.file_data:
                        del self.file_data[os.path.basename(path)]
                        self.file_paths[key] = None
                        self.file_list_widget.takeItem(self.file_list_widget.row(selected_item))
                        break

    @Slot(str)
    def handle_read_error(self, error_msg):
        QMessageBox.critical(self, "Lỗi đọc file", error_msg)
        self.loading_gif.hide_gif()

    def closeEvent(self, event):
        for worker in self.workers:
            worker.quit()
            worker.wait()
        event.accept()

# # ... import DataReaderWorker ...

# class FileListForm(QWidget):
#     data_loaded = Signal(dict) # Signal phát ra khi cả hai file FE và BE đã được đọc
#     file_selected = Signal(pd.DataFrame) # Signal phát ra khi một file được chọn từ list

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.folder_path = None
#         self.file_paths = {"FE": None, "BE": None}
#         self.file_data = {} # Lưu trữ dữ liệu của cả hai file sau khi đọc
#         self.workers = []
#         self.loading_gif = LoadingGifLabel(self)
#         self.initUI()

#     def initUI(self):
#         main_layout = QVBoxLayout(self)

#         # Chọn thư mục
#         folder_layout = QHBoxLayout()
#         self.folder_label = MyQLabel("Chọn thư mục:")
#         self.folder_line_edit = MyQLineEdit()
#         self.browse_folder_button = MyQPushButton("Duyệt...")
#         self.browse_folder_button.clicked.connect(self.browse_folder)
#         folder_layout.addWidget(self.folder_label)
#         folder_layout.addWidget(self.folder_line_edit)
#         folder_layout.addWidget(self.browse_folder_button)
#         main_layout.addLayout(folder_layout)

#         # Danh sách file
#         self.file_list_widget = QListWidget()
#         self.file_list_widget.itemClicked.connect(self.handle_file_clicked)
#         main_layout.addWidget(self.file_list_widget)

#         # Nút xóa file
#         self.delete_button = MyQPushButton("Xóa File")
#         self.delete_button.set_style_3D()
#         self.delete_button.clicked.connect(self.delete_selected_file)
#         main_layout.addWidget(self.delete_button)

#         # Label hiển thị GIF tải (đã là một widget riêng)
#         main_layout.addWidget(self.loading_gif)

#         self.setLayout(main_layout)

#     @Slot()
#     def browse_folder(self):
#         folder_dialog = QFileDialog()
#         folder_path = folder_dialog.getExistingDirectory(self, "Chọn thư mục chứa files Excel")
#         if folder_path:
#             self.folder_line_edit.setText(folder_path)
#             self.folder_path = folder_path
#             self.load_all_data_from_folder(folder_path)

#     def load_all_data_from_folder(self, folder_path):
#         self.file_list_widget.clear() # Clear list widget ở đây
#         self.file_paths = {"FE": None, "BE": None}
#         self.file_data = {}
#         dir = QDir(folder_path)
#         dir.setFilter(QDir.Files | QDir.NoDotAndDotDot)
#         dir.setSorting(QDir.Name)
#         entry_list = dir.entryList(["*.xlsx", "*.xls"])

#         fe_path = None
#         be_path = None
#         for entry in entry_list:
#             file_path = os.path.join(folder_path, entry)
#             print(f"Tìm thấy file: {entry}, đường dẫn: {file_path}")
#             if "FE" in entry and fe_path is None:
#                 fe_path = file_path
#                 self.file_paths["FE"] = file_path
#             elif "BE" in entry and be_path is None:
#                 be_path = file_path
#                 self.file_paths["BE"] = file_path

#         print(f"Đường dẫn file FE: {fe_path}")
#         print(f"Đường dẫn file BE: {be_path}")

#         files_to_load = []
#         if fe_path:
#             files_to_load.append(("FE", fe_path))
#         if be_path:
#             files_to_load.append(("BE", be_path))

#         if files_to_load:
#             self.loading_gif.show_gif()
#             self.workers = []
#             for name, path in files_to_load:
#                 worker = DataReaderWorker(path)
#                 worker.data_ready.connect(self.handle_data_ready_all)
#                 worker.error_occurred.connect(self.handle_read_error)
#                 self.workers.append(worker)
#                 worker.start()
#         else:
#             QMessageBox.warning(self, "Cảnh báo", "Không tìm thấy file FE hoặc BE trong thư mục.")


#     @Slot(str, pd.DataFrame)
#     def handle_data_ready_all(self, file_name, data):
#         print(f"handle_data_ready_all được gọi với file: {file_name}")
#         self.file_data[file_name] = data
#         print(f"Dữ liệu đã đọc: {list(self.file_data.keys())}")
#         loaded_files = list(self.file_data.keys())
#         # Không clear file_list_widget ở đây nữa

#         if "FE" in self.file_paths["FE"]:
#             print(f"Thêm FE vào list: {os.path.basename(self.file_paths['FE'])}")
#             # Kiểm tra xem item đã tồn tại chưa trước khi thêm (nếu cần)
#             found = False
#             for i in range(self.file_list_widget.count()):
#                 if self.file_list_widget.item(i).text().startswith("FE:"):
#                     found = True
#                     break
#             if not found:
#                 self.file_list_widget.addItem(f"FE: {os.path.basename(self.file_paths['FE'])}")

#         if "BE" in self.file_paths["BE"]:
#             print(f"Thêm BE vào list: {os.path.basename(self.file_paths['BE'])}")
#             # Kiểm tra xem item đã tồn tại chưa trước khi thêm (nếu cần)
#             found = False
#             for i in range(self.file_list_widget.count()):
#                 if self.file_list_widget.item(i).text().startswith("BE:"):
#                     found = True
#                     break
#             if not found:
#                 self.file_list_widget.addItem(f"BE: {os.path.basename(self.file_paths['BE'])}")

#         if len(loaded_files) == 2 or (len(loaded_files) == 1 and (self.file_paths["FE"] is None or self.file_paths["BE"] is None)):
#             self.loading_gif.hide_gif()
#             self.data_loaded.emit(self.file_data) # Phát tín hiệu khi cả hai (hoặc có thể một) file đã đọc xong
           

#     @Slot(object)
#     def handle_file_clicked(self, item):
#         file_name_prefix = item.text().split(":")[1].strip()
#         if file_name_prefix in self.file_data:
#             # self.loading_gif.show_gif()
#             # Phát tín hiệu file_selected trực tiếp với dữ liệu đã có
#             self.file_selected.emit(self.file_data[file_name_prefix])
#             # self.loading_gif.hide_gif()
#         else:
#             QMessageBox.warning(self, "Cảnh báo", f"Không tìm thấy dữ liệu cho file: {file_name_prefix}")

#     # @Slot(object)
#     # def handle_file_clicked(self, item):
#     #     file_name_prefix = item.text().split(":")[1].strip()
#     #     if file_name_prefix in self.file_data.keys():
#     #         self.loading_gif.show_gif()
#     #         # Dừng worker cũ nếu đang chạy
#     #         for worker in self.workers[:]:
#     #             if isinstance(worker, DataProcessorWorker) and worker.isRunning():
#     #                 worker.quit()
#     #                 worker.wait()
#     #                 self.workers.remove(worker)
#     #                 # worker.finished.connect(self.loading_gif.hide_gif)
                    

#     #         # Tạo worker mới
#     #         worker = DataProcessorWorker(self.file_data[file_name_prefix])
#     #         worker.processed_data_ready.connect(self.emit_selected_data)
#     #         worker.finished.connect(self.loading_gif.hide_gif)
#     #         self.workers.append(worker)
#     #         worker.start()

    
#     @Slot(pd.DataFrame)
#     def emit_selected_data(self, data):
#         self.file_selected.emit(data)

#     @Slot()
#     def delete_selected_file(self):
#         selected_item = self.file_list_widget.currentItem()
#         if selected_item:
#             text = selected_item.text()
#             if text.startswith("FE:"):
#                 self.file_paths["FE"] = None
#                 if "FE" in self.file_data:
#                     del self.file_data["FE"]
#             elif text.startswith("BE:"):
#                 self.file_paths["BE"] = None
#                 if "BE" in self.file_data:
#                     del self.file_data["BE"]
#             self.file_list_widget.takeItem(self.file_list_widget.row(selected_item))

#     @Slot(str)
#     def handle_read_error(self, error_msg):
#         QMessageBox.critical(self, "Lỗi đọc file", error_msg)
#         self.loading_gif.hide_gif()

#     def closeEvent(self, event):
#         for worker in self.workers:
#             worker.quit()
#             worker.wait()
#         event.accept()