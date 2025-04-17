from PySide6.QtCore import QThread, Signal, QObject
import os
import pandas as pd

import pandas as pd
import os
from PySide6.QtCore import Signal, Slot, QThread
import time

class DataReaderWorker(QThread):
    data_ready = Signal(str, pd.DataFrame)
    error_occurred = Signal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    

    def run(self):
        try:
            df = pd.read_excel(self.file_path, header=None)
            start_row_index = -1
            stt_column_index = -1
            for index, row in df.iterrows():
                for col_index, cell in enumerate(row):
                    if isinstance(cell, str) and cell.lower() == 'stt':
                        start_row_index = index
                        stt_column_index = col_index
                        break
                if start_row_index != -1:
                    break

            if start_row_index != -1:
                # Lấy toàn bộ data bắt đầu từ dòng start_row_index và cột stt_column_index
                data_df = df.iloc[start_row_index:, stt_column_index:].copy()

                # Tạo header (có thể là dòng đầu tiên của data_df sau khi cắt)
                if not data_df.empty:
                    header = [str(h).strip() for h in data_df.iloc[0].tolist()]
                    data_df = data_df[1:].copy() # Loại bỏ dòng header khỏi data
                    data_df.columns = header[:len(data_df.columns)] # Gán header (đảm bảo số cột khớp)

                self.data_ready.emit(os.path.basename(self.file_path), data_df)
            else:
                self.error_occurred.emit(f"Không tìm thấy cột 'STT' trong file: {os.path.basename(self.file_path)}")
        except FileNotFoundError:
            self.error_occurred.emit(f"Không tìm thấy file: {os.path.basename(self.file_path)}")
        except Exception as e:
            self.error_occurred.emit(f"Lỗi khi đọc file: {os.path.basename(self.file_path)} - {e}")


class DataProcessorWorker(QThread):
    processed_data_ready = Signal(pd.DataFrame)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data

    def run(self):
        self.processed_data_ready.emit(self.data) # Trong trường hợp này, chỉ cần pass data trực tiếp


class DataLoadingWorker(QObject):
    finished = Signal()
    data_loaded = Signal(pd.DataFrame)
    error_occurred = Signal(str)

    def __init__(self, data):
        super().__init__()
        self.data_to_process = data

    def run(self):
        try:
            # Thực hiện các tác vụ xử lý dữ liệu tốn thời gian ở đây
            processed_data = self.data_to_process # Ví dụ đơn giản: không xử lý gì thêm

            self.data_loaded.emit(processed_data)
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.finished.emit()