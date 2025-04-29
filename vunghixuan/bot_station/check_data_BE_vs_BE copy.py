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
from vunghixuan.bot_station.check_cost import CheckCost
# from vunghixuan.bot_station.to_excel import ExcelWriter
import xlwings as xw

from vunghixuan.bot_station.to_excel import ExcelWithTOC
from vunghixuan.bot_station.nomal_fe_be import NoMalFEBE

class DataComparisonWorker(QObject):
    finished = Signal()
    result_ready = Signal(pd.DataFrame, str)
    error_occurred = Signal(str)

    def __init__(self, fe_data: pd.DataFrame, be_data: pd.DataFrame, revenue_data: pd.DataFrame, antagonize_data: pd.DataFrame, output_dir: str):
        super().__init__()
        self.fe_data = fe_data
        self.be_data = be_data
        self.revenue_data = revenue_data
        self.antagonize_data = antagonize_data
        self.output_dir = output_dir

    # def get_id_column_name(self, col_name, pd_columns):
    #     if col_name in pd_columns:
    #         return pd_columns.get_loc(col_name)
    #     else:
    #         return None

    

    # def _load_and_standardize_fe(self, df, col_name):
    #     if df is not None and col_name in df.columns:
    #         # Chuyển đổi sang kiểu chuỗi
    #         df[col_name] = df[col_name].astype(str)
    #         # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
    #         df_cleaned = df[df[col_name] != 'nan'].copy()
    #         # Thêm dấu nháy đơn nếu giá trị không phải là 'nan'
    #         # print(df_cleaned[col_name].head(20))
    #         df_cleaned[col_name] = df_cleaned[col_name].apply(lambda x: "'" + x if pd.notna(x) else x)

            
    #         return df_cleaned
    #     elif df is None:
    #         print("Chưa có dữ liệu FE được tải.")
    #         return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán
    #     else:
    #         print(f"Không tìm thấy cột '{col_name}' trong dữ liệu FE.")
    #         return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán

    # def _load_and_standardize_be(self, df, col_name):
    #     if df is not None and col_name in df.columns:
    #         # Chuyển đổi sang kiểu chuỗi
    #         df[col_name] = df[col_name].astype(str)
    #         # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
    #         df_cleaned = df[df[col_name] != 'nan'].copy()
    #         # Thêm dấu nháy đơn nếu giá trị không phải là 'nan'
    #         # print(df_cleaned[col_name].head(20))
    #         df_cleaned[col_name] = df_cleaned[col_name].apply(lambda x: "'" + x if pd.notna(x) else x)


            
    #         return df_cleaned
    #     elif df is None:
    #         print("Chưa có dữ liệu BE được tải.")
    #         return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán
    #     else:
    #         print(f"Không tìm thấy cột '{col_name}' trong dữ liệu BE.")
    #         return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán

    # def get_mgd_has_value_0(self, df, col_name):
    #     """
    #     Kiểm tra và trả về các dòng có mã giao dịch trùng lặp trong DataFrame
    #     sau khi đã loại bỏ các dòng có giá trị 'nan' trong cột chỉ định.

    #     Args:
    #         df (pd.DataFrame): DataFrame cần kiểm tra.
    #         col_name (str, optional): Tên cột chứa mã giao dịch.
    #                                    Mặc định là 'Mã giao dịch'.

    #     Returns:
    #         pd.DataFrame: DataFrame chứa các dòng có mã giao dịch trùng lặp
    #                        sau khi đã loại bỏ dòng có giá trị 'nan'.
    #                        Trả về DataFrame rỗng nếu không có trùng lặp hoặc
    #                        cột không tồn tại.
    #     """
    #     if df is not None and col_name in df.columns:
    #         # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
    #         df_cleaned = df.copy()            
    #         # Kiểm tra trùng lặp trên DataFrame đã loại bỏ 'nan'
    #         duplicated_mask = df_cleaned.duplicated(subset=[col_name], keep=False)
    #         return df_cleaned[duplicated_mask]
    #     elif df is None:
    #         print("DataFrame đầu vào là None.")
    #         return pd.DataFrame()
    #     else:
    #         print(f"Không tìm thấy cột '{col_name}' trong DataFrame.")
    #         return pd.DataFrame()
    
    # def add_summary_row(self, df, cost_col_name='Chi phí', ma_giao_dich_col='Mã giao dịch'):
    #     """
    #     Thêm dòng tổng số giao dịch và tổng chi phí vào cuối DataFrame.

    #     Args:
    #         df (pd.DataFrame): DataFrame cần thêm dòng tổng kết.
    #         cost_col_name (str, optional): Tên cột chứa chi phí.
    #                                        Mặc định là 'Chi phí'.
    #         ma_giao_dich_col (str, optional): Tên cột chứa mã giao dịch.
    #                                            Mặc định là 'Mã giao dịch'.

    #     Returns:
    #         pd.DataFrame: DataFrame đã thêm dòng tổng kết.
    #     """
    #     if df is not None and not df.empty:
    #         total_transactions = len(df)-1
    #         summary_data = {}

    #         # Lấy danh sách tất cả các cột
    #         all_cols = df.columns.tolist()

    #         # Đảm bảo cột đầu tiên có giá trị 'TỔNG'
    #         if all_cols:
    #             first_col = all_cols[0]
    #             summary_data[first_col] = ['TỔNG']

    #         # Đưa tổng số giao dịch vào cột mã giao dịch
    #         if ma_giao_dich_col in all_cols:
    #             summary_data[ma_giao_dich_col] = [f'({total_transactions} giao dịch)']

    #         # Tính và đưa tổng chi phí vào cột tương ứng
    #         if cost_col_name in all_cols :#and pd.api.types.is_numeric_dtype(df[cost_col_name]):
    #             summary_data[cost_col_name] = [df[cost_col_name].sum()]

    #         # Tạo DataFrame dòng tổng kết
    #         summary = pd.DataFrame(summary_data)

    #         # Nối dòng tổng kết vào cuối DataFrame, điền các cột thiếu bằng NaN
    #         df_with_summary = pd.concat([df, summary], ignore_index=True, sort=False)
    #         return df_with_summary
    #     elif df is None:
    #         print("DataFrame đầu vào là None.")
    #         return pd.DataFrame()
    #     else:
    #         print("DataFrame đầu vào rỗng.")
    #         return df.copy() # Trả về bản sao của DataFrame rỗng
    
    # def _prepare_and_rename_cols(self, df, col_list, prefix=''):
    #     """
    #     Kiểm tra sự tồn tại của các cột trong DataFrame và trả về DataFrame
    #     với các cột đã chọn và có tiền tố (nếu cần).

    #     Args:
    #         df (pd.DataFrame): DataFrame đầu vào.
    #         col_list (list): Danh sách tên các cột cần chọn.
    #         prefix (str, optional): Tiền tố để thêm vào tên cột. Mặc định là ''.

    #     Returns:
    #         pd.DataFrame: DataFrame chứa các cột đã chọn và được đổi tên,
    #                      hoặc None nếu có cột không tồn tại.
    #     """
    #     missing_cols = [col for col in col_list if col not in df.columns]
    #     if missing_cols:
    #         print(f"Lỗi: Các cột sau không tồn tại trong DataFrame: {missing_cols}")
    #         return None

    #     selected_df = df[col_list].copy()
    #     if prefix:
    #         rename_dict = {col: f'{prefix}_{col}' for col in selected_df.columns}
    #         selected_df.rename(columns=rename_dict, inplace=True)
    #     return selected_df

    # def summarize_data(self, df_list, colname_fe_lists, colname_be_lists, sum_colname_fe, sum_colname_be, ma_giao_dich_col='Mã giao dịch'):
    #     """
    #     Tổng hợp dữ liệu từ hai DataFrame dựa trên mã giao dịch.
    #     """
    #     if len(df_list) != 2:
    #         print("Lỗi: df_list phải chứa đúng hai DataFrame.")
    #         return pd.DataFrame()
        
        

    #     df_fe = df_list[0].copy()
    #     df_be = df_list[1].copy()

       
        
    #     if ma_giao_dich_col not in df_fe.columns or ma_giao_dich_col not in df_be.columns:
    #         print(f"Lỗi: Cột '{ma_giao_dich_col}' không tồn tại trong một hoặc cả hai DataFrame.")
    #         return pd.DataFrame()

    #     # Chọn các cột cần thiết từ FE
    #     fe_selected = df_fe[[ma_giao_dich_col] + colname_fe_lists].copy()

    #     # Chọn các cột cần thiết từ BE và đổi tên
    #     be_selected = df_be[[ma_giao_dich_col] + colname_be_lists].copy()
    #     be_renamed_cols = {col: f'BE_{col}' if col != ma_giao_dich_col else col for col in be_selected.columns}
    #     be_selected.rename(columns=be_renamed_cols, inplace=True)

    #     # Merge hai DataFrame dựa trên mã giao dịch
    #     merged_df = pd.merge(fe_selected, be_selected, on=ma_giao_dich_col, how='outer')       
        

    #     # Tạo dòng tổng
    #     summary_data = {}
    #     all_cols = merged_df.columns.tolist()
    #     all_cols.append('Chênh lệch (Phí thu)')        
        
    #     # Cột đầu tiên là 'TỔNG'
    #     if all_cols:
    #         summary_data[all_cols[0]] = ['TỔNG']

    
    #     # Tổng số giao dịch ở cột mã giao dịch
    #     if ma_giao_dich_col in all_cols:
    #         total_fe = len(df_fe)-1
    #         total_be = len(df_be)-1
    #         summary_data[ma_giao_dich_col] = [f'Tổng cộng: FE có {total_fe} giao dịch, BE có {total_be} giao dịch']
        
        

    #     # Tính tổng cho các cột của FE
    #     for col in sum_colname_fe:
    #         if col in all_cols : #and pd.api.types.is_numeric_dtype(merged_df[col])
    #             summary_data[col] = [merged_df[col].sum()]
    #         else:
    #             summary_data.setdefault(col, [None])

    #     # Tính tổng cho các cột của BE
    #     for col in sum_colname_be:
    #         be_col = f'BE_{col}'
    #         if be_col in all_cols : #and pd.api.types.is_numeric_dtype(merged_df[be_col])
    #             summary_data[be_col] = [merged_df[be_col].sum()]
    #         else:
    #             summary_data.setdefault(be_col, [None])
        
        
    #     # Tính chênh lệch phí
    #     if 'Phí thu' in merged_df.columns and f'BE_{col}' in merged_df.columns:
    #         merged_df['Chênh lệch (Phí thu)'] = merged_df['Phí thu'].fillna(0) - merged_df[f'BE_{col}'].fillna(0)
    #         # Giải quyết cảnh báo  merged_df['Chênh lệch (Phí thu)'] = merged_df['Phí thu'].fillna(0) - merged_df[f'BE_{col}'].fillna(0) trong phương thức .fillna(), .ffill(), và .bfill() với kiểu dữ liệu object
    #         merged_df = merged_df.infer_objects()
    #         summary_data['Chênh lệch (Phí thu)'] = [merged_df['Chênh lệch (Phí thu)'].sum()]
    #     else:
    #         summary_data.setdefault('Chênh lệch (Phí thu)', [None])

    #     # for col in summary_data['Chênh lệch (Phí thu)']:
    #     #     summary_data['Chênh lệch (Phí thu)'] = [summary_data['Chênh lệch (Phí thu)'].sum()]


    #     summary_df = pd.DataFrame(summary_data)

    #     # Nối dòng tổng vào DataFrame kết quả
    #     final_df = pd.concat([merged_df, summary_df], ignore_index=True, sort=False)
    #     return final_df

    # # Chuân hoá Sheet tổng hợp dữ liệu
    # def merge_FE_BE(self, df_list):
    #     col_name = 'Mã giao dịch'
    #     colname_fe = ['Số xe đăng ký', 'Mã thẻ','Phí thu', 'Làn','Ngày giờ', 'Loại vé']
    #     colname_be = ['Biển số xe', 'Số etag', 'Loại giá vé', 'Tiền bao gồm thuế', 'Thời gian qua trạm', 'Làn']
    #     sum_col_fe = ['Phí thu']
    #     sum_col_be = ['Tiền bao gồm thuế']
        
        
    #     # Sheet Tổng hợp dữ liệu
    #     df_FE_BE = self.summarize_data(
    #         df_list,
    #         colname_fe,
    #         colname_be,
    #         sum_col_fe,
    #         sum_col_be,
    #         col_name
    #     )
    #     """
    #     Nhiệm vụ ngày 250423: 
    #         ***** Nhóm theo 'biển số' hay hơn nhóm Group 'mã thẻ' vì 1 xe gắn nhiều mã thẻ, có thể trừ tiền cả 2 thẻ nếu xe gắn vào 
    #         - Tìm Cột 'Phí thu' mà FE tính tiền mà BE không tính tiền
    #         - Sau đó tra lại cột 'Mã thẻ' nhóm thành Group theo cột 'Mã thẻ'
    #             Lưu ý: Xét đến trường hợp cùng số xe nhưng có nhiều thẻ vẫn bị trừ tiền
    #             Một "Mã thẻ' có thể gắn nhiều xe (Có thể loại)
                
    #         * Điều kiện: Nếu BE phí = 0 nghĩa là hoàn tiền, cũng chính là số chênh lệch giữa phí BE và FE
    #         ? Có cần thêm cột 'Hoàn tiền' để làm sao cho BE và FE khớp số ==> Nghĩa là để cột 'chênh lệch phí thu' = 0 VNĐ
    #     """
     
    #     return df_FE_BE

    # def load_and_standardize_fe_be(self):
    #     try:
    #         if self.fe_data is None or self.be_data is None:
    #             raise ValueError("Không có dữ liệu FE hoặc BE để so sánh.")            
           

    #         col_name = 'Mã giao dịch'
    #         id_col_name_in_fe = self.get_id_column_name(col_name, self.fe_data.columns)
    #         id_col_name_in_be = self.get_id_column_name(col_name, self.be_data.columns)
    #         if id_col_name_in_fe is None or id_col_name_in_be is None:
    #             raise ValueError("Cột 'mã giao dịch' không tồn tại trong một hoặc cả hai file.")

    #         # Chuẩn hóa cột 'Mã giao dịch' cho FE và BE
    #         col_names_FE = ['Số xe đăng ký'] # Không cần chuẩn hoá cột 'Mã giao dịch' và , 'Mã thẻ': có sẵn dấu ' rồi
    #         fe_processed = self.fe_data.copy()
    #         for name in col_names_FE:
    #             fe_processed = self._load_and_standardize_fe(fe_processed, name)
            
    #         col_names_BE = ['Mã giao dịch', 'Biển số xe', 'Số etag']
    #         be_processed = self.be_data.copy()
    #         for name in col_names_BE:                
    #             be_processed = self._load_and_standardize_be(be_processed, name)
            
    #         # # Chuẩn hoá lại file gốc
    #         # self.fe_data = fe_processed
    #         # self.be_data = be_processed
    #         return fe_processed, be_processed
    #     except Exception as e:
    #         print ("Lỗi: ",e)
    
    # def add_standard_car_license(self, df):
    #     """
    #     Chuẩn hóa cột biển số xe từ DataFrame có hai cột 'Số xe đăng ký' và 'BE_Biển số xe'.

    #     Args:
    #         df (pd.DataFrame): DataFrame chứa hai cột biển số xe.

    #     Returns:
    #         pd.DataFrame: DataFrame với cột 'Biển số chuẩn'.
    #     """
    #     df_copy = df.copy()

    #     # 1. Lấy giá trị biển số từ cột FE nếu không phải NaN
    #     df_copy['Biển số chuẩn'] = df_copy['Số xe đăng ký'].where(pd.notna(df_copy['Số xe đăng ký']), df_copy['BE_Biển số xe'])

    #     # 2. Loại bỏ dấu nháy đơn ở đầu chuỗi (nếu có)
    #     # df_copy['Biển số chuẩn'] = df_copy['Biển số chuẩn'].str.lstrip("'")

    #     # 3. Loại bỏ các ký tự không phải chữ và số (trừ khoảng trắng nếu cần)
    #     df_copy['Biển số chuẩn'] = df_copy['Biển số chuẩn'].str.replace(r"[^a-zA-Z0-9']", '', regex=True)

    #      # 4. Bỏ chữ 'T' hoặc 'V' ở cuối nếu có
    #     def remove_tv_suffix(bien_so):
    #         if isinstance(bien_so, str) and len(bien_so) > 0 and bien_so[-1] in ['T', 'V']:
    #             return bien_so[:-1]
    #         return bien_so

    #     df_copy['Biển số chuẩn'] = df_copy['Biển số chuẩn'].apply(remove_tv_suffix)
    #     df_copy = self.add_standard_lan(df_copy)

    #     return df_copy

    # def add_standard_lan(self, df):
    #     """
    #     Chuẩn hóa cột làn dựa vào 'Làn' và 'BE_Làn'.

    #     Args:
    #         df (pd.DataFrame): DataFrame chứa cột 'Làn' và 'BE_Làn'.

    #     Returns:
    #         pd.DataFrame: DataFrame với cột 'Làn chuẩn'.
    #     """
    #     df_copy = df.copy()
    #     df_copy['Làn chuẩn'] = np.nan  # Khởi tạo cột kết quả

    #     # Xử lý khi có dữ liệu BE_Làn
    #     mask_be_lan = pd.notna(df_copy['BE_Làn'])
    #     df_copy.loc[mask_be_lan, 'Làn chuẩn'] = df_copy.loc[mask_be_lan, 'BE_Làn'].astype(str).str.split('(').str[0].str.strip()

    #     # Xử lý khi không có dữ liệu BE_Làn, sử dụng cột Làn
    #     mask_lan_only = pd.isna(df_copy['BE_Làn']) & pd.notna(df_copy['Làn'])
    #     df_copy.loc[mask_lan_only, 'Làn'] = df_copy.loc[mask_lan_only, 'Làn'].astype(str).str.lstrip('0')
    #     df_copy.loc[mask_lan_only, 'Làn chuẩn'] = 'Làn ' + df_copy.loc[mask_lan_only, 'Làn']

    #     return df_copy
    
    def to_excel(self, output_dir, dic):
        "Liên kết với file to_excel.py gọi class ExcelWithTOC"
        try:
            with ExcelWithTOC(output_dir, dic) as excel_toc:
                    print(f"Workbook đã được tạo và lưu tại: {excel_toc.output_path}")         

            # return dic
        except Exception as e:
            print ('Lỗi ghi file', e)

    def add_sheet_name_and_df_into_dic(self, dic, sheet_name, df):
        "Thêm tên sheets và df"
        dic[sheet_name] = df
        return dic
    
    def run(self):
        data_for_excel = {}
        try:
            

            "1. Chuẩn hoá file fe và be"

            df_nomalizer = NoMalFEBE(self.fe_data, self.be_data)
            fe_processed, be_processed, df_FE_BE = df_nomalizer.nomal_fe_be()

            # a. Đưa vào data_for_excel
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'FE', fe_processed)
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'BE', be_processed)
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'FE-BE', df_FE_BE)
            
            # b.Đưa các dữ liệu Ngươn nhờ 'DoanhThuVETC' và 'DoiSoatGDVETC'
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'DoanhThuVETC', self.revenue_data)
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'DoiSoatGDVETC', self.antagonize_data)
           
            # c. Nhóm df_fe_be theo biển số chuẩn            
            df_group_cars_time = df_nomalizer.group_cars_and_time_from_df_FE_BE(df_FE_BE)            
            
            # Thêm dòng cuối cho df_fe_be
            df_group_cars_time = df_nomalizer.add_summary_columns(df_group_cars_time)
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'Xe_ThoiGianGiaoDich', df_group_cars_time)

            # In ra list hỏi Chat
            print([df_group_cars_time.columns.tolist()] + df_group_cars_time.values.tolist())

            "2. Phân tích dữ liệu"

            """
            ** Tạo Quy trình kiểm soát như sau:
            B1: Nhóm các biển số xe lại: Dễ tìm ra các xe vào làn nào ra làn nào
            """

            " 1234. Ghi dữ liệu ra file Excel"
            self.to_excel(self.output_dir, data_for_excel)

            
            # print(df_FE_BE[(df_FE_BE['BE_Biển số đăng ký']) & (df_FE_BE['Số xe đăng ký'])])

            
            # Kiểm tra các điều kiện về chi phí: bằng hàm tiên đoán nguyên nhân chênh lệch phí
            """ Tạm bỏ 
            
            check_cost = CheckCost()
            df_predict_fee = check_cost.predict_fee_differentials(df_FE_BE.copy())            

            # B1: Lọc ra các xe làm cho chi phí !=0 để tìm nguyên nhân và tiên đoán chênh lệch
            "Sắp xếp xe FE-BE"
            df_fee_diff = check_cost.fee_diff_filtered_cars(df_predict_fee.copy())
            
            # sh xác định nguyên nhân chênh lệch do phí nguội
            df_evasion_result = check_cost.result_evasion_toll(df_fee_diff.copy())
           
            # Lấy ra các dòng của df_fee_diff mà 'Mã giao dịch' không có trong df_evasion_result
            df_remaining = df_fee_diff[~df_fee_diff['Mã giao dịch'].isin(df_evasion_result['Mã giao dịch'])]

            
            # Lọc xe theo tiên đoán lỗi cam
            df_fillter_predict_cam = check_cost.fillter_predict_multiple_camera_reads(df_fee_diff.copy())
            "Mai kiểm tra lại code này"

            # Kết quả xác định lỗi cam lần 1
            df_diff_free_cam = check_cost.find_multiple_camera_reads_with_fee_discrepancy(df_fillter_predict_cam)
            print(df_diff_free_cam)

            col_name = 'Mã giao dịch'
            # Lấy các mã giao dịch chỉ có trong file FE mà không có trong file BE
            mgd_not_be = fe_processed[~fe_processed[col_name].isin(be_processed[col_name])]            


            # Lấy các dòng có mã giao dịch là ' 0' sau khi loại bỏ 'nan'
            fe_mgd_has_value_0_df = self.get_mgd_has_value_0(fe_processed, col_name)
            be_mgd_has_value_0_df = self.get_mgd_has_value_0(be_processed, col_name)
            """
            # Xuất Excel
            
            # # dic_excel = {'path_file': self.output_dir}
            # col_name = 'Mã giao dịch'
            # sheets_and_data = {
            #     # 1.Phần thu thập dữ liệu
            #     'FE': self.add_summary_row(fe_processed, 'Phí thu', col_name),
            #     'BE': self.add_summary_row(be_processed, 'Tiền bao gồm thuế', col_name),
            #     'FE-BE': df_FE_BE,
            #     'DoanhThuVETC': self.revenue_data,
            #     'DoiSoatGDVETC' : self.antagonize_data,
                
            #     # 2. Liệt kê theo nhóm
            #     'DanhMucXe FE-BE': df_group_cars_time,

            #     # # Phần phân loại xe nghi vấn
            #     # 'Xe gây CL phí': df_fee_diff,
            #     # 'Xe trùng GD': df_fillter_predict_cam,
            #     # 'Có FE không có BE': self.add_summary_row(mgd_not_be, 'Phí thu', col_name),
            #     # 'Xe UTToanQuoc_FE': self.add_summary_row(fe_mgd_has_value_0_df, 'Phí thu', col_name),
            #     # 'Xe UTToanQuoc_BE': self.add_summary_row(be_mgd_has_value_0_df, 'Tiền bao gồm thuế', col_name),

            #     # # Phần tiên đoán và loại duy dần
            #     # 'Chênh lệch phí thu': df_predict_fee,

            #     # # Phần kết quả
                
            #     # 'KQ thu phí nguội': df_evasion_result,
            #     # 'KQ phí trùng GD': df_diff_free_cam,
            # }

            # # sheet_names = list(sheets_and_data.keys())

            # # Khởi tạo ExcelWithTOC
            # with ExcelWithTOC(self.output_dir, sheets_and_data) as excel_toc:
            #     print(f"Workbook đã được tạo và lưu tại: {excel_toc.output_path}")

          

            return data_for_excel
            

        except ValueError as ve:
            print(ve)
        #     self.error_occurred.emit(str(ve))
        #     self.finished.emit()
        except Exception as e:
            print(e)
            # self.error_occurred.emit(f"Lỗi không xác định: {e}")
            # self.finished.emit()

