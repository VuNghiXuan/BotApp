import pandas as pd

class TimesClass:  # Thay YourClass bằng tên class thực tế của bạn
    def find_non_time_values_loop(self, df, column_name):
        non_time_values = []
        for value in df[column_name]:
            try:
                pd.to_datetime(value, errors='raise')  # errors='raise' để bắt lỗi ngay lập tức
            except (ValueError, TypeError):
                if pd.notna(value):
                    non_time_values.append(value)
        return list(set(non_time_values))  

    
    def process_time_columns(self, df_FE_BE):
        df_time = df_FE_BE.copy()
        time_column = 'Thời gian chuẩn'

        # print(f"Kiểm tra giá trị duy nhất trước chuyển đổi của cột '{time_column}':")
        # print(df_time[time_column].unique()[:20])  # In 20 giá trị duy nhất đầu tiên

        # Thử chuyển đổi sang datetime với nhiều định dạng và xử lý lỗi
        def flexible_datetime_conversion(series):
            formats = ['%d-%m-%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S',
                       '%Y/%m/%d %H:%M:%S', '%m-%d-%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                       '%H:%M:%S', '%H:%M', '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d']
            converted = pd.to_datetime(series, errors='coerce')
            for fmt in formats:
                mask_na = converted.isna()
                converted[mask_na] = pd.to_datetime(series[mask_na], format=fmt, errors='coerce', dayfirst=True)
            return converted

        df_time[time_column] = flexible_datetime_conversion(df_time[time_column])

        # print('Số dòng bị NaT sau chuyển đổi:', pd.isna(df_time[time_column]).sum())
        # print('Kiểu dữ liệu cột "Thời gian chuẩn" sau chuyển đổi:', df_time[time_column].dtype)

        nat_rows = df_time[pd.isna(df_time[time_column])]
        if not nat_rows.empty:
            print('Các dòng có giá trị NaT (5 dòng đầu):')
            print(nat_rows.head())

        # Trích xuất giờ phút giây cho các giá trị không phải NaT
        df_time['Thời gian HH:MM:SS'] = df_time[time_column].dt.strftime('%H:%M:%S')
        df_time['Thời gian chuẩn'] = df_time['Thời gian HH:MM:SS']
        df_time = df_time.drop(columns=['Thời gian HH:MM:SS'])

        # print('Thời gian chuẩn sau trích xuất giờ (5 dòng đầu):')
        # print(df_time['Thời gian chuẩn'].head(5))

        return  df_time

    def create_standardized_time(self, df):
        """
        Tạo cột 'Thời gian chuẩn' dạng chuỗi 'HH:MM:SS' ưu tiên BE, sau đó FE (chỉ lấy giờ).
        """
        try:
            df_copy = df.copy()
            standardized_time_list = []

            be_times = df_copy['BE_Thời gian qua trạm'].astype(str).tolist()
            fe_times = df_copy['Ngày giờ'].astype(str).tolist()

            for idx, fe_time in enumerate(fe_times):
                if pd.notna(pd.to_datetime(fe_time, errors='coerce')): # Kiểm tra xem BE có phải là datetime hợp lệ không
                    standardized_time_list.append(fe_time)
                elif pd.notna(pd.to_datetime(be_times[idx], errors='coerce')): # Kiểm tra xem FE có phải là datetime hợp lệ không
                    try:
                        standardized_time_list.append(be_times[idx].replace("'", "").split(' ')[1])
                    except IndexError:
                        standardized_time_list.append(None) # Xử lý trường hợp không tách được giờ
                else:
                    standardized_time_list.append(None)

            df_copy['Thời gian chuẩn'] = standardized_time_list

            # Chuyển hoá time sang pd
            df_copy = self.process_time_columns(df_copy)
            # df_copy['Thời gian chuẩn'] = df_copy['Thời gian chuẩn'].str.strip("'").str.strip()

            # df_copy['Thời gian chuẩn'].dt.strftime('%H:%M:%S')
        except Exception as e:
            print('Lỗi hàm create_standardized_time_str', e)
        return df_copy
            

# Ví dụ sử dụng (bạn cần điều chỉnh để phù hợp với cách bạn đọc dữ liệu)
# if __name__ == "__main__":
#     data = {'Ngày giờ': ["'13-04-2025 06:29:55", "2025/04/14 07:30:00", "invalid", "15-04-2025 10:00", None],
#             'BE_Thời gian qua trạm': ["'13-04-2025 08:00:00", "08:30:15", "wrong", "11:45", pd.NaT]}
#     df_FE_BE = pd.DataFrame(data)
#
#     processor = YourClass()
#     df_processed = processor.process_time_columns(df_FE_BE)
#     df_final = processor.create_standardized_time_str(df_processed)
#
    print("\nDataFrame sau khi chuẩn hóa thời gian:")
#     print(df_final[['Ngày giờ', 'FE_Thời gian chuẩn', 'BE_Thời gian qua trạm', 'BE_Thời gian chuẩn', 'Thời gian chuẩn']])