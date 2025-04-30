import pandas as pd
import numpy as np
import re

class NoMalFEBE():
    def __init__(self, df_fe, df_be):
        self.df_fe = df_fe
        self.df_be = df_be
    
    
    def get_id_column_name(self, col_name, pd_columns):
        if col_name in pd_columns:
            return pd_columns.get_loc(col_name)
        else:
            return None

    def load_and_standardize_fe_be(self):
        try:
            if self.df_fe is None or self.df_be is None:
                raise ValueError("Không có dữ liệu FE hoặc BE để so sánh.")            
           

            col_name = 'Mã giao dịch'
            id_col_name_in_fe = self.get_id_column_name(col_name, self.df_fe.columns)
            id_col_name_in_be = self.get_id_column_name(col_name, self.df_be.columns)
            if id_col_name_in_fe is None or id_col_name_in_be is None:
                raise ValueError("Cột 'mã giao dịch' không tồn tại trong một hoặc cả hai file.")

            # Chuẩn hóa cột 'Mã giao dịch' cho FE và BE
            col_names_FE = ['Số xe đăng ký'] # Không cần chuẩn hoá cột 'Mã giao dịch' và , 'Mã thẻ': có sẵn dấu ' rồi
            fe_processed = self.df_fe.copy()
            for name in col_names_FE:
                fe_processed = self._load_and_standardize_fe(fe_processed, name)
            
            col_names_BE = ['Mã giao dịch', 'Biển số xe', 'Số etag']
            be_processed = self.df_be.copy()
            for name in col_names_BE:                
                be_processed = self._load_and_standardize_be(be_processed, name)
            
            # # Chuẩn hoá lại file gốc
            # self.df_fe = fe_processed
            # self.df_be = be_processed
            return fe_processed, be_processed
        except Exception as e:
            print ("Lỗi: ",e)

    def _load_and_standardize_fe(self, df, col_name):
        if df is not None and col_name in df.columns:
            # Chuyển đổi sang kiểu chuỗi
            df[col_name] = df[col_name].astype(str)
            # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
            df_cleaned = df[df[col_name] != 'nan'].copy()
            # Thêm dấu nháy đơn nếu giá trị không phải là 'nan'
            # print(df_cleaned[col_name].head(20))
            df_cleaned[col_name] = df_cleaned[col_name].apply(lambda x: "'" + x if pd.notna(x) else x)
            return df_cleaned
        elif df is None:
            print("Chưa có dữ liệu FE được tải.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán
        else:
            print(f"Không tìm thấy cột '{col_name}' trong dữ liệu FE.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán

    def _load_and_standardize_be(self, df, col_name):
        if df is not None and col_name in df.columns:
            # Chuyển đổi sang kiểu chuỗi
            df[col_name] = df[col_name].astype(str)
            # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
            df_cleaned = df[df[col_name] != 'nan'].copy()
            # Thêm dấu nháy đơn nếu giá trị không phải là 'nan'
            # print(df_cleaned[col_name].head(20))
            df_cleaned[col_name] = df_cleaned[col_name].apply(lambda x: "'" + x if pd.notna(x) else x)
            return df_cleaned
        elif df is None:
            print("Chưa có dữ liệu BE được tải.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán
        else:
            print(f"Không tìm thấy cột '{col_name}' trong dữ liệu BE.")
            return pd.DataFrame()  # Trả về DataFrame rỗng để nhất quán

    def get_mgd_has_value_0(self, df, col_name):
        """
        Kiểm tra và trả về các dòng có mã giao dịch trùng lặp trong DataFrame
        sau khi đã loại bỏ các dòng có giá trị 'nan' trong cột chỉ định.

        Args:
            df (pd.DataFrame): DataFrame cần kiểm tra.
            col_name (str, optional): Tên cột chứa mã giao dịch.
                                       Mặc định là 'Mã giao dịch'.

        Returns:
            pd.DataFrame: DataFrame chứa các dòng có mã giao dịch trùng lặp
                           sau khi đã loại bỏ dòng có giá trị 'nan'.
                           Trả về DataFrame rỗng nếu không có trùng lặp hoặc
                           cột không tồn tại.
        """
        if df is not None and col_name in df.columns:
            # Loại bỏ các dòng có giá trị 'nan' trong cột chỉ định
            df_cleaned = df.copy()            
            # Kiểm tra trùng lặp trên DataFrame đã loại bỏ 'nan'
            duplicated_mask = df_cleaned.duplicated(subset=[col_name], keep=False)
            return df_cleaned[duplicated_mask]
        elif df is None:
            print("DataFrame đầu vào là None.")
            return pd.DataFrame()
        else:
            print(f"Không tìm thấy cột '{col_name}' trong DataFrame.")
            return pd.DataFrame()
    
    def add_summary_row(self, df, cost_col_name='Chi phí', ma_giao_dich_col='Mã giao dịch'):
        """
        Thêm dòng tổng số giao dịch và tổng chi phí vào cuối DataFrame.

        Args:
            df (pd.DataFrame): DataFrame cần thêm dòng tổng kết.
            cost_col_name (str, optional): Tên cột chứa chi phí.
                                           Mặc định là 'Chi phí'.
            ma_giao_dich_col (str, optional): Tên cột chứa mã giao dịch.
                                               Mặc định là 'Mã giao dịch'.

        Returns:
            pd.DataFrame: DataFrame đã thêm dòng tổng kết.
        """
        if df is not None and not df.empty:
            total_transactions = len(df)-1
            summary_data = {}

            # Lấy danh sách tất cả các cột
            all_cols = df.columns.tolist()

            # Đảm bảo cột đầu tiên có giá trị 'TỔNG'
            if all_cols:
                first_col = all_cols[0]
                summary_data[first_col] = ['TỔNG']

            # Đưa tổng số giao dịch vào cột mã giao dịch
            if ma_giao_dich_col in all_cols:
                summary_data[ma_giao_dich_col] = [f'({total_transactions} giao dịch)']

            # Tính và đưa tổng chi phí vào cột tương ứng
            if cost_col_name in all_cols :#and pd.api.types.is_numeric_dtype(df[cost_col_name]):
                summary_data[cost_col_name] = [df[cost_col_name].sum()]

            # Tạo DataFrame dòng tổng kết
            summary = pd.DataFrame(summary_data)

            # Nối dòng tổng kết vào cuối DataFrame, điền các cột thiếu bằng NaN
            df_with_summary = pd.concat([df, summary], ignore_index=True, sort=False)
            return df_with_summary
        elif df is None:
            print("DataFrame đầu vào là None.")
            return pd.DataFrame()
        else:
            print("DataFrame đầu vào rỗng.")
            return df.copy() # Trả về bản sao của DataFrame rỗng
    
    def _prepare_and_rename_cols(self, df, col_list, prefix=''):
        """
        Kiểm tra sự tồn tại của các cột trong DataFrame và trả về DataFrame
        với các cột đã chọn và có tiền tố (nếu cần).

        Args:
            df (pd.DataFrame): DataFrame đầu vào.
            col_list (list): Danh sách tên các cột cần chọn.
            prefix (str, optional): Tiền tố để thêm vào tên cột. Mặc định là ''.

        Returns:
            pd.DataFrame: DataFrame chứa các cột đã chọn và được đổi tên,
                         hoặc None nếu có cột không tồn tại.
        """
        missing_cols = [col for col in col_list if col not in df.columns]
        if missing_cols:
            print(f"Lỗi: Các cột sau không tồn tại trong DataFrame: {missing_cols}")
            return None

        selected_df = df[col_list].copy()
        if prefix:
            rename_dict = {col: f'{prefix}_{col}' for col in selected_df.columns}
            selected_df.rename(columns=rename_dict, inplace=True)
        return selected_df

    

    def _select_and_rename_be_cols(self, df_be, ma_giao_dich_col, colname_be_lists):
        """Chọn và đổi tên các cột của DataFrame BE."""
        be_selected = df_be[[ma_giao_dich_col] + colname_be_lists].copy()
        be_renamed_cols = {col: f'BE_{col}' if col != ma_giao_dich_col else col for col in be_selected.columns}
        be_selected.rename(columns=be_renamed_cols, inplace=True)
        return be_selected
    
    def _merge_fe_be_data(self, df_fe, be_selected, ma_giao_dich_col):
        """Gộp DataFrame FE và BE dựa trên mã giao dịch và tạo cột 'Mã giao dịch chuẩn'."""
        merged_df = pd.merge(df_fe, be_selected, on=ma_giao_dich_col, how='outer')
        merged_df['Mã giao dịch chuẩn'] = merged_df[ma_giao_dich_col]
        return merged_df
    
    
    def _add_summary_row(self, merged_df, df_fe, df_be, ma_giao_dich_col, sum_colname_fe, sum_colname_be):
        """Thêm dòng tổng vào DataFrame đã gộp."""
        summary_data = {}
        all_cols = merged_df.columns.tolist()
        all_cols.append('Chênh lệch (Phí thu)')

        if all_cols:
            summary_data[all_cols[0]] = ['TỔNG']

        if ma_giao_dich_col in all_cols:
            total_fe = len(df_fe)-1
            total_be = len(df_be)-1
            summary_data[ma_giao_dich_col] = [f'Tổng cộng: \nFE có {total_fe} giao dịch, \nBE có {total_be} giao dịch']

        for col in sum_colname_fe:
            if col in all_cols and pd.api.types.is_numeric_dtype(merged_df[col]):
                summary_data[col] = [merged_df[col].sum()]
            else:
                summary_data.setdefault(col, [None])

        for col in sum_colname_be:
            be_col = f'BE_{col}'
            if be_col in all_cols and pd.api.types.is_numeric_dtype(merged_df[be_col]):
                summary_data[be_col] = [merged_df[be_col].sum()]
            else:
                summary_data.setdefault(be_col, [None])

        if 'Phí thu' in merged_df.columns and f'BE_{sum_colname_be[0]}' in merged_df.columns and sum_colname_be:
            be_phi_col = f'BE_{sum_colname_be[0]}'
            merged_df['Chênh lệch (Phí thu)'] = merged_df['Phí thu'].fillna(0) - merged_df[be_phi_col].fillna(0)
            merged_df = merged_df.infer_objects()
            summary_data['Chênh lệch (Phí thu)'] = [merged_df['Chênh lệch (Phí thu)'].sum()]
        else:
            summary_data.setdefault('Chênh lệch (Phí thu)', [None])

        summary_df = pd.DataFrame(summary_data)
        final_df = pd.concat([merged_df, summary_df], ignore_index=True, sort=False)

        # Chuẩn hoá cột phí thu
        final_df['Phí thu'] = pd.to_numeric(final_df['Phí thu'], errors='coerce')
        final_df['BE_Tiền bao gồm thuế'] = pd.to_numeric(final_df['BE_Tiền bao gồm thuế'], errors='coerce')        
        

        return final_df

    def summarize_data(self, df_list, colname_fe_lists, colname_be_lists, sum_colname_fe, sum_colname_be, ma_giao_dich_col='Mã giao dịch'):
        """
        Tổng hợp dữ liệu từ hai DataFrame dựa trên mã giao dịch và tạo cột 'Mã giao dịch chuẩn'
        bằng cách sử dụng các hàm tách biệt.
        """
        if len(df_list) != 2:
            print("Lỗi: df_list phải chứa đúng hai DataFrame.")
            return pd.DataFrame()

        df_fe = df_list[0].copy()
        df_be = df_list[1].copy()
        

        if ma_giao_dich_col not in df_fe.columns or ma_giao_dich_col not in df_be.columns:
            print(f"Lỗi: Cột '{ma_giao_dich_col}' không tồn tại trong một hoặc cả hai DataFrame.")
            return pd.DataFrame()

        # Phần gộp dữ liệu
        fe_selected = df_fe[[ma_giao_dich_col] + colname_fe_lists].copy()
        be_selected = self._select_and_rename_be_cols(df_be, ma_giao_dich_col, colname_be_lists)
        merged_df = self._merge_fe_be_data(fe_selected, be_selected, ma_giao_dich_col)

        # Phần thêm dòng tổng
        final_df = self._add_summary_row(merged_df, df_fe, df_be, ma_giao_dich_col, sum_colname_fe, sum_colname_be)

        return final_df

    # Chuân hoá Sheet tổng hợp dữ liệu
    def merge_FE_BE_with_standard_mgd(self, df_list):
        col_name = 'Mã giao dịch'
        colname_fe = ['Số xe đăng ký', 'Mã thẻ','Phí thu', 'Làn','Ngày giờ', 'Loại vé']
        colname_be = ['Biển số xe', 'Số etag', 'Loại giá vé', 'Tiền bao gồm thuế', 'Thời gian qua trạm', 'Làn']
        sum_col_fe = ['Phí thu']
        sum_col_be = ['Tiền bao gồm thuế']

        # Sheet Tổng hợp dữ liệu
        df_FE_BE = self.summarize_data(
            df_list,
            colname_fe,
            colname_be,
            sum_col_fe,
            sum_col_be,
            col_name
        )
        """
        Nhiệm vụ ngày 250423:
            ***** Nhóm theo 'biển số' hay hơn nhóm Group 'mã thẻ' vì 1 xe gắn nhiều mã thẻ, có thể trừ tiền cả 2 thẻ nếu xe gắn vào
            - Tìm Cột 'Phí thu' mà FE tính tiền mà BE không tính tiền
            - Sau đó tra lại cột 'Mã thẻ' nhóm thành Group theo cột 'Mã thẻ'
                Lưu ý: Xét đến trường hợp cùng số xe nhưng có nhiều thẻ vẫn bị trừ tiền
                Một "Mã thẻ' có thể gắn nhiều xe (Có thể loại)

            * Điều kiện: Nếu BE phí = 0 nghĩa là hoàn tiền, cũng chính là số chênh lệch giữa phí BE và FE
            ? Có cần thêm cột 'Hoàn tiền' để làm sao cho BE và FE khớp số ==> Nghĩa là để cột 'chênh lệch phí thu' = 0 VNĐ
        """

        return df_FE_BE
    
    
    
    def create_col_standard_car_license(self, df):
        """
        Chuẩn hóa cột biển số xe từ DataFrame có hai cột 'Số xe đăng ký' và 'BE_Biển số xe'.

        Args:
            df (pd.DataFrame): DataFrame chứa hai cột biển số xe.

        Returns:
            pd.DataFrame: DataFrame với cột 'Biển số chuẩn'.
        """
        df_copy = df.copy()

        # 1. Lấy giá trị biển số từ cột FE nếu không phải NaN
        df_copy['Biển số chuẩn'] = df_copy['Số xe đăng ký'].where(pd.notna(df_copy['Số xe đăng ký']), df_copy['BE_Biển số xe'])

        # 2. Loại bỏ dấu nháy đơn ở đầu chuỗi (nếu có)
        # df_copy['Biển số chuẩn'] = df_copy['Biển số chuẩn'].str.lstrip("'")

        # 3. Loại bỏ các ký tự không phải chữ và số (trừ khoảng trắng nếu cần)
        df_copy['Biển số chuẩn'] = df_copy['Biển số chuẩn'].str.replace(r"[^a-zA-Z0-9']", '', regex=True)

         # 4. Bỏ chữ 'T' hoặc 'V' ở cuối nếu có
        def remove_tv_suffix(bien_so):
            if isinstance(bien_so, str) and len(bien_so) > 0 and bien_so[-1] in ['T', 'V']:
                return bien_so[:-1]
            return bien_so

        df_copy['Biển số chuẩn'] = df_copy['Biển số chuẩn'].apply(remove_tv_suffix)
        df_copy = self.add_standard_lan(df_copy)

        return df_copy

    def add_standard_lan(self, df):
        """
        Chuẩn hóa cột làn dựa vào 'Làn' và 'BE_Làn'.

        Args:
            df (pd.DataFrame): DataFrame chứa cột 'Làn' và 'BE_Làn'.

        Returns:
            pd.DataFrame: DataFrame với cột 'Làn chuẩn'.
        """
        df_copy = df.copy()
        df_copy['Làn chuẩn'] = np.nan  # Khởi tạo cột kết quả

        # Xử lý khi có dữ liệu BE_Làn
        mask_be_lan = pd.notna(df_copy['BE_Làn'])
        df_copy.loc[mask_be_lan, 'Làn chuẩn'] = df_copy.loc[mask_be_lan, 'BE_Làn'].astype(str).str.split('(').str[0].str.strip()

        # Xử lý khi không có dữ liệu BE_Làn, sử dụng cột Làn
        mask_lan_only = pd.isna(df_copy['BE_Làn']) & pd.notna(df_copy['Làn'])
        df_copy.loc[mask_lan_only, 'Làn'] = df_copy.loc[mask_lan_only, 'Làn'].astype(str).str.lstrip('0')
        df_copy.loc[mask_lan_only, 'Làn chuẩn'] = 'Làn ' + df_copy.loc[mask_lan_only, 'Làn']


        return df_copy

    # def _parse_special_time(self, time_str):
    #     """Phân tích một định dạng thời gian đặc biệt (ví dụ: DDMMYY HHMMSS)."""
    #     if isinstance(time_str, str): # Kiểm tra kiểu dữ liệu trước khi xử lý
    #         match = re.match(r'(\d{2})(\d{2})(\d{2}) (\d{2})(\d{2})(\d{2})', time_str)
    #         if match:
    #             day, month, year_short, hour, minute, second = match.groups()
    #             year = f'20{year_short}' if int(year_short) < 100 else year_short
    #             try:
    #                 return pd.to_datetime(f'{year}-{month}-{day} {hour}:{minute}:{second}', errors='raise')
    #             except ValueError:
    #                 return pd.NaT
    #     return pd.NaT

    # def _nomal_time(self, df, col_name):
    #     """Chuẩn hóa cột thời gian về kiểu datetime."""
    #     if col_name in df.columns:
    #         df[col_name] = df[col_name].str.strip("'").str.strip()
    #         # Loại bỏ dấu ':' ở đầu nếu có
    #         df[col_name] = df[col_name].str.lstrip(':')
    #         time_formats = ['%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
    #                         '%d-%m-%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S']
    #         for fmt in time_formats:
    #             df[col_name] = df[col_name].fillna(pd.to_datetime(df[col_name], format=fmt, errors='coerce'))
    #     return df

    # def create_standardized_time_str(self, df):
    #     """
    #     Tạo cột 'Thời gian chuẩn' bằng cách kết hợp _nomal_time và _parse_special_time.
    #     Ưu tiên giá trị từ 'BE_Thời gian qua trạm', sau đó thử 'Ngày giờ'.
    #     """
    #     df_copy = df.copy()
    #     try:
    #         # Chuẩn hóa cả hai cột về kiểu datetime
    #         df_copy = self._nomal_time(df_copy, 'BE_Thời gian qua trạm')
    #         df_copy = self._nomal_time(df_copy, 'Ngày giờ')

    #         # Tạo cột 'Thời gian chuẩn' ưu tiên 'BE_Thời gian qua trạm'
    #         df_copy['Thời gian chuẩn'] = df_copy['BE_Thời gian qua trạm'].where(
    #             pd.notna(df_copy['BE_Thời gian qua trạm']),
    #             df_copy['Ngày giờ']
    #         )

    #         # Xử lý các giá trị NaT còn lại bằng _parse_special_time (nếu cần)
    #         mask_nat = df_copy['Thời gian chuẩn'].isna()
    #         # Chỉ áp dụng _parse_special_time cho các giá trị không phải NaT
    #         df_copy.loc[mask_nat, 'Thời gian chuẩn'] = df_copy.loc[mask_nat, 'Thời gian chuẩn'].apply(
    #             lambda x: self._parse_special_time(x) if pd.notna(x) else x
    #         )

    #     except Exception as e:
    #         print('Lỗi:', e)
    #     return df_copy
    
   
    def create_standardized_time_str(self, df):
        """
        Tạo cột 'Thời gian chuẩn' dạng chuỗi 'HH:MM:SS' ưu tiên BE, sau đó FE (chỉ lấy giờ).
        """
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
        return df_copy
            

    "Phiên bản 1.0.8"
    # def create_standardized_time_str(self, df):
    #     """
    #     Tạo cột 'Thời gian chuẩn' dạng chuỗi từ cột 'BE_Thời gian qua trạm' và 'Ngày giờ'
    #     bằng cách xử lý chúng như hai list. Ưu tiên giá trị từ list 'BE_Thời gian qua trạm'.
    #     Bỏ qua kiểm tra ngày tháng và chỉ lấy phần giờ:phút:giây.

    #     Args:
    #         df (pd.DataFrame): DataFrame chứa cột 'Ngày giờ' và 'BE_Thời gian qua trạm'.

    #     Returns:
    #         pd.DataFrame: DataFrame với cột 'Thời gian chuẩn' chứa list các giá trị
    #                     thời gian đã được chuẩn hóa dạng 'HH:MM:SS'.
    #     """
    #     df_copy = df.copy()

    #     be_time_list = df_copy['BE_Thời gian qua trạm'].astype(str).tolist()
    #     fe_time_list = df_copy['Ngày giờ'].astype(str).tolist()
    #     standardized_time_list = []
        
    #     def extract_time_str(time_str):
    #         if pd.isna(time_str) or time_str == 'NaT':
    #             return None
    #         try:
    #             # Thử trích xuất giờ:phút:giây từ định dạng 'dd/mm/yyyy HH:MM:SS'
    #             return time_str.split(' ')[1]
    #         except IndexError:
    #             try:
    #                 # Thử trích xuất giờ:phút:giây từ định dạng 'dd-mm-yyyy HH:MM:SS' (sau khi bỏ dấu ')
    #                 return time_str.replace("'", "").split(' ')[1]
    #             except IndexError:
    #                 return None

    #     for be_time, fe_time in zip(be_time_list, fe_time_list):
    #         extracted_be = extract_time_str(be_time)
    #         extracted_fe = extract_time_str(fe_time)

    #         if extracted_be:
    #             standardized_time_list.append(extracted_be)
    #         elif extracted_fe:
    #             standardized_time_list.append(extracted_fe)
    #         else:
    #             standardized_time_list.append(None)

    #     df_copy['Thời gian chuẩn'] = standardized_time_list
    #     return df_copy

    

    def group_cars_and_time_from_df_FE_BE(self, df):
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
        
        # Chuyển cột 'Thời gian chuẩn' sang kiểu datetime nếu chưa phải
        if not pd.api.types.is_datetime64_any_dtype(df['Thời gian chuẩn']):
            try:
                df['Thời gian chuẩn'] = pd.to_datetime(df['Thời gian chuẩn'], errors='coerce')
                # df['Thời gian chuẩn'] = pd.to_datetime(df['Thời gian chuẩn'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
            except Exception as e:
                print(f"Lỗi chuyển đổi kiểu dữ liệu cho cột 'Thời gian chuẩn': {e}")
                return df

        # Gộp các dòng có cùng 'Biển số chuẩn'
        grouped = df.groupby('Biển số chuẩn', dropna=True)

        # Sắp xếp các giao dịch trong mỗi nhóm theo 'Thời gian chuẩn'
        sorted_groups = grouped.apply(lambda x: x.sort_values(by='Thời gian chuẩn'))

        # Bỏ chỉ mục nhóm để có DataFrame phẳng
        final_df = sorted_groups.reset_index(drop=True)

        return final_df

    def add_summary_columns(self, df, ma_gd_fe='Mã giao dịch',ma_gd_be='BE_Mã giao dịch', phi_thu='Phí thu', chenh_lech='Chênh lệch (Phí thu)', be_tien_thue='BE_Tiền bao gồm thuế'):
        """
        Thêm dòng tổng vào cuối DataFrame cho các cột được chỉ định.

        Args:
            df (pd.DataFrame): DataFrame cần thêm dòng tổng.
            ma_gd_fe (str, optional): Tên cột 'Mã giao dịch' của FE. Mặc định là 'Mã giao dịch'.
            ma_gd_be (str, optional): Tên cột 'BE_Mã giao dịch'. Mặc định là 'BE_Mã giao dịch'.
            phi_thu (str, optional): Tên cột 'Phí thu'. Mặc định là 'Phí thu'.
            chenh_lech (str, optional): Tên cột 'Chênh lệch (Phí thu)'. Mặc định là 'Chênh lệch (Phí thu)'.
            be_tien_thue (str, optional): Tên cột 'BE_Tiền bao gồm thuế'. Mặc định là 'BE_Tiền bao gồm thuế'.

        Returns:
            pd.DataFrame: DataFrame đã thêm dòng tổng.
        """
        if df is None or df.empty:
            print("DataFrame đầu vào là None hoặc rỗng.")
            return df.copy()

        summary_data = {}
        all_cols = df.columns.tolist()

        # Thêm nhãn 'TỔNG' vào cột đầu tiên
        if all_cols:
            summary_data[all_cols[0]] = ['TỔNG']

        # Đếm tổng số giao dịch (không tính dòng tổng nếu có)
        total_rows = len(df)-1
        if all(label not in df.iloc[-1].values for label in ['TỔNG', 'TONG']):
            total_transactions = total_rows
        else:
            total_transactions = total_rows - 1

        # Thêm tổng số giao dịch vào cột 'Mã giao dịch' FE
        if ma_gd_fe in all_cols:
            summary_data[ma_gd_fe] = [f'Tổng: {total_transactions} GD']
        elif all_cols:
            summary_data.setdefault(all_cols[0], [f'Tổng: {total_transactions} GD'])

        # Thêm tổng số giao dịch vào cột 'BE_Mã giao dịch'
        if ma_gd_be in all_cols:
            summary_data[ma_gd_be] = [f'Tổng: {total_transactions} GD']

        # Tính tổng cho cột 'Phí thu'
        if phi_thu in all_cols and pd.api.types.is_numeric_dtype(df[phi_thu]):
            summary_data[phi_thu] = [df[phi_thu].sum()]
        else:
            summary_data.setdefault(phi_thu, [None])

        # Tính tổng cho cột 'Chênh lệch (Phí thu)'
        if chenh_lech in all_cols and pd.api.types.is_numeric_dtype(df[chenh_lech]):
            summary_data[chenh_lech] = [df[chenh_lech].sum()]
        else:
            summary_data.setdefault(chenh_lech, [None])

        # Tính tổng cho cột 'BE_Tiền bao gồm thuế'
        if be_tien_thue in all_cols and pd.api.types.is_numeric_dtype(df[be_tien_thue]):
            summary_data[be_tien_thue] = [df[be_tien_thue].sum()]
        else:
            summary_data.setdefault(be_tien_thue, [None])

        summary_df = pd.DataFrame(summary_data)

        # Nối dòng tổng vào cuối DataFrame, điền các cột thiếu bằng NaN
        df_with_summary = pd.concat([df, summary_df], ignore_index=True, sort=False)
        return df_with_summary

    def create_col_standarder_tickets_type(self, df):
        """
        Chuẩn hóa cột 'Loại vé' dựa trên cột 'BE_Loại giá vé'.

        Args:
            df (pd.DataFrame): DataFrame chứa cột 'Loại vé' và 'BE_Loại giá vé'.

        Returns:
            pd.DataFrame: DataFrame với cột 'Loại vé chuẩn'.
        """
        df['Loại vé chuẩn'] = df['Loại vé'].fillna(df['BE_Loại giá vé'])

        # Chuẩn hóa và bổ sung các trường hợp cụ thể
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'Vé lượt thường': 'Giá thường'})
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'Miễn phí quay đầu': 'Miễn phí quay đầu'})
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'Giá thường': 'Giá thường'})
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'UT toàn quốc': 'UT toàn quốc'})
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'Miễn giảm 100% trạm 2A 2B trạm 768': 'Miễn giảm 100%'}) # Chuẩn hóa tên
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'Miễn phí liên trạm': 'Miễn phí liên trạm'})
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'NaN': None}) # Chuyển 'NaN' string thành None

        # Thêm logic chuẩn hóa nếu có sự khác biệt nhỏ về tên gọi
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'UT Toàn Quốc': 'UT toàn quốc'})
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'Miễn giảm 100% Trạm 2A 2B Trạm 768': 'Miễn giảm 100%'})
        df['Loại vé chuẩn'] = df['Loại vé chuẩn'].replace({'Miễn Phí Liên Trạm': 'Miễn phí liên trạm'})


        return df
    
    def nomal_fe_be(self):
        # 1. Chuẩn hoá lại file gốc            
        fe_processed, be_processed = self.load_and_standardize_fe_be()
        
        # 2. Gộp 2 fe và be thành df_fe_be
        df_list = [fe_processed, be_processed]            
        df_FE_BE = self.merge_FE_BE_with_standard_mgd(df_list) # Chuẩn hoá mã giao dịch

        # 3. Thêm cột chuẩn hoá biển số
        df_FE_BE = self.create_col_standard_car_license(df_FE_BE)

        # 4. Thêm cột chuẩn hoá vé lượt
        df_FE_BE = self.create_col_standarder_tickets_type(df_FE_BE)

        # 5. Thêm cột chuẩn hoá thời gian
        df_FE_BE = self.create_standardized_time_str(df_FE_BE)


        # print(df_FE_BE[['Ngày giờ', 'BE_Thời gian qua trạm', 'Thời gain chuẩn']]) #'BE_Thời gian qua trạm']), df_copy['Ngày giờ']

        # 'test'
        # nan_time_df = df_FE_BE[df_FE_BE['Thời gian chuẩn'].isna()]
        # abc =nan_time_df[['Ngày giờ', 'BE_Thời gian qua trạm', 'Thời gian chuẩn']]
        # print(abc)
        # df_FE_BE[['Ngày giờ','BE_Thời gian qua trạm']]

        return fe_processed, be_processed, df_FE_BE

    