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

    def tach_nhom_xe_ko_thu_phi(self, df):
        """
        Tách DataFrame thành hai nhóm: xe có vé ưu tiên/miễn phí và xe không.

        Args:
            df (pd.DataFrame): DataFrame đã gộp và chuẩn hóa, có cột 'Loại vé chuẩn',
                               'Phí thu' (FE), và 'BE_Tiền bao gồm thuế' (BE).

        Returns:
            tuple: Một tuple chứa hai DataFrame:
                   - df_mien_phi_uu_tien: DataFrame chứa các xe có vé miễn phí/ưu tiên
                                         và phí thu BE/FE là NaN hoặc = 0.
                   - df_con_lai: DataFrame chứa các xe không thuộc nhóm trên.
        """
        dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['Miễn giảm 100%', 'UT toàn quốc', 'Miễn giảm ĐP', 'Vé quý thường', 'Vé tháng thường'])
        dieu_kien_phi_nan_hoac_khong = (df['Phí thu'].isna() | (df['Phí thu'] == 0)) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))

        df_mien_phi_uu_tien = df[dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong].copy()
        df_con_lai = df[~(dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong)].copy()

        return df_mien_phi_uu_tien, df_con_lai

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
            df (pd.DataFrame): DataFrame chứa các xe trả phí (df_con_lai từ hàm tach_nhom_xe_ko_thu_phi).

        Returns:
            pd.DataFrame: DataFrame đã được đánh dấu các trường hợp nghi vấn đọc nhiều lượt.
        """
        df[self.cot_so_lan_qua_tram] = df.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('count')
        df_nhieu_luot = df[df[self.cot_so_lan_qua_tram] >= 2].copy()
        df_nhieu_luot = df_nhieu_luot.sort_values(['Biển số chuẩn', 'Thời gian chuẩn'])
        df_nhieu_luot[self.cot_thoi_gian_cach_lan_truoc] = df_nhieu_luot.groupby('Biển số chuẩn')['Thời gian chuẩn'].diff().dt.total_seconds() / 60

        df_nhieu_luot[self.cot_ket_qua] = np.where(
            (df_nhieu_luot[self.cot_thoi_gian_cach_lan_truoc] <= 5) &
            (df_nhieu_luot.groupby('Biển số chuẩn')['Làn chuẩn'].shift() == df_nhieu_luot['Làn chuẩn']) &
            ((df_nhieu_luot['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot['Phí thu'] > 0)),
            'Nghi vấn đọc nhiều lượt (cùng làn)',
            None
        )

        df_nhieu_luot[self.cot_ket_qua] = np.where(
            (df_nhieu_luot[self.cot_thoi_gian_cach_lan_truoc] <= 5) &
            (df_nhieu_luot.groupby('Biển số chuẩn')['tram'].shift() == df_nhieu_luot['tram']) &
            ((df_nhieu_luot['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot['Phí thu'] > 0)) &
            (df_nhieu_luot[self.cot_ket_qua].isna()),
            'Nghi vấn đọc nhiều lượt (khác làn cùng trạm)',
            df_nhieu_luot[self.cot_ket_qua]
        )
        return df_nhieu_luot

    def kiem_tra_thu_phi_nguoi(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp nghi vấn thu phí nguội (BE có phí, FE không).

        Args:
            df (pd.DataFrame): DataFrame chứa các xe trả phí.

        Returns:
            pd.DataFrame: DataFrame đã được đánh dấu các trường hợp nghi vấn thu phí nguội.
        """
        df_thu_phi_nguoi = df[(df['BE_Tiền bao gồm thuế'] > 0) & (df['Phí thu'].isna() | (df['Phí thu'] == 0))].copy()
        df_thu_phi_nguoi[self.cot_ket_qua] = 'Nghi vấn thu phí nguội'
        df_thu_phi_nguoi[self.cot_nguyen_nhan] = 'BE có phí, FE không có phí'
        return df_thu_phi_nguoi

    def kiem_tra_fe_co_be_khong(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp FE có phí, BE không có.

        Args:
            df (pd.DataFrame): DataFrame chứa các xe trả phí.

        Returns:
            pd.DataFrame: DataFrame đã được đánh dấu các trường hợp FE có phí, BE không.
        """
        df_fe_co_be_khong = df[(df['Phí thu'] > 0) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))].copy()
        df_fe_co_be_khong[self.cot_ket_qua] = 'FE có phí, BE không có'
        df_fe_co_be_khong[self.cot_nguyen_nhan] = 'FE có giao dịch tính tiền, BE không có'
        return df_fe_co_be_khong

    def kiem_tra_chenh_lech_phi(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp chênh lệch phí thu giữa FE và BE.

        Args:
            df (pd.DataFrame): DataFrame chứa các xe trả phí.

        Returns:
            pd.DataFrame: DataFrame đã được đánh dấu các trường hợp chênh lệch phí.
        """
        df['Chenh Lech Phi'] = df['Phí thu'] - df['BE_Tiền bao gồm thuế']
        df_chenh_lech = df[df['Chenh Lech Phi'] != 0].copy()
        df_chenh_lech[self.cot_ket_qua] = 'Chênh lệch phí'
        df_chenh_lech[self.cot_nguyen_nhan] = 'Khác phí thu giữa FE và BE'
        return df_chenh_lech

    def doi_soat_phi(self, df_gop_chuan_hoa):
        """
        Quy trình đối soát phí thu tổng hợp.

        Args:
            df_gop_chuan_hoa (pd.DataFrame): DataFrame đã gộp và chuẩn hóa.

        Returns:
            pd.DataFrame: DataFrame đã được đối soát và đánh dấu các trường hợp chênh lệch.
        """
        df_mien_phi, df_tra_phi = self.tach_nhom_xe_ko_thu_phi(df_gop_chuan_hoa.copy())

        # Khởi tạo cột kết quả và nguyên nhân cho df trả phí
        df_tra_phi[self.cot_ket_qua] = None
        df_tra_phi[self.cot_nguyen_nhan] = None
        df_tra_phi['tram'] = df_tra_phi['Làn chuẩn'].apply(self._get_tram_from_lane)

        # Kiểm tra đọc nhiều lượt
        df_doc_nhieu_luot = self.kiem_tra_doc_nhieu_luot(df_tra_phi.copy())
        df_tra_phi = pd.concat([df_tra_phi[df_tra_phi[self.cot_ket_qua].isna()], df_doc_nhieu_luot]).drop_duplicates(subset=df_gop_chuan_hoa.columns.tolist() + [self.cot_ket_qua, self.cot_nguyen_nhan, self.cot_so_lan_qua_tram, self.cot_thoi_gian_cach_lan_truoc], keep='first')

        # Kiểm tra thu phí nguội
        df_thu_phi_nguoi = self.kiem_tra_thu_phi_nguoi(df_tra_phi.copy())
        df_tra_phi = pd.concat([df_tra_phi[df_tra_phi[self.cot_ket_qua].isna()], df_thu_phi_nguoi]).drop_duplicates(subset=df_gop_chuan_hoa.columns.tolist() + [self.cot_ket_qua, self.cot_nguyen_nhan, self.cot_so_lan_qua_tram, self.cot_thoi_gian_cach_lan_truoc], keep='first')

        # Kiểm tra FE có BE không
        df_fe_co_be_khong = self.kiem_tra_fe_co_be_khong(df_tra_phi.copy())
        df_tra_phi = pd.concat([df_tra_phi[df_tra_phi[self.cot_ket_qua].isna()], df_fe_co_be_khong]).drop_duplicates(subset=df_gop_chuan_hoa.columns.tolist() + [self.cot_ket_qua, self.cot_nguyen_nhan, self.cot_so_lan_qua_tram, self.cot_thoi_gian_cach_lan_truoc], keep='first')

        # Kiểm tra chênh lệch phí
        df_chenh_lech_phi = self.kiem_tra_chenh_lech_phi(df_tra_phi.copy())
        df_tra_phi = pd.concat([df_tra_phi[df_tra_phi[self.cot_ket_qua].isna()], df_chenh_lech_phi]).drop_duplicates(subset=df_gop_chuan_hoa.columns.tolist() + [self.cot_ket_qua, self.cot_nguyen_nhan, self.cot_so_lan_qua_tram, self.cot_thoi_gian_cach_lan_truoc, 'Chenh Lech Phi'], keep='first')

        # Gán nhãn "Khớp" cho các trường hợp không rơi vào các loại chênh lệch
        df_tra_phi[self.cot_ket_qua] = df_tra_phi[self.cot_ket_qua].fillna('Khớp')

        return pd.concat([df_mien_phi, df_tra_phi], ignore_index=True)

# # Dữ liệu ví dụ (giả sử DataFrame của bạn có tên là df_gop_chuan_hoa):
# data = {
#     'Biển số chuẩn': ['A1', 'A1', 'B2', 'C3', 'D4', 'E5', 'F6', 'G7', 'H8', 'I9'],
#     'Loại vé chuẩn': ['Vé lượt', 'Vé lượt', 'Miễn giảm 100%', 'Vé tháng', 'UT toàn quốc', 'Vé lượt', 'Miễn giảm ĐP', 'Vé quý thường', 'Vé tháng thường', 'Vé lượt'],
#     'Phí thu': [30000, 30000, 0, 500000, np.nan, 30000, 0, 0, np.nan, 40000],
#     'BE_Tiền bao gồm thuế': [30000, 30000, 0, 500000, 0, np.nan, 0, np.nan, 0, 35000],
#     'Thời gian chuẩn': ['2024-04-29 10:00:00', '2024-04-29 10:03:00', '2024-04-29 11:00:00', '2024-04-29 12:00:00', '2024-04-29 13:00:00', '2024-04-29 14:00:00', '2024-04-29 15:00:00', '2024-04-29 16:00:00', '2024-04-29 17:00:00', '2024-04-29 18:00:00'],
#     'Làn chuẩn': ['Làn 1A(1)', 'Làn 1A(1)', None, 'Làn 2A(10)', 'Làn 3B(7)', 'Làn 1A(3)', None, None, None, 'Làn 3A(5)'],
#     # ... các cột khác đã được chuẩn hóa
# }
# df_gop_chuan_hoa = pd.DataFrame(data)

# # Sử dụng hàm để đối soát
# doi_soat = DoiSoatPhi()
# df_da_doi_soat = doi_soat.doi_soat_phi(df_gop_chuan_hoa)
# print(df_da_doi_soat[['Biển số chuẩn', 'Loại vé chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', 'Thời gian chuẩn', 'Làn chuẩn', 'Kết quả đối soát', 'Nguyên nhân chênh lệch', 'Số lần qua trạm', 'Thời gian cách lần trước (phút)']])