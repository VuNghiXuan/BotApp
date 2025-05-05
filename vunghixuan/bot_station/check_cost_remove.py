import pandas as pd
import numpy as np

class CheckCost:
    def __init__(self):
        add_col_names = ['Phí khớp FE', 'Phí khớp BE', 'Chênh lệch khớp', 'Nguyên nhân']
        self.fee_matching_FE = add_col_names[0] # Thêm cột phí điều chỉnh FE
        self.fee_matching_BE = add_col_names[1] # Thêm cột phí điều chỉnh BE
        self.fee_matching_diff = add_col_names[2]
        self.reason = add_col_names[3] # Thêm cột phí nguyên nhân

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
        
        # Lọc ra các dòng mà cả hai cột thời gian đều không phải NaT
        valid_times_df = merged_df.dropna(subset=['Ngày giờ', 'BE_Thời gian qua trạm'])
        
        if not valid_times_df.empty:
            time_diff = np.abs(valid_times_df['Ngày giờ'] - valid_times_df['BE_Thời gian qua trạm'])
        
        # Lấy index của các dòng có sai lệch thời gian lớn
        large_diff_indices = valid_times_df.loc[time_diff > time_diff_threshold].index
        
        # Cập nhật cột 'Tiên đoán chênh lệch' cho các dòng có sai lệch thời gian lớn trong DataFrame gốc
        merged_df.loc[large_diff_indices, 'Tiên đoán chênh lệch'] = merged_df.loc[large_diff_indices, 'Tiên đoán chênh lệch'].apply(lambda x: f'{x}; Sai lệch thời gian lớn' if x else 'Sai lệch thời gian lớn')
        
        return merged_df

    def add_summary_row(self, df, sum_column):
        """
        Adds a summary row to the end of a DataFrame, calculating the sum
        of a specified column and optionally adding counts of unique values
        from a list of specified columns.

        Args:
            df (pd.DataFrame): The input DataFrame.
            sum_column (str): The name of the column to calculate the sum for.
            count_unique_columns (list, optional): A list of column names to
                                                   count unique values from.
                                                   Defaults to None.

        Returns:
            pd.DataFrame: A new DataFrame with the summary row appended.
        """
        if df is None or df.empty:
            return pd.DataFrame()

        if 'Mã giao dịch' in df.columns:
            summary_data = {'Mã giao dịch': f'Tổng cộng: {len(df)} giao dịch'}

        for col_name in sum_column:
            if col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
                summary_data[col_name] = df[col_name].sum()
            # else:
            #     summary_data[col_name] = ''  # Or some other placeholder

        summary_row = pd.DataFrame([summary_data])
        return pd.concat([df, summary_row], ignore_index=True)
    

    def predict_fee_differentials(self, merged_df):
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
        # merged_df['Số xe đăng ký'] = merged_df['Số xe đăng ký'].str.strip("' ").replace('', np.nan)
        # merged_df['BE_Biển số xe'] = merged_df['BE_Biển số xe'].str.strip("' ").replace('', np.nan)
        merged_df['Phí thu'] = pd.to_numeric(merged_df['Phí thu'], errors='coerce').fillna(0)
        merged_df['BE_Tiền bao gồm thuế'] = pd.to_numeric(merged_df['BE_Tiền bao gồm thuế'], errors='coerce').fillna(0)

        # Chuẩn hóa cột thời gian
        merged_df = self._nomal_time(merged_df, 'Ngày giờ')
        merged_df = self._nomal_time(merged_df, 'BE_Thời gian qua trạm')

        # # Tạo cột biển số chuẩn (nếu chưa có)
        # if 'Biển số chuẩn' not in merged_df.columns:
        #     merged_df['Biển số chuẩn'] = merged_df['Số xe đăng ký'].fillna(merged_df['BE_Biển số xe'])

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
        merged_df.loc[condition_fe_co_tien_be_khong, 'Tiên đoán chênh lệch'] = 'Nghi vấn lỗi trùng lặp'


        # Trường hợp 5: Chỉ có giao dịch ở BE 
        condition_only_be_or_be_zero = ((merged_df['BE_Tiền bao gồm thuế'] > 0) & (merged_df['Phí thu'] == 0 ) & (merged_df['Chênh lệch (Phí thu)']< 0 ))
        merged_df.loc[condition_only_be_or_be_zero, 'Ghi chú'] = 'Giao dịch chỉ có BE'        
        merged_df.loc[condition_only_be_or_be_zero, 'Tiên đoán chênh lệch'] = 'Thu nguội do né trạm'


        # Trường hợp 6: Nghi vấn FE tính phí nhiều lần (cùng xe, thời gian ngắn) - Cần gọi hàm check_time_consistency
        # Trường hợp 7: Đối soát khớp (tạm thời, có thể được cập nhật sau kiểm tra thời gian)
        condition_khop = (merged_df['Chênh lệch (Phí thu)'] == 0) & (merged_df['Tiên đoán chênh lệch'] == '')
        merged_df.loc[condition_khop, 'Ghi chú'] = 'Đối soát khớp'
        merged_df.loc[condition_khop, 'Tiên đoán chênh lệch'] = 'Khớp'

        # Sắp xếp kết quả để dễ theo dõi
        merged_df = merged_df.sort_values(by=['Biển số chuẩn', 'Ngày giờ', 'BE_Thời gian qua trạm'])

        return merged_df
    # """
    # def adjust_fee_for_evasion(self, df):
    #     """
    #     Điều chỉnh phí thu (FE và BE) cho các trường hợp 'Thu nguội do né trạm'
    #     sao cho chênh lệch phí bằng 0, đồng thời thêm cột 'Nguyên nhân phí nguội'.
        

    #     Args:
    #     df (pd.DataFrame): DataFrame chứa thông tin đối soát phí, đã được xác định
    #     các trường hợp 'Thu nguội do né trạm' trong cột 'Tiên đoán chênh lệch'.
    #     Yêu cầu DataFrame có các cột: 'Phí thu', 'BE_Tiền bao gồm thuế',
    #     'Chênh lệch (Phí thu)', 'Tiên đoán chênh lệch'.
        

    #     Returns:
    #     pd.DataFrame: DataFrame đã điều chỉnh phí và thêm cột 'Nguyên nhân phí nguội'.
    #     """
    #     if not all(col in df.columns for col in ['Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch (Phí thu)', 'Tiên đoán chênh lệch']):
    #         print("Lỗi: DataFrame cần có các cột 'Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch (Phí thu)', 'Tiên đoán chênh lệch'.")
    #         return pd.DataFrame()
        

    #     df_adjusted = df.copy()
        

    #     # Thêm cột 'Nguyên nhân phí nguội'
    #     df_adjusted['Nguyên nhân phí nguội'] = np.where(
    #     df_adjusted['Tiên đoán chênh lệch'].str.contains('Thu nguội do né trạm', na=False),
    #     'Thu nguội do né trạm',
    #     np.nan
    #     )
        

    #     # Điều chỉnh phí thu và BE để chênh lệch bằng 0 cho các trường hợp 'Thu nguội do né trạm'
    #     for index, row in df_adjusted.iterrows():
    #         if 'Thu nguội do né trạm' in str(row['Tiên đoán chênh lệch']):
    #             if row['Chênh lệch (Phí thu)'] > 0:
    #                 df_adjusted.loc[index, 'BE_Tiền bao gồm thuế'] = row['Phí thu']
    #             elif row['Chênh lệch (Phí thu)'] < 0:
    #                 df_adjusted.loc[index, 'Phí thu'] = row['BE_Tiền bao gồm thuế']
    #                 df_adjusted.loc[index, 'Chênh lệch (Phí thu)'] = 0.0
        

    #     # Xóa cột 'Tiên đoán chênh lệch' sau khi đã xử lý và có thông tin ở cột mới
    #     df_adjusted = df_adjusted.drop(columns=['Tiên đoán chênh lệch'])
        

    #     return df_adjusted
    # """

    def result_evasion_toll(self, checked_df):
        """
        Filters all records of vehicles where the 'Tiên đoán chênh lệch'
        (Prediction of Discrepancy) column contains the phrase
        'Thu nguội do né trạm' (Post-collection due to toll evasion).

        Args:
            checked_df (pd.DataFrame): DataFrame processed by the check_cost_station function.

        Returns:
            pd.DataFrame: DataFrame containing all records where the
                          'Tiên đoán chênh lệch' column indicates
                          'Thu nguội do né trạm'.
        """
        evasion_df = checked_df[checked_df['Tiên đoán chênh lệch'].str.contains('Thu nguội do né trạm', na=False)].copy()
        
        # Thêm cột Phí thu FE điều chỉnh       
        evasion_df[self.fee_matching_FE] = evasion_df['BE_Tiền bao gồm thuế']
        # Thêm cột Phí thu BE điều chỉnh  
        evasion_df[self.fee_matching_BE] = evasion_df['BE_Tiền bao gồm thuế']
        # Thêm cột xác định nguyên nhân
        evasion_df[self.fee_matching_diff] = evasion_df['BE_Tiền bao gồm thuế']- evasion_df['BE_Tiền bao gồm thuế']
        # Thêm cột xác định nguyên nhân
        evasion_df[self.reason] = 'Kiểm tra Chứng từ MTC và Bổ sung Phí nguội cho FE'

        evasion_df = self.add_summary_row(evasion_df, ['Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch (Phí thu)',self.fee_matching_FE, self.fee_matching_BE, self.fee_matching_diff])
        
        # Xóa cột 'Tiên đoán chênh lệch' sau khi đã xử lý và có thông tin ở cột mới
        evasion_df = evasion_df.drop(columns=['Tiên đoán chênh lệch'])
        return evasion_df
    
    def fee_diff_filtered_cars(self, checked_df):
        """
        Lọc ra tất cả các bản ghi của các xe có biển số mà có ít nhất một bản ghi
        có chênh lệch phí thu khác 0.

        Args:
            checked_df (pd.DataFrame): DataFrame đã được xử lý bởi hàm check_cost_station.

        Returns:
            pd.DataFrame: DataFrame chứa tất cả các bản ghi của các xe có chênh lệch phí thu khác 0.
        """
        discrepancy_df = checked_df[checked_df['Chênh lệch (Phí thu)'] != 0]
        discrepancy_vehicles = pd.concat([discrepancy_df['Biển số chuẩn'],
                                        discrepancy_df['Số xe đăng ký'],
                                        discrepancy_df['BE_Biển số xe']]).unique()
        discrepancy_vehicles_cleaned = pd.Series(discrepancy_vehicles).dropna().unique()

        # Tạo một DataFrame mới chứa tất cả các bản ghi của các xe có biển số trong danh sách discrepancy_vehicles_cleaned
        filtered_df = checked_df[
            checked_df['Biển số chuẩn'].isin(discrepancy_vehicles_cleaned) |
            checked_df['Số xe đăng ký'].isin(discrepancy_vehicles_cleaned) |
            checked_df['BE_Biển số xe'].isin(discrepancy_vehicles_cleaned)
        ].copy()

        return filtered_df

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

        grouped_fe = merged_df.groupby('Biển số chuẩn')
        merged_df['Tiên đoán chênh lệch_multiple_fe'] = grouped_fe.apply(check_multiple_fe_charges).fillna('')
        merged_df['Tiên đoán chênh lệch'] = merged_df.apply(lambda row: f"{row['Tiên đoán chênh lệch']}; {row['Tiên đoán chênh lệch_multiple_fe']}".lstrip('; ') if row['Tiên đoán chênh lệch_multiple_fe'] else row['Tiên đoán chênh lệch'], axis=1)
        merged_df = merged_df.drop(columns=['Tiên đoán chênh lệch_multiple_fe'])

        # Kiểm tra các trường hợp BE hoàn tiền rõ ràng hơn (BE có tiền âm)
        condition_be_hoan_tien_am = (merged_df['BE_Tiền bao gồm thuế'] < 0)
        merged_df.loc[condition_be_hoan_tien_am, 'Tiên đoán chênh lệch'] = merged_df.loc[condition_be_hoan_tien_am, 'Tiên đoán chênh lệch'].apply(lambda x: f'{x}; BE hoàn tiền' if x else 'BE hoàn tiền')

        return merged_df

    def fillter_predict_multiple_camera_reads(self, df):
        """
        Lọc DataFrame để lấy các bản ghi của các xe mà cột 'Tiên đoán chênh lệch'
        có giá trị chứa cụm từ 'Nghi vấn lỗi trùng lặp'. Sau đó, lấy biển số xe
        và lọc ra tất cả các dòng có cùng biển số xe.

        Args:
        df (pd.DataFrame): DataFrame chứa thông tin đối soát phí.
        Yêu cầu DataFrame có cột 'Biển số chuẩn' và 'Tiên đoán chênh lệch'.

        Returns:
        pd.DataFrame: DataFrame chỉ chứa các bản ghi của các xe có 'Tiên đoán chênh lệch'
        là 'Nghi vấn lỗi trùng lặp' và tất cả các dòng khác có cùng biển số xe.
        """
        if 'Tiên đoán chênh lệch' not in df.columns or 'Biển số chuẩn' not in df.columns:
            print("Lỗi: DataFrame cần có cột 'Tiên đoán chênh lệch' và 'Biển số chuẩn'.")
            return pd.DataFrame()

        # Lọc các dòng có 'Tiên đoán chênh lệch' là 'Nghi vấn lỗi trùng lặp'
        nghi_van_df = df[df['Tiên đoán chênh lệch'] == 'Nghi vấn lỗi trùng lặp']

        if nghi_van_df.empty:
            return pd.DataFrame()

        # Lấy danh sách các biển số xe có nghi vấn trùng lặp
        bien_so_nghi_van = nghi_van_df['Biển số chuẩn'].unique()

        # Lọc DataFrame ban đầu để lấy tất cả các dòng có biển số xe nằm trong danh sách nghi vấn
        df_result = df[df['Biển số chuẩn'].isin(bien_so_nghi_van)].copy()

        df_result = self.add_summary_row(df_result, ['Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch (Phí thu)'])

        return df_result

    # def fillter_predict_multiple_camera_reads(self, df):
    #     """
    #     Lọc DataFrame để lấy các bản ghi của các xe mà cột 'Tiên đoán chênh lệch'
    #     có giá trị chứa cụm từ 'Nghi vấn lỗi trùng lặp'.
        

    #     Args:
    #     df (pd.DataFrame): DataFrame chứa thông tin đối soát phí.
    #     Yêu cầu DataFrame có cột 'Biển số chuẩn' và 'Tiên đoán chênh lệch'.
        

    #     Returns:
    #     pd.DataFrame: DataFrame chỉ chứa các bản ghi của các xe có 'Tiên đoán chênh lệch'
    #     là 'Nghi vấn lỗi trùng lặp'.
    #     """
    #     if 'Tiên đoán chênh lệch' not in df.columns or 'Biển số chuẩn' not in df.columns:
    #         print("Lỗi: DataFrame cần có cột 'Tiên đoán chênh lệch' và 'Biển số chuẩn'.")
    #         return pd.DataFrame()
        

    #     # Lọc các dòng có 'Tiên đoán chênh lệch' là 'Nghi vấn lỗi trùng lặp'
    #     multiple_reads_df = df[df['Tiên đoán chênh lệch'] == 'Nghi vấn lỗi trùng lặp'].copy()        
    #     multiple_reads_df = self.add_summary_row(multiple_reads_df, ['Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch (Phí thu)'])


    #     return multiple_reads_df

    def find_multiple_camera_reads_with_fee_discrepancy(self, df):
        """
        Tìm các lỗi do camera đọc nhiều lần cho cùng 1 biển số gây chênh lệch phí.
        Lọc các giao dịch mà chỉ có thông tin phí thu (FE), không có thông tin phí
        qua trạm (BE), được đánh dấu 'Nghi vấn lỗi trùng lặp', và nhóm theo
        biển số xe để xác định các trường hợp quét trùng.
        

        Args:
        df (pd.DataFrame): DataFrame chứa thông tin đối soát phí.
        Yêu cầu DataFrame có các cột: 'Biển số chuẩn', 'Phí thu',
        'BE_Tiền bao gồm thuế', 'Ngày giờ', 'Làn', 'Tiên đoán chênh lệch'.
        

        Returns:
        pd.DataFrame: DataFrame chứa các giao dịch nghi ngờ lỗi do camera đọc
        nhiều lần gây chênh lệch phí, đã được sắp xếp theo biển số xe và thời gian.
        In ra thông tin chi tiết về các lỗi phát hiện.
        """
        if not all(col in df.columns for col in ['Biển số chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', 'Ngày giờ', 'Làn', 'Tiên đoán chênh lệch']):
            print("Lỗi: DataFrame cần có các cột 'Biển số chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', 'Ngày giờ', 'Làn', 'Tiên đoán chênh lệch'.")
            return pd.DataFrame()
        

        # Lọc các giao dịch chỉ có phí thu và được đánh dấu lỗi camera
        fe_only_multiple_reads = df[(df['Phí thu'] > 0) & (df['BE_Tiền bao gồm thuế'] == 0) & (df['Tiên đoán chênh lệch'] == 'Nghi vấn lỗi trùng lặp')].copy()
        
        

        if fe_only_multiple_reads.empty:
            print("Không tìm thấy lỗi camera đọc nhiều lần gây chênh lệch phí.")
            return pd.DataFrame()
            

        # Chuyển đổi cột 'Ngày giờ' sang kiểu datetime để dễ dàng so sánh
        fe_only_multiple_reads['Ngày giờ'] = pd.to_datetime(fe_only_multiple_reads['Ngày giờ'], errors='coerce')
        fe_only_multiple_reads = fe_only_multiple_reads.dropna(subset=['Ngày giờ']).sort_values(by=['Biển số chuẩn', 'Ngày giờ'])
        

        # Nhóm theo biển số xe và kiểm tra các giao dịch liên tiếp
        grouped = fe_only_multiple_reads.groupby('Biển số chuẩn')
        suspicious_transactions = []
        

        for plate, group in grouped:
            if len(group) >= 2:
                # Sắp xếp lại theo thời gian để đảm bảo tính liên tục
                group = group.sort_values(by='Ngày giờ')
                for i in range(len(group) - 1):
                    current_transaction = group.iloc[i]
                    next_transaction = group.iloc[i+1]            

                    # Kiểm tra xem thời gian giữa hai giao dịch có gần nhau không (ví dụ: vài phút)
                    time_difference = (next_transaction['Ngày giờ'] - current_transaction['Ngày giờ']).total_seconds()
                    if 1 <= time_difference <= 300: # Giới hạn thời gian là 5 phút (300 giây) - có thể điều chỉnh
                        print(f"Nghi ngờ quét trùng biển số '{plate}':")
                        print(f"- Giao dịch 1: Ngày giờ = {current_transaction['Ngày giờ']}, Làn = {current_transaction['Làn']}")
                        print(f"- Giao dịch 2: Ngày giờ = {next_transaction['Ngày giờ']}, Làn = {next_transaction['Làn']}")
                        suspicious_transactions.append(current_transaction.to_dict())
                        suspicious_transactions.append(next_transaction.to_dict())

                        # Xoá nội dung cột tiên đoán chênh lệch ='' lần vào trạn đấu 
        

        suspicious_df = pd.DataFrame(suspicious_transactions).drop_duplicates()
        # Thêm hàm lấy phần df còn lại sau lọc để tìm ra lỗi khác ở đây
        

        if suspicious_df.empty:
            print("Không phát hiện thêm các lỗi quét trùng camera nghi ngờ gây chênh lệch phí.")
        else:
            print("\nCác giao dịch nghi ngờ quét trùng camera gây chênh lệch phí:")
        print(suspicious_df)
        

        return suspicious_df