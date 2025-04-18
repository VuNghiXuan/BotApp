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
import platform
import subprocess

class DataComparisonWorker(QObject):
    finished = Signal()
    result_ready = Signal(pd.DataFrame, str)
    error_occurred = Signal(str)

    def __init__(self, fe_data: pd.DataFrame, be_data: pd.DataFrame, output_dir: str):
        super().__init__()
        self.fe_data = fe_data
        self.be_data = be_data
        self.output_dir = output_dir
    
    def get_id_column_name(self, col_name, pd_columns):
        if col_name in pd_columns:
            return pd_columns.get_loc(col_name)
        else:
            return None
    
    def replace_single_quote(self, col_name):
        if self.fe_data is not None and col_name in self.fe_data.columns:
            # Sử dụng .astype(str) để đảm bảo tất cả các ô đều được xử lý như chuỗi
            self.fe_data[col_name] = self.fe_data[col_name].astype(str).str.replace("'", "")
        elif self.fe_data is None:
            print("Chưa có dữ liệu FE được tải.")
        else:
            print(f"Không tìm thấy cột '{col_name}' trong dữ liệu FE.")

    def get_fe_data(self):
        return self.fe_data

    def open_file(filepath):
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", filepath])
        elif platform.system() == "Linux":
            subprocess.Popen(["xdg-open", filepath])
        else:
            print(f"Không hỗ trợ mở file trên hệ điều hành: {platform.system()}")

    def run(self):
        try:
            if self.fe_data is None or self.be_data is None:
                raise ValueError("Không có dữ liệu FE hoặc BE để so sánh.")

            # Đảm bảo cột 'mã giao dịch' tồn tại trong cả hai DataFrame
            col_name = 'Mã giao dịch'
            id_col_name_in_fe = self.get_id_column_name(col_name, self.fe_data.columns)
            id_col_name_in_be = self.get_id_column_name(col_name, self.be_data.columns)
            if id_col_name_in_fe is None or id_col_name_in_be is None:            
                raise ValueError("Cột 'mã giao dịch' không tồn tại trong một hoặc cả hai file.")
            
            # Thay thế dấu ' trong cột 'Mã giao dịch' cho file FE
            self.replace_single_quote(col_name)
            # Lấy các mã giao dịch chỉ có trong file FE mà không có trong file BE
            fe_only = self.fe_data[~self.fe_data[col_name].isin(self.be_data[col_name])]

            if not fe_only.empty:
                # result_filename = "Kết quả đối soát.xlsx"
                # result_path = os.path.join(self.output_dir, result_filename)
                # if os.path.exists(result_path):
                fe_only.to_excel(self.output_dir, index=False)
                self.result_ready.emit(fe_only, fe_only)
                return fe_only

                # # Tạo DataFrame kết quả với cấu trúc giống file BE
                # be_columns = self.be_data.columns.tolist()
                # result_df = pd.DataFrame(fe_only.reindex(columns=be_columns))
                # result_filename = "Kết quả đối soát.xlsx"
                # result_path = os.path.join(self.output_dir, result_filename)
                # if os.path.exists(result_path):
                #     result_df.to_excel(result_path, index=False)
                #     self.result_ready.emit(result_df, result_path)
                # else:
                #     print(f'Đường dẫn "{result_path}" không tồn tại:')
            else:
                self.result_ready.emit(pd.DataFrame(columns=self.be_data.columns), None) # Phát DataFrame rỗng

            self.finished.emit()
        except ValueError as ve:
            self.error_occurred.emit(str(ve))
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"Lỗi không xác định: {e}")
            self.finished.emit()

