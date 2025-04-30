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
from vunghixuan.bot_station.doi_soat_chi_phi import DoiSoatPhi

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
            data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'FE-BE(Nhóm xe)', df_group_cars_time)

            # In ra list hỏi Chat
            # print([df_group_cars_time.columns.tolist()] + df_group_cars_time.values.tolist())

            
            # '2. Lấy danh sách xe ưu tiên và danh sách trả phí'
            # doi_soat_cp = DoiSoatPhi()
            # df_ko_thu_phi, df_tra_phi = doi_soat_cp.tach_nhom_xe_ko_thu_phi(df_group_cars_time.copy())
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'Xe-KhongThuPhi', df_ko_thu_phi)
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'Xe-TraPhi', df_tra_phi)

            # '3. Nhóm xe có chênh lệch phí do anten đọc nhiều lần'
            # df_doi_soat_tra_phi = doi_soat_cp.kiem_tra_doc_nhieu_luot(df_tra_phi.copy())
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'NghiVan-DocNhieuLan', df_doi_soat_tra_phi)

            # '4. Nhóm xe có chênh lệch phí do phí nguội'
            # df_phi_nguoi = doi_soat_cp.kiem_tra_thu_phi_nguoi(df_tra_phi.copy())
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'NghiVan-PhiNguoi', df_phi_nguoi)

            # '5. Nhóm xe có chênh lệch phí fe_co_be_khong'
            # df_fe_co_be_khong = doi_soat_cp.kiem_tra_fe_co_be_khong(df_tra_phi.copy())
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'FE-co-BE_khong', df_fe_co_be_khong)

            # '4. Nhóm xe có chênh lệch phí do phí nguội'
            # df_phithu_be_khac_fe = doi_soat_cp.kiem_tra_chenh_lech_phi(df_tra_phi.copy())
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'PhiThu-KhacNhau', df_phithu_be_khac_fe)
            
            # "4. Báo cáo tổng hợp đối soát phí"
            # df_bao_cao_doi_soat = doi_soat_cp.doi_soat_phi(df_group_cars_time)
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'BaoCaoDoiSoat', df_bao_cao_doi_soat)

            '2. Kết quả đối soát'
            doi_soat_cp = DoiSoatPhi()
            # df_kq_VuNghiXuan = doi_soat_cp.doi_soat(df_group_cars_time.copy())
            # data_for_excel = self.add_sheet_name_and_df_into_dic(data_for_excel, 'DoiSoat-VuNghiXuan', df_kq_VuNghiXuan)
            
            '3. Xuất các sheets thống kê báo cáo'
            dic_report  = doi_soat_cp.doi_soat_va_phan_loai(df_group_cars_time.copy())
            data_for_excel.update(dic_report)

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

