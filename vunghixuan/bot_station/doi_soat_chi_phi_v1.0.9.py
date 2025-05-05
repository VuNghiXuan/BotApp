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
        self.cot_so_lan_qua_tram = 'Số lần qua trạm'
        self.cot_thoi_gian_cach_lan_truoc = 'K/C 2 lần đọc (phút)'
        self.cot_phi_dieu_chinh_fe = 'Phí điều chỉnh FE'
        self.cot_phi_dieu_chinh_be = 'Phí điều chỉnh BE'
        self.cot_ghi_chu_xu_ly = 'Ghi chú xử lý'
        self.cot_xe_khong_thu_phi = 'Xe không thu phí'
        self.cot_loi_doc_nhieu_lan = 'Lỗi Anten'
        self.cot_thu_phi_nguoi = 'Thu nguội'
        self.cot_chi_co_be = 'Giao dịch chỉ có BE'
        self.cot_ket_qua_doi_soat = 'Kết quả đối soát'
        self.cot_nguyen_nhan_doi_soat = 'Nguyên nhân đối soát'
        self.cot_buoc_doi_soat = 'Bước đối soát'

    def tach_nhom_xe_ko_thu_phi(self, df):
        """
        Đánh dấu các xe không thu phí trực tiếp vào DataFrame.

        Args:
            df (pd.DataFrame): DataFrame đã gộp và chuẩn hóa.

        Returns:
            pd.DataFrame: DataFrame đã được đánh dấu cột 'Xe không thu phí'.
        """
        dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['Miễn giảm 100%', 'UT toàn quốc', 'Miễn giảm ĐP', 'Vé quý thường', 'Vé tháng thường'])
        dieu_kien_phi_nan_hoac_khong = (df['Phí thu'].isna() | (df['Phí thu'] == 0)) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))
        df[self.cot_xe_khong_thu_phi] = dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong
        return df

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
            df (pd.DataFrame): DataFrame chứa dữ liệu đối soát.

        Returns:
            pd.DataFrame: DataFrame đã được cập nhật với thông tin về lỗi đọc nhiều lượt.
        """
        df[self.cot_so_lan_qua_tram] = df.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('count')
        df['Trạm'] = df['Làn chuẩn'].apply(self._get_tram_from_lane)
        df[self.cot_thoi_gian_cach_lan_truoc] = df.groupby('Biển số chuẩn')['Thời gian chuẩn'].diff().dt.total_seconds() / 60
        df[self.cot_loi_doc_nhieu_lan] = False

        # Ensure the adjustment columns exist, initializing with 0 if not
        if self.cot_phi_dieu_chinh_fe not in df.columns:
            df[self.cot_phi_dieu_chinh_fe] = 0
        else:
            df[self.cot_phi_dieu_chinh_fe] = df[self.cot_phi_dieu_chinh_fe].fillna(0)

        if self.cot_phi_dieu_chinh_be not in df.columns:
            df[self.cot_phi_dieu_chinh_be] = 0
        else:
            df[self.cot_phi_dieu_chinh_be] = df[self.cot_phi_dieu_chinh_be].fillna(0)

        # Ensure the ghi_chu_xu_ly column exists, initializing with '' if not
        if self.cot_ghi_chu_xu_ly not in df.columns:
            df[self.cot_ghi_chu_xu_ly] = ''
        else:
            df[self.cot_ghi_chu_xu_ly] = df[self.cot_ghi_chu_xu_ly].fillna('')

        df_nhieu_luot_filtered = df[df[self.cot_so_lan_qua_tram] >= 2].sort_values(['Biển số chuẩn', 'Thời gian chuẩn']).copy()

        dieu_kien_cung_lan = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Làn chuẩn'].shift() == df_nhieu_luot_filtered['Làn chuẩn']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0))
        df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_loi_doc_nhieu_lan] = True
        df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_phi_dieu_chinh_fe] = df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_phi_dieu_chinh_fe] - df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, 'Phí thu'].fillna(0)
        df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_phi_dieu_chinh_be] = df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_phi_dieu_chinh_be] - df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, 'BE_Tiền bao gồm thuế'].fillna(0)
        df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_ghi_chu_xu_ly] = df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_ghi_chu_xu_ly] + '; Trả lại phí do đọc trùng'

        dieu_kien_khac_lan_cung_tram = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Trạm'].shift() == df_nhieu_luot_filtered['Trạm']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0)) & (~dieu_kien_cung_lan)
        df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_loi_doc_nhieu_lan] = True
        df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_phi_dieu_chinh_fe] = df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_phi_dieu_chinh_fe] - df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, 'Phí thu'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0).fillna(0)
        df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_phi_dieu_chinh_be] = df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_phi_dieu_chinh_be] - df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, 'BE_Tiền bao gồm thuế'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0).fillna(0)
        df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_ghi_chu_xu_ly] = df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_ghi_chu_xu_ly] + '; Cần kiểm tra, điều chỉnh phí do đọc nhiều lượt'

        return df

    def kiem_tra_thu_phi_nguoi(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp nghi vấn thu phí nguội,
        đồng thời tạo cột 'Thu nguội' và các cột liên quan.

        Args:
            df (pd.DataFrame): DataFrame.

        Returns:
            pd.DataFrame: DataFrame đã được đánh dấu cột 'Thu nguội' và các cột liên quan.
        """
        dieu_kien_thu_phi_nguoi = (df['BE_Tiền bao gồm thuế'] > 0) & (df['Phí thu'].isna() | (df['Phí thu'] == 0))
        df[self.cot_thu_phi_nguoi] = dieu_kien_thu_phi_nguoi
        df[self.cot_phi_dieu_chinh_fe] = np.where(dieu_kien_thu_phi_nguoi, df[self.cot_phi_dieu_chinh_fe] + df['BE_Tiền bao gồm thuế'].fillna(0), df[self.cot_phi_dieu_chinh_fe])
        df[self.cot_phi_dieu_chinh_be] = np.where(dieu_kien_thu_phi_nguoi, df[self.cot_phi_dieu_chinh_be], df[self.cot_phi_dieu_chinh_be])
        df[self.cot_ghi_chu_xu_ly] = np.where(dieu_kien_thu_phi_nguoi & (df[self.cot_ghi_chu_xu_ly] == ''), 'Bổ sung phí cho FE',
                                            np.where(dieu_kien_thu_phi_nguoi & (df[self.cot_ghi_chu_xu_ly] != ''), df[self.cot_ghi_chu_xu_ly] + '; Bổ sung phí cho FE', df[self.cot_ghi_chu_xu_ly]))
        return df

    def kiem_tra_fe_co_be_khong(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp FE có phí, BE không có,
        đồng thời tạo cột 'Giao dịch chỉ có BE' và các cột liên quan.

        Args:
            df (pd.DataFrame): DataFrame.

        Returns:
            pd.DataFrame: DataFrame đã được đánh dấu cột 'Giao dịch chỉ có BE' và các cột liên quan.
        """
        dieu_kien_fe_co_be_khong = (df['Phí thu'] > 0) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))
        df[self.cot_chi_co_be] = dieu_kien_fe_co_be_khong
        df[self.cot_phi_dieu_chinh_fe] = np.where(dieu_kien_fe_co_be_khong, df[self.cot_phi_dieu_chinh_fe], df[self.cot_phi_dieu_chinh_fe])
        df[self.cot_phi_dieu_chinh_be] = np.where(dieu_kien_fe_co_be_khong, df[self.cot_phi_dieu_chinh_be] + df['Phí thu'].fillna(0), df[self.cot_phi_dieu_chinh_be])
        df[self.cot_ghi_chu_xu_ly] = np.where(dieu_kien_fe_co_be_khong & (df[self.cot_ghi_chu_xu_ly] == ''), 'Bổ sung phí cho BE',
                                            np.where(dieu_kien_fe_co_be_khong & (df[self.cot_ghi_chu_xu_ly] != ''), df[self.cot_ghi_chu_xu_ly] + '; Bổ sung phí cho BE', df[self.cot_ghi_chu_xu_ly]))
        return df

    def kiem_tra_chenh_lech_phi(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp chênh lệch phí thu giữa FE và BE.

        Args:
            df (pd.DataFrame): DataFrame.

        Returns:
            pd.DataFrame: DataFrame đã được điều chỉnh cột phí và ghi chú.
        """
        dieu_kien_chenh_lech = df['Phí thu'].fillna(0) != df['BE_Tiền bao gồm thuế'].fillna(0)
        df['CL Phí-Đối Soát'] = df['BE_Tiền bao gồm thuế'].fillna(0) - df['Phí thu'].fillna(0)
        df.loc[dieu_kien_chenh_lech, self.cot_phi_dieu_chinh_fe] = df.loc[dieu_kien_chenh_lech, self.cot_phi_dieu_chinh_fe] + np.where(df.loc[dieu_kien_chenh_lech, 'Phí thu'].fillna(0) > df.loc[dieu_kien_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0), -(df.loc[dieu_kien_chenh_lech, 'Phí thu'].fillna(0) - df.loc[dieu_kien_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0)), 0)
        df.loc[dieu_kien_chenh_lech, self.cot_phi_dieu_chinh_be] = df.loc[dieu_kien_chenh_lech, self.cot_phi_dieu_chinh_be] + np.where(df.loc[dieu_kien_chenh_lech, 'Phí thu'].fillna(0) < df.loc[dieu_kien_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0), -(df.loc[dieu_kien_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0) - df.loc[dieu_kien_chenh_lech, 'Phí thu'].fillna(0)), 0)

        # Update ghi_chu_xu_ly for chênh lệch
        mask_chenh_lech = df['Phí thu'].fillna(0) != df['BE_Tiền bao gồm thuế'].fillna(0)
        df.loc[mask_chenh_lech, self.cot_ghi_chu_xu_ly] = np.where(
            df.loc[mask_chenh_lech, self.cot_ghi_chu_xu_ly] == '',
            np.where(df.loc[mask_chenh_lech, 'Phí thu'].fillna(0) > df.loc[mask_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0),
                     'FE thu thừa, cần trả lại',
                     'BE thu thiếu, cần bổ sung'),
            df.loc[mask_chenh_lech, self.cot_ghi_chu_xu_ly] + '; ' + np.where(
                df.loc[mask_chenh_lech, 'Phí thu'].fillna(0) > df.loc[mask_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0),
                'FE thu thừa, cần trả lại',
                'BE thu thiếu, cần bổ sung'
            )
        )
        return df
    
    def doi_soat(self, df_gop_chuan_hoa):
        """
        Quy trình đối soát phí thu tổng hợp, trả về một DataFrame duy nhất
        với đầy đủ dữ liệu các bước và cột mô tả.

        Args:
            df_gop_chuan_hoa (pd.DataFrame): DataFrame đã gộp và chuẩn hóa.

        Returns:
            pd.DataFrame: DataFrame duy nhất đã được đánh dấu, điều chỉnh
                        và có cột mô tả các bước.
        """
        try:
            df = df_gop_chuan_hoa.copy()
            df[self.cot_buoc_doi_soat] = 'Dữ liệu ban đầu'
            df[self.cot_ket_qua_doi_soat] = 'Khớp'
            df[self.cot_nguyen_nhan_doi_soat] = None
            df[self.cot_thu_phi_nguoi] = False
            df[self.cot_chi_co_be] = False

            # Bước 1: Xác định xe không thu phí và đánh dấu
            df = self.tach_nhom_xe_ko_thu_phi(df)
            df.loc[df[self.cot_xe_khong_thu_phi], self.cot_buoc_doi_soat] = 'Xác định xe không thu phí'
            df.loc[df[self.cot_xe_khong_thu_phi], self.cot_ket_qua_doi_soat] = 'Không thu phí'
            df.loc[df[self.cot_xe_khong_thu_phi], self.cot_nguyen_nhan_doi_soat] = 'Không thu phí phí/ưu tiên'

            # Bước 2: Thêm cột trạm dựa trên làn
            df['Trạm'] = df['Làn chuẩn'].apply(self._get_tram_from_lane)

            # Bước 3: Kiểm tra và đánh dấu lỗi đọc nhiều lượt
            df = self.kiem_tra_doc_nhieu_luot(df)
            df.loc[df[self.cot_loi_doc_nhieu_lan], self.cot_buoc_doi_soat] = 'Kiểm tra đọc nhiều lượt'
            df.loc[df[self.cot_loi_doc_nhieu_lan], self.cot_ket_qua_doi_soat] = 'Nghi vấn đọc nhiều lượt'
            df.loc[df[self.cot_loi_doc_nhieu_lan], self.cot_nguyen_nhan_doi_soat] = 'Thời gian gần giữa các lần qua trạm'

            # Bước 4: Kiểm tra và đánh dấu thu phí nguội
            df_thu_phi_nguoi = self.kiem_tra_thu_phi_nguoi(df[~df[self.cot_xe_khong_thu_phi]].copy())
            df.update(df_thu_phi_nguoi)
            df.loc[df[self.cot_thu_phi_nguoi], self.cot_buoc_doi_soat] = 'Kiểm tra thu phí nguội'
            df.loc[df[self.cot_thu_phi_nguoi], self.cot_ket_qua_doi_soat] = 'Nghi vấn thu phí nguội'
            df.loc[df[self.cot_thu_phi_nguoi], self.cot_nguyen_nhan_doi_soat] = 'BE có phí, FE không có phí'

            # Bước 5: Kiểm tra và đánh dấu trường hợp FE có BE không
            df_fe_co_be_khong = self.kiem_tra_fe_co_be_khong(df[~df[self.cot_xe_khong_thu_phi] & ~df[self.cot_thu_phi_nguoi]].copy())
            df.update(df_fe_co_be_khong)
            df.loc[df[self.cot_chi_co_be], self.cot_buoc_doi_soat] = 'Kiểm tra FE có BE không'
            df.loc[df[self.cot_chi_co_be], self.cot_ket_qua_doi_soat] = 'Chỉ có giao dịch BE'
            df.loc[df[self.cot_chi_co_be], self.cot_nguyen_nhan_doi_soat] = 'FE có phí, BE không có phí'

            # Bước 6: Kiểm tra và đánh dấu chênh lệch phí
            # mask_for_chenh_lech = ~(df[self.cot_xe_khong_thu_phi] | df[self.cot_thu_phi_nguoi] | df[self.cot_chi_co_be])
            mask_for_chenh_lech = ~ (df[self.cot_xe_khong_thu_phi] | df[self.cot_thu_phi_nguoi] | df[self.cot_chi_co_be])
            df_chenh_lech_phi = self.kiem_tra_chenh_lech_phi(df[mask_for_chenh_lech].copy())
            df.update(df_chenh_lech_phi)
            dieu_kien_chenh_lech = (df['Phí điều chỉnh FE'] != 0) | (df['Phí điều chỉnh BE'] != 0)
            df.loc[dieu_kien_chenh_lech, self.cot_buoc_doi_soat] = 'Kiểm tra chênh lệch phí'
            df.loc[dieu_kien_chenh_lech, self.cot_ket_qua_doi_soat] = 'Chênh lệch phí'
            df.loc[dieu_kien_chenh_lech, self.cot_nguyen_nhan_doi_soat] = 'Khác phí thu giữa FE và BE'


        except Exception as e:
            print('Lỗi file doi_soat, class DoiSoatPhi', e)

        return df
    
    # Đưa vào dic_ecxcel
    def _select_columns(self, df, columns):
        """
        Chọn các cột cụ thể từ DataFrame nếu chúng tồn tại.

        Args:
            df (pd.DataFrame): DataFrame đầu vào.
            columns (list): Danh sách tên các cột cần chọn.

        Returns:
            pd.DataFrame: DataFrame chỉ chứa các cột đã chọn (nếu có).
        """
        existing_columns = [col for col in columns if col in df.columns]
        return df[existing_columns].copy()

    def doi_soat_va_phan_loai(self, df):
        """
        Phân loại DataFrame đã đối soát thành các DataFrame con
        dựa trên kết quả và các bước đối soát, chỉ giữ lại các cột liên quan.

        Args:
            df_da_doi_soat (pd.DataFrame): DataFrame đã trải qua quy trình đối soát.

        Returns:
            dict: Dictionary chứa các DataFrame con đã được phân loại,
                  mỗi DataFrame con chỉ chứa các cột liên quan.
        """
       
        df_da_doi_soat = self.doi_soat(df.copy())
        
        results = {}

        # Định nghĩa các cột cần thiết cho từng bảng
        cols_khong_thu_phi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Loại vé chuẩn', self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_doc_nhieu_lan = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', self.cot_so_lan_qua_tram, self.cot_thoi_gian_cach_lan_truoc, 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_phi_nguoi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_chi_co_be = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_chenh_lech_phi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', 'CL Phí-Đối Soát', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_khop = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_ket_qua_doi_soat]
        
        # cols_bao_cao = df_da_doi_soat.columns.tolist() # Lấy tất cả các cột cho báo cáo tổng hợp
        # cols_bao_cao = ['Mã giao dịch chuẩn', 'Biển số chuẩn', 'Mã thẻ', 'Phí thu', 'Ngày giờ', 'BE_Biển số xe', 'BE_Số etag', 'BE_Tiền bao gồm thuế', 'BE_Thời gian qua trạm',  'Chênh lệch (Phí thu)', 'Loại vé chuẩn', 'Bước đối soát', 'Kết quả đối soát', 'Nguyên nhân đối soát', 'Thu nguội', 'Giao dịch chỉ có BE', 'Xe không thu phí', 'Trạm', 'Làn chuẩn','Số lần qua trạm', 'Thời gian chuẩn', 'K/C 2 lần đọc (phút)', 'Lỗi Anten', 'Phí điều chỉnh FE', 'Phí điều chỉnh BE', 'Ghi chú xử lý']
        cols_bao_cao = ['Mã giao dịch chuẩn', 'Biển số chuẩn', 'Mã thẻ', 'BE_Số etag','Phí thu', 'BE_Tiền bao gồm thuế',  'Loại vé chuẩn', 'Thu nguội', 'Giao dịch chỉ có BE', 'Xe không thu phí','Lỗi Anten', 'Trạm', 'Làn chuẩn','Số lần qua trạm', 'Thời gian chuẩn', 'K/C 2 lần đọc (phút)',  'Phí điều chỉnh FE', 'Phí điều chỉnh BE', 'Ghi chú xử lý']

        # 1. Sheets dành riênng cho VunghiXuan ------------------ ***
        results['VuNghiXuan'] = df_da_doi_soat

        # 1. Xe không thu phí
        df_khong_thu_phi = df_da_doi_soat[df_da_doi_soat[self.cot_xe_khong_thu_phi]].copy()
        results['DoiSoat-KhongThuPhi'] = self._select_columns(df_khong_thu_phi, cols_khong_thu_phi)

        # 1. Xe trả phí
        dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['Miễn giảm 100%', 'UT toàn quốc', 'Miễn giảm ĐP', 'Vé quý thường', 'Vé tháng thường'])
        dieu_kien_phi_nan_hoac_khong = (df['Phí thu'].isna() | (df['Phí thu'] == 0)) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))
        df_tra_phi = df[~(dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong)].copy()
        results['XeTraPhi'] = self._select_columns(df_tra_phi, cols_khong_thu_phi) 

        # 2. Nghi vấn đọc nhiều lần
        df_doc_nhieu_luot = df_da_doi_soat[df_da_doi_soat[self.cot_loi_doc_nhieu_lan]].copy()
        results['DoiSoat-DocNhieuLan'] = self._select_columns(df_doc_nhieu_luot, cols_doc_nhieu_lan)

        # 3. Nghi vấn thu phí nguội
        df_thu_phi_nguoi = df_da_doi_soat[df_da_doi_soat[self.cot_thu_phi_nguoi]].copy()
        results['DoiSoat-PhiNguoi'] = self._select_columns(df_thu_phi_nguoi, cols_phi_nguoi)

        # 4. Giao dịch chỉ có BE
        df_chi_co_be = df_da_doi_soat[df_da_doi_soat[self.cot_chi_co_be]].copy()
        results['DoiSoat-ChiCo-FE'] = self._select_columns(df_chi_co_be, cols_chi_co_be)

        # 5. Chênh lệch phí
        dieu_kien_chenh_lech = (df_da_doi_soat['Phí điều chỉnh FE'] != 0) | (df_da_doi_soat['Phí điều chỉnh BE'] != 0)
        df_chenh_lech_phi = df_da_doi_soat[dieu_kien_chenh_lech].copy()
        results['DoiSoat-GiaThuPhi'] = self._select_columns(df_chenh_lech_phi, cols_chenh_lech_phi)

        # 6. Giao dịch khớp (những giao dịch không rơi vào các trường hợp lỗi trên)
        dieu_kien_khop = ~(df_da_doi_soat[self.cot_xe_khong_thu_phi] | df_da_doi_soat[self.cot_loi_doc_nhieu_lan] | df_da_doi_soat[self.cot_thu_phi_nguoi] | df_da_doi_soat[self.cot_chi_co_be] | dieu_kien_chenh_lech)
        df_khop = df_da_doi_soat[dieu_kien_khop].copy()
        results['DoiSoat-Khop'] = self._select_columns(df_khop, cols_khop)

        # 7. Báo cáo tổng hợp (tất cả dữ liệu đã đối soát)
        results['BaoCaoTong_DoiSoat'] = self._select_columns(df_da_doi_soat, cols_bao_cao)


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
#         self.cot_thoi_gian_cach_lan_truoc = 'K/C 2 lần đọc (phút)'
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
#                    - df_khong_thu_phi: DataFrame chứa các xe có vé miễn phí/ưu tiên
#                                          và phí thu BE/FE là NaN hoặc = 0.
#                    - df_tra_phi: DataFrame chứa các xe không thuộc nhóm trên.
#         """
#         dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['Miễn giảm 100%', 'UT toàn quốc', 'Miễn giảm ĐP', 'Vé quý thường', 'Vé tháng thường'])
#         dieu_kien_phi_nan_hoac_khong = (df['Phí thu'].isna() | (df['Phí thu'] == 0)) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))

