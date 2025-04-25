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
import numpy as np
from vunghixuan.bot_station.check_cost import CheckTickets
import xlwings as xw

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

    # Loại bỏ các dòng nan
    def clear_nan_rows_from_colname(self, df, col_name):
        """
        Hàm này mục đích để loại bỏ các dòng cuối, như:
         - Dòng thời gian thống kê, chữ ký
         - Chọn cột có đầy đủ dữ liệu nhất và không chứa các các giá trị này :'thời gian thống kê, chữ ký'
          """
        # Chuyển đổi sang kiểu chuỗi
        df[col_name] = df[col_name].astype(str)
        # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
        df_cleaned = df[df[col_name] != 'nan'].copy()
        
        return df_cleaned

    def standardize_ma_giao_dich_fe(self, df, col_name):
        if df is not None and col_name in df.columns:
            # Chuyển đổi sang kiểu chuỗi
            df[col_name] = df[col_name].astype(str)
            # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
            df_cleaned = df[df[col_name] != 'nan'].copy()
            
            return df_cleaned
        elif df is None:
            print("Chưa có dữ liệu FE được tải.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán
        else:
            print(f"Không tìm thấy cột '{col_name}' trong dữ liệu FE.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán

    def standardize_ma_giao_dich_be(self, df, col_name):
        if df is not None and col_name in df.columns:
            # Chuyển đổi sang kiểu chuỗi
            df[col_name] = df[col_name].astype(str)
            # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
            df_cleaned = df[df[col_name] != 'nan'].copy()
            # Thêm dấu nháy đơn ở đầu chuỗi (nếu BE cần)
            df_cleaned[col_name] = "'" + df_cleaned[col_name]
            
            return df_cleaned
        elif df is None:
            print("Chưa có dữ liệu BE được tải.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán
        else:
            print(f"Không tìm thấy cột '{col_name}' trong dữ liệu BE.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán

    def get_mgd_has_value_0(self, df, col_name):
        """
        Kiểm tra và trả về các dòng có mã giao dịch trùng lặp trong DataFrame
        sau khi đã loại bỏ các dòng có giá trị 'nan' trong cột chỉ định.

        Args:
            df (pd.DataFrame): DataFrame cần kiểm tra.
            col_name (str, optional): Tên cột chứa mã giao dịch.
                                       Mặc định là 'Mã giao dịch'.

        Returns:
            pd.DataFrame: DataFrame chứa các dòng có mã giao dịch trùng lặp
                           sau khi đã loại bỏ dòng có giá trị 'nan'.
                           Trả về DataFrame rỗng nếu không có trùng lặp hoặc
                           cột không tồn tại.
        """
        if df is not None and col_name in df.columns:
            # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
            df_cleaned = df.copy()            
            # Kiểm tra trùng lặp trên DataFrame đã loại bỏ 'nan'
            duplicated_mask = df_cleaned.duplicated(subset=[col_name], keep=False)
            return df_cleaned[duplicated_mask]
        elif df is None:
            print("DataFrame đầu vào là None.")
            return pd.DataFrame()
        else:
            print(f"Không tìm thấy cột '{col_name}' trong DataFrame.")
            return pd.DataFrame()
    
    def add_summary_row(self, df, cost_col_name='Chi phí', ma_giao_dich_col='Mã giao dịch'):
        """
        Thêm dòng tổng số giao dịch và tổng chi phí vào cuối DataFrame.

        Args:
            df (pd.DataFrame): DataFrame cần thêm dòng tổng kết.
            cost_col_name (str, optional): Tên cột chứa chi phí.
                                           Mặc định là 'Chi phí'.
            ma_giao_dich_col (str, optional): Tên cột chứa mã giao dịch.
                                               Mặc định là 'Mã giao dịch'.

        Returns:
            pd.DataFrame: DataFrame đã thêm dòng tổng kết.
        """
        if df is not None and not df.empty:
            total_transactions = len(df)-1
            summary_data = {}

            # Lấy danh sách tất cả các cột
            all_cols = df.columns.tolist()

            # Đảm bảo cột đầu tiên có giá trị 'TỔNG'
            if all_cols:
                first_col = all_cols[0]
                summary_data[first_col] = ['TỔNG']

            # Đưa tổng số giao dịch vào cột mã giao dịch
            if ma_giao_dich_col in all_cols:
                summary_data[ma_giao_dich_col] = [f'({total_transactions} giao dịch)']

            # Tính và đưa tổng chi phí vào cột tương ứng
            if cost_col_name in all_cols :#and pd.api.types.is_numeric_dtype(df[cost_col_name]):
                summary_data[cost_col_name] = [df[cost_col_name].sum()]

            # Tạo DataFrame dòng tổng kết
            summary = pd.DataFrame(summary_data)

            # Nối dòng tổng kết vào cuối DataFrame, điền các cột thiếu bằng NaN
            df_with_summary = pd.concat([df, summary], ignore_index=True, sort=False)
            return df_with_summary
        elif df is None:
            print("DataFrame đầu vào là None.")
            return pd.DataFrame()
        else:
            print("DataFrame đầu vào rỗng.")
            return df.copy() # Trả về bản sao của DataFrame rỗng
    
    def _prepare_and_rename_cols(self, df, col_list, prefix=''):
        """
        Kiểm tra sự tồn tại của các cột trong DataFrame và trả về DataFrame
        với các cột đã chọn và có tiền tố (nếu cần).

        Args:
            df (pd.DataFrame): DataFrame đầu vào.
            col_list (list): Danh sách tên các cột cần chọn.
            prefix (str, optional): Tiền tố để thêm vào tên cột. Mặc định là ''.

        Returns:
            pd.DataFrame: DataFrame chứa các cột đã chọn và được đổi tên,
                         hoặc None nếu có cột không tồn tại.
        """
        missing_cols = [col for col in col_list if col not in df.columns]
        if missing_cols:
            print(f"Lỗi: Các cột sau không tồn tại trong DataFrame: {missing_cols}")
            return None

        selected_df = df[col_list].copy()
        if prefix:
            rename_dict = {col: f'{prefix}_{col}' for col in selected_df.columns}
            selected_df.rename(columns=rename_dict, inplace=True)
        return selected_df

    def summarize_data(self, df_list, colname_fe_lists, colname_be_lists, sum_colname_fe, sum_colname_be, ma_giao_dich_col='Mã giao dịch'):
        """
        Tổng hợp dữ liệu từ hai DataFrame dựa trên mã giao dịch.
        """
        if len(df_list) != 2:
            print("Lỗi: df_list phải chứa đúng hai DataFrame.")
            return pd.DataFrame()

        df_fe = df_list[0].copy()
        df_be = df_list[1].copy()

        if ma_giao_dich_col not in df_fe.columns or ma_giao_dich_col not in df_be.columns:
            print(f"Lỗi: Cột '{ma_giao_dich_col}' không tồn tại trong một hoặc cả hai DataFrame.")
            return pd.DataFrame()

        # Chọn các cột cần thiết từ FE
        fe_selected = df_fe[[ma_giao_dich_col] + colname_fe_lists].copy()

        # Chọn các cột cần thiết từ BE và đổi tên
        be_selected = df_be[[ma_giao_dich_col] + colname_be_lists].copy()
        be_renamed_cols = {col: f'BE_{col}' if col != ma_giao_dich_col else col for col in be_selected.columns}
        be_selected.rename(columns=be_renamed_cols, inplace=True)

        # Merge hai DataFrame dựa trên mã giao dịch
        merged_df = pd.merge(fe_selected, be_selected, on=ma_giao_dich_col, how='outer')       
        

        # Tạo dòng tổng
        summary_data = {}
        all_cols = merged_df.columns.tolist()
        all_cols.append('Chênh lệch (Phí thu)')        
        
        # Cột đầu tiên là 'TỔNG'
        if all_cols:
            summary_data[all_cols[0]] = ['TỔNG']

    
        # Tổng số giao dịch ở cột mã giao dịch
        if ma_giao_dich_col in all_cols:
            total_fe = len(df_fe)-1
            total_be = len(df_be)-1
            summary_data[ma_giao_dich_col] = [f'Tổng cộng: FE có {total_fe} giao dịch, BE có {total_be} giao dịch']
        
        

        # Tính tổng cho các cột của FE
        for col in sum_colname_fe:
            if col in all_cols : #and pd.api.types.is_numeric_dtype(merged_df[col])
                summary_data[col] = [merged_df[col].sum()]
            else:
                summary_data.setdefault(col, [None])

        # Tính tổng cho các cột của BE
        for col in sum_colname_be:
            be_col = f'BE_{col}'
            if be_col in all_cols : #and pd.api.types.is_numeric_dtype(merged_df[be_col])
                summary_data[be_col] = [merged_df[be_col].sum()]
            else:
                summary_data.setdefault(be_col, [None])
        
        
        # Tính chênh lệch phí
        if 'Phí thu' in merged_df.columns and f'BE_{col}' in merged_df.columns:
            merged_df['Chênh lệch (Phí thu)'] = merged_df['Phí thu'].fillna(0) - merged_df[f'BE_{col}'].fillna(0)
            # Giải quyết cảnh báo  merged_df['Chênh lệch (Phí thu)'] = merged_df['Phí thu'].fillna(0) - merged_df[f'BE_{col}'].fillna(0) trong phương thức .fillna(), .ffill(), và .bfill() với kiểu dữ liệu object
            merged_df = merged_df.infer_objects()
            summary_data['Chênh lệch (Phí thu)'] = [merged_df['Chênh lệch (Phí thu)'].sum()]
        else:
            summary_data.setdefault('Chênh lệch (Phí thu)', [None])

        # for col in summary_data['Chênh lệch (Phí thu)']:
        #     summary_data['Chênh lệch (Phí thu)'] = [summary_data['Chênh lệch (Phí thu)'].sum()]


        summary_df = pd.DataFrame(summary_data)

        # Nối dòng tổng vào DataFrame kết quả
        final_df = pd.concat([merged_df, summary_df], ignore_index=True, sort=False)
        return final_df

    # Chuân hoá Sheet tổng hợp dữ liệu
    def get_sh_TongHop(self, df_list):
        col_name = 'Mã giao dịch'
        colname_fe = ['Số xe đăng ký', 'Mã thẻ','Phí thu', 'Làn','Ngày giờ', 'Loại vé']
        colname_be = ['Biển số xe', 'Số etag', 'Loại giá vé', 'Tiền bao gồm thuế', 'Thời gian qua trạm', 'Làn']
        sum_col_fe = ['Phí thu']
        sum_col_be = ['Tiền bao gồm thuế']
        
        # Sheet Tổng hợp dữ liệu
        aggregated_df = self.summarize_data(
            df_list,
            colname_fe,
            colname_be,
            sum_col_fe,
            sum_col_be,
            col_name
        )
        """
        Nhiệm vụ ngày 250423: 
            ***** Nhóm theo 'biển số' hay hơn nhóm Group 'mã thẻ' vì 1 xe gắn nhiều mã thẻ, có thể trừ tiền cả 2 thẻ nếu xe gắn vào 
            - Tìm Cột 'Phí thu' mà FE tính tiền mà BE không tính tiền
            - Sau đó tra lại cột 'Mã thẻ' nhóm thành Group theo cột 'Mã thẻ'
                Lưu ý: Xét đến trường hợp cùng số xe nhưng có nhiều thẻ vẫn bị trừ tiền
                Một "Mã thẻ' có thể gắn nhiều xe (Có thể loại)
                
            * Điều kiện: Nếu BE phí = 0 nghĩa là hoàn tiền, cũng chính là số chênh lệch giữa phí BE và FE
            ? Có cần thêm cột 'Hoàn tiền' để làm sao cho BE và FE khớp số ==> Nghĩa là để cột 'chênh lệch phí thu' = 0 VNĐ
        """
     
        return aggregated_df


    def run(self):
        try:
            if self.fe_data is None or self.be_data is None:
                raise ValueError("Không có dữ liệu FE hoặc BE để so sánh.")
            
            "Chạy hảm đối soát vé import numpy as np"

            # # Chuẩn hóa cột 'Mã giao dịch' cho FE và BE
            # col_name = 'Mã giao dịch'
            # fe_processed = self.clear_nan_rows_from_colname(self.fe_data.copy(), col_name)
            # be_processed = self.standardize_ma_giao_dich_be(self.be_data.copy(), col_name)


           

            # # df_doi_soat = self.doi_soat_thu_phi(fe_processed, be_processed)
            # df_doi_soat = DoiSoatThuPhi().doi_soat_thu_phi(fe_processed, be_processed)

            # print(df_doi_soat)
            # with pd.ExcelWriter(self.output_dir) as writer: 
            #     df_doi_soat.to_excel(writer, sheet_name='doi_soat', index=False)

            # return df_doi_soat

            "tạm dừng sau khi xuất file exe import numpy as np"


            col_name = 'Mã giao dịch'
            id_col_name_in_fe = self.get_id_column_name(col_name, self.fe_data.columns)
            id_col_name_in_be = self.get_id_column_name(col_name, self.be_data.columns)
            if id_col_name_in_fe is None or id_col_name_in_be is None:
                raise ValueError("Cột 'mã giao dịch' không tồn tại trong một hoặc cả hai file.")

            # Chuẩn hóa cột 'Mã giao dịch' cho FE và BE
            fe_processed = self.standardize_ma_giao_dich_fe(self.fe_data.copy(), col_name)
            be_processed = self.standardize_ma_giao_dich_be(self.be_data.copy(), col_name)

            # Lấy dữ liệu cho Sheet Tổng hợp
            df_list = [fe_processed, be_processed]
            aggregated_df = self.get_sh_TongHop(df_list)

            
            # Kiểm tra các điều kiện về chi phí
            df_check_cost = CheckTickets().check_cost_station(aggregated_df.copy())
            # print(df_check_cost)
           

            # # Sau đó, kiểm tra tính nhất quán về thời gian trên kết quả đã có
            # df_final_check = check_cost.check_time_consistency(aggregated_df.copy(), time_threshold_minutes=3)

            # # df_final_check bây giờ sẽ có thông tin về cả chênh lệch chi phí và thời gian
            # print(df_final_check[['Biển số xe chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)', 'Ngày giờ', 'BE_Thời gian qua trạm', 'Ghi chú']].head(20))

                     
            # return aggregated_df # Trả về DataFrame kết quả
            
            # Lấy các mã giao dịch chỉ có trong file FE mà không có trong file BE
            mgd_not_be = fe_processed[~fe_processed[col_name].isin(be_processed[col_name])]            


            # Lấy các dòng có mã giao dịch là ' 0' sau khi loại bỏ 'nan'
            fe_mgd_has_value_0_df = self.get_mgd_has_value_0(fe_processed, col_name)
            be_mgd_has_value_0_df = self.get_mgd_has_value_0(be_processed, col_name)


            dic_excel= {
                'path_file': self.output_dir
            }

            # Xuất ra file Excel với hai sheet
            with pd.ExcelWriter(self.output_dir) as writer:                
                # Tính phí và Ghi ra file FE chuẩn hoá
                fe_processed = self.add_summary_row(fe_processed, 'Phí thu', col_name)
                fe_processed.to_excel(writer, sheet_name='FE', index=False)
                dic_excel['FE'] = fe_processed
                
                # Tính phí và Ghi ra file BE chuẩn hoá
                be_processed = self.add_summary_row(be_processed, 'Tiền bao gồm thuế', col_name)
                be_processed.to_excel(writer, sheet_name='BE', index=False)
                dic_excel['BE'] = be_processed

                # Ghi sheet báo cáo tổng hợp
                # sheet_report_fe_vs_be
                aggregated_df.to_excel(writer, sheet_name='Tổng hợp FE_BE', index=False)
                dic_excel['Tổng hợp FE_BE'] = aggregated_df

                # Ghi data cho sh_check_cosst
                df_check_cost.to_excel(writer, sheet_name='Đối soát phí thu', index=False)
                dic_excel['Đối soát phí thu'] = df_check_cost

                # Tính phí và Ghi ra sheet mã giao dịch không có trong BE
                mgd_not_be = self.add_summary_row(mgd_not_be, 'Phí thu', col_name)
                mgd_not_be.to_excel(writer, sheet_name='GiaoDich_ko_tồn_tại_BE', index=False)
                dic_excel['GiaoDich_ko_tồn_tại_BE'] = mgd_not_be

                fe_mgd_has_value_0_df = self.add_summary_row(fe_mgd_has_value_0_df, 'Phí thu', col_name)
                fe_mgd_has_value_0_df.to_excel(writer, sheet_name='LoaiVe_UT_ToanQuoc_FE', index=False)
                dic_excel['LoaiVe_UT_ToanQuoc_FE'] = fe_mgd_has_value_0_df

                be_mgd_has_value_0_df = self.add_summary_row(be_mgd_has_value_0_df, 'Tiền bao gồm thuế', col_name)
                be_mgd_has_value_0_df.to_excel(writer, sheet_name='LoaiVe_UT_ToanQuoc_BE', index=False)
                dic_excel['LoaiVe_UT_ToanQuoc_BE'] = be_mgd_has_value_0_df

                

            # self.result_ready.emit(pd.DataFrame(), self.output_dir) # Phát tín hiệu hoàn thành (không trả về DataFrame cụ thể)
            # self.finished.emit()

            # Trả kết quả để check_tick_form tiếp tục show lên bảng hoặc mở file, sheets
            return dic_excel

        except ValueError as ve:
            print(ve)
        #     self.error_occurred.emit(str(ve))
        #     self.finished.emit()
        except Exception as e:
            print(e)
            # self.error_occurred.emit(f"Lỗi không xác định: {e}")
            # self.finished.emit()


# # vunghixuan/bot_station/check_data_BE_vs_BE.py
# # -*- coding: utf-8 -*-
# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
# )
# from vunghixuan.bot_station.table_data import TableData
# from vunghixuan.bot_station.file_list_form import FileListForm
# from PySide6.QtCore import Slot, QThread, Signal, QObject
# import pandas as pd
# import os
# from vunghixuan.bot_station.load_gif_file import LoadingGifLabel
# import platform
# import subprocess

# class DataComparisonWorker(QObject):
#     finished = Signal()
#     result_ready = Signal(pd.DataFrame, str)
#     error_occurred = Signal(str)

#     def __init__(self, fe_data: pd.DataFrame, be_data: pd.DataFrame, output_dir: str):
#         super().__init__()
#         self.fe_data = fe_data
#         self.be_data = be_data
#         self.output_dir = output_dir
    
#     def get_id_column_name(self, col_name, pd_columns):
#         if col_name in pd_columns:
#             return pd_columns.get_loc(col_name)
#         else:
#             return None
    
#     def replace_single_quote(self, col_name):
#         if self.fe_data is not None and col_name in self.fe_data.columns:
#             # Sử dụng .astype(str) để đảm bảo tất cả các ô đều được xử lý như chuỗi
#             self.fe_data[col_name] = self.fe_data[col_name].astype(str).str.replace("'", "")
#         elif self.fe_data is None:
#             print("Chưa có dữ liệu FE được tải.")
#         else:
#             print(f"Không tìm thấy cột '{col_name}' trong dữ liệu FE.")

#     def get_fe_data(self):
#         return self.fe_data

#     def open_file(filepath):
#         if platform.system() == "Windows":
#             os.startfile(filepath)
#         elif platform.system() == "Darwin":
#             subprocess.Popen(["open", filepath])
#         elif platform.system() == "Linux":
#             subprocess.Popen(["xdg-open", filepath])
#         else:
#             print(f"Không hỗ trợ mở file trên hệ điều hành: {platform.system()}")

#     def run(self):
#         try:
#             if self.fe_data is None or self.be_data is None:
#                 raise ValueError("Không có dữ liệu FE hoặc BE để so sánh.")

#             # Đảm bảo cột 'mã giao dịch' tồn tại trong cả hai DataFrame
#             col_name = 'Mã giao dịch'
#             id_col_name_in_fe = self.get_id_column_name(col_name, self.fe_data.columns)
#             id_col_name_in_be = self.get_id_column_name(col_name, self.be_data.columns)
#             if id_col_name_in_fe is None or id_col_name_in_be is None:            
#                 raise ValueError("Cột 'mã giao dịch' không tồn tại trong một hoặc cả hai file.")
            
#             # Thay thế dấu ' trong cột 'Mã giao dịch' cho file FE
#             self.replace_single_quote(col_name)
#             # Lấy các mã giao dịch chỉ có trong file FE mà không có trong file BE
#             fe_only = self.fe_data[~self.fe_data[col_name].isin(self.be_data[col_name])]

#             if not fe_only.empty:
#                 # result_filename = "Kết quả đối soát.xlsx"
#                 # result_path = os.path.join(self.output_dir, result_filename)
#                 # if os.path.exists(result_path):
#                 fe_only.to_excel(self.output_dir, index=False)
#                 self.result_ready.emit(fe_only, fe_only)
#                 return fe_only

#                 # # Tạo DataFrame kết quả với cấu trúc giống file BE
#                 # be_columns = self.be_data.columns.tolist()
#                 # result_df = pd.DataFrame(fe_only.reindex(columns=be_columns))
#                 # result_filename = "Kết quả đối soát.xlsx"
#                 # result_path = os.path.join(self.output_dir, result_filename)
#                 # if os.path.exists(result_path):
#                 #     result_df.to_excel(result_path, index=False)
#                 #     self.result_ready.emit(result_df, result_path)
#                 # else:
#                 #     print(f'Đường dẫn "{result_path}" không tồn tại:')
#             else:
#                 self.result_ready.emit(pd.DataFrame(columns=self.be_data.columns), None) # Phát DataFrame rỗng

#             self.finished.emit()
#         except ValueError as ve:
#             self.error_occurred.emit(str(ve))
#             self.finished.emit()
#         except Exception as e:
#             self.error_occurred.emit(f"Lỗi không xác định: {e}")
#             self.finished.emit()

