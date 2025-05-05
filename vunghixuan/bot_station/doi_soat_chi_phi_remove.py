import pandas as pd
import numpy as np
from vunghixuan.bot_station.classify_car_by_fee import ChecKTurns


class DoiSoatPhi:
    def __init__(self):
        # self.mapping_lane = {
        #     '2A': {'in': ['10', '11'], 'out': ['12'], 'tram': 'Đồng Khởi'},
        #     '1A': {'in': ['1', '2'], 'out': ['3', '4'], 'tram': 'ĐT768_1A'},
        #     '3B': {'in': ['7', '8', '9'], 'out': [], 'tram': 'ĐT768_3B'},
        #     '3A': {'in': [], 'out': ['5', '6'], 'tram': 'ĐT768_3A'}
        # }
        self.mapping_lane = {
            '2A': {'in': ['Làn 10', 'Làn 11'], 'out': ['Làn 12'], 'tram': 'Đồng Khởi_2A'},
            '1A': {'in': ['Làn 1', 'Làn 2'], 'out': ['Làn 3', 'Làn 4'], 'tram': 'ĐT768_1A'},
            '3B': {'in': ['Làn 7', 'Làn 8', 'Làn 9'], 'out': [], 'tram': 'ĐT768_3B'},
            '3A': {'in': [], 'out': ['Làn 5', 'Làn 6'], 'tram': 'ĐT768_3A'}
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
        self.cot_luot_di_hop_ly = 'Lượt đi hợp lý'  # Khởi tạo biến này
        self.cot_luot_di_bat_thuong = 'Lượt đi bất thường'

    def tach_nhom_xe_ko_thu_phi(self, df):
        """
        Đánh dấu các xe không thu phí trực tiếp vào DataFrame.
        """
        dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['UT toàn quốc', 'Miễn giảm 100%', 'Miễn giảm ĐP', 'Miễn phí quay đầu', 'Miễn phí liên trạm', 'Vé tháng thường'])
        dieu_kien_phi_nan_hoac_khong = (df['Phí thu'].isna() | (df['Phí thu'] == 0)) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))
        df[self.cot_xe_khong_thu_phi] = dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong
        return df

    def _get_tram_from_lane(self, lane):
        """Trích xuất tên trạm từ tên làn, xử lý giá trị NaN."""
        if pd.isna(lane):
            return None
        lane_str = str(lane).strip()
        for tram_code, lane_info in self.mapping_lane.items():
            for type in ['in', 'out']:
                if lane_str in [l.strip() for l in lane_info.get(type, [])]:
                    return lane_info['tram']
        return None

    def _get_lane_type(self, lane):
        """Xác định loại làn (in/out) từ tên làn, xử lý giá trị NaN."""
        if pd.isna(lane):
            return None
        lane_str = str(lane).strip()
        for tram_code, lane_info in self.mapping_lane.items():
            if lane_str in [l.strip() for l in lane_info.get('in', [])]:
                return 'in'
            if lane_str in [l.strip() for l in lane_info.get('out', [])]:
                return 'out'
        return None

    def kiem_tra_luot_di(self, df):
        """
        Kiểm tra lượt đi hợp lý và bất thường bằng cách so sánh tất cả các cặp giao dịch
        trong mỗi group (theo biển số xe). Xử lý các trường hợp quét trùng hoặc đọc đồng thời.
        Chỉ thêm ghi chú và lý do nếu chúng chưa tồn tại.

        Args:
            df (pd.DataFrame): DataFrame chứa dữ liệu giao dịch đã được gộp và chuẩn hóa,
                               với các cột 'Biển số chuẩn', 'Thời gian chuẩn', 'Làn chuẩn',
                               'Phí thu', 'BE_Tiền bao gồm thuế', và 'Ghi chú xử lý'.

        Returns:
            tuple: Một tuple chứa:
                - df (pd.DataFrame): DataFrame đã được cập nhật với các cột
                  'Lượt đi hợp lý', 'Lượt đi bất thường', và 'Ghi chú xử lý'.
                - df_luot_di_hop_ly (pd.DataFrame): DataFrame chứa chỉ các giao dịch
                  được đánh dấu là lượt đi hợp lý.
        """
        try:
            df[self.cot_luot_di_hop_ly] = False
            df[self.cot_luot_di_bat_thuong] = False
            df[self.cot_ghi_chu_xu_ly] = df[self.cot_ghi_chu_xu_ly].fillna('')
            thoi_gian_hop_ly = pd.Timedelta(minutes=10)
            thoi_gian_toi_da_cho_luot_di_ngan = pd.Timedelta(minutes=10)
            thoi_gian_quet_trung = pd.Timedelta(seconds=300)  # Tăng lên 5 phút (300 giây)

            # Khởi tạo các cột điều chỉnh nếu chưa tồn tại
            if self.cot_phi_dieu_chinh_fe not in df.columns:
                df[self.cot_phi_dieu_chinh_fe] = 0.0
            if self.cot_phi_dieu_chinh_be not in df.columns:
                df[self.cot_phi_dieu_chinh_be] = 0.0
            if 'Lý do điều chỉnh' not in df.columns:
                df['Lý do điều chỉnh'] = ''
            if 'Trạng thái xử lý' not in df.columns:
                df['Trạng thái xử lý'] = 'Chưa xử lý'
            if 'Người xử lý' not in df.columns:
                df['Người xử lý'] = ''
            if 'Thời gian xử lý' not in df.columns:
                df['Thời gian xử lý'] = pd.NaT
            if self.cot_so_lan_qua_tram not in df.columns:
                df[self.cot_so_lan_qua_tram] = 0
            if self.cot_thoi_gian_cach_lan_truoc not in df.columns:
                df[self.cot_thoi_gian_cach_lan_truoc] = np.nan
            if self.cot_loi_doc_nhieu_lan not in df.columns:
                df[self.cot_loi_doc_nhieu_lan] = False

            for bien_so, group in df.groupby('Biển số chuẩn'):
                group_sorted = group.sort_values('Thời gian chuẩn').reset_index(drop=True)
                n_rows = len(group_sorted)
                if n_rows >= 2:
                    for i in range(n_rows):
                        for j in range(i + 1, n_rows):
                            giao_dich_1 = group_sorted.iloc[i]
                            giao_dich_2 = group_sorted.iloc[j]

                            time_diff = giao_dich_2['Thời gian chuẩn'] - giao_dich_1['Thời gian chuẩn']
                            tram_1 = self._get_tram_from_lane(str(giao_dich_1['Làn chuẩn']))
                            tram_2 = self._get_tram_from_lane(str(giao_dich_2['Làn chuẩn']))
                            lane_type_1 = self._get_lane_type(str(giao_dich_1['Làn chuẩn']))
                            lane_type_2 = self._get_lane_type(str(giao_dich_2['Làn chuẩn']))
                            phi_1 = giao_dich_1['Phí thu'] if pd.notna(giao_dich_1['Phí thu']) else giao_dich_1['BE_Tiền bao gồm thuế']
                            phi_2 = giao_dich_2['Phí thu'] if pd.notna(giao_dich_2['Phí thu']) else giao_dich_2['BE_Tiền bao gồm thuế']

                            # Xử lý quét trùng (cùng trạm, thời gian ngắn)
                            if (pd.isna(phi_1) == pd.isna(phi_2)) and (
                                    (pd.isna(phi_1) or phi_1 == phi_2) or
                                    (lane_type_1 in ['in', None] and lane_type_2 in ['out', None]) or
                                    (lane_type_1 in ['out', None] and lane_type_2 in ['in', None])):
                                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_luot_di_bat_thuong] = True
                                ghi_chu_quet_trung = '; Nghi vấn quét trùng anten'
                                if ghi_chu_quet_trung not in df.loc[giao_dich_1.name, self.cot_ghi_chu_xu_ly]:
                                    df.loc[giao_dich_1.name, self.cot_ghi_chu_xu_ly] += ghi_chu_quet_trung
                                if ghi_chu_quet_trung not in df.loc[giao_dich_2.name, self.cot_ghi_chu_xu_ly]:
                                    df.loc[giao_dich_2.name, self.cot_ghi_chu_xu_ly] += ghi_chu_quet_trung
                                ly_do_quet_trung = 'Quét trùng anten'
                                if ly_do_quet_trung not in df.loc[giao_dich_1.name, 'Lý do điều chỉnh']:
                                    df.loc[giao_dich_1.name, 'Lý do điều chỉnh'] = ly_do_quet_trung
                                if ly_do_quet_trung not in df.loc[giao_dich_2.name, 'Lý do điều chỉnh']:
                                    df.loc[giao_dich_2.name, 'Lý do điều chỉnh'] = ly_do_quet_trung
                                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_phi_dieu_chinh_fe] = 0.0
                                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_phi_dieu_chinh_be] = 0.0
                                df.loc[[giao_dich_1.name, giao_dich_2.name], 'Trạng thái xử lý'] = 'Chưa xử lý'

                            # Kiểm tra lượt đi hợp lý
                            tram_vao = tram_1
                            tram_ra = tram_2
                            lane_vao_type = lane_type_1
                            lane_ra_type = lane_type_2
                            phi_vao = phi_1 > 0
                            phi_ra = phi_2 > 0

                            if tram_vao == tram_ra and time_diff > thoi_gian_hop_ly and ((lane_vao_type in ['in', None] and lane_ra_type in ['out', None]) or
                                     (lane_vao_type in ['out', None] and lane_ra_type in ['in', None])) and (phi_vao or phi_1 is not None) and (phi_ra or phi_2 is not None):
                                df.loc[giao_dich_1.name, self.cot_luot_di_hop_ly] = True
                                df.loc[giao_dich_2.name, self.cot_luot_di_hop_ly] = True
                            # Kiểm tra lượt đi bất thường (thời gian ngắn, cùng trạm)
                            elif time_diff <= thoi_gian_toi_da_cho_luot_di_ngan and tram_vao == tram_ra and (phi_vao or phi_1 is not None):
                                ghi_chu_quay_dau = '; Nghi vấn quay đầu có phí (thời gian ngắn)'
                                if ghi_chu_quay_dau not in df.loc[giao_dich_1.name, self.cot_ghi_chu_xu_ly]:
                                    df.loc[giao_dich_1.name, self.cot_ghi_chu_xu_ly] += ghi_chu_quay_dau
                                if ghi_chu_quay_dau not in df.loc[giao_dich_2.name, self.cot_ghi_chu_xu_ly]:
                                    df.loc[giao_dich_2.name, self.cot_ghi_chu_xu_ly] += ghi_chu_quay_dau
                                ly_do_quay_dau = 'Quay đầu có phí'
                                if ly_do_quay_dau not in df.loc[giao_dich_1.name, 'Lý do điều chỉnh']:
                                    df.loc[giao_dich_1.name, 'Lý do điều chỉnh'] = ly_do_quay_dau
                                if ly_do_quay_dau not in df.loc[giao_dich_2.name, 'Lý do điều chỉnh']:
                                    df.loc[giao_dich_2.name, 'Lý do điều chỉnh'] = ly_do_quay_dau
                                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_luot_di_bat_thuong] = True
                                df.loc[[giao_dich_1.name, giao_dich_2.name], 'Trạng thái xử lý'] = 'Chưa xử lý'
                            elif time_diff <= thoi_gian_toi_da_cho_luot_di_ngan and tram_vao == tram_ra and lane_vao_type is not None and lane_ra_type is not None and lane_vao_type != lane_ra_type and (phi_vao or phi_1 is not None):
                                ghi_chu_lan_khac = f'; Nghi vấn vào {lane_vao_type} ra {lane_ra_type} phí (thời gian ngắn)'
                                if ghi_chu_lan_khac not in df.loc[giao_dich_1.name, self.cot_ghi_chu_xu_ly]:
                                    df.loc[giao_dich_1.name, self.cot_ghi_chu_xu_ly] += ghi_chu_lan_khac
                                if ghi_chu_lan_khac not in df.loc[giao_dich_2.name, self.cot_ghi_chu_xu_ly]:
                                    df.loc[giao_dich_2.name, self.cot_ghi_chu_xu_ly] += ghi_chu_lan_khac
                                ly_do_lan_khac = f'Vào {lane_vao_type} ra {lane_ra_type} phí'
                                if ly_do_lan_khac not in df.loc[giao_dich_1.name, 'Lý do điều chỉnh']:
                                    df.loc[giao_dich_1.name, 'Lý do điều chỉnh'] = ly_do_lan_khac
                                if ly_do_lan_khac not in df.loc[giao_dich_2.name, 'Lý do điều chỉnh']:
                                    df.loc[giao_dich_2.name, 'Lý do điều chỉnh'] = ly_do_lan_khac
                                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_luot_di_bat_thuong] = True
                                df.loc[[giao_dich_1.name, giao_dich_2.name], 'Trạng thái xử lý'] = 'Chưa xử lý'

        except Exception as e:
            print('Lỗi hàm kiem_tra_luot_di', e)

        return df, df[df[self.cot_luot_di_hop_ly]].copy()

    def kiem_tra_doc_nhieu_luot(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp đọc nhiều lượt (lỗi Anten).
        """
        df[self.cot_so_lan_qua_tram] = df.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('count')
        df[self.cot_thoi_gian_cach_lan_truoc] = df.groupby('Biển số chuẩn')['Thời gian chuẩn'].diff().dt.total_seconds() / 60
        dieu_kien_doc_nhieu_lan = (df[self.cot_so_lan_qua_tram] > 2) & (df[self.cot_thoi_gian_cach_lan_truoc].fillna(0) < 1) & (df['Phí thu'].fillna(0) == 0) & (df['BE_Tiền bao gồm thuế'].fillna(0) == 0)
        df[self.cot_loi_doc_nhieu_lan] = dieu_kien_doc_nhieu_lan
        df[self.cot_ghi_chu_xu_ly] = np.where(dieu_kien_doc_nhieu_lan & (df[self.cot_ghi_chu_xu_ly] == ''), 'Nghi vấn lỗi đọc nhiều lần',
                                        np.where(dieu_kien_doc_nhieu_lan & (df[self.cot_ghi_chu_xu_ly] != ''), df[self.cot_ghi_chu_xu_ly] + '; Nghi vấn lỗi đọc nhiều lần', df[self.cot_ghi_chu_xu_ly]))
        return df

    def kiem_tra_thu_phi_nguoi(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp nghi vấn thu phí nguội.
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
        Kiểm tra và đánh dấu các trường hợp FE có phí, BE không có.
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
        Quy trình đối soát phí thu tổng hợp.
        """
        try:
            df = df_gop_chuan_hoa.copy()
            df[self.cot_buoc_doi_soat] = 'Dữ liệu ban đầu'
            df[self.cot_ket_qua_doi_soat] = 'Khớp'
            df[self.cot_nguyen_nhan_doi_soat] = None
            df[self.cot_luot_di_hop_ly] = False
            df[self.cot_luot_di_bat_thuong] = False
            df[self.cot_thu_phi_nguoi] = False
            df[self.cot_chi_co_be] = False
            df[self.cot_ghi_chu_xu_ly] = ''
            if self.cot_loi_doc_nhieu_lan in df.columns:
                df = df.drop(columns=[self.cot_loi_doc_nhieu_lan])
            df[self.cot_loi_doc_nhieu_lan] = False # Đảm bảo cột này được khởi tạo (nếu cần cho các bước sau)

            # Bước 1: Xác định xe không thu phí
            df = self.tach_nhom_xe_ko_thu_phi(df)
            df_xe_khong_tra_phi = df[df[self.cot_xe_khong_thu_phi]].copy()
            df_xe_tra_phi = df[~df[self.cot_xe_khong_thu_phi]].copy()

            df_xe_khong_tra_phi.loc[:, self.cot_buoc_doi_soat] = 'Xác định xe không thu phí'
            df_xe_khong_tra_phi.loc[:, self.cot_ket_qua_doi_soat] = 'Không thu phí'
            df_xe_khong_tra_phi.loc[:, self.cot_nguyen_nhan_doi_soat] = 'Không thu phí phí/ưu tiên'

            # Bước 2: Thêm cột trạm cho df_xe_tra_phi
            df_xe_tra_phi['Trạm'] = df_xe_tra_phi['Làn chuẩn'].apply(lambda x: self._get_tram_from_lane(str(x)) if isinstance(x, str) else None)

            # Bước 3: Kiểm tra lượt đi hợp lý và bất thường cho df_xe_tra_phi
            turns = ChecKTurns()
            df_xe_tra_phi = turns.kiem_tra_luot_di(df_xe_tra_phi.copy())
            # print()

            # df_xe_tra_phi, df_luot_hop_ly_tra_phi = self.kiem_tra_luot_di(df_xe_tra_phi)
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_buoc_doi_soat] = 'Kiểm tra lượt đi bất thường'
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_ket_qua_doi_soat] = 'Nghi vấn lượt đi bất thường'
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_nguyen_nhan_doi_soat] = df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_ghi_chu_xu_ly]
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_hop_ly], self.cot_buoc_doi_soat] = 'Xác định lượt đi hợp lý'
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_hop_ly], self.cot_ket_qua_doi_soat] = 'Lượt đi hợp lý'

            # Bỏ Bước 4: Kiểm tra đọc nhiều lượt

            # # Bước 5: Kiểm tra thu phí nguội (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
            # mask_phi_nguoi_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
            # df_xe_tra_phi = self.kiem_tra_thu_phi_nguoi(df_xe_tra_phi[mask_phi_nguoi_tra_phi].copy())
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_thu_phi_nguoi], self.cot_buoc_doi_soat] = 'Kiểm tra thu phí nguội'
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_thu_phi_nguoi], self.cot_ket_qua_doi_soat] = 'Nghi vấn thu phí nguội'

            # # Bước 6: Kiểm tra FE có BE không (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
            # mask_fe_co_be_khong_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
            # df_xe_tra_phi = self.kiem_tra_fe_co_be_khong(df_xe_tra_phi[mask_fe_co_be_khong_tra_phi].copy())
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_chi_co_be], self.cot_buoc_doi_soat] = 'Kiểm tra FE có BE không'
            # df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_chi_co_be], self.cot_ket_qua_doi_soat] = 'Chỉ có giao dịch FE'

            # # Bước 7: Kiểm tra chênh lệch phí (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
            # mask_chenh_lech_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
            # df_xe_tra_phi = self.kiem_tra_chenh_lech_phi(df_xe_tra_phi[mask_chenh_lech_tra_phi].copy())
            # dieu_kien_chenh_lech_tra_phi = (df_xe_tra_phi['Phí điều chỉnh FE'] != 0) | (df_xe_tra_phi['Phí điều chỉnh BE'] != 0)
            # df_xe_tra_phi.loc[dieu_kien_chenh_lech_tra_phi, self.cot_buoc_doi_soat] = 'Kiểm tra chênh lệch phí'
            # df_xe_tra_phi.loc[dieu_kien_chenh_lech_tra_phi, self.cot_ket_qua_doi_soat] = 'Chênh lệch phí'

            # df_da_doi_soat = pd.concat([df_xe_khong_tra_phi, df_xe_tra_phi], ignore_index=True)

        except Exception as e:
            print('Lỗi ham doi_soat', e)

        # return  df_xe_tra_phi[df_xe_tra_phi[self.cot_luot_di_hop_ly]].copy(), df_xe_khong_tra_phi
        return df_xe_khong_tra_phi, df_xe_tra_phi
    
    # def doi_soat(self, df_gop_chuan_hoa):
    #     """
    #     Quy trình đối soát phí thu tổng hợp.
    #     """
    #     try:
    #         df = df_gop_chuan_hoa.copy()
    #         df[self.cot_buoc_doi_soat] = 'Dữ liệu ban đầu'
    #         df[self.cot_ket_qua_doi_soat] = 'Khớp'
    #         df[self.cot_nguyen_nhan_doi_soat] = None
    #         df[self.cot_luot_di_hop_ly] = False
    #         df[self.cot_luot_di_bat_thuong] = False
    #         df[self.cot_thu_phi_nguoi] = False
    #         df[self.cot_chi_co_be] = False
    #         df[self.cot_ghi_chu_xu_ly] = ''
    #         df[self.cot_loi_doc_nhieu_lan] = False # Đảm bảo cột này được khởi tạo

    #         # Bước 1: Xác định xe không thu phí
    #         df = self.tach_nhom_xe_ko_thu_phi(df)
    #         df_xe_khong_tra_phi = df[df[self.cot_xe_khong_thu_phi]].copy()
    #         df_xe_tra_phi = df[~df[self.cot_xe_khong_thu_phi]].copy()

    #         df_xe_khong_tra_phi.loc[:, self.cot_buoc_doi_soat] = 'Xác định xe không thu phí'
    #         df_xe_khong_tra_phi.loc[:, self.cot_ket_qua_doi_soat] = 'Không thu phí'
    #         df_xe_khong_tra_phi.loc[:, self.cot_nguyen_nhan_doi_soat] = 'Không thu phí phí/ưu tiên'

    #         # Bước 2: Thêm cột trạm cho df_xe_tra_phi
    #         df_xe_tra_phi['Trạm'] = df_xe_tra_phi['Làn chuẩn'].apply(lambda x: self._get_tram_from_lane(str(x)) if isinstance(x, str) else None)

    #         # Bước 3: Kiểm tra lượt đi hợp lý và bất thường cho df_xe_tra_phi
    #         df_xe_tra_phi, df_luot_hop_ly_tra_phi = self.kiem_tra_luot_di(df_xe_tra_phi)
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_buoc_doi_soat] = 'Kiểm tra lượt đi bất thường'
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_ket_qua_doi_soat] = 'Nghi vấn lượt đi bất thường'
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_nguyen_nhan_doi_soat] = df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_ghi_chu_xu_ly]
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_hop_ly], self.cot_buoc_doi_soat] = 'Xác định lượt đi hợp lý'
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_hop_ly], self.cot_ket_qua_doi_soat] = 'Lượt đi hợp lý'

    #         # Bước 4: Kiểm tra đọc nhiều lượt (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
    #         mask_nhieu_luot_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
    #         df_xe_tra_phi = self.kiem_tra_doc_nhieu_luot(df_xe_tra_phi[mask_nhieu_luot_tra_phi].copy())
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_loi_doc_nhieu_lan], self.cot_buoc_doi_soat] = 'Kiểm tra đọc nhiều lượt'
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_loi_doc_nhieu_lan], self.cot_ket_qua_doi_soat] = 'Nghi vấn đọc nhiều lượt'

    #         # Bước 5: Kiểm tra thu phí nguội (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
    #         mask_phi_nguoi_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
    #         df_xe_tra_phi = self.kiem_tra_thu_phi_nguoi(df_xe_tra_phi[mask_phi_nguoi_tra_phi].copy())
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_thu_phi_nguoi], self.cot_buoc_doi_soat] = 'Kiểm tra thu phí nguội'
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_thu_phi_nguoi], self.cot_ket_qua_doi_soat] = 'Nghi vấn thu phí nguội'

    #         # Bước 6: Kiểm tra FE có BE không (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
    #         mask_fe_co_be_khong_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
    #         df_xe_tra_phi = self.kiem_tra_fe_co_be_khong(df_xe_tra_phi[mask_fe_co_be_khong_tra_phi].copy())
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_chi_co_be], self.cot_buoc_doi_soat] = 'Kiểm tra FE có BE không'
    #         df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_chi_co_be], self.cot_ket_qua_doi_soat] = 'Chỉ có giao dịch FE'

    #         # Bước 7: Kiểm tra chênh lệch phí (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
    #         mask_chenh_lech_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
    #         df_xe_tra_phi = self.kiem_tra_chenh_lech_phi(df_xe_tra_phi[mask_chenh_lech_tra_phi].copy())
    #         dieu_kien_chenh_lech_tra_phi = (df_xe_tra_phi['Phí điều chỉnh FE'] != 0) | (df_xe_tra_phi['Phí điều chỉnh BE'] != 0)
    #         df_xe_tra_phi.loc[dieu_kien_chenh_lech_tra_phi, self.cot_buoc_doi_soat] = 'Kiểm tra chênh lệch phí'
    #         df_xe_tra_phi.loc[dieu_kien_chenh_lech_tra_phi, self.cot_ket_qua_doi_soat] = 'Chênh lệch phí'

    #         df_da_doi_soat = pd.concat([df_xe_khong_tra_phi, df_xe_tra_phi], ignore_index=True)

    #     except Exception as e:
    #         print('Lỗi ham doi_soat', e)

    #     return df_da_doi_soat, df_xe_tra_phi[df_xe_tra_phi[self.cot_luot_di_hop_ly]].copy(), df_xe_khong_tra_phi

    # Đưa vào dic_ecxcel
    def _select_columns(self, df, columns):
        """
        Chọn các cột cụ thể từ DataFrame nếu chúng tồn tại.
        """
        existing_columns = [col for col in columns if col in df.columns]
        return df[existing_columns].copy()

    def doi_soat_va_phan_loai(self, df):
        """
        Phân loại DataFrame đã đối soát.
        """
        df_xe_khong_tra_phi, df_xe_tra_phi = self.doi_soat(df.copy())
        results = {}

        cols_luot_hop_ly = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_ket_qua_doi_soat]
        cols_khong_thu_phi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Loại vé chuẩn', self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_luot_di_bat_thuong = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_doc_nhieu_lan = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', self.cot_so_lan_qua_tram, self.cot_thoi_gian_cach_lan_truoc, 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_phi_nguoi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_chi_co_be = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_chenh_lech_phi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', 'CL Phí-Đối Soát', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat]
        cols_khop = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_ket_qua_doi_soat]
        cols_bao_cao = ['Mã giao dịch chuẩn', 'Biển số chuẩn', 'Mã thẻ', 'BE_Số etag','Phí thu', 'BE_Tiền bao gồm thuế', 'Loại vé chuẩn', 'Thu nguội', 'Giao dịch chỉ có BE', 'Xe không thu phí','Lỗi Anten', 'Trạm', 'Làn chuẩn','Số lần qua trạm', 'Thời gian chuẩn', 'K/C 2 lần đọc (phút)', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly, self.cot_luot_di_hop_ly, self.cot_luot_di_bat_thuong, self.cot_ket_qua_doi_soat, self.cot_nguyen_nhan_doi_soat, self.cot_buoc_doi_soat]


        # 0. Sheets dành riêng cho VunghiXuan ------------------ ***
        results['VuNghiXuan'] = df_xe_tra_phi.copy() # Đảm bảo không ảnh hưởng đến df_xe_tra_phi gốc

        # 1. Sheet Xe không thu phí
        # df_khong_thu_phi = df_xe_tra_phi[df_xe_tra_phi[self.cot_xe_khong_thu_phi]].copy()
        results['DoiSoat-KhongThuPhi'] = self._select_columns(df_xe_khong_tra_phi, cols_khong_thu_phi)

        # # 2. Sheet Xe trả phí
        # dieu_kien_mien_phi_uu_tien = df_xe_tra_phi['Loại vé chuẩn'].isin(['Miễn giảm 100% trạm 2A 2B trạm 768', 'UT toàn quốc', 'Miễn phí quay đầu', 'Miễn phí liên trạm', 'Vé tháng thường'])
        # dieu_kien_phi_nan_hoac_khong = (df_xe_tra_phi['Phí thu'].isna() | (df_xe_tra_phi['Phí thu'] == 0)) & (df_xe_tra_phi['BE_Tiền bao gồm thuế'].isna() | (df_xe_tra_phi['BE_Tiền bao gồm thuế'] == 0))
        # df_tra_phi = df_xe_tra_phi[~(dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong)].copy()
        # results['XeTraPhi'] = self._select_columns(df_tra_phi, cols_khong_thu_phi) # Chọn các cột cơ bản

        # # 3. Sheet Lượt đi hợp lý (chỉ trên xe trả phí)
        # results['DoiSoat-LuotDiHopLy'] = self._select_columns(df_xe_tra_phi, cols_luot_hop_ly)

        # # 4. Sheet Lượt đi bất thường
        # df_luot_di_bat_thuong = df_xe_tra_phi[df_xe_tra_phi[self.cot_luot_di_bat_thuong]].copy()
        # results['DoiSoat-LuotDiBatThuong'] = self._select_columns(df_luot_di_bat_thuong, cols_luot_di_bat_thuong)

        # # 5. Sheet Nghi vấn đọc nhiều lần
        # df_doc_nhieu_luot = df_xe_tra_phi[df_xe_tra_phi[self.cot_loi_doc_nhieu_lan]].copy()
        # results['DoiSoat-DocNhieuLan'] = self._select_columns(df_doc_nhieu_luot, cols_doc_nhieu_lan)

        # # 6. Sheet Nghi vấn thu phí nguội
        # df_thu_phi_nguoi = df_xe_tra_phi[df_xe_tra_phi[self.cot_thu_phi_nguoi]].copy()
        # results['DoiSoat-PhiNguoi'] = self._select_columns(df_thu_phi_nguoi, cols_phi_nguoi)

        # # 7. Sheet Giao dịch chỉ có BE
        # df_chi_co_be = df_xe_tra_phi[df_xe_tra_phi[self.cot_chi_co_be]].copy()
        # results['DoiSoat-ChiCo-FE'] = self._select_columns(df_chi_co_be, cols_chi_co_be)

        # # 8. Sheet Chênh lệch phí
        # dieu_kien_chenh_lech = (df_xe_tra_phi['Phí điều chỉnh FE'] != 0) | (df_xe_tra_phi['Phí điều chỉnh BE'] != 0)
        # df_chenh_lech_phi = df_xe_tra_phi[dieu_kien_chenh_lech].copy()
        # results['DoiSoat-GiaThuPhi'] = self._select_columns(df_chenh_lech_phi, cols_chenh_lech_phi)

        # # 9. Sheet Giao dịch khớp (loại trừ xe không thu phí và lượt đi hợp lý trên xe trả phí và các trường hợp bất thường khác)
        # mask_khop = ~(df_xe_tra_phi[self.cot_xe_khong_thu_phi] | (df_xe_tra_phi['Biển số chuẩn'].isin(df_xe_tra_phi['Biển số chuẩn'])) | df_xe_tra_phi[self.cot_luot_di_bat_thuong] | df_xe_tra_phi[self.cot_loi_doc_nhieu_lan] | df_xe_tra_phi[self.cot_thu_phi_nguoi] | df_xe_tra_phi[self.cot_chi_co_be] | dieu_kien_chenh_lech)
        # df_khop = df_xe_tra_phi[mask_khop].copy()
        # results['DoiSoat-Khop'] = self._select_columns(df_khop, cols_khop)

        # # 10. Sheet Báo cáo tổng hợp
        # results['BaoCaoTong_DoiSoat'] = self._select_columns(df_xe_tra_phi, cols_bao_cao)

        return results