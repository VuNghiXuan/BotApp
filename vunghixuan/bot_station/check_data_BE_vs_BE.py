# vunghixuan/bot_station/check_data_BE_vs_BE.py
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
)
from vunghixuan.bot_station.table_data import TableData
from vunghixuan.bot_station.form_get_file_list import FileListForm
from PySide6.QtCore import Slot, QThread, Signal, QObject
import pandas as pd
import os
from vunghixuan.bot_station.load_gif_file import LoadingGifLabel
import platform
import subprocess
import numpy as np
# from vunghixuan.bot_station.check_cost_remove import CheckCost
# from vunghixuan.bot_station.to_excel import ExcelWriter
import xlwings as xw

from vunghixuan.bot_station.to_excel import ExcelWithTOC
from vunghixuan.bot_station.standardize_fe_be import StandardizeData
# from vunghixuan.bot_station.doi_soat_chi_phi_remove import DoiSoatPhi
from vunghixuan.bot_station.classify_car_by_fee import CarByFee
from vunghixuan.bot_station.car_journey_in_24h import Cars
# from vunghixuan.bot_station.turn_and_journey_remove import TollDataProcessor


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

            df_nomalizer = StandardizeData(self.fe_data, self.be_data)
            fe_processed, be_processed, df_FE_BE = df_nomalizer.merge_df_be_and_be()

            # a. Đưa vào data_for_excel
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'FE', fe_processed)
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'BE', be_processed)
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'FE-BE', df_FE_BE)
            
            # b.Đưa các dữ liệu Ngươn nhờ 'DoanhThuVETC' và 'DoiSoatGDVETC'
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'DoanhThuVETC', self.revenue_data)
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'DoiSoatGDVETC', self.antagonize_data)
           
            # c. Nhóm df_fe_be chuẩn hoá: Biển số, loại vé, thời gian và gộp biển số
            df_group_cars_time = df_nomalizer.standarize_fe_be(df_FE_BE.copy())           
            # df_group_cars_time = df_nomalizer.group_cars_from_df_FE_BE(df_FE_BE.copy())            
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'FE-BE(Nhóm xe)', df_group_cars_time)
            
           

            "2. Tách xe không trả phí và xe trả phí"
            car_by_fee = CarByFee() #Phân loại xe theo không thu và trả phí qua trạm
            df_xe_khong_tra_phi, df_xe_tra_phi = car_by_fee.split_group_cars_not_fee_and_has_fee(df_group_cars_time)
            
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'Xe-KhongTraPhi', df_xe_khong_tra_phi.copy())
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'Xe-TraPhi', df_xe_tra_phi.copy())           

            # dic_report = car_by_fee.doi_soat_va_phan_loai(df_group_cars_time.copy())
            # data_for_excel.update(dic_report)
            
            '3. Phân tích hành trình 1 xe trong dự án, tìm ra các chênh lệch'
            # 3.1 Khởi tạo nhiều hành trình 24h cho nhiều tất cả các loại xe vào dự án trong 24 h
            # cars_24h = Cars(df_has_fee = df_xe_tra_phi.copy())
            # df_chk_fee = cars_24h.get_transactions_info_df()
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'DoiSoat-XeTraPhi', df_chk_fee) 


            # mapping_lane_config = {
            #     'Đồng Khởi_2A': {'vào': ['Làn 10', 'Làn 11'], 'ra': ['Làn 12']},
            #     'ĐT768_1A': {'vào': ['Làn 1', 'Làn 2'], 'ra': ['Làn 3', 'Làn 4']},
            #     'ĐT768_3': {'vào': ['Làn 7', 'Làn 8', 'Làn 9'], 'ra': ['Làn 5', 'Làn 6']}
            # }
            mapping_lane_config = {
                '2A': {'vào': ['Làn 10', 'Làn 11'], 'ra': ['Làn 12']},
                '1A': {'vào': ['Làn 1', 'Làn 2'], 'ra': ['Làn 3', 'Làn 4']},
                '3&4': {'vào': ['Làn 7', 'Làn 8', 'Làn 9'], 'ra': ['Làn 5', 'Làn 6']}
            }
            cars_24h = Cars(df_xe_tra_phi.copy(), mapping_lane_config)
            df_chk_fee = cars_24h.get_transactions_info_df()
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'DoiSoat-XeTraPhi', df_chk_fee) 

            # '4. Tổng đói soát'
            # df_report = TollDataProcessor(df_xe_tra_phi.copy()).get_simplified_transactions()
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'BaoCao_TomTat', df_report) 

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