#         df_khong_thu_phi = df[dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong].copy()
#         df_tra_phi = df[~(dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong)].copy()

#         return df_khong_thu_phi, df_tra_phi

#     def _get_tram_from_lane(self, lane):
#         """Trích xuất tên trạm từ tên làn."""
#         if pd.isna(lane):
#             return None
#         for tram, lanes in self.mapping_lane.items():
#             for l in lanes:
#                 if str(l) in str(lane):
#                     return tram
#         return None

    # def kiem_tra_doc_nhieu_luot(self, df):
    #     """
    #     Kiểm tra và đánh dấu các trường hợp nghi vấn đọc nhiều lượt do anten.

    #     Args:
    #         df (pd.DataFrame): DataFrame chứa các xe trả phí.

    #     Returns:
    #         pd.DataFrame: DataFrame chứa các trường hợp nghi vấn đọc nhiều lượt.
    #     """
    #     df_nhieu_luot = df.copy()
    #     df_nhieu_luot[self.cot_so_lan_qua_tram] = df_nhieu_luot.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('count')
    #     df_nhieu_luot_filtered = df_nhieu_luot[df_nhieu_luot[self.cot_so_lan_qua_tram] >= 2].sort_values(['Biển số chuẩn', 'Thời gian chuẩn']).copy()
    #     df_nhieu_luot_filtered['Trạm'] = df_nhieu_luot_filtered['Làn chuẩn'].apply(self._get_tram_from_lane)
    #     df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] = df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].diff().dt.total_seconds() / 60
    #     df_nhieu_luot_filtered[self.cot_ket_qua] = None
    #     df_nhieu_luot_filtered[self.cot_nguyen_nhan] = None
    #     df_nhieu_luot_filtered[self.cot_phi_dieu_chinh_fe] = 0
    #     df_nhieu_luot_filtered[self.cot_phi_dieu_chinh_be] = 0
    #     df_nhieu_luot_filtered[self.cot_ghi_chu_xu_ly] = None

    #     dieu_kien_cung_lan = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Làn chuẩn'].shift() == df_nhieu_luot_filtered['Làn chuẩn']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0))
    #     df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_ket_qua] = 'Nghi vấn đọc nhiều lượt (cùng làn)'
    #     df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_nguyen_nhan] = 'Thời gian gần, cùng làn và có phí'
    #     df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_phi_dieu_chinh_fe] = -df_nhieu_luot_filtered['Phí thu']
    #     df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_phi_dieu_chinh_be] = -df_nhieu_luot_filtered['BE_Tiền bao gồm thuế']
    #     df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, self.cot_ghi_chu_xu_ly] = 'Trả lại phí do đọc trùng'

    #     dieu_kien_khac_lan_cung_tram = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Trạm'].shift() == df_nhieu_luot_filtered['Trạm']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0)) & (df_nhieu_luot_filtered[self.cot_ket_qua].isna())
    #     df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_ket_qua] = 'Nghi vấn đọc nhiều lượt (khác làn cùng trạm)'
    #     df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_nguyen_nhan] = 'Thời gian gần, khác làn cùng trạm và có phí'
    #     # Logic điều chỉnh phí cho trường hợp khác làn cùng trạm cần được xem xét cụ thể hơn
    #     # Ví dụ: Lấy phí của giao dịch đầu tiên làm chuẩn, các giao dịch sau điều chỉnh về 0 hoặc theo mức phí đúng
    #     df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_phi_dieu_chinh_fe] = -df_nhieu_luot_filtered['Phí thu'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0)
    #     df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_phi_dieu_chinh_be] = -df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0)
    #     df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, self.cot_ghi_chu_xu_ly] = 'Cần kiểm tra, điều chỉnh phí do đọc nhiều lượt'

    #     return df_nhieu_luot_filtered[~df_nhieu_luot_filtered[self.cot_ket_qua].isna()].copy()

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
#         dieu_kien_chenh_lech = df_chenh_lech['Phí thu'].fillna(0) != df_chenh_lech['BE_Tiền bao gồm thuế'].fillna(0)
#         df_chenh_lech_phi = df_chenh_lech[dieu_kien_chenh_lech].copy()
#         df_chenh_lech_phi[self.cot_ket_qua] = 'Chênh lệch phí'
#         df_chenh_lech_phi[self.cot_nguyen_nhan] = 'Khác phí thu giữa FE và BE'
#         df_chenh_lech_phi[self.cot_phi_dieu_chinh_fe] = np.where(df_chenh_lech_phi['Phí thu'].fillna(0) > df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0), -(df_chenh_lech_phi['Phí thu'].fillna(0) - df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0)), 0)
#         df_chenh_lech_phi[self.cot_phi_dieu_chinh_be] = np.where(df_chenh_lech_phi['Phí thu'].fillna(0) < df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0), -(df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0) - df_chenh_lech_phi['Phí thu'].fillna(0)), 0)
#         df_chenh_lech_phi[self.cot_ghi_chu_xu_ly] = np.where(df_chenh_lech_phi['Phí thu'].fillna(0) > df_chenh_lech_phi['BE_Tiền bao gồm thuế'].fillna(0), 'FE thu thừa, cần trả lại', 'BE thu thiếu, cần bổ sung')
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
#         # df_chenh_lech_phi = self.kiem_tra_chenh_lech_phi(df_tra_phi.copy())

#         df_khop = df_tra_phi[~df_tra_phi.index.isin(df_doc_nhieu_luot.index) &
#                              ~df_tra_phi.index.isin(df_thu_phi_nguoi.index) &
#                              ~df_tra_phi.index.isin(df_fe_co_be_khong.index) ].copy() #&~df_tra_phi.index.isin(df_chenh_lech_phi.index)

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
#             # df_chenh_lech_phi,
#             df_khop
#         ], ignore_index=True)

#         results = {
#             'XeTraPhi': df_khong_thu_phi,
#             'DoiSoat-KhongThuPhi': df_khong_thu_phi,
#             'DoiSoat-DocNhieuLan': df_doc_nhieu_luot,
#             'DoiSoat-PhiNguoi': df_thu_phi_nguoi,
#             'DoiSoat-ChiCo-FE': df_fe_co_be_khong,
#             # 'DoiSoat-GiaThuPhi': df_chenh_lech_phi,
#             'DoiSoat-Khop': df_khop,
#             'BaoCaoTong_DoiSoat': df_bao_cao
#         }

#         return results

