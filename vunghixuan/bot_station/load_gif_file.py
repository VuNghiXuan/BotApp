from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QListWidget, QMessageBox
)
from PySide6.QtCore import Qt, QDir, Slot, Signal, QThread
from PySide6.QtGui import QMovie
from vunghixuan.gui.widgets import MyQLabel, MyQLineEdit, MyQPushButton
from vunghixuan.settings import STATIC_DIR_RELATIVE

import os
import pandas as pd

class LoadingGifLabel(QLabel):
    def __init__(self, parent=None, gif_path=f"{STATIC_DIR_RELATIVE}/gif/01-36-23-338_512.webp"):
        super().__init__(parent)
        self.movie = QMovie(gif_path)
        self.setAlignment(Qt.AlignCenter)
        self.setMovie(self.movie)
        self.hide()

    def show_gif(self):
        self.show()
        self.movie.start()

    def hide_gif(self):
        self.hide()
        self.movie.stop()

# class DataReaderWorker(QThread):
#     data_ready = Signal(str, pd.DataFrame)
#     error_occurred = Signal(str)

#     def __init__(self, file_path, parent=None):
#         super().__init__(parent)
#         self.file_path = file_path

#     def run(self):
#         try:
#             df = pd.read_excel(self.file_path, header=None)
#             # Tìm dòng bắt đầu dựa trên cột 'STT'
#             start_row_index = -1
#             for index, row in df.iterrows():
#                 for cell in row:
#                     if isinstance(cell, str) and cell.lower() == 'stt':
#                         start_row_index = index
#                         break
#                 if start_row_index != -1:
#                     break

#             if start_row_index != -1:
#                 header = [str(h).strip() for h in df.iloc[start_row_index].tolist()]
#                 data_df = df.iloc[start_row_index + 1:].copy()
#                 data_df.columns = header[:len(data_df.columns)] # Đảm bảo số cột khớp
#                 self.data_ready.emit(os.path.basename(self.file_path), data_df)
#             else:
#                 self.error_occurred.emit(f"Không tìm thấy cột 'STT' trong file: {os.path.basename(self.file_path)}")
#         except FileNotFoundError:
#             self.error_occurred.emit(f"Không tìm thấy file: {os.path.basename(self.file_path)}")
#         except Exception as e:
#             self.error_occurred.emit(f"Lỗi khi đọc file: {os.path.basename(self.file_path)} - {e}")
