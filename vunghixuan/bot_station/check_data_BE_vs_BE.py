# vunghixuan/bot_station/check_data_BE_vs_BE.py
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
)
from vunghixuan.bot_station.table_data import TableData
from vunghixuan.bot_station.file_list_form import FileListForm
from PySide6.QtCore import Slot, QThread, Signal, QObject
import pandas as pd
import os
from vunghixuan.bot_station.load_gif_file import LoadingGifLabel

class DataComparisonWorker(QObject):
    finished = Signal()
    result_ready = Signal(pd.DataFrame, str)
    error_occurred = Signal(str)

    def __init__(self, fe_data: pd.DataFrame, be_data: pd.DataFrame, output_dir: str):
        super().__init__()
        self.fe_data = fe_data
        self.be_data = be_data
        self.output_dir = output_dir

    def run(self):
        try:
            if self.fe_data is None or self.be_data is None:
                raise ValueError("Không có dữ liệu FE hoặc BE để so sánh.")

            # Đảm bảo cột 'mã giao dịch' tồn tại trong cả hai DataFrame
            if 'mã giao dịch' not in self.fe_data.columns or 'mã giao dịch' not in self.be_data.columns:
                raise ValueError("Cột 'mã giao dịch' không tồn tại trong một hoặc cả hai file.")

            # Lấy các mã giao dịch chỉ có trong file FE mà không có trong file BE
            fe_only = self.fe_data[~self.fe_data['mã giao dịch'].isin(self.be_data['mã giao dịch'])]

            if not fe_only.empty:
                # Tạo DataFrame kết quả với cấu trúc giống file BE
                be_columns = self.be_data.columns.tolist()
                result_df = pd.DataFrame(fe_only.reindex(columns=be_columns))
                result_filename = "kết quả.xlsx"
                result_path = os.path.join(self.output_dir, result_filename)
                result_df.to_excel(result_path, index=False)
                self.result_ready.emit(result_df, result_path)
            else:
                self.result_ready.emit(pd.DataFrame(columns=self.be_data.columns), None) # Phát DataFrame rỗng

            self.finished.emit()
        except ValueError as ve:
            self.error_occurred.emit(str(ve))
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"Lỗi không xác định: {e}")
            self.finished.emit()

