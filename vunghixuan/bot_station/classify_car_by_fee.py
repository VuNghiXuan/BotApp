import pandas as pd
import numpy as np
# from vunghixuan.bot_station.car_journey_In_24h import CarJourney24h

class CarByFee:
    def __init__(self):
        self.cot_xe_khong_thu_phi = 'Xe không trả phí'
        self.cot_xe_tra_phi = 'Xe trả phí'
        # self.cot_luot_di_hop_ly = 'Lượt đi hợp lý'
        # self.cot_luot_di_bat_thuong = 'Lượt đi bất thường'
        # # self.cot_ly_do_dieu_chinh = 'Ghi chú xử lý'
        
        # self.cot_so_luot_di ='Số lượt đi'
        # self.cot_thoi_gian_giua_luot = 'Thời gian giữa 2 lượt (phút)'
        # self.cot_loi_doc_nhieu_lan = 'Lỗi đọc Antent'
        # self.cot_phi_dieu_chinh_fe = 'Phí điều chỉnh FE'
        # self.cot_phi_dieu_chinh_be = 'Phí điều chỉnh BE'
        # self.cot_ly_do_dieu_chinh = 'Lý do điều chỉnh'
        # Khởi tạo mapping_lane, nếu không được truyền vào sẽ dùng một giá trị mặc định (ví dụ)
       
       

    def _khoi_tao_cac_cot(self, df):
        """Khởi tạo các cột cần thiết nếu chúng chưa tồn tại."""
        if self.cot_xe_khong_thu_phi not in df.columns:
            df[self.cot_xe_khong_thu_phi] = False
        if self.cot_xe_tra_phi not in df.columns:
            df[self.cot_xe_tra_phi] = False

        # if self.cot_luot_di_hop_ly not in df.columns:
        #     df[self.cot_luot_di_hop_ly] = False
        # if self.cot_luot_di_bat_thuong not in df.columns:
        #     df[self.cot_luot_di_bat_thuong] = False
        # if self.cot_so_luot_di not in df.columns:
        #     df[self.cot_so_luot_di] = 0
        # # df[self.cot_ly_do_dieu_chinh] = df[self.cot_ly_do_dieu_chinh].fillna('').astype(str)
          
        # if self.cot_thoi_gian_giua_luot not in df.columns:
        #     df[self.cot_thoi_gian_giua_luot] = np.nan
        # if self.cot_loi_doc_nhieu_lan not in df.columns:
        #     df[self.cot_loi_doc_nhieu_lan] = False
       
        # if self.cot_phi_dieu_chinh_fe not in df.columns:
        #     df[self.cot_phi_dieu_chinh_fe] = 0.0
        # if self.cot_phi_dieu_chinh_be not in df.columns:
        #     df[self.cot_phi_dieu_chinh_be] = 0.0
        # if self.cot_ly_do_dieu_chinh not in df.columns:
        #     df[self.cot_ly_do_dieu_chinh] = ''
        # if 'Thời gian giữa 2 lần đọc (phút)' not in df.columns: # Đổi tên cột cho thống nhất
        #     df['Thời gian giữa 2 lần đọc (phút)'] = np.nan
        return df

    def group_cars_from_df_FE_BE(self, df):
        """
        Gộp các dòng có cùng 'Biển số chuẩn' và sắp xếp theo 'Thời gian chuẩn'.

        Args:
            df (pd.DataFrame): DataFrame đã có cột 'Biển số chuẩn' và 'Thời gian chuẩn'.

        Returns:
            pd.DataFrame: DataFrame đã gộp và sắp xếp.
        """
        if 'Biển số chuẩn' not in df.columns or 'Thời gian chuẩn' not in df.columns:
            print("Lỗi: DataFrame cần có cột 'Biển số chuẩn' và 'Thời gian chuẩn'.")
            return df
        
        # # Chuyển cột 'Thời gian chuẩn' sang kiểu datetime nếu chưa phải
        # if not pd.api.types.is_datetime64_any_dtype(df['Thời gian chuẩn']):
        #     try:
        #         df['Thời gian chuẩn'] = pd.to_datetime(df['Thời gian chuẩn'], errors='coerce')
        #         # df['Thời gian chuẩn'] = pd.to_datetime(df['Thời gian chuẩn'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
        #     except Exception as e:
        #         print(f"Lỗi chuyển đổi kiểu dữ liệu cho cột 'Thời gian chuẩn': {e}")
        #         return df

        # Gộp các dòng có cùng 'Biển số chuẩn'
        grouped = df.groupby('Biển số chuẩn', dropna=True)

        # Sắp xếp các giao dịch trong mỗi nhóm theo 'Thời gian chuẩn'
        sorted_groups = grouped.apply(lambda x: x.sort_values(by='Thời gian chuẩn'))

        # Bỏ chỉ mục nhóm để có DataFrame phẳng
        final_df = sorted_groups.reset_index(drop=True)

        return final_df
    
    def split_group_cars_not_fee_and_has_fee(self, df):
        """
        Tách các xe không trả phí và xe trả phí.
        Một xe được coi là không trả phí nếu có ít nhất một giao dịch
        có 'Loại vé chuẩn' thuộc danh sách miễn phí/ưu tiên.
        """
        try:
            df = df.copy()
            cac_loai_ve_mien_phi = ['UT toàn quốc', 'Miễn giảm 100%', 'Vé quý thường', 'Vé tháng thường', 'Miễn giảm ĐP'] #, 'Vé lượt miễn phí', 'Vé quay đầu'

            # Tìm các biển số xe có ít nhất một giao dịch thuộc loại vé miễn phí/ưu tiên
            bien_so_khong_phi_theo_ve = df[df['Loại vé chuẩn'].isin(cac_loai_ve_mien_phi)]['Biển số chuẩn'].unique()

            # Tạo cột đánh dấu xe không thu phí cho TẤT CẢ các giao dịch của các biển số này
            df[self.cot_xe_khong_thu_phi] = df['Biển số chuẩn'].isin(bien_so_khong_phi_theo_ve)

            # Tách thành hai DataFrame
            df_xe_khong_tra_phi = df[df[self.cot_xe_khong_thu_phi]].copy()
            df_xe_tra_phi = df[~df[self.cot_xe_khong_thu_phi]].copy()

            # Nhóm lại cùng biển số:
            df_xe_khong_tra_phi = self.group_cars_from_df_FE_BE(df_xe_khong_tra_phi)
            df_xe_tra_phi = self.group_cars_from_df_FE_BE(df_xe_tra_phi)

            return df_xe_khong_tra_phi, df_xe_tra_phi

        except Exception as e:
            print('Lỗi Hàm _tach_nhom_xe_ko_thu_phi: ', e)
            return pd.DataFrame(), pd.DataFrame() # Trả về DataFrame rỗng để tránh lỗi ở nơi gọi

    
   

    def _kiem_tra_quet_trung(self, giao_dich_1, giao_dich_2, thoi_gian_quet_trung, df):
        """Kiểm tra và xử lý trường hợp quét trùng."""
        try:
            thoi_gian_1, _, loai_lan_1, phi_1, phi_fe_1, phi_be_1 = self._lay_thong_tin_giao_dich(giao_dich_1)
            thoi_gian_2, _, loai_lan_2, phi_2, phi_fe_2, phi_be_2 = self._lay_thong_tin_giao_dich(giao_dich_2)
            if thoi_gian_1 is None or thoi_gian_2 is None:
                return False
            time_diff = thoi_gian_2 - thoi_gian_1
            if time_diff <= thoi_gian_quet_trung and (pd.isna(phi_1) == pd.isna(phi_2)) and (
                (pd.isna(phi_1) or phi_1 == phi_2) or
                (loai_lan_1 in ['in', None] and loai_lan_2 in ['out', None]) or
                (loai_lan_1 in ['out', None] and loai_lan_2 in ['in', None])):
                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_luot_di_bat_thuong] = True
                df.loc[[giao_dich_1.name, giao_dich_2.name],self.cot_thoi_gian_giua_luot] = time_diff.total_seconds() / 60
                self._them_ghi_chu(df, giao_dich_1.name, 'Nghi vấn quét trùng anten')
                self._them_ghi_chu(df, giao_dich_2.name, 'Nghi vấn quét trùng anten')
                self._them_ly_do_dieu_chinh(df, giao_dich_1.name, 'Trả lại phí do đọc trùng lặp')
                self._them_ly_do_dieu_chinh(df, giao_dich_2.name, 'Trả lại phí do đọc trùng lặp')

                # Tính toán và gán phí điều chỉnh (giảm toàn bộ phí đã thu)
                if phi_fe_1 is not None:
                    df.loc[giao_dich_1.name, self.cot_phi_dieu_chinh_fe] -= phi_fe_1
                if phi_be_1 is not None:
                    df.loc[giao_dich_1.name, self.cot_phi_dieu_chinh_be] -= phi_be_1
                if phi_fe_2 is not None:
                    df.loc[giao_dich_2.name, self.cot_phi_dieu_chinh_fe] -= phi_fe_2
                if phi_be_2 is not None:
                    df.loc[giao_dich_2.name, self.cot_phi_dieu_chinh_be] -= phi_be_2

                # df.loc[[giao_dich_1.name, giao_dich_2.name], 'Trạng thái xử lý'] = 'Đã xử lý'
                return True
            return False
        except Exception as e:
            print('Lõi hàm _kiem_tra_quet_trung: ', e)
            return False

    def _kiem_tra_luot_di_hop_ly(self, giao_dich_1, giao_dich_2, thoi_gian_hop_ly, df):
        """Kiểm tra và đánh dấu lượt đi hợp lý."""
        try:
            thoi_gian_1, tram_1, loai_lan_1, phi_1, phi_fe_1, phi_be_1 = self._lay_thong_tin_giao_dich(giao_dich_1)
            thoi_gian_2, tram_2, loai_lan_2, phi_2, phi_fe_2, phi_be_2 = self._lay_thong_tin_giao_dich(giao_dich_2)
            time_diff = thoi_gian_2 - thoi_gian_1
            phi_vao = phi_1 > 0
            phi_ra = phi_2 > 0
            if tram_1 == tram_2 and time_diff > thoi_gian_hop_ly and ((loai_lan_1 in ['in', None] and loai_lan_2 in ['out', None]) or
                    (loai_lan_1 in ['out', None] and loai_lan_2 in ['in', None])) and (phi_vao or phi_1 is not None) and (phi_ra or phi_2 is not None):
                df.loc[giao_dich_1.name, self.cot_luot_di_hop_ly] = True
                df.loc[giao_dich_2.name, self.cot_luot_di_hop_ly] = True
                return True
            return False
        except Exception as e:
            print('Lõi hàm _kiem_tra_luot_di_hop_ly: ', e)

    def _kiem_tra_luot_di_bat_thuong_ngan(self, giao_dich_1, giao_dich_2, thoi_gian_toi_da_cho_luot_di_ngan, df):
        """Kiểm tra và xử lý lượt đi bất thường (thời gian ngắn, cùng trạm)."""
        try:
            thoi_gian_1, tram_1, loai_lan_1, phi_1, phi_fe_1, phi_be_1 = self._lay_thong_tin_giao_dich(giao_dich_1)
            thoi_gian_2, tram_2, loai_lan_2, phi_2, phi_fe_2, phi_be_2 = self._lay_thong_tin_giao_dich(giao_dich_2)
            time_diff = thoi_gian_2 - thoi_gian_1
            phi_vao = phi_1 > 0
            if time_diff <= thoi_gian_toi_da_cho_luot_di_ngan and tram_1 == tram_2 and (phi_vao or phi_1 is not None):
                ghi_chu = '; Nghi vấn quay đầu có phí (thời gian ngắn)'
                self._them_ghi_chu(df, giao_dich_1.name, ghi_chu)
                self._them_ghi_chu(df, giao_dich_2.name, ghi_chu)
                self._them_ly_do_dieu_chinh(df, giao_dich_1.name, 'Quay đầu có phí')
                self._them_ly_do_dieu_chinh(df, giao_dich_2.name, 'Quay đầu có phí')
                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_luot_di_bat_thuong] = True
                # df.loc[[giao_dich_1.name, giao_dich_2.name], 'Trạng thái xử lý'] = 'Chưa xử lý'
                return True
            elif time_diff <= thoi_gian_toi_da_cho_luot_di_ngan and tram_1 == tram_2 and loai_lan_1 is not None and loai_lan_2 is not None and loai_lan_1 != loai_lan_2 and (phi_vao or phi_1 is not None):
                ghi_chu = f'; Nghi vấn vào {loai_lan_1} ra {loai_lan_2} phí (thời gian ngắn)'
                self._them_ghi_chu(df, giao_dich_1.name, ghi_chu)
                self._them_ghi_chu(df, giao_dich_2.name, ghi_chu)
                ly_do = f'Vào {loai_lan_1} ra {loai_lan_2} phí'
                self._them_ly_do_dieu_chinh(df, giao_dich_1.name, ly_do)
                self._them_ly_do_dieu_chinh(df, giao_dich_2.name, ly_do)
                df.loc[[giao_dich_1.name, giao_dich_2.name], self.cot_luot_di_bat_thuong] = True
                # df.loc[[giao_dich_1.name, giao_dich_2.name], 'Trạng thái xử lý'] = 'Chưa xử lý'
                return True
            return False
        except Exception as e:
            print('Lõi hàm _kiem_tra_luot_di_bat_thuong_ngan: ', e)

    def _them_ghi_chu(self, df, index, ghi_chu_moi):
        """Thêm ghi chú vào cột 'Ghi chú xử lý' nếu chưa tồn tại."""
        try:
            current_ghi_chu = str(df.loc[index, self.cot_ly_do_dieu_chinh])
            if ghi_chu_moi not in current_ghi_chu:
                df.loc[index, self.cot_ly_do_dieu_chinh] = current_ghi_chu + '; '+ ghi_chu_moi
        except Exception as e:
            print('Lõi hàm _them_ghi_chu: ', e)

    def _them_ly_do_dieu_chinh(self, df, index, ly_do_moi):
        """Thêm lý do điều chỉnh vào cột 'Lý do điều chỉnh' nếu chưa tồn tại."""
        try:
            current_ly_do = str(df.loc[index, 'Lý do điều chỉnh'])
            if ly_do_moi not in current_ly_do:
                df.loc[index, 'Lý do điều chỉnh'] = current_ly_do + '; ' + ly_do_moi
        except Exception as e:
            print('Lõi hàm _them_ly_do_dieu_chinh: ', e)
    

    
    def kiem_tra_luot_di(self, df):
        
        """
        Kiểm tra lượt đi hợp lý và bất thường bằng cách so sánh tất cả các cặp giao dịch
        trong mỗi group (theo biển số xe). Xử lý các trường hợp quét trùng hoặc đọc đồng thời.
        Chỉ thêm ghi chú và lý do nếu chúng chưa tồn tại.

        Args:
            df (pd.DataFrame): DataFrame chứa dữ liệu giao dịch đã được gộp và chuẩn hóa.

        Returns:
            tuple: DataFrame đã được cập nhật và DataFrame chứa lượt đi hợp lý.
        """
        try:
            df = self._khoi_tao_cac_cot(df)
            

            for bien_so, group in df.groupby('Biển số chuẩn'):
                group_sorted = group.sort_values('Thời gian chuẩn').reset_index(drop=True)
                
                # car_journey_24h = CarJourney24h(bien_so, group_sorted)

                print('Nhóm xe kiểm soát lượt đi: ', group_sorted)
                giao_dich_nhom_xe = {}

                n_rows = len(group_sorted)
                if n_rows >= 2:
                    # 'Lấy dữ liệu test'
                    # head = group_sorted.columns.tolist()
                    # val = group_sorted.values.tolist()
                    # list_2D = [head] + val
                    # print(head, val)

                    for i in range(n_rows):
                        giao_dich = self._lay_thong_tin_giao_dich(group_sorted.iloc[i])
                        
                        # for j in range(i + 1, n_rows):
                            
                        #     giao_dich_1 = group_sorted.iloc[i]
                        #     giao_dich_2 = group_sorted.iloc[j]

                        #     "Quay lại chuẩn hoá cột thời gian cho FE -------------------------------------"

                        #     if self._kiem_tra_quet_trung(giao_dich_1, giao_dich_2, thoi_gian_quet_trung, df):
                        #         continue  # Nếu là quét trùng, bỏ qua các kiểm tra khác cho cặp này

                        #     self._kiem_tra_luot_di_hop_ly(giao_dich_1, giao_dich_2, thoi_gian_hop_ly, df)
                        #     self._kiem_tra_luot_di_bat_thuong_ngan(giao_dich_1, giao_dich_2, thoi_gian_toi_da_cho_luot_di_ngan, df)
                else:
                    print('Chưa xử lý trường hợp n_rows<2')
        except Exception as e:
            print('Lỗi hàm kiem_tra_luot_di', e)

        # return df, df[df[self.cot_luot_di_hop_ly]].copy(), df[df[self.cot_luot_di_bat_thuong]].copy()
        return df
    
    def kiem_tra_thu_phi_nguoi(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp nghi vấn thu phí nguội.
        """
        dieu_kien_thu_phi_nguoi = (df['BE_Tiền bao gồm thuế'] > 0) & (df['Phí thu'].isna() | (df['Phí thu'] == 0))
        df[self.cot_thu_phi_nguoi] = dieu_kien_thu_phi_nguoi
        df[self.cot_phi_dieu_chinh_fe] = np.where(dieu_kien_thu_phi_nguoi, df[self.cot_phi_dieu_chinh_fe] + df['BE_Tiền bao gồm thuế'].fillna(0), df[self.cot_phi_dieu_chinh_fe])
        df[self.cot_phi_dieu_chinh_be] = np.where(dieu_kien_thu_phi_nguoi, df[self.cot_phi_dieu_chinh_be], df[self.cot_phi_dieu_chinh_be])
        df[self.cot_ly_do_dieu_chinh] = np.where(dieu_kien_thu_phi_nguoi & (df[self.cot_ly_do_dieu_chinh] == ''), 'Bổ sung phí cho FE',
                                        np.where(dieu_kien_thu_phi_nguoi & (df[self.cot_ly_do_dieu_chinh] != ''), df[self.cot_ly_do_dieu_chinh] + '; Bổ sung phí cho FE', df[self.cot_ly_do_dieu_chinh]))
        return df

    def kiem_tra_fe_co_be_khong(self, df):
        """
        Kiểm tra và đánh dấu các trường hợp FE có phí, BE không có.
        """
        dieu_kien_fe_co_be_khong = (df['Phí thu'] > 0) & (df['BE_Tiền bao gồm thuế'].isna() | (df['BE_Tiền bao gồm thuế'] == 0))
        df[self.cot_chi_co_be] = dieu_kien_fe_co_be_khong
        df[self.cot_phi_dieu_chinh_fe] = np.where(dieu_kien_fe_co_be_khong, df[self.cot_phi_dieu_chinh_fe], df[self.cot_phi_dieu_chinh_fe])
        df[self.cot_phi_dieu_chinh_be] = np.where(dieu_kien_fe_co_be_khong, df[self.cot_phi_dieu_chinh_be] + df['Phí thu'].fillna(0), df[self.cot_phi_dieu_chinh_be])
        df[self.cot_ly_do_dieu_chinh] = np.where(dieu_kien_fe_co_be_khong & (df[self.cot_ly_do_dieu_chinh] == ''), 'Bổ sung phí cho BE',
                                        np.where(dieu_kien_fe_co_be_khong & (df[self.cot_ly_do_dieu_chinh] != ''), df[self.cot_ly_do_dieu_chinh] + '; Bổ sung phí cho BE', df[self.cot_ly_do_dieu_chinh]))
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
        df.loc[mask_chenh_lech, self.cot_ly_do_dieu_chinh] = np.where(
            df.loc[mask_chenh_lech, self.cot_ly_do_dieu_chinh] == '',
            np.where(df.loc[mask_chenh_lech, 'Phí thu'].fillna(0) > df.loc[mask_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0),
                     'FE thu thừa, cần trả lại',
                     'BE thu thiếu, cần bổ sung'),
            df.loc[mask_chenh_lech, self.cot_ly_do_dieu_chinh] + '; ' + np.where(
                df.loc[mask_chenh_lech, 'Phí thu'].fillna(0) > df.loc[mask_chenh_lech, 'BE_Tiền bao gồm thuế'].fillna(0),
                'FE thu thừa, cần trả lại',
                'BE thu thiếu, cần bổ sung'
            )
        )
        return df
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
        
        
        results = {}

        # cols_luot_hop_ly = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', ]
        # cols_khong_thu_phi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Loại vé chuẩn']#, self.cot_nguyen_nhan_doi_soat
        # cols_luot_di_bat_thuong = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_be, self.cot_phi_dieu_chinh_fe, self.cot_ly_do_dieu_chinh]
        # cols_doc_nhieu_lan = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', self.cot_so_luot_di, self.cot_thoi_gian_giua_luot, 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ly_do_dieu_chinh]
        # cols_phi_nguoi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ly_do_dieu_chinh]
        # cols_chi_co_be = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ly_do_dieu_chinh]
        # cols_chenh_lech_phi = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế', 'CL Phí-Đối Soát', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ly_do_dieu_chinh]
        # cols_khop = ['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Trạm', 'Phí thu', 'BE_Tiền bao gồm thuế'] # , 
        # cols_bao_cao = ['Mã giao dịch chuẩn', 'Biển số chuẩn', 'Mã thẻ', 'BE_Số etag','Phí thu', 'BE_Tiền bao gồm thuế', 'Loại vé chuẩn', 'Thu nguội', 'Giao dịch chỉ có BE', 'Xe không thu phí','Lỗi Anten', 'Trạm', 'Làn chuẩn','Số lần qua trạm', 'Thời gian chuẩn', 'K/C 2 lần đọc (phút)', self.cot_phi_dieu_chinh_fe, self.cot_phi_dieu_chinh_be, self.cot_ly_do_dieu_chinh, self.cot_luot_di_hop_ly, self.cot_luot_di_bat_thuong]

        # 1. Lọc xe không có phí và xe trả phí
        df_xe_khong_tra_phi, df_xe_tra_phi = self._tach_nhom_xe_ko_thu_phi(df)
        results['Xe-KhongTraPhi'] = df_xe_khong_tra_phi
        results['Xe-TraPhi'] = df_xe_tra_phi

        # results['Xe-KhongTraPhi'] = self._select_columns(df_xe_khong_tra_phi, cols_khong_thu_phi)
        # results['Xe-TraPhi'] = self._select_columns(df_xe_tra_phi, cols_bao_cao)

        # # 2. Kiểm tra lượt xe 
        # df_kiem_luot_xe = self.kiem_tra_luot_di(df_xe_tra_phi)

        # # 0. Sheets dành riêng cho VunghiXuan ------------------ ***
        # results['VuNghiXuan'] = df_kiem_luot_xe.copy() # Đảm bảo không ảnh hưởng đến df_xe_tra_phi gốc

        # print()


        # 2. Sheet Xe không thu phí        

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