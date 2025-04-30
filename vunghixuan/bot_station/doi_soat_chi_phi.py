import pandas as pd
import numpy as np


class DoiSoatPhi:
    def __init__(self):
        self.mapping_lane = {
            '2A': ['10', '11', '12'],
            '1A': ['1', '2', '3', '4'],
            '3B': ['7', '8', '9'],
            '3A': ['5', '6']
        }
        self.cot_ket_qua = 'Kết quả đối soát'
        self.cot_nguyen_nhan = 'Nguyên nhân chênh lệch'
        self.cot_so_lan_qua_tram = 'Số lần qua trạm'
        self.cot_thoi_gian_cach_lan_truoc = 'Thời gian cách lần trước (phút)'
        self.cot_phi_dieu_chinh_fe = 'Phí điều chỉnh FE'
        self.cot_phi_dieu_chinh_be = 'Phí điều chỉnh BE'
        self.cot_ghi_chu_xu_ly = 'Ghi chú xử lý'

    def tach_nhom_xe_ko_thu_phi(self, df):
        """
        Tách DataFrame thành hai nhóm: xe có vé ưu tiên/miễn phí và xe không.

        Args:
            df (pd.DataFrame): DataFrame đã gộp và chuẩn hóa, có cột 'Loại vé chuẩn',
                               'Phí thu' (FE), và 'BE_Tiền bao gồm thuế' (BE).

        Returns:
            tuple: Một tuple chứa hai DataFrame:
                   - df_khong_thu_phi_uu_tien: DataFrame chứa các xe có vé miễn phí/ưu tiên
                                         và phí thu BE/FE là NaN hoặc = 0.
                   - df_tra_phi: DataFrame chứa các xe không thuộc nhóm trên.
        """
        dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['Miễn giảm 100%', 'UT toàn quốc', 'Miễn giảm ĐP', 'Vé quý thường', 'Vé tháng thường'])
        dieu_kien_phi_nan_hoac_khong = (df['Phí thu'].isna() | (df['Phí thu'] == 0)) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))

        df_khong_thu_phi_uu_tien = df[dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong].copy()
        df_tra_phi = df[~(dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong)].copy()

        return df_khong_thu_phi_uu_tien, df_tra_phi

    def _get_tram_from_lane(self, lane):
        """Trích xuất tên trạm từ tên làn."""
        if pd.isna(lane):
            return None
        for tram, lanes in self.mapping_lane.items():
            for l in lanes:
                if str(l) in str(lane):
                    return tram
        return None

    def kiem_tra_doc_nhieu_luot(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp nghi vấn đọc nhiều lượt do anten.

        Args:
            df (pd.DataFrame): DataFrame chứa các xe trả phí.

        Returns:
            pd.DataFrame: DataFrame chứa các trường hợp nghi vấn đọc nhiều lượt.
        """
        df_nhieu_luot = df.copy()
        df_nhieu_luot[self.cot_so_lan_qua_tram] = df_nhieu_luot.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('count')
        df_nhieu_luot_filtered = df_nhieu_luot[df_nhieu_luot[self.cot_so_lan_qua_tram] >= 2].sort_values(['Biển số chuẩn', 'Thời gian chuẩn']).copy()
        df_nhieu_luot_filtered['Trạm'] = df_nhieu_luot_filtered['Làn chuẩn'].apply(self._get_tram_from_lane)
        df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] = df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].diff().dt.total_seconds() / 60
        df_nhieu_luot_filtered[self.cot_ket_qua] = None
        df_nhieu_luot_filtered[self.cot_nguyen_nhan] = None
        df_nhieu_luot_filtered[self.cot_phi_dieu_chinh_fe] = 0
        df_nhieu_luot_filtered[self.cot_phi_dieu_chinh_be] = 0
        df_nhieu_luot_filtered[self.cot_ghi_chu_xu_ly] = None

        dieu_kien_cung_lan = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Làn chuẩn'].shift() == df_nhieu_luot_filtered['Làn chuẩn']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0))
        df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_ket_qua] = 'Nghi vấn đọc nhiều lượt (cùng làn)'
        df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_nguyen_nhan] = 'Thời gian gần, cùng làn và có phí'
        df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_phi_dieu_chinh_fe] = -df_nhieu_luot_filtered['Phí thu']
        df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_phi_dieu_chinh_be] = -df_nhieu_luot_filtered['BE_Tiền bao gồm thuế']
        df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_ghi_chu_xu_ly] = 'Trả lại phí do đọc trùng'

        dieu_kien_khac_lan_cung_tram = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Trạm'].shift() == df_nhieu_luot_filtered['Trạm']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0)) & (df_nhieu_luot_filtered[self.cot_ket_qua].isna())
        df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_ket_qua] = 'Nghi vấn đọc nhiều lượt (khác làn cùng trạm)'
        df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_nguyen_nhan] = 'Thời gian gần, khác làn cùng trạm và có phí'
        # Logic điều chỉnh phí cho trường hợp khác làn cùng trạm cần được xem xét cụ thể hơn
        # Ví dụ: Lấy phí của giao dịch đầu tiên làm chuẩn, các giao dịch sau điều chỉnh về 0 hoặc theo mức phí đúng
        df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_phi_dieu_chinh_fe] = -df_nhieu_luot_filtered['Phí thu'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0)
        df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_phi_dieu_chinh_be] = -df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0)
        df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_ghi_chu_xu_ly] = 'Cần kiểm tra, điều chỉnh phí do đọc nhiều lượt'

        return df_nhieu_luot_filtered[~df_nhieu_luot_filtered[self.cot_ket_qua].isna()].copy()

    def kiem_tra_thu_phi_nguoi(self, df):
        """
        Kiểm tra và trả về các trường hợp nghi vấn thu phí nguội (BE có phí, FE không).

        Args:
            df (pd.DataFrame): DataFrame chứa các xe trả phí.

        Returns:
            pd.DataFrame: DataFrame chứa các trường hợp nghi vấn thu phí nguội.
        """
        df_thu_phi_nguoi = df[(df['BE_Tiền bao gồm thuế'] > 0) & (df['Phí thu'].isna() | (df['Phí thu'] == 0))].copy()
        df_thu_phi_nguoi[self.cot_ket_qua] = 'Nghi vấn thu phí nguội'
        df_thu_phi_nguoi[self.cot_nguyen_nhan] = 'BE có phí, FE không có phí'
        df_thu_phi_nguoi[self.cot_phi_dieu_chinh_fe] = df_thu_phi_nguoi['BE_Tiền bao gồm thuế']
        df_thu_phi_nguoi[self.cot_phi_dieu_chinh_be] = 0
        df_thu_phi_nguoi[self.cot_ghi_chu_xu_ly] = 'Bổ sung phí cho FE'
        return df_thu_phi_nguoi

    def kiem_tra_fe_co_be_khong(self, df):
        """
        Kiểm tra và trả về các trường hợp FE có phí, BE không có.

        Args:
            df (pd.DataFrame): DataFrame chứa các xe trả phí.

        Returns:
            pd.DataFrame: DataFrame chứa các trường hợp FE có phí, BE không có.
        """
        df_fe_co_be_khong = df[(df['Phí thu'] > 0) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))].copy()
        df_fe_co_be_khong[self.cot_ket_qua] = 'FE có phí, BE không có'
        df_fe_co_be_khong[self.cot_nguyen_nhan] = 'FE có giao dịch tính tiền, BE không có'
        df_fe_co_be_khong[self.cot_phi_dieu_chinh_fe] = 0
        df_fe_co_be_khong[self.cot_phi_dieu_chinh_be] = df_fe_co_be_khong['Phí thu']
        df_fe_co_be_khong[self.cot_ghi_chu_xu_ly] = 'Bổ sung phí cho BE'
        return df_fe_co_be_khong

    def kiem_tra_chenh_lech_phi(self, df):
        """
        Kiểm tra và trả về các trường hợp chênh lệch phí thu giữa FE và BE.

        Args:
            df (pd.DataFrame): DataFrame chứa các xe trả phí.

        Returns:
            pd.DataFrame: DataFrame chứa các trường hợp chênh lệch phí.
        """
        df_chenh_lech = df.copy()
        dieu_kien_chenh_lech = df_chenh_lech['Phí thu'].fillna(0) != df_chenh_lech['BE_Tiền bao gồm thuế'].fillna(0)
        df_chenh_lech_phi = df_chenh_lech[dieu_kien_chenh_lech].copy()
        df_chenh_lech_phi[self.cot_ket_qua] = 'Chênh lệch phí'
        df_chenh_lech_phi[self.cot_nguyen_nhan] = 'Khác phí thu giữa FE và BE'
        df_chenh_lech_phi[self.cot_phi_dieu_chinh_fe] = np.where(df_chenh_lech_phi['Phí thu'].fillna(0) > df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0), -(df_chenh_lech_phi['Phí thu'].fillna(0) - df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0)), 0)
        df_chenh_lech_phi[self.cot_phi_dieu_chinh_be] = np.where(df_chenh_lech_phi['Phí thu'].fillna(0) < df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0), -(df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0) - df_chenh_lech_phi['Phí thu'].fillna(0)), 0)
        df_chenh_lech_phi[self.cot_ghi_chu_xu_ly] = np.where(df_chenh_lech_phi['Phí thu'].fillna(0) > df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0), 'FE thu thừa, cần trả lại', 'BE thu thiếu, cần bổ sung')
        return df_chenh_lech_phi

    def doi_soat_phi_tach_df(self, df_gop_chuan_hoa):
        """
        Quy trình đối soát phí thu tổng hợp, trả về dictionary chứa các DataFrame kết quả.

        Args:
            df_gop_chuan_hoa (pd.DataFrame): DataFrame đã gộp và chuẩn hóa.

        Returns:
            dict: Dictionary chứa các DataFrame kết quả cho từng phương án kiểm tra.
        """
        df_khong_thu_phi, df_tra_phi = self.tach_nhom_xe_ko_thu_phi(df_gop_chuan_hoa.copy())
        df_tra_phi['Trạm'] = df_tra_phi['Làn chuẩn'].apply(self._get_tram_from_lane)

        df_doc_nhieu_luot = self.kiem_tra_doc_nhieu_luot(df_tra_phi.copy())
        df_thu_phi_nguoi = self.kiem_tra_thu_phi_nguoi(df_tra_phi.copy())
        df_fe_co_be_khong = self.kiem_tra_fe_co_be_khong(df_tra_phi.copy())
        # df_chenh_lech_phi = self.kiem_tra_chenh_lech_phi(df_tra_phi.copy())

        df_khop = df_tra_phi[~df_tra_phi.index.isin(df_doc_nhieu_luot.index) &
                             ~df_tra_phi.index.isin(df_thu_phi_nguoi.index) &
                             ~df_tra_phi.index.isin(df_fe_co_be_khong.index) ].copy() #&~df_tra_phi.index.isin(df_chenh_lech_phi.index)

        df_khop[self.cot_ket_qua] = 'Khớp'
        df_khop[self.cot_nguyen_nhan] = 'Không có chênh lệch'
        df_khop[self.cot_phi_dieu_chinh_fe] = 0
        df_khop[self.cot_phi_dieu_chinh_be] = 0
        df_khop[self.cot_ghi_chu_xu_ly] = None

        df_bao_cao = pd.concat([
            df_khong_thu_phi,
            df_doc_nhieu_luot,
            df_thu_phi_nguoi,
            df_fe_co_be_khong,
            # df_chenh_lech_phi,
            df_khop
        ], ignore_index=True)

        results = {
            'DoiSoat-KhongThuPhi': df_khong_thu_phi,
            'DoiSoat-DocNhieuLan': df_doc_nhieu_luot,
            'DoiSoat-PhiNguoi': df_thu_phi_nguoi,
            'DoiSoat-ChiCo-FE': df_fe_co_be_khong,
            # 'DoiSoat-GiaThuPhi': df_chenh_lech_phi,
            'DoiSoat-Khop': df_khop,
            'BaoCaoTong_DoiSoat': df_bao_cao
        }

        return results

# class DoiSoatPhi:
#     def __init__(self):
#         self.mapping_lane = {
#             '2A': ['10', '11', '12'],
#             '1A': ['1', '2', '3', '4'],
#             '3B': ['7', '8', '9'],
#             '3A': ['5', '6']
#         }
#         self.cot_ket_qua = 'Kết quả đối soát'
#         self.cot_nguyen_nhan = 'Nguyên nhân chênh lệch'
#         self.cot_so_lan_qua_tram = 'Số lần qua trạm'
#         self.cot_thoi_gian_cach_lan_truoc = 'Thời gian cách lần trước (phút)'
#         self.cot_phi_dieu_chinh_fe = 'Phí điều chỉnh FE'
#         self.cot_phi_dieu_chinh_be = 'Phí điều chỉnh BE'
#         self.cot_ghi_chu_xu_ly = 'Ghi chú xử lý'

#     def tach_nhom_xe_ko_thu_phi(self, df):
#         """
#         Tách DataFrame thành hai nhóm: xe có vé ưu tiên/miễn phí và xe không.

#         Args:
#             df (pd.DataFrame): DataFrame đã gộp và chuẩn hóa, có cột 'Loại vé chuẩn',
#                                'Phí thu' (FE), và 'BE_Tiền bao gồm thuế' (BE).

#         Returns:
#             tuple: Một tuple chứa hai DataFrame:
#                    - df_khong_thu_phi_uu_tien: DataFrame chứa các xe có vé miễn phí/ưu tiên
#                                          và phí thu BE/FE là NaN hoặc = 0.
#                    - df_tra_phi: DataFrame chứa các xe không thuộc nhóm trên.
#         """
#         dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['Miễn giảm 100%', 'UT toàn quốc', 'Miễn giảm ĐP', 'Vé quý thường', 'Vé tháng thường'])
#         dieu_kien_phi_nan_hoac_khong = (df['Phí thu'].isna() | (df['Phí thu'] == 0)) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))

#         df_khong_thu_phi_uu_tien = df[dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong].copy()
#         df_tra_phi = df[~(dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong)].copy()

#         return df_khong_thu_phi_uu_tien, df_tra_phi

#     def _get_tram_from_lane(self, lane):
#         """Trích xuất tên trạm từ tên làn."""
#         if pd.isna(lane):
#             return None
#         for tram, lanes in self.mapping_lane.items():
#             for l in lanes:
#                 if str(l) in str(lane):
#                     return tram
#         return None

#     def kiem_tra_doc_nhieu_luot(self, df):
#         """
#         Kiểm tra và đánh dấu các trường hợp nghi vấn đọc nhiều lượt do anten.

#         Args:
#             df (pd.DataFrame): DataFrame chứa các xe trả phí.

#         Returns:
#             pd.DataFrame: DataFrame chứa các trường hợp nghi vấn đọc nhiều lượt.
#         """
#         df_nhieu_luot = df.copy()
#         df_nhieu_luot[self.cot_so_lan_qua_tram] = df_nhieu_luot.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('count')
#         df_nhieu_luot_filtered = df_nhieu_luot[df_nhieu_luot[self.cot_so_lan_qua_tram] >= 2].sort_values(['Biển số chuẩn', 'Thời gian chuẩn']).copy()
#         df_nhieu_luot_filtered['Trạm'] = df_nhieu_luot_filtered['Làn chuẩn'].apply(self._get_tram_from_lane)
#         df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] = df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].diff().dt.total_seconds() / 60
#         df_nhieu_luot_filtered[self.cot_ket_qua] = None
#         df_nhieu_luot_filtered[self.cot_nguyen_nhan] = None
#         df_nhieu_luot_filtered[self.cot_phi_dieu_chinh_fe] = 0
#         df_nhieu_luot_filtered[self.cot_phi_dieu_chinh_be] = 0
#         df_nhieu_luot_filtered[self.cot_ghi_chu_xu_ly] = None

#         dieu_kien_cung_lan = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Làn chuẩn'].shift() == df_nhieu_luot_filtered['Làn chuẩn']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0))
#         df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_ket_qua] = 'Nghi vấn đọc nhiều lượt (cùng làn)'
#         df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_nguyen_nhan] = 'Thời gian gần, cùng làn và có phí'
#         df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_phi_dieu_chinh_fe] = -df_nhieu_luot_filtered['Phí thu']
#         df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_phi_dieu_chinh_be] = -df_nhieu_luot_filtered['BE_Tiền bao gồm thuế']
#         df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_ghi_chu_xu_ly] = 'Trả lại phí do đọc trùng'

#         dieu_kien_khac_lan_cung_tram = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Trạm'].shift() == df_nhieu_luot_filtered['Trạm']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0)) & (df_nhieu_luot_filtered[self.cot_ket_qua].isna())
#         df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_ket_qua] = 'Nghi vấn đọc nhiều lượt (khác làn cùng trạm)'
#         df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_nguyen_nhan] = 'Thời gian gần, khác làn cùng trạm và có phí'
#         # Logic điều chỉnh phí cho trường hợp khác làn cùng trạm cần được xem xét cụ thể hơn
#         # Ví dụ: Lấy phí của giao dịch đầu tiên làm chuẩn, các giao dịch sau điều chỉnh về 0 hoặc theo mức phí đúng
#         df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_phi_dieu_chinh_fe] = -df_nhieu_luot_filtered['Phí thu'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0)
#         df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_phi_dieu_chinh_be] = -df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0)
#         df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_ghi_chu_xu_ly] = 'Cần kiểm tra, điều chỉnh phí do đọc nhiều lượt'

#         return df_nhieu_luot_filtered[~df_nhieu_luot_filtered[self.cot_ket_qua].isna()].copy()

#     def kiem_tra_thu_phi_nguoi(self, df):
#         """
#         Kiểm tra và trả về các trường hợp nghi vấn thu phí nguội (BE có phí, FE không).

#         Args:
#             df (pd.DataFrame): DataFrame chứa các xe trả phí.

#         Returns:
#             pd.DataFrame: DataFrame chứa các trường hợp nghi vấn thu phí nguội.
#         """
#         df_thu_phi_nguoi = df[(df['BE_Tiền bao gồm thuế'] > 0) & (df['Phí thu'].isna() | (df['Phí thu'] == 0))].copy()
#         df_thu_phi_nguoi[self.cot_ket_qua] = 'Nghi vấn thu phí nguội'
#         df_thu_phi_nguoi[self.cot_nguyen_nhan] = 'BE có phí, FE không có phí'
#         df_thu_phi_nguoi[self.cot_phi_dieu_chinh_fe] = df_thu_phi_nguoi['BE_Tiền bao gồm thuế']
#         df_thu_phi_nguoi[self.cot_phi_dieu_chinh_be] = 0
#         df_thu_phi_nguoi[self.cot_ghi_chu_xu_ly] = 'Bổ sung phí cho FE'
#         return df_thu_phi_nguoi

#     def kiem_tra_fe_co_be_khong(self, df):
#         """
#         Kiểm tra và trả về các trường hợp FE có phí, BE không có.

#         Args:
#             df (pd.DataFrame): DataFrame chứa các xe trả phí.

#         Returns:
#             pd.DataFrame: DataFrame chứa các trường hợp FE có phí, BE không có.
#         """
#         df_fe_co_be_khong = df[(df['Phí thu'] > 0) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))].copy()
#         df_fe_co_be_khong[self.cot_ket_qua] = 'FE có phí, BE không có'
#         df_fe_co_be_khong[self.cot_nguyen_nhan] = 'FE có giao dịch tính tiền, BE không có'
#         df_fe_co_be_khong[self.cot_phi_dieu_chinh_fe] = 0
#         df_fe_co_be_khong[self.cot_phi_dieu_chinh_be] = df_fe_co_be_khong['Phí thu']
#         df_fe_co_be_khong[self.cot_ghi_chu_xu_ly] = 'Bổ sung phí cho BE'
#         return df_fe_co_be_khong

#     def kiem_tra_chenh_lech_phi(self, df):
#         """
#         Kiểm tra và trả về các trường hợp chênh lệch phí thu giữa FE và BE.

#         Args:
#             df (pd.DataFrame): DataFrame chứa các xe trả phí.

#         Returns:
#             pd.DataFrame: DataFrame chứa các trường hợp chênh lệch phí.
#         """
#         df_chenh_lech = df.copy()
#         df_chenh_lech['Chenh Lech Phi'] = df_chenh_lech['Phí thu'] - df_chenh_lech['BE_Tiền bao gồm thuế']
#         df_chenh_lech_phi = df_chenh_lech[df_chenh_lech['Chenh Lech Phi'] != 0].copy()
#         df_chenh_lech_phi[self.cot_ket_qua] = 'Chênh lệch phí'
#         df_chenh_lech_phi[self.cot_nguyen_nhan] = 'Khác phí thu giữa FE và BE'
#         df_chenh_lech_phi[self.cot_phi_dieu_chinh_fe] = np.where(df_chenh_lech_phi['Chenh Lech Phi'] > 0, -df_chenh_lech_phi['Chenh Lech Phi'], 0)
#         df_chenh_lech_phi[self.cot_phi_dieu_chinh_be] = np.where(df_chenh_lech_phi['Chenh Lech Phi'] < 0, -df_chenh_lech_phi['Chenh Lech Phi'], 0)
#         df_chenh_lech_phi[self.cot_ghi_chu_xu_ly] = np.where(df_chenh_lech_phi['Chenh Lech Phi'] > 0, 'FE thu thừa, cần trả lại', 'BE thu thiếu, cần bổ sung')
#         return df_chenh_lech_phi

#     def doi_soat_phi_tach_df(self, df_gop_chuan_hoa):
#         """
#         Quy trình đối soát phí thu tổng hợp, trả về dictionary chứa các DataFrame kết quả.

#         Args:
#             df_gop_chuan_hoa (pd.DataFrame): DataFrame đã gộp và chuẩn hóa.

#         Returns:
#             dict: Dictionary chứa các DataFrame kết quả cho từng phương án kiểm tra.
#         """
#         df_khong_thu_phi, df_tra_phi = self.tach_nhom_xe_ko_thu_phi(df_gop_chuan_hoa.copy())
#         df_tra_phi['Trạm'] = df_tra_phi['Làn chuẩn'].apply(self._get_tram_from_lane)

#         df_doc_nhieu_luot = self.kiem_tra_doc_nhieu_luot(df_tra_phi.copy())
#         df_thu_phi_nguoi = self.kiem_tra_thu_phi_nguoi(df_tra_phi.copy())
#         df_fe_co_be_khong = self.kiem_tra_fe_co_be_khong(df_tra_phi.copy())
#         df_chenh_lech_phi = self.kiem_tra_chenh_lech_phi(df_tra_phi.copy())

#         df_khop = df_tra_phi[~df_tra_phi.index.isin(df_doc_nhieu_luot.index) &
#                              ~df_tra_phi.index.isin(df_thu_phi_nguoi.index) &
#                              ~df_tra_phi.index.isin(df_fe_co_be_khong.index) &
#                              ~df_tra_phi.index.isin(df_chenh_lech_phi.index)].copy()
        
#         df_khop[self.cot_ket_qua] = 'Khớp'
#         df_khop[self.cot_nguyen_nhan] = 'Không có chênh lệch'
#         df_khop[self.cot_phi_dieu_chinh_fe] = 0
#         df_khop[self.cot_phi_dieu_chinh_be] = 0
#         df_khop[self.cot_ghi_chu_xu_ly] = None
        
#         df_bao_cao = pd.concat([
#             df_khong_thu_phi,
#             df_doc_nhieu_luot,
#             df_thu_phi_nguoi,
#             df_fe_co_be_khong,
#             df_chenh_lech_phi,
#             df_khop
#         ], ignore_index=True)

#         results = {
#             'DoiSoat-KhongThuPhi': df_khong_thu_phi,
#             'DoiSoat-DocNhieuLan': df_doc_nhieu_luot,
#             'DoiSoat-PhiNguoi': df_thu_phi_nguoi,
#             'DoiSoat-ChiCo-FE': df_fe_co_be_khong,
#             'DoiSoat-GiaThuPhi': df_chenh_lech_phi,
#             'DoiSoat-Khop': df_khop,
#             'BaoCaoTong_DoiSoat': df_bao_cao
#         }

#         return results
    
