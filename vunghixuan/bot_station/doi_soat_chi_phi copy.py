import pandas as pd
import numpy as np


class DoiSoatPhi:
    def __init__(self):
        self.mapping_lane = {
            '2A': {'in': ['10', '11'], 'out': ['12'], 'tram': 'Đồng Khởi'},
            '1A': {'in': ['1', '2'], 'out': ['3', '4'], 'tram': 'ĐT768_1A'},
            '3B': {'in': ['7', '8', '9'], 'out': [], 'tram': 'ĐT768_3B'},
            '3A': {'in': [], 'out': ['5', '6'], 'tram': 'ĐT768_3A'}
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
        dieu_kien_mien_phi_uu_tien = df['Loại vé chuẩn'].isin(['Miễn giảm 100% trạm 2A 2B trạm 768', 'UT toàn quốc', 'Miễn phí quay đầu', 'Miễn phí liên trạm', 'Vé tháng thường'])
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
        Kiểm tra lượt đi hợp lý và bất thường, có xử lý các trường hợp quét trùng hoặc đọc đồng thời.

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
            thoi_gian_quet_trung = pd.Timedelta(seconds=15)  # Ngưỡng thời gian cho quét trùng

            # Khởi tạo các cột điều chỉnh nếu chưa tồn tại
            if 'Lý do điều chỉnh' not in df.columns:
                df['Lý do điều chỉnh'] = ''
            if 'Giá trị điều chỉnh FE' not in df.columns:
                df['Giá trị điều chỉnh FE'] = 0.0
            if 'Giá trị điều chỉnh BE' not in df.columns:
                df['Giá trị điều chỉnh BE'] = 0.0
            if 'Trạng thái xử lý' not in df.columns:
                df['Trạng thái xử lý'] = 'Chưa xử lý'
            if 'Người xử lý' not in df.columns:
                df['Người xử lý'] = ''
            if 'Thời gian xử lý' not in df.columns:
                df['Thời gian xử lý'] = pd.NaT

            for bien_so, group in df.groupby('Biển số chuẩn'):
                group_sorted = group.sort_values('Thời gian chuẩn').reset_index(drop=True)
                n_rows = len(group_sorted)
                i = 0
                while i < n_rows - 1:
                    giao_dich_hien_tai = group_sorted.iloc[i]
                    giao_dich_ke_tiep = group_sorted.iloc[i + 1]

                    time_diff = giao_dich_ke_tiep['Thời gian chuẩn'] - giao_dich_hien_tai['Thời gian chuẩn']
                    tram_hien_tai = self._get_tram_from_lane(str(giao_dich_hien_tai['Làn chuẩn']))
                    tram_ke_tiep = self._get_tram_from_lane(str(giao_dich_ke_tiep['Làn chuẩn']))

                    # Xử lý quét trùng hoặc đọc đồng thời
                    if tram_hien_tai == tram_ke_tiep and time_diff <= thoi_gian_quet_trung:
                        lan_hien_tai_type = self._get_lane_type(str(giao_dich_hien_tai['Làn chuẩn']))
                        lan_ke_tiep_type = self._get_lane_type(str(giao_dich_ke_tiep['Làn chuẩn']))
                        phi_hien_tai = giao_dich_hien_tai['Phí thu'] if pd.notna(giao_dich_hien_tai['Phí thu']) else giao_dich_hien_tai['BE_Tiền bao gồm thuế']
                        phi_ke_tiep = giao_dich_ke_tiep['Phí thu'] if pd.notna(giao_dich_ke_tiep['Phí thu']) else giao_dich_ke_tiep['BE_Tiền bao gồm thuế']

                        # Nếu cùng trạm, thời gian rất ngắn, có thể là quét trùng, bỏ qua giao dịch kế tiếp
                        # Hoặc nếu vào ra cùng lúc ở cùng trạm
                        if (pd.isna(phi_hien_tai) == pd.isna(phi_ke_tiep) and
                                (pd.isna(phi_hien_tai) or phi_hien_tai == phi_ke_tiep) or
                                (lan_hien_tai_type in ['in', None] and lan_ke_tiep_type in ['out', None]) or
                                (lan_hien_tai_type in ['out', None] and lan_ke_tiep_type in ['in', None])):
                            df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Lượt đi bất thường'] = True
                            df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Ghi chú xử lý'] += '; Nghi vấn quét trùng anten'
                            df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Lý do điều chỉnh'] = 'Quét trùng anten'
                            df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Giá trị điều chỉnh FE'] = 0.0
                            df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Giá trị điều chỉnh BE'] = 0.0
                            df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Trạng thái xử lý'] = 'Chưa xử lý'
                            i += 2
                            continue
                        else:
                            # Nếu không rõ là quét trùng, vẫn xử lý như cặp giao dịch bình thường
                            pass

                    # Kiểm tra lượt đi hợp lý
                    tram_vao = tram_hien_tai
                    tram_ra = tram_ke_tiep
                    lane_vao_type = self._get_lane_type(str(giao_dich_hien_tai['Làn chuẩn']))
                    lane_ra_type = self._get_lane_type(str(giao_dich_ke_tiep['Làn chuẩn']))
                    phi_fe_vao = giao_dich_hien_tai['Phí thu'] > 0
                    phi_be_vao = giao_dich_hien_tai['BE_Tiền bao gồm thuế'] > 0
                    phi_fe_ra = giao_dich_ke_tiep['Phí thu'] > 0
                    phi_be_ra = giao_dich_ke_tiep['BE_Tiền bao gồm thuế'] > 0

                    if tram_vao == tram_ra and time_diff > thoi_gian_hop_ly and \
                       ((lane_vao_type in ['in', None] and lane_ra_type in ['out', None]) or \
                        (lane_vao_type in ['out', None] and lane_ra_type in ['in', None])) and \
                       (phi_fe_vao or phi_be_vao) and (phi_fe_ra or phi_be_ra):
                        df.loc[giao_dich_hien_tai.name, self.cot_luot_di_hop_ly] = True
                        df.loc[giao_dich_ke_tiep.name, self.cot_luot_di_hop_ly] = True
                    # Kiểm tra lượt đi bất thường (thời gian ngắn, cùng trạm)
                    elif time_diff <= thoi_gian_toi_da_cho_luot_di_ngan and tram_vao == tram_ra and (phi_fe_vao or phi_be_vao):
                        ghi_chu = '; Nghi vấn quay đầu có phí (thời gian ngắn)'
                        if ghi_chu not in df.loc[giao_dich_hien_tai.name, self.cot_ghi_chu_xu_ly]:
                            df.loc[giao_dich_hien_tai.name, self.cot_ghi_chu_xu_ly] += ghi_chu
                        if ghi_chu not in df.loc[giao_dich_ke_tiep.name, self.cot_ghi_chu_xu_ly]:
                            df.loc[giao_dich_ke_tiep.name, self.cot_ghi_chu_xu_ly] += ghi_chu
                        df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], self.cot_luot_di_bat_thuong] = True
                        df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Lý do điều chỉnh'] = 'Quay đầu có phí'
                        df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Trạng thái xử lý'] = 'Chưa xử lý'
                    elif time_diff <= thoi_gian_toi_da_cho_luot_di_ngan and tram_vao == tram_ra and lane_vao_type is not None and lane_ra_type is not None and lane_vao_type != lane_ra_type and (phi_fe_vao or phi_be_vao):
                        ghi_chu = f'; Nghi vấn vào {lane_vao_type} ra {lane_ra_type} phí (thời gian ngắn)'
                        if ghi_chu not in df.loc[giao_dich_hien_tai.name, self.cot_ghi_chu_xu_ly]:
                            df.loc[giao_dich_hien_tai.name, self.cot_ghi_chu_xu_ly] += ghi_chu
                        if ghi_chu not in df.loc[giao_dich_ke_tiep.name, self.cot_ghi_chu_xu_ly]:
                            df.loc[giao_dich_ke_tiep.name, self.cot_ghi_chu_xu_ly] += ghi_chu
                        df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], self.cot_luot_di_bat_thuong] = True
                        df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Lý do điều chỉnh'] = f'Vào {lane_vao_type} ra {lane_ra_type} phí'
                        df.loc[[giao_dich_hien_tai.name, giao_dich_ke_tiep.name], 'Trạng thái xử lý'] = 'Chưa xử lý'

                    i += 1

        except Exception as e:
            print('Lỗi hàm kiem_tra_luot_di', e)

        return df, df[df[self.cot_luot_di_hop_ly]].copy()

    def _kiem_tra_luot_di_ngan(self, df_ngan):
        """Kiểm tra các lượt đi có thời gian giữa các giao dịch <= 10 phút để tìm bất thường."""
        df_ngan[self.cot_luot_di_bat_thuong] = False
        df_ngan[self.cot_ghi_chu_xu_ly] = df_ngan[self.cot_ghi_chu_xu_ly].fillna('')
        thoi_gian_toi_da_cho_luot_di_ngan = pd.Timedelta(minutes=10)

        for bien_so, group in df_ngan.groupby('Biển số chuẩn'):
            group_sorted = group.sort_values('Thời gian chuẩn')
            if len(group_sorted) >= 2:
                for i in range(len(group_sorted) - 1):
                    giao_dich_hien_tai = group_sorted.iloc[i]
                    giao_dich_tiep_theo = group_sorted.iloc[i + 1]
                    thoi_gian_chenh_lech = giao_dich_tiep_theo['Thời gian chuẩn'] - giao_dich_hien_tai['Thời gian chuẩn']
                    tram_hien_tai = self._get_tram_from_lane(str(giao_dich_hien_tai['Làn chuẩn']))
                    tram_tiep_theo = self._get_tram_from_lane(str(giao_dich_tiep_theo['Làn chuẩn']))
                    lan_hien_tai_type = self._get_lane_type(str(giao_dich_hien_tai['Làn chuẩn']))
                    lan_tiep_theo_type = self._get_lane_type(str(giao_dich_tiep_theo['Làn chuẩn']))

                    # Kiểm tra quay đầu có phí (thời gian ngắn)
                    if tram_hien_tai == tram_tiep_theo and thoi_gian_chenh_lech <= thoi_gian_toi_da_cho_luot_di_ngan and (giao_dich_hien_tai['Phí thu'] > 0 or giao_dich_hien_tai['BE_Tiền bao gồm thuế'] > 0):
                        df_ngan.loc[[giao_dich_hien_tai.name, giao_dich_tiep_theo.name], self.cot_luot_di_bat_thuong] = True
                        df_ngan.loc[[giao_dich_hien_tai.name, giao_dich_tiep_theo.name], self.cot_ghi_chu_xu_ly] += '; Nghi vấn quay đầu có phí (thời gian ngắn)'

                    # Kiểm tra vào làn ra hoặc ra làn vào có phí (thời gian ngắn)
                    if tram_hien_tai == tram_tiep_theo and lan_hien_tai_type is not None and lan_tiep_theo_type is not None and lan_hien_tai_type != lan_tiep_theo_type and thoi_gian_chenh_lech <= thoi_gian_toi_da_cho_luot_di_ngan and (giao_dich_hien_tai['Phí thu'] > 0 or giao_dich_tiep_theo['BE_Tiền bao gồm thuế'] > 0):
                        df_ngan.loc[[giao_dich_hien_tai.name, giao_dich_tiep_theo.name], self.cot_luot_di_bat_thuong] = True
                        df_ngan.loc[[giao_dich_hien_tai.name, giao_dich_tiep_theo.name], self.cot_ghi_chu_xu_ly] += f'; Nghi vấn vào làn {lan_hien_tai_type}, ra làn {lan_tiep_theo_type} có phí (thời gian ngắn)'
        return df_ngan
    
    def kiem_tra_doc_nhieu_luot(self, df):
        
        """
        Kiểm tra và đánh dấu các trường hợp nghi vấn đọc nhiều lượt do anten.
        """
        try:
            df[self.cot_so_lan_qua_tram] = df.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('count')
            df['Trạm'] = df['Làn chuẩn'].apply(lambda x: self._get_tram_from_lane(x.split('-')[-1])) # Lấy số làn cuối cùng
            df[self.cot_thoi_gian_cach_lan_truoc] = df.groupby('Biển số chuẩn')['Thời gian chuẩn'].diff().dt.total_seconds() / 60
            df[self.cot_loi_doc_nhieu_lan] = False

            # Ensure columns exist
            for col in [self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ghi_chu_xu_ly]:
                if col not in df.columns:
                    df[col] = 0 if 'phi' in col else ''
                else:
                    df[col] = df[col].fillna(0) if 'phi' in col else df[col].fillna('')

            df_nhieu_luot_filtered = df[df[self.cot_so_lan_qua_tram] >= 2].sort_values(['Biển số chuẩn', 'Thời gian chuẩn']).copy()

            dieu_kien_cung_lan = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Làn chuẩn'].shift() == df_nhieu_luot_filtered['Làn chuẩn']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0))
            df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_loi_doc_nhieu_lan] = True
            df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_phi_dieu_chinh_fe] -= df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, 'Phí thu'].fillna(0)
            df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_phi_dieu_chinh_be] -= df_nhieu_luot_filtered.loc[dieu_kien_cung_lan, 'BE_Tiền bao gồm thuế'].fillna(0)
            df.loc[df_nhieu_luot_filtered[dieu_kien_cung_lan].index, self.cot_ghi_chu_xu_ly] += '; Trả lại phí do đọc trùng'

            dieu_kien_khac_lan_cung_tram = (df_nhieu_luot_filtered[self.cot_thoi_gian_cach_lan_truoc] <= 5) & (df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Trạm'].shift() == df_nhieu_luot_filtered['Trạm']) & ((df_nhieu_luot_filtered['BE_Tiền bao gồm thuế'] > 0) | (df_nhieu_luot_filtered['Phí thu'] > 0)) & (~dieu_kien_cung_lan)
            df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_loi_doc_nhieu_lan] = True
            df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_phi_dieu_chinh_fe] -= df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, 'Phí thu'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0).fillna(0)
            df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_phi_dieu_chinh_be] -= df_nhieu_luot_filtered.loc[dieu_kien_khac_lan_cung_tram, 'BE_Tiền bao gồm thuế'].where(df_nhieu_luot_filtered.groupby('Biển số chuẩn')['Thời gian chuẩn'].transform('rank') > 1, 0).fillna(0)
            df.loc[df_nhieu_luot_filtered[dieu_kien_khac_lan_cung_tram].index, self.cot_ghi_chu_xu_ly] += '; Cần kiểm tra, điều chỉnh phí do đọc nhiều lượt'
        except Exception as e:
             print('Lỗi hàm kiem_tra_doc_nhieu_luot', e)
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
            df_xe_tra_phi, df_luot_hop_ly_tra_phi = self.kiem_tra_luot_di(df_xe_tra_phi)
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_buoc_doi_soat] = 'Kiểm tra lượt đi bất thường'
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_ket_qua_doi_soat] = 'Nghi vấn lượt đi bất thường'
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_nguyen_nhan_doi_soat] = df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_bat_thuong], self.cot_ghi_chu_xu_ly]
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_hop_ly], self.cot_buoc_doi_soat] = 'Xác định lượt đi hợp lý'
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_luot_di_hop_ly], self.cot_ket_qua_doi_soat] = 'Lượt đi hợp lý'

            # Bước 4: Kiểm tra đọc nhiều lượt (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
            mask_nhieu_luot_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
            df_xe_tra_phi = self.kiem_tra_doc_nhieu_luot(df_xe_tra_phi[mask_nhieu_luot_tra_phi].copy())
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_loi_doc_nhieu_lan], self.cot_buoc_doi_soat] = 'Kiểm tra đọc nhiều lượt'
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_loi_doc_nhieu_lan], self.cot_ket_qua_doi_soat] = 'Nghi vấn đọc nhiều lượt'

            # Bước 5: Kiểm tra thu phí nguội (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
            mask_phi_nguoi_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
            df_xe_tra_phi = self.kiem_tra_thu_phi_nguoi(df_xe_tra_phi[mask_phi_nguoi_tra_phi].copy())
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_thu_phi_nguoi], self.cot_buoc_doi_soat] = 'Kiểm tra thu phí nguội'
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_thu_phi_nguoi], self.cot_ket_qua_doi_soat] = 'Nghi vấn thu phí nguội'

            # Bước 6: Kiểm tra FE có BE không (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
            mask_fe_co_be_khong_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
            df_xe_tra_phi = self.kiem_tra_fe_co_be_khong(df_xe_tra_phi[mask_fe_co_be_khong_tra_phi].copy())
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_chi_co_be], self.cot_buoc_doi_soat] = 'Kiểm tra FE có BE không'
            df_xe_tra_phi.loc[df_xe_tra_phi[self.cot_chi_co_be], self.cot_ket_qua_doi_soat] = 'Chỉ có giao dịch FE'

            # Bước 7: Kiểm tra chênh lệch phí (loại trừ lượt đi hợp lý) trên df_xe_tra_phi
            mask_chenh_lech_tra_phi = ~df_xe_tra_phi[self.cot_luot_di_hop_ly]
            df_xe_tra_phi = self.kiem_tra_chenh_lech_phi(df_xe_tra_phi[mask_chenh_lech_tra_phi].copy())
            dieu_kien_chenh_lech_tra_phi = (df_xe_tra_phi['Phí điều chỉnh FE'] != 0) | (df_xe_tra_phi['Phí điều chỉnh BE'] != 0)
            df_xe_tra_phi.loc[dieu_kien_chenh_lech_tra_phi, self.cot_buoc_doi_soat] = 'Kiểm tra chênh lệch phí'
            df_xe_tra_phi.loc[dieu_kien_chenh_lech_tra_phi, self.cot_ket_qua_doi_soat] = 'Chênh lệch phí'

            df_da_doi_soat = pd.concat([df_xe_khong_tra_phi, df_xe_tra_phi], ignore_index=True)

        except Exception as e:
            print('Lỗi ham doi_soat', e)

        return df_da_doi_soat, df_xe_tra_phi[df_xe_tra_phi[self.cot_luot_di_hop_ly]].copy(), df_xe_khong_tra_phi

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
        df_da_doi_soat = self.doi_soat(df.copy())
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
        results['VuNghiXuan'] = df_da_doi_soat.copy() # Đảm bảo không ảnh hưởng đến df_da_doi_soat gốc

        # 1. Sheet Xe không thu phí
        df_khong_thu_phi = df_da_doi_soat[df_da_doi_soat[self.cot_xe_khong_thu_phi]].copy()
        results['DoiSoat-KhongThuPhi'] = self._select_columns(df_khong_thu_phi, cols_khong_thu_phi)

        # 2. Sheet Xe trả phí
        dieu_kien_mien_phi_uu_tien = df_da_doi_soat['Loại vé chuẩn'].isin(['Miễn giảm 100% trạm 2A 2B trạm 768', 'UT toàn quốc', 'Miễn phí quay đầu', 'Miễn phí liên trạm', 'Vé tháng thường'])
        dieu_kien_phi_nan_hoac_khong = (df_da_doi_soat['Phí thu'].isna() | (df_da_doi_soat['Phí thu'] == 0)) & (df_da_doi_soat['BE_Tiền bao gồm thuế'].isna() | (df_da_doi_soat['BE_Tiền bao gồm thuế'] == 0))
        df_tra_phi = df_da_doi_soat[~(dieu_kien_mien_phi_uu_tien & dieu_kien_phi_nan_hoac_khong)].copy()
        results['XeTraPhi'] = self._select_columns(df_tra_phi, cols_khong_thu_phi) # Chọn các cột cơ bản

        # 3. Sheet Lượt đi hợp lý (chỉ trên xe trả phí)
        df_luot_hop_ly_tra_phi = df_tra_phi[df_tra_phi[self.cot_luot_di_hop_ly]].copy()
        results['DoiSoat-LuotDiHopLy'] = self._select_columns(df_luot_hop_ly_tra_phi, cols_luot_hop_ly)

        # 4. Sheet Lượt đi bất thường
        df_luot_di_bat_thuong = df_da_doi_soat[df_da_doi_soat[self.cot_luot_di_bat_thuong]].copy()
        results['DoiSoat-LuotDiBatThuong'] = self._select_columns(df_luot_di_bat_thuong, cols_luot_di_bat_thuong)

        # 5. Sheet Nghi vấn đọc nhiều lần
        df_doc_nhieu_luot = df_da_doi_soat[df_da_doi_soat[self.cot_loi_doc_nhieu_lan]].copy()
        results['DoiSoat-DocNhieuLan'] = self._select_columns(df_doc_nhieu_luot, cols_doc_nhieu_lan)

        # 6. Sheet Nghi vấn thu phí nguội
        df_thu_phi_nguoi = df_da_doi_soat[df_da_doi_soat[self.cot_thu_phi_nguoi]].copy()
        results['DoiSoat-PhiNguoi'] = self._select_columns(df_thu_phi_nguoi, cols_phi_nguoi)

        # 7. Sheet Giao dịch chỉ có BE
        df_chi_co_be = df_da_doi_soat[df_da_doi_soat[self.cot_chi_co_be]].copy()
        results['DoiSoat-ChiCo-FE'] = self._select_columns(df_chi_co_be, cols_chi_co_be)

        # 8. Sheet Chênh lệch phí
        dieu_kien_chenh_lech = (df_da_doi_soat['Phí điều chỉnh FE'] != 0) | (df_da_doi_soat['Phí điều chỉnh BE'] != 0)
        df_chenh_lech_phi = df_da_doi_soat[dieu_kien_chenh_lech].copy()
        results['DoiSoat-GiaThuPhi'] = self._select_columns(df_chenh_lech_phi, cols_chenh_lech_phi)

        # 9. Sheet Giao dịch khớp (loại trừ xe không thu phí và lượt đi hợp lý trên xe trả phí)
        mask_khop = ~(df_da_doi_soat[self.cot_xe_khong_thu_phi] | (df_da_doi_soat['Biển số chuẩn'].isin(df_luot_hop_ly_tra_phi['Biển số chuẩn'])) | df_da_doi_soat[self.cot_luot_di_bat_thuong] | df_da_doi_soat[self.cot_loi_doc_nhieu_lan] | df_da_doi_soat[self.cot_thu_phi_nguoi] | df_da_doi_soat[self.cot_chi_co_be] | dieu_kien_chenh_lech)
        df_khop = df_da_doi_soat[mask_khop].copy()
        results['DoiSoat-Khop'] = self._select_columns(df_khop, cols_khop)

        # 10. Sheet Báo cáo tổng hợp
        results['BaoCaoTong_DoiSoat'] = self._select_columns(df_da_doi_soat, cols_bao_cao)

        return results