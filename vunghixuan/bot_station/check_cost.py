import pandas as pd
import numpy as np

class CheckTickets:
    def _nomal_time(self, df, col_name):
        """Chuẩn hóa cột thời gian về kiểu datetime."""
        if col_name in df.columns:
            df[col_name] = df[col_name].str.strip("'").str.strip()
            time_formats = ['%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                            '%d-%m-%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S']
            for fmt in time_formats:
                df[col_name] = df[col_name].fillna(pd.to_datetime(df[col_name], format=fmt, errors='coerce'))
        return df

    def _check_time_differences(self, merged_df, time_threshold_minutes=5):
        """Kiểm tra và đánh dấu sai lệch thời gian."""
        if 'Ngày giờ' in merged_df.columns and 'BE_Thời gian qua trạm' in merged_df.columns:
            time_diff_threshold = pd.Timedelta(minutes=time_threshold_minutes)
            time_diff = np.abs(merged_df['Ngày giờ'] - merged_df['BE_Thời gian qua trạm'])
            merged_df.loc[time_diff > time_diff_threshold, 'Tiên đoán chênh lệch'] = merged_df.loc[time_diff > time_diff_threshold, 'Tiên đoán chênh lệch'].apply(lambda x: f'{x}; Sai lệch thời gian lớn' if x else 'Sai lệch thời gian lớn')
        return merged_df

    def check_cost_station(self, merged_df):
        """
        Đối soát chênh lệch thu phí và kiểm tra các điều kiện nhóm theo biển số và chênh lệch.

        Args:
            merged_df (pd.DataFrame): DataFrame đã được gộp từ hệ thống FE và BE.
                                      Giả định các cột cần thiết đã có (ví dụ: 'Số xe đăng ký',
                                      'BE_Biển số xe', 'Phí thu', 'BE_Tiền bao gồm thuế',
                                      'Ngày giờ', 'BE_Thời gian qua trạm').

        Returns:
            pd.DataFrame: DataFrame kết quả đối soát với cột 'Tiên đoán chênh lệch'.
        """
        # Xóa cột 'Chênh lệch (Phí thu)' nếu nó đã tồn tại
        if 'Chênh lệch (Phí thu)' in merged_df.columns:
            merged_df = merged_df.drop(columns=['Chênh lệch (Phí thu)'])

        # Chuẩn hóa dữ liệu ban đầu
        merged_df['Số xe đăng ký'] = merged_df['Số xe đăng ký'].str.strip("' ").replace('', np.nan)
        merged_df['BE_Biển số xe'] = merged_df['BE_Biển số xe'].str.strip("' ").replace('', np.nan)
        merged_df['Phí thu'] = pd.to_numeric(merged_df['Phí thu'], errors='coerce').fillna(0)
        merged_df['BE_Tiền bao gồm thuế'] = pd.to_numeric(merged_df['BE_Tiền bao gồm thuế'], errors='coerce').fillna(0)

        # Chuẩn hóa cột thời gian
        merged_df = self._nomal_time(merged_df, 'Ngày giờ')
        merged_df = self._nomal_time(merged_df, 'BE_Thời gian qua trạm')

        # Tạo cột biển số xe chuẩn (nếu chưa có)
        if 'Biển số xe chuẩn' not in merged_df.columns:
            merged_df['Biển số xe chuẩn'] = merged_df['Số xe đăng ký'].fillna(merged_df['BE_Biển số xe'])

        # Tính toán chênh lệch
        merged_df['Chênh lệch (Phí thu)'] = merged_df['Phí thu'] - merged_df['BE_Tiền bao gồm thuế']
        merged_df['Ghi chú'] = ''
        merged_df['Tiên đoán chênh lệch'] = ''

        # Xác định các trường hợp chênh lệch và tạo cột Tiên đoán chênh lệch
        
        
        # Trường hợp 1: FE thu phí, BE hoàn tiền
        condition_fe_thu_be_hoan = (merged_df['Phí thu'] > 0) & (merged_df['BE_Tiền bao gồm thuế'] == 0)
        merged_df.loc[condition_fe_thu_be_hoan, 'Ghi chú'] = 'Giao dịch chỉ có FE'
        merged_df.loc[condition_fe_thu_be_hoan, 'Tiên đoán chênh lệch'] = 'FE thu phí, BE hoàn tiền'

        # # Trường hợp 2: BE hoàn tiền (BE ghi nhận tiền âm hoặc bằng 0 khi FE không thu)
        # condition_be_hoan_tien_khi_fe_khong_thu = (merged_df['Phí thu'] == 0) & (merged_df['BE_Tiền bao gồm thuế'] > 0)
        # merged_df.loc[condition_be_hoan_tien_khi_fe_khong_thu, 'Tiên đoán chênh lệch'] = 'BE hoàn tiền (FE không thu)'

        # Trường hợp 3: Chênh lệch giá trị thu phí
        condition_chenh_lech_gia_tri = ((merged_df['Chênh lệch (Phí thu)'] != 0) & (merged_df['BE_Tiền bao gồm thuế'] > 0) & (merged_df['Phí thu'] > 0))
        merged_df.loc[condition_chenh_lech_gia_tri, 'Ghi chú'] = 'Chênh lệch phí thu FE và BE'
        merged_df.loc[condition_chenh_lech_gia_tri, 'Tiên đoán chênh lệch'] = 'Chênh lệch giá trị: ' + merged_df['Chênh lệch (Phí thu)'].astype(str)

        # Trường hợp 4: FE có tiền thu, BE không có giao dịch hoặc tiền bằng 0
        condition_fe_co_tien_be_khong = (merged_df['Phí thu'] > 0) & (merged_df['BE_Biển số xe'].isnull() | (merged_df['BE_Tiền bao gồm thuế'] == 0))
        merged_df.loc[condition_fe_co_tien_be_khong, 'Ghi chú'] = 'Giao dịch chỉ có FE'
        merged_df.loc[condition_fe_co_tien_be_khong, 'Tiên đoán chênh lệch'] = 'Lỗi do đọc 2 lần, xem lại thời gian lân cận'


        # Trường hợp 5: Chỉ có giao dịch ở BE 
        condition_only_be_or_be_zero = ((merged_df['BE_Tiền bao gồm thuế'] > 0) & (merged_df['Phí thu'] == 0 ) & (merged_df['Chênh lệch (Phí thu)']< 0 ))
        merged_df.loc[condition_only_be_or_be_zero, 'Ghi chú'] = 'Giao dịch chỉ có BE'        
        merged_df.loc[condition_only_be_or_be_zero, 'Tiên đoán chênh lệch'] = 'Thu nguội do né trạm'


        # Trường hợp 6: Nghi vấn FE tính phí nhiều lần (cùng xe, thời gian ngắn) - Cần gọi hàm check_time_consistency
        # Trường hợp 7: Đối soát khớp (tạm thời, có thể được cập nhật sau kiểm tra thời gian)
        condition_khop = (merged_df['Chênh lệch (Phí thu)'] == 0) & (merged_df['Tiên đoán chênh lệch'] == '')
        merged_df.loc[condition_khop, 'Ghi chú'] = 'Đối soát khớp'

        # Sắp xếp kết quả để dễ theo dõi
        merged_df = merged_df.sort_values(by=['Biển số xe chuẩn', 'Ngày giờ', 'BE_Thời gian qua trạm'])

        return merged_df

    def check_related_discrepancies(self, merged_df, time_threshold_minutes=5):
        """
        Kiểm tra các chênh lệch liên quan đến phí thu dựa trên thông tin về xe, thời gian và các hệ thống.

        Args:
            merged_df (pd.DataFrame): DataFrame đã được đối soát cơ bản (sau khi chạy check_cost_station).
            time_threshold_minutes (int): Ngưỡng thời gian (phút) để xác định giao dịch gần nhau.

        Returns:
            pd.DataFrame: DataFrame với cột 'Tiên đoán chênh lệch' được cập nhật thông tin chi tiết về nguyên nhân chênh lệch.
        """
        merged_df = self._nomal_time(merged_df, 'Ngày giờ')
        merged_df = self._nomal_time(merged_df, 'BE_Thời gian qua trạm')

        # Kiểm tra nghi vấn FE tính phí nhiều lần cho 1 xe (thời gian gần nhau)
        def check_multiple_fe_charges(group):
            fe_times = group['Ngày giờ'].dropna().sort_values()
            time_threshold = pd.Timedelta(minutes=time_threshold_minutes)
            ghi_chu_multiple_fe = ''
            if len(fe_times) > 1:
                for i in range(len(fe_times) - 1):
                    if (fe_times.iloc[i+1] - fe_times.iloc[i]) < time_threshold:
                        ghi_chu_multiple_fe = f'{ghi_chu_multiple_fe}; Nghi vấn FE tính phí nhiều lần' if ghi_chu_multiple_fe else 'Nghi vấn FE tính phí nhiều lần'
            return ghi_chu_multiple_fe.lstrip('; ')

        grouped_fe = merged_df.groupby('Biển số xe chuẩn')
        merged_df['Tiên đoán chênh lệch_multiple_fe'] = grouped_fe.apply(check_multiple_fe_charges).fillna('')
        merged_df['Tiên đoán chênh lệch'] = merged_df.apply(lambda row: f"{row['Tiên đoán chênh lệch']}; {row['Tiên đoán chênh lệch_multiple_fe']}".lstrip('; ') if row['Tiên đoán chênh lệch_multiple_fe'] else row['Tiên đoán chênh lệch'], axis=1)
        merged_df = merged_df.drop(columns=['Tiên đoán chênh lệch_multiple_fe'])

        # Kiểm tra các trường hợp BE hoàn tiền rõ ràng hơn (BE có tiền âm)
        condition_be_hoan_tien_am = (merged_df['BE_Tiền bao gồm thuế'] < 0)
        merged_df.loc[condition_be_hoan_tien_am, 'Tiên đoán chênh lệch'] = merged_df.loc[condition_be_hoan_tien_am, 'Tiên đoán chênh lệch'].apply(lambda x: f'{x}; BE hoàn tiền' if x else 'BE hoàn tiền')

        return merged_df

    def check_time_consistency(self, merged_df, time_threshold_minutes=5):
        """
        Kiểm tra tính nhất quán về thời gian giữa FE và BE, bao gồm sai lệch lớn và nghi vấn trùng lặp.

        Args:
            merged_df (pd.DataFrame): DataFrame đã được gộp và đã được chuẩn hóa thời gian.
            time_threshold_minutes (int): Ngưỡng thời gian (phút) để xác định sai lệch lớn và trùng lặp.

        Returns:
            pd.DataFrame: DataFrame với cột 'Tiên đoán chênh lệch' được cập nhật thông tin về sai lệch thời gian.
        """
        merged_df = self._check_time_differences(merged_df, time_threshold_minutes)

        # Trường hợp 2: Nghi vấn quét trùng/nhiều làn (cần ngưỡng thời gian)
        def detect_multiple_transactions(group):
            fe_times = group['Ngày giờ'].dropna().sort_values()
            be_times = group['BE_Thời gian qua trạm'].dropna().sort_values()
            time_threshold = pd.Timedelta(minutes=time_threshold_minutes)
            ghi_chu = ''
            if len(fe_times) > 1:
                for i in range(len(fe_times) - 1):
                    if (fe_times.iloc[i+1] - fe_times.iloc[i]) < time_threshold:
                        ghi_chu = f'{ghi_chu}; Nghi vấn FE quét trùng/nhiều làn' if ghi_chu else 'Nghi vấn FE quét trùng/nhiều làn'
                        break
            if len(be_times) > 1:
                for i in range(len(be_times) - 1):
                    if (be_times.iloc[i+1] - be_times.iloc[i]) < time_threshold:
                        ghi_chu = f'{ghi_chu}; Nghi vấn BE ghi trùng' if ghi_chu else 'Nghi vấn BE ghi trùng'
                        break
            return ghi_chu.lstrip('; ')

        grouped = merged_df.groupby('Biển số xe chuẩn')
        merged_df['Tiên đoán chênh lệch_quet_trung'] = grouped.apply(detect_multiple_transactions).fillna('')
        merged_df['Tiên đoán chênh lệch'] = merged_df.apply(lambda row: f"{row['Tiên đoán chênh lệch']}; {row['Tiên đoán chênh lệch_quet_trung']}".lstrip('; ') if row['Tiên đoán chênh lệch_quet_trung'] else row['Tiên đoán chênh lệch'], axis=1)
        merged_df = merged_df.drop(columns=['Tiên đoán chênh lệch_quet_trung'])

        return merged_df

# import pandas as pd
# import numpy as np

# class CheckTickets:
#     def _nomal_time(self, df, col_name):
#         """Chuẩn hóa cột thời gian về kiểu datetime."""
#         if col_name in df.columns:
#             df[col_name] = df[col_name].str.strip("'").str.strip()
#             time_formats = ['%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
#                             '%d-%m-%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S']
#             for fmt in time_formats:
#                 df[col_name] = df[col_name].fillna(pd.to_datetime(df[col_name], format=fmt, errors='coerce'))
#         return df

#     def _check_time_differences(self, merged_df, time_threshold_minutes=5):
#         """Kiểm tra và đánh dấu sai lệch thời gian."""
#         if 'Ngày giờ' in merged_df.columns and 'BE_Thời gian qua trạm' in merged_df.columns:
#             time_diff_threshold = pd.Timedelta(minutes=time_threshold_minutes)
#             time_diff = np.abs(merged_df['Ngày giờ'] - merged_df['BE_Thời gian qua trạm'])
#             merged_df.loc[time_diff > time_diff_threshold, 'Tiên đoán chênh lệch'] = merged_df.loc[time_diff > time_diff_threshold, 'Tiên đoán chênh lệch'].apply(lambda x: f'{x}; Sai lệch thời gian lớn' if x else 'Sai lệch thời gian lớn')
#         return merged_df

#     def check_cost_station(self, merged_df):
#         """
#         Đối soát chênh lệch thu phí và kiểm tra các điều kiện nhóm theo biển số và chênh lệch.

#         Args:
#             merged_df (pd.DataFrame): DataFrame đã được gộp từ hệ thống FE và BE.
#                                       Giả định các cột cần thiết đã có (ví dụ: 'Số xe đăng ký',
#                                       'BE_Biển số xe', 'Phí thu', 'BE_Tiền bao gồm thuế',
#                                       'Ngày giờ', 'BE_Thời gian qua trạm').

#         Returns:
#             pd.DataFrame: DataFrame kết quả đối soát với cột 'Tiên đoán chênh lệch' (chưa bao gồm kiểm tra trùng lặp thời gian).
#         """
#         # Xóa cột 'Chênh lệch (Phí thu)' nếu nó đã tồn tại
#         if 'Chênh lệch (Phí thu)' in merged_df.columns:
#             merged_df = merged_df.drop(columns=['Chênh lệch (Phí thu)'])
            
#         # Chuẩn hóa dữ liệu ban đầu
#         merged_df['Số xe đăng ký'] = merged_df['Số xe đăng ký'].str.strip("' ").replace('', np.nan)
#         merged_df['BE_Biển số xe'] = merged_df['BE_Biển số xe'].str.strip("' ").replace('', np.nan)
#         merged_df['Phí thu'] = pd.to_numeric(merged_df['Phí thu'], errors='coerce').fillna(0)
#         merged_df['BE_Tiền bao gồm thuế'] = pd.to_numeric(merged_df['BE_Tiền bao gồm thuế'], errors='coerce').fillna(0)

#         # Chuẩn hóa cột thời gian
#         merged_df = self._nomal_time(merged_df, 'Ngày giờ')
#         merged_df = self._nomal_time(merged_df, 'BE_Thời gian qua trạm')

#         # Tạo cột biển số xe chuẩn (nếu chưa có)
#         if 'Biển số xe chuẩn' not in merged_df.columns:
#             merged_df['Biển số xe chuẩn'] = merged_df['Số xe đăng ký'].fillna(merged_df['BE_Biển số xe'])

#         # Tính toán chênh lệch
#         merged_df['Chênh lệch (Phí thu)'] = merged_df['Phí thu'] - merged_df['BE_Tiền bao gồm thuế']
#         merged_df['Tiên đoán chênh lệch'] = ''

#         # Xác định các trường hợp chênh lệch và tạo cột Tiên đoán chênh lệch

#         # Trường hợp 1: FE thu phí, BE hoàn tiền
#         condition_fe_thu_be_hoan = (merged_df['Phí thu'] > 0) & (merged_df['BE_Tiền bao gồm thuế'] == 0)
#         merged_df.loc[condition_fe_thu_be_hoan, 'Tiên đoán chênh lệch'] = 'FE thu phí, BE hoàn tiền'

#         # Trường hợp 3: Chênh lệch giá trị thu phí
#         condition_chenh_lech_gia_tri = (merged_df['Chênh lệch (Phí thu)'] != 0) & ~condition_fe_thu_be_hoan
#         merged_df.loc[condition_chenh_lech_gia_tri, 'Tiên đoán chênh lệch'] = 'Chênh lệch giá trị: ' + merged_df['Chênh lệch (Phí thu)'].astype(str)

#         # Trường hợp 4: Chỉ có giao dịch ở FE
#         condition_only_fe = merged_df['BE_Biển số xe'].isnull()
#         merged_df.loc[condition_only_fe, 'Tiên đoán chênh lệch'] = 'Chỉ có giao dịch ở FE'

#         # Trường hợp 5: Chỉ có giao dịch ở BE
#         condition_only_be = merged_df['Số xe đăng ký'].isnull()
#         merged_df.loc[condition_only_be, 'Tiên đoán chênh lệch'] = 'Chỉ có giao dịch ở BE'

#         # Trường hợp 7: Đối soát khớp (tạm thời, có thể được cập nhật sau kiểm tra thời gian)
#         condition_khop = (merged_df['Chênh lệch (Phí thu)'] == 0) & (merged_df['Tiên đoán chênh lệch'] == '')
#         merged_df.loc[condition_khop, 'Tiên đoán chênh lệch'] = 'Đối soát khớp'

#         # Sắp xếp kết quả để dễ theo dõi
#         merged_df = merged_df.sort_values(by=['Biển số xe chuẩn', 'Ngày giờ', 'BE_Thời gian qua trạm'])

#         # Xác định các cột trả về
#         # columns_to_return = [col for col in merged_df.columns if col in ['Mã giao dịch', 'Số xe đăng ký', 'BE_Biển số xe', 'Biển số xe chuẩn', 'Mã thẻ', 'Phí thu',
#         #                                                                  'BE_Thời gian qua trạm', 'BE_Làn', 'BE_Tổng tiền bao gồm thuế',
#         #                                                                  'Chênh lệch (Phí thu)', 'Tiên đoán chênh lệch']]
#         # return merged_df[columns_to_return]
#         head = merged_df.columns.tolist()
#         values = merged_df.values.tolist()
#         list_2D = values.insert(0,head)
#         return merged_df

#     def check_time_consistency(self, merged_df, time_threshold_minutes=5):
#         """
#         Kiểm tra tính nhất quán về thời gian giữa FE và BE, bao gồm sai lệch lớn và nghi vấn trùng lặp.

#         Args:
#             merged_df (pd.DataFrame): DataFrame đã được gộp và đã được chuẩn hóa thời gian.
#             time_threshold_minutes (int): Ngưỡng thời gian (phút) để xác định sai lệch lớn và trùng lặp.

#         Returns:
#             pd.DataFrame: DataFrame với cột 'Tiên đoán chênh lệch' được cập nhật thông tin về sai lệch thời gian.
#         """
#         merged_df = self._check_time_differences(merged_df, time_threshold_minutes)

#         # Trường hợp 2: Nghi vấn quét trùng/nhiều làn (cần ngưỡng thời gian)
#         def detect_multiple_transactions(group):
#             fe_times = group['Ngày giờ'].dropna().sort_values()
#             be_times = group['BE_Thời gian qua trạm'].dropna().sort_values()
#             time_threshold = pd.Timedelta(minutes=time_threshold_minutes)
#             ghi_chu = ''
#             if len(fe_times) > 1:
#                 for i in range(len(fe_times) - 1):
#                     if (fe_times.iloc[i+1] - fe_times.iloc[i]) < time_threshold:
#                         ghi_chu = f'{ghi_chu}; Nghi vấn FE quét trùng/nhiều làn' if ghi_chu else 'Nghi vấn FE quét trùng/nhiều làn'
#                         break
#             if len(be_times) > 1:
#                 for i in range(len(be_times) - 1):
#                     if (be_times.iloc[i+1] - be_times.iloc[i]) < time_threshold:
#                         ghi_chu = f'{ghi_chu}; Nghi vấn BE ghi trùng' if ghi_chu else 'Nghi vấn BE ghi trùng'
#                         break
#             return ghi_chu.lstrip('; ')

#         grouped = merged_df.groupby('Biển số xe chuẩn')
#         merged_df['Tiên đoán chênh lệch_quet_trung'] = grouped.apply(detect_multiple_transactions).fillna('')
#         merged_df['Tiên đoán chênh lệch'] = merged_df.apply(lambda row: f"{row['Tiên đoán chênh lệch']}; {row['Tiên đoán chênh lệch_quet_trung']}".lstrip('; ') if row['Tiên đoán chênh lệch_quet_trung'] else row['Tiên đoán chênh lệch'], axis=1)
#         merged_df = merged_df.drop(columns=['Tiên đoán chênh lệch_quet_trung'])

#         return merged_df


