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
from vunghixuan.bot_station.check_data_BE_vs_BE import DataComparisonWorker
from vunghixuan.settings import FILES_URL
import xlwings as xw

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
        file_names = self.file_data.keys()
        result_file_name_base = 'Kết quả đối soát'
        fe_data = None
        be_data = None
        date_str = ''

        for file_name in file_names:
            if 'FE' in file_name:
                fe_data = self.file_data[file_name]
                try:
                    date_str = file_name.split('FE')[1].split('.')[0]
                except IndexError:
                    date_str = ''
            elif 'BE' in file_name:
                be_data = self.file_data[file_name]

        result_file_name = f'{result_file_name_base}{date_str}.xlsx'
        output_dir = os.path.join(FILES_URL, 'output')
        os.makedirs(output_dir, exist_ok=True)  # Tạo thư mục output nếu chưa tồn tại
        output_path = os.path.join(output_dir, result_file_name)

        if fe_data is not None and be_data is not None:
            result_pd = DataComparisonWorker(fe_data, be_data, output_path)
            dic_excel = result_pd.run()
            print (dic_excel)

            # self.load_data_to_table(dic_excel['Tổng hợp FE_BE'])
            # self.load_data_to_table(dic_excel)
            self.load_data_to_table(dic_excel['Đối soát phí thu']) 


            # Xuất dữ liệu ra file Excel bằng pandas
            # df = pd.DataFrame(data_BE_vs_BE)  # Chuyển dữ liệu thành DataFrame
            try:
                
                # Mở file Excel sau khi lưu (tùy chọn)
                wb = xw.Book(output_path)
                
                # Iterate through each sheet in the workbook
                for sheet in wb.sheets:
                    # # Autofit columns
                    sheet.autofit('columns')
                    # # Autofit rows
                    sheet.autofit('rows')
                    # Thiết lập thuộc tính WrapText cho toàn bộ ô
                    # sheet.range('A1').expand().api.WrapText = True
                    # sheet.autofit('columns')
                    

                    # Save and close the workbook
                    wb.save()
                # wb.close()

            except Exception as e:
                print(f"Lỗi khi xuất file Excel: {e}")
        else:
            print("Không đủ dữ liệu FE và BE để thực hiện đối soát và xuất file.")

        pass

    @Slot(pd.DataFrame)
    def load_data_to_table(self, df):
        """
        Slot này nhận DataFrame và tải dữ liệu vào TableData.
        """
        # Kiểm tra xem df có phải là None trước khi truy cập thuộc tính 'empty'
        if df is not None:
            if not df.empty:
                # Chuyển DataFrame thành list of dict để phù hợp với TableData (nếu cần)
                data_for_table = df.to_dict('records')
                self.data_table.load_data(data_for_table)
            else:
                self.data_table.clear()
        else:
            print("Hàm load_data_to_table nhận vào một đối tượng None.")
            self.data_table.clear() # Đảm bảo bảng được làm trống nếu không có dữ liệu

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