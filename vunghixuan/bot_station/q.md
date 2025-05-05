Tôi muốn viết hàm kiẻm tra 1 lượt vé đi xem phí thu của BE hay FE sai hay cả 2 đều đúng và xe có bao nhiêu lượt 1 ngày, với nội dung như sau:
Phương án thu phí theo self.mapping_lane với 1 lượt đi bao gồm vào và ra dự án

1. Nếu xe khởi hành từ ngoài dự án vào, thì làn đầu tiên thu phí, các làn ra miễn phí (miễn đúng làn ra, còn bị thu phí các làn không phải là làn ra là bị quét trùng lỗi antent)
2. Nếu xe khởi hành từ dự án đi ra (làn ra là làn đầu tiên sẽ thu phí (các loại xe này là dân sinh sống trong khu vực dự án nên có khởi hành khác với các loại xe khác), và nếu đi vào cùng 1 trạm nhưng đúng làn vào thì cũng xem như 1 lượt di hợp lệ. Nếu trường hợp này xe vào mà trạm khác thì được xem là lượt đi mới phải tính phí lượt đi mới.
Hãy thêm các hàm và biến trong Transaction và các biến phù hợp. Cuối cùng xuất ra all_transactions_data thêm các cột như tôi kiểm tra các hàm đọc lỗi antent
Lưu ý chỉ xuất ra 2 cột:
    +Cột Mô tả hành trình (Lượt đi thứ mấy, ra vào trạm (làn nào), phí (FE=bao nhiêu) nhỏ hoặc lớn (BE=bao nhiêu))
        Lưu ý: 1 lượt đi hợp lý khi điều kiện lỗi Antent không bị đọc trùng lặp và là số nguyên, nếu xe chỉ có vào chưa ra thì ghi chú xe chưa quay đầu ngược lại



import pandas as pd
import numpy as np
import traceback

class Transaction:
    def __init__(self, transaction):
        """
        Khởi tạo đối tượng ThongTinGiaoDich từ một giao dịch.
        """
        # self.transaction = transaction #'50E11142
        self.tran_reasonable_time_minutes = 10 # Thời gian hợp lý (phút)
        self.tran_unusual_time_minutes = 10 # Thời gian chuyến đi bất thường (phút)
        self.duplicate_transactions_minutes = 5 # Giao dịch xảy ra trùng lặp do Antent (phút)

        self.time = None
        self.station = None
        self.lane_type = None
        self.fee_of_fe = None
        self.fee_of_be = None
        self.diff_fee = None # Chênh lệch phí giữa FE và BE
        self.time_diff_to_previous = None
        self.index_in_df = None # Lưu trữ index của giao dịch trong DataFrame
        self.lane = None
        self.info = {} # Dictionary để lưu trữ thông tin đầy đủ của giao dịch

        self.mapping_lane = {
            '2A': {'vào': ['Làn 10', 'Làn 11'], 'ra': ['Làn 12'], 'trạm': 'Đồng Khởi_2A'},
            '1A': {'vào': ['Làn 1', 'Làn 2'], 'ra': ['Làn 3', 'Làn 4'], 'trạm': 'ĐT768_1A'},
            '3B': {'vào': ['Làn 7', 'Làn 8', 'Làn 9'], 'ra': [], 'trạm': 'ĐT768_3B'},
            '3A': {'vào': [], 'ra': ['Làn 5', 'Làn 6'], 'trạm': 'ĐT768_3A'}}

        # Phân tích biến đổi kiểu dữ liệu
        self._parse_transaction(transaction)


    def _parse_transaction(self, transaction):
        """Phân tích thông tin từ giao dịch."""
        try:
            self.info = transaction.to_dict() # Lưu trữ toàn bộ giao dịch dưới dạng dictionary
            self.car_name = transaction['Biển số chuẩn']
            self.name = transaction['Mã giao dịch']
            self.time = pd.to_datetime(transaction['Thời gian chuẩn'])
            # Xử lý 'Phí thu'
            phi_thu = pd.to_numeric(transaction['Phí thu'], errors='coerce')
            self.fee_of_fe = phi_thu if pd.notna(phi_thu) else 0

            # Xử lý 'BE_Tiền bao gồm thuế'
            be_tien = pd.to_numeric(transaction['BE_Tiền bao gồm thuế'], errors='coerce')
            self.fee_of_be = be_tien if pd.notna(be_tien) else 0

            self.lane = str(transaction['Làn chuẩn'])
            self.station = self._get_station_from_lane(self.lane )
            self.lane_type = self._get_lane_type(self.lane )
            self.diff_fee = self.fee_of_fe - self.fee_of_be #if pd.notna(self.fee_of_fe) and pd.notna(self.fee_of_be) else 0
            self.index_in_df = transaction.name # Lấy index từ Series
            
            # 1. Nghi vấn lỗi antent
            self.time_diff_to_previous = None
            self.fix_antent = False
            self.antent_doubt = '' # NGhi vấn lỗi antent

            # 2. Lỗi chênh lệch phí do chỉ có FE hoặc BE
            self.tran_only_fe_not_be = False
            self.fe_or_be_doubt = '' # Nghi vấn chênh lệch BE hoặc FE
            self.transactions_only_has_FE_or_BE()



            # 3. Kiểm tra vé lượt
            
            self.is_in_lane = self._check_lane_type(self.lane, 'vào')
            self.is_out_lane = self._check_lane_type(self.lane, 'ra')
            # 4. Kiểm tra thứ tự xe vào/ra
          


            self.journey_descripts = ''
        except Exception:
            print(f"Lỗi xảy ra trong hàm _parse_transaction:")
            traceback.print_exc()    
  
        
    def _get_station_from_lane(self, lane):
        """Trích xuất tên trạm từ tên làn, xử lý giá trị NaN."""
        try:
            if pd.isna(lane):
                return None
            lane_str = str(lane).strip()
            for tram_code, lane_info in self.mapping_lane.items():
                for type in ['vào', 'ra']:
                    if lane_str in [l.strip() for l in lane_info.get(type, [])]:
                        return lane_info['trạm']
            return None
        except Exception:
            print(f"Lỗi xảy ra trong hàm _get_station_from_lane:")
            traceback.print_exc()
            return None

    def _get_lane_type(self, lane):
        """Xác định loại làn (in/out) từ tên làn, xử lý giá trị NaN."""
        try:
            if pd.isna(lane):
                return None
            lane_str = str(lane).strip()
            for tram_code, lane_info in self.mapping_lane.items():
                if lane_str in [l.strip() for l in lane_info.get('vào', [])]:
                    return 'vào'
                if lane_str in [l.strip() for l in lane_info.get('ra', [])]:
                    return 'ra'
            return None
        except Exception:
            print(f"Lỗi xảy ra trong hàm _get_lane_type:")
            traceback.print_exc()
            return None

    def _check_lane_type(self, lane, type):
        """Kiểm tra xem làn có thuộc loại 'vào' hoặc 'ra' không."""
        try:
            if pd.isna(lane):
                return False
            lane_str = str(lane).strip()
            for tram_code, lane_info in self.mapping_lane.items():
                if lane_str in [l.strip() for l in lane_info.get(type, [])]:
                    return True
            return False
        except Exception:
            print(f"Lỗi xảy ra trong hàm _check_lane_type:")
            traceback.print_exc()
            return False
    
    # def add_doubt_notes(self, doubt_note):
    #     "Thêm dòng ghi chú"
    #     if self.antent_doubt == '': #NGhi vấn
    #         self.antent_doubt = doubt_note #NGhi vấn
    #     else:
    #         self.antent_doubt += '; ' + doubt_note

    def transactions_only_has_FE_or_BE(self):
        "Thống kê các giao dịch chỉ có BE hoặc FE"
        if self.fee_of_fe!=0 and self.fee_of_be==0:
            self.tran_only_fe_not_be = True
            self.fe_or_be_doubt ='Giao dịch có FE, không có BE  '
        elif self.fee_of_fe == 0 and self.fee_of_be !=0:
            self.fe_or_be_doubt ='Nghi vấn thu phí nguội'
        elif self.diff_fee == 0:
            self.fe_or_be_doubt ='Khớp giao dịch'

    def calculate_the_time_difference_for_fix_from_antent(self, orther_transaction):
        """Tính chênh lệch thời gian với giao dịch trước đó (phút)."""
        try:
            orther_time = pd.to_datetime(orther_transaction['Thời gian chuẩn'])
            time_diff_seconds = (self.time - orther_time).total_seconds()
            time_diff_minutes = time_diff_seconds / 60

            if time_diff_minutes < self.duplicate_transactions_minutes:   
                doubt_note = 'Lỗi Antents đọc trùng' # Ghi chú lỗi
                if self.diff_fee !=0:
                    self.time_diff_to_previous = round(time_diff_minutes,3) # Lấy chênh lệch thời gian

                    self.fix_antent = True # Gán có lỗi Antent
                    self.antent_doubt = doubt_note #NGhi vấn
                else:
                    "Tạm thời chấp nhận giao dòng khác lỗi"
                    orther_transaction.time_diff_to_previous = round(time_diff_minutes,3) # Lấy chênh lệch thời gian
                    orther_transaction.fix_antent = True # Gán có lỗi Antent
                    orther_transaction.doubt = doubt_note # NGhi vấn
            

        except Exception:
            print(f"Lỗi xảy ra trong hàm calculate_the_time_difference_for_fix_from_antent:")
            traceback.print_exc()
            self.time_diff_to_previous = None
import pandas as pd
import numpy as np
from vunghixuan.bot_station.transaction_info import Transaction
# from transaction_info import Transaction



import pandas as pd
import numpy as np


class Car:
    def __init__(self, car_license, journey):
        """
        Khởi tạo đối tượng Car: là tổng các lượt đi trong ngày (24h)
        """
        try:
            self.name = car_license
            self.journey = journey.sort_values(by='Thời gian chuẩn').reset_index(drop=True) # Giữ lại index sau khi sort
            self.total_journey = len(self.journey)
            self.transactions = []
            self.create_transactions()
            self._update_time_diff_column_doubt_fix_antent() # Cập nhật cột sau khi tạo transactions
        except Exception as e:
            print(f'Lỗi hàm __init__ trong class Car: {e}')
            self.name = None
            self.journey = pd.DataFrame()
            self.total_journey = 0
            self.transactions = []

    def create_transactions(self):
        """
        Tạo các đối tượng Transaction từ DataFrame và tính toán chênh lệch thời gian.
        """
        try:
            for i in range(self.total_journey):
                transaction_row = self.journey.iloc[i]
                trans = Transaction(transaction_row)
                if i > 0:
                    trans.calculate_the_time_difference_for_fix_from_antent(self.journey.iloc[i-1])
                self.transactions.append(trans)
        except Exception as e:
            print(f'Lỗi hàm create_transactions trong class Car: {e}')
            self.transactions = []

    

    def _update_time_diff_column_doubt_fix_antent(self):
        """
        Cập nhật cột 'T/gian 2 lượt (phút)' của DataFrame.
        """
        try:
            time_diff_values = [tran.time_diff_to_previous for tran in self.transactions]
            # self.journey['T/gian 2 lượt (phút)'] = time_diff_values
            # Kiểm tra có chênh lệch phí 
            ""
        except Exception as e:
            print(f'Lỗi hàm _update_time_diff_column_doubt_fix_antent trong class Car: {e}')
            if 'T/gian 2 lượt (phút)' in self.journey.columns:
                self.journey['T/gian 2 lượt (phút)'] = np.nan

    def get_journey_df(self):
        """
        Trả về DataFrame của hành trình xe với cột 'T/gian 2 lượt (phút)'.
        """
        try:
            return self.journey
        except Exception as e:
            print(f'Lỗi hàm get_journey_df trong class Car: {e}')
            return pd.DataFrame()

class Cars():
    def __init__(self, df_has_fee):
        try:
            self.df_has_fee = df_has_fee
            self.name = 'Xe trả phí'
            self.car_journeys = {} # Dictionary để lưu trữ các đối tượng Car

            # Thêm hành trình xe và giao dịch vào dự án
            self.create_car_journeys()
        except Exception as e:
            print(f'Lỗi hàm __init__ trong class Cars: {e}')
            self.df_has_fee = pd.DataFrame()
            self.car_journeys = {}

    def create_car_journeys(self):
        try:
            for name, group in self.df_has_fee.groupby('Biển số chuẩn'):
                group_sorted = group.sort_values('Thời gian chuẩn').reset_index(drop=True)
                car = Car(name, group_sorted)
                self.car_journeys[name] = car # Lưu trữ đối tượng Car
        except Exception as e:
            print(f'Lỗi hàm create_car_journeys trong class Cars: {e}')
            self.car_journeys = {}

    def get_all_journeys_df(self):
        """
        Trả về một DataFrame chứa thông tin của tất cả các hành trình xe,
        bao gồm cả cột 'T/gian 2 lượt (phút)'.
        """
        try:
            all_journeys = []
            for car_license, car_obj in self.car_journeys.items():
                journey_df = car_obj.get_journey_df()
                all_journeys.append(journey_df)

            if all_journeys:
                final_df = pd.concat(all_journeys, ignore_index=True)
                return final_df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f'Lỗi hàm get_all_journeys_df trong class Cars: {e}')
            return pd.DataFrame()

    def get_transactions_info_df(self):
        """
        Trả về DataFrame chứa thông tin giao dịch từ tất cả các xe,
        bao gồm tất cả các cột ban đầu của Transaction và thêm
        'T/gian 2 lượt (phút)' và 'Chênh lệch phí FE-BE'.
        """
        try:
            all_transactions_data = []
            for car_license, car_obj in self.car_journeys.items():
                for trans in car_obj.transactions:
                    transaction_info = trans.info.copy()  # Lấy bản sao dictionary từ thuộc tính 'info' của Transaction
                    
                    transaction_info['Chênh lệch phí FE-BE'] = trans.diff_fee
                    # 1. Lỗi antent
                    transaction_info['Lỗi Antent'] = trans.fix_antent
                    transaction_info['T/gian 2 lượt (phút)'] = trans.time_diff_to_previous
                    transaction_info['Nghi vấn lỗi Antent'] = trans.antent_doubt

                    # 2. Lỗi giao địch chỉ 1 phía BE hoặc FE
                    transaction_info['Giao dịch có FE hoặc BE'] = trans.tran_only_fe_not_be
                    transaction_info['Nghi vấn giao dịch 1 phía'] = trans.fe_or_be_doubt

                    all_transactions_data.append(transaction_info)
            return pd.DataFrame(all_transactions_data)
        except Exception as e:
            print(f'Lỗi hàm get_transactions_info_df trong class Cars: {e}')
            return pd.DataFrame()


if __name__ == '__main__':
    head = ['Mã giao dịch', 'Số xe đăng ký', 'Mã thẻ', 'Phí thu', 'Làn', 'Ngày giờ', 'Loại vé', 'BE_Biển số xe', 'BE_Số etag', 'BE_Loại giá vé', 'BE_Tiền bao gồm thuế', 'BE_Thời gian qua trạm', 'BE_Làn', 'Mã giao dịch chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Loại vé chuẩn', 'Thời gian chuẩn', 'Xe không trả phí']
    val = [["'1736121104", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 00:02:37", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1736121104", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 00:02:37', False],
           ["'1736765135", "'50H20700", "'3416214B8817620004936445", 0, '8', "'13-04-2025 12:17:39", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1736765135", "'50H20700", 'Làn 8', 'Vé quý thường', '2025-04-13 12:17:39', False],
           ["'1736769963", "'50H20700", "'3416214B8817620004936445", 0, '7', "'13-04-2025 12:21:20", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1736769963", "'50H20700", 'Làn 7', 'Vé quý thường', '2025-04-13 12:21:20', False],
           ["'1736852606", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 13:25:32", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1736852606", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 13:25:32', False],
           ["'1736921436", "'50H20700", "'3416214B8817620004936445", 0, '11', "'13-04-2025 14:07:22", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1736921436", "'50H20700", 'Làn 11', 'Vé quý thường', '2025-04-13 14:07:22', False],
           ["'1736957673", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 14:31:02", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1736957673", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 14:31:02', False],
           ["'1737043660", "'50H20700", "'3416214B8817620004936445", 0, '10', "'13-04-2025 15:16:20", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1737043660", "'50H20700", 'Làn 10', 'Vé quý thường', '2025-04-13 15:16:20', False],
           ["'1737091024", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 15:45:52", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1737091024", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 15:45:52', False],
           ["'1737356833", "'50H20700", "'3416214B8817620004936445", 0, '10', "'13-04-2025 18:33:11", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1737356833", "'50H20700", 'Làn 10', 'Vé quý thường', '2025-04-13 18:33:11', False],
           ["'1737402928", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 19:14:47", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1737402928", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 19:14:47', False],
           ["'1737468742", "'50H20700", "'3416214B8817620004936445", 0, '11', "'13-04-2025 20:13:13", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1737468742", "'50H20700", 'Làn 11', 'Vé quý thường', '2025-04-13 20:13:13', False],
           ["'1737510726", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 20:56:43", 'Vé quý thường', np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, "'1737510726", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 20:56:43', False]]

    df = pd.DataFrame(val, columns=head)
    df['Thời gian chuẩn'] = pd.to_datetime(df['Thời gian chuẩn']) # Chuyển đổi sang datetime
    bs ="'50H20700"
    journey = Cars(df)
    df_output = journey.get_transactions_info_df()
    print(df_output[['Thời gian chuẩn', 'T/gian 2 lượt (phút)', 'Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch phí FE-BE']])