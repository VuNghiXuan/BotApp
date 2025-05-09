Sửa code hàm _count_valid_trips tính chưa đúng lượt đi:
Mô tả phương án thu phí theo self.mapping_lane cho một lượt đi (vào và ra dự án):

1. Lượt đi cho Xe khởi hành từ bên ngoài đi vào dự án :

Giao dịch ở làn vào đầu tiên sẽ bị thu phí.'Lỗi Antent'==True
Các giao dịch tiếp theo, nếu cột 'Lỗi Antent'==False và thuộc một trong các làn ra của dự án  kết thúc 1 lượt đi phù hợp. Lượt ra là miễn phí nên lượt ra tính phí thì xem lỗi FE hay BE.

2. Lượt đi cho Xe khởi hành từ bên trong ra dự án (dân sinh):

Giao dịch ở làn ra đầu tiên sẽ bị thu phí. Điều này áp dụng cho cư dân sống trong khu vực dự án, có thể có hành trình khởi hành khác biệt.'Lỗi Antent'==True
Nếu xe sau đó đi vào lại cùng trạm và đúng làn vào, thì giao dịch vào này vẫn được xem là lượt đi hợp lệ  và kết thúc lượt đi.
Nếu xe đi vào ở một trạm khác sau khi đã ra, thì đây được xem là một lượt đi mới và sẽ tính phí cho lượt đi mới này.
Yêu cầu về hàm và biến trong class Transaction:

Thêm các hàm và biến trong class Transaction để hỗ trợ việc xác định lượt đi theo logic trên.
Cần có các biến để theo dõi trạng thái lượt đi (ví dụ: đã vào, đã ra, lượt đi thứ mấy).
Cần có thông tin về phí FE và BE để so sánh.
Cần có cơ chế để xác định và đánh dấu các trường hợp lỗi quét trùng Anten.
Yêu cầu về output all_transactions_data:

Bạn muốn xuất ra DataFrame all_transactions_data (từ get_transactions_info_df của class Cars).
DataFrame này cần bao gồm các cột bạn đã kiểm tra cho lỗi Anten (ví dụ: Lỗi Antent, T/gian 2 lượt (phút), Nghi vấn lỗi Antent).
Đặc biệt, bạn chỉ muốn xuất ra 2 cột sau:
Mô tả hành trình:
Thông tin về lượt đi thứ mấy.
Trạng thái ra/vào và trạm (làn nào).
Nếu xe chỉ có giao dịch vào mà chưa có ra, cần ghi chú "xe chưa quay đầu". Ngược lại (chỉ có ra mà chưa vào), có thể ghi chú "xe đã ra mà chưa xác định điểm vào".
Các phần còn lại và ccột còn lại giữ nguyên

def _analyze_trips(self):
        """Phân tích các giao dịch để xác định lượt đi."""
        current_trip_id = None
        previous_transaction = None
        trip_index = 0 # Số lượt đi
        entry_transaction = None # Lượt vào

        for i, trans in enumerate(self.transactions):
            if trans.fix_antent:
                continue

            is_free_ticket = 'miễn phí' in str(trans.standard_ticket_type).lower()
            is_round_trip_ticket = 'quay đầu' in str(trans.standard_ticket_type).lower()

            if is_round_trip_ticket and current_trip_id is not None:
                # Giao dịch quay đầu kết thúc lượt hiện tại
                trans.trip_id = current_trip_id
                trans.trip_description = f"Lượt {trip_index}: Quay đầu tại trạm {trans.station} (làn {trans.lane}), vé '{trans.standard_ticket_type}'"
                trans.has_matching_exit = True
                if entry_transaction:
                    entry_transaction.has_matching_exit = True
                trans.fee_status = 'Quay đầu - Miễn phí'
                current_trip_id = None
                entry_transaction = None
            elif is_free_ticket:
                trans.fee_status = 'Vé miễn phí'
                if trans.is_entry and current_trip_id is None:
                    trip_index += 1
                    current_trip_id = str(uuid.uuid4())
                    trans.trip_id = current_trip_id
                    trans.is_first_transaction_in_trip = True
                    trans.trip_description = f"Lượt {trip_index}: Vào trạm {trans.station} (làn {trans.lane}), vé '{trans.standard_ticket_type}'"
                    entry_transaction = trans
                elif trans.is_exit and current_trip_id is not None and entry_transaction is not None and trans.station == entry_transaction.station:
                    trans.trip_id = current_trip_id
                    trans.trip_description = f"Lượt {trip_index}: Ra trạm {trans.station} (làn {trans.lane}), vé '{trans.standard_ticket_type}'"
                    trans.has_matching_exit = True
                    entry_transaction.has_matching_exit = True
                    current_trip_id = None
                    entry_transaction = None
                elif trans.is_entry and current_trip_id is None:
                    # Nếu là vé miễn phí và là giao dịch vào đầu tiên
                    trip_index += 1
                    current_trip_id = str(uuid.uuid4())
                    trans.trip_id = current_trip_id
                    trans.is_first_transaction_in_trip = True
                    trans.trip_description = f"Lượt {trip_index}: Vào trạm {trans.station} (làn {trans.lane}), vé '{trans.standard_ticket_type}'"
                    entry_transaction = trans
            elif trans.is_entry and trans.is_chargeable and current_trip_id is None:
                trip_index += 1
                current_trip_id = str(uuid.uuid4())
                trans.trip_id = current_trip_id
                trans.is_first_transaction_in_trip = True
                trans.trip_description = f"Lượt {trip_index}: Vào trạm {trans.station} (làn {trans.lane}), phí FE={trans.fee_of_fe}"
                entry_transaction = trans
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
            elif trans.is_exit and current_trip_id is not None and entry_transaction is not None and trans.station == entry_transaction.station:
                trans.trip_id = current_trip_id
                trans.trip_description = f"Lượt {trip_index}: Ra trạm {trans.station} (làn {trans.lane}), phí BE={trans.fee_of_be}"
                trans.has_matching_exit = True
                entry_transaction.has_matching_exit = True
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
                current_trip_id = None
                entry_transaction = None
            elif trans.is_entry and trans.is_chargeable and current_trip_id is not None and entry_transaction is None:
                # Trường hợp vào tiếp mà chưa ra
                trip_index += 1
                current_trip_id = str(uuid.uuid4())
                trans.trip_id = current_trip_id
                trans.is_first_transaction_in_trip = True
                trans.trip_description = f"Lượt {trip_index}: Vào trạm {trans.station} (làn {trans.lane}), phí FE={trans.fee_of_fe} (Vào khi chưa ra lượt trước?)"
                entry_transaction = trans
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
            elif trans.is_exit and current_trip_id is None:
                # Xe có thể bắt đầu từ làn ra (dân cư)
                trip_index += 1
                current_trip_id = str(uuid.uuid4())
                trans.trip_id = current_trip_id
                trans.trip_description = f"Lượt {trip_index}: Ra trạm {trans.station} (làn {trans.lane}), phí BE={trans.fee_of_be} (Xuất phát từ dự án?)"
                trans.has_matching_exit = True
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
                current_trip_id = None

            previous_transaction = trans

        # Xử lý các giao dịch vào mà không có ra
        for trans in self.transactions:
            if trans.is_entry and trans.trip_id is not None and not trans.has_matching_exit and not trans.fix_antent:
                trans.trip_description += " (Chưa có giao dịch ra)"

    def _check_fee_consistency(self, fe_fee, be_fee):
        """Kiểm tra sự nhất quán giữa phí FE và BE."""
        if 'miễn phí' in str(self.journey['Loại vé chuẩn'].iloc[0]).lower() or 'quay đầu' in str(self.journey['Loại vé chuẩn'].iloc[0]).lower():
            return 'Vé miễn phí/Quay đầu'
        elif fe_fee > be_fee:
            return f'FE lớn hơn BE ({fe_fee} > {be_fee})'
        elif fe_fee < be_fee:
            return f'FE nhỏ hơn BE ({fe_fee} < {be_fee})'
        elif fe_fee == be_fee and fe_fee > 0:
            return f'FE = BE = {fe_fee}'
        elif fe_fee == 0 and be_fee == 0:
            return 'Không thu phí'
        elif fe_fee > 0 and be_fee == 0:
            return f'Chỉ có FE = {fe_fee}'
        elif fe_fee == 0 and be_fee > 0:
            return f'Chỉ có BE = {be_fee}'
        else:
            return 'Không xác định'

    def _count_valid_trips(self):
        """Đếm số lượt đi hợp lệ (có cả vào và ra)."""
        return sum(1 for trans in self.transactions if trans.is_exit and trans.has_matching_exit and not trans.fix_antent)




    '-----------------------------------------------------------------------------'





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



    Ý tưởng như thế này nhé: 
    Trong vòng lặp for :
    
        Bước 1: Sau khi kiểm tra nếu có lỗi antent, kiểm tra fe, be mà thu phí là sai, ghi chú cho cột Trạng thái phí, continoun đi tiếp

        Bước 2: Nếu không có lỗi Antent: Tức là giao dịch này là giao dịch và làn này là làn khởi hành, is_depart = TRue, kiểm tra trạng thái BE, FE có thu phí không ghi vào cột trạng thái

        Qua bước 1, bước 2: ta xác định được làn khởi hành mà không lỗi Antent, hai bước này không kiểm tra làn 7 vì nếu có làn 7 thì nó vẫn là làn khởi hành.
        Bước 3: Vòng lặp đi tới dòng giao dịch tiếp, kiểm tra làn 7 có hay không?
            - Trường hợp có làn 7:
                + Nếu là giao dịch cuối: Thì xác định làn 7 là làn kết thúc hành trình, ghi vào hành trình, kiểm tra trạng thái phí (nếu thu phí là sai)
                + Nếu không phải là dòng cuối cùng của giao dịch này, thì tiếp tục đi tìm làn kết thúc hành trình các giao dịch tiếp theo, với điều kiện:
                    * Nếu các dòng cuối tìm ra làn kết thúc hành trình thì làn 7 trên là làn kiểm soát, quay lại ghi vào mô tả hành trình và kiểm tra nếu có tính phí là sai.
                    *Nếu không tìm thấy làn kết thúc hành trình, có các lý do sau:
                        Mày mô tả thêm các trường hợp này rồi bàn tiếp





                    <!-- * Nếu dòng tiếp theo bị lỗi Anten thì và là dòng cuối thì quay lại giao dịch tại dòng 7: kết luận là làn kết thúc hành trình, ghi vào cột 'Mô tả hành trình', kiểm tra trạng thái BE, FE có thu phí không ghi vào cột trạng thái, nếu có thu phí là sai

                    * Nếu dòng tiếp theo không bị lỗi Anten thì kiểm tra có phải là làn kết thúc hành trình hay không: ghi vào cột cột 'Mô tả hành trình' là làn kiểm soát, kiểm tra trạng thái BE, FE có thu phí không ghi vào cột trạng thái, nếu có thu phí là sai. Continoun 
                + Nếu  -->


Quy tắc xác định lượt đi và trạng thái phí:

1. Lượt đi một chiều (từ ngoài vào):

Bắt đầu: Giao dịch đầu tiên ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'vào' (theo định nghĩa trong self.mapping_lane). Giao dịch này được xem là điểm khởi đầu của lượt đi.
Kết thúc: Giao dịch tiếp theo ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'ra' (theo định nghĩa trong self.mapping_lane).
Kiểm tra đặc biệt cho làn 7: Nếu làn kết thúc là làn số 7, cần kiểm tra các giao dịch tiếp theo (bên dưới) để xác định giao dịch kết thúc lượt đi chính xác hơn dựa trên loại vé chuẩn:
Nếu tồn tại giao dịch ở làn 7 có cột loại vé chuẩn là "Miễn phí liên trạm" và phí thu bằng 0, thì giao dịch này được xem là làn kiểm soát, chưa phải là giao dịch kết thúc cuối cùng của lượt đi. Cần tiếp tục tìm giao dịch ra hợp lệ sau đó.
Nếu tồn tại giao dịch ở làn 7 có cột loại vé chuẩn là 'Miễn phí quay đầu', thì giao dịch này chính là giao dịch kết thúc của lượt đi.
Nếu không có các trường hợp đặc biệt trên, giao dịch ra đầu tiên ở làn 'ra' (bao gồm cả làn 7 nếu không thuộc trường hợp "Miễn phí liên trạm") được xem là kết thúc lượt đi.
Trạng thái phí:
Nếu giao dịch khởi hành (làn vào) không bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị thiếu hay không.
Nếu giao dịch kết thúc (làn ra) bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị tính thừa hay không.
2. Lượt đi dân sinh (từ trong ra, quay đầu tại trạm):

Bắt đầu: Giao dịch ra đầu tiên ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'ra' (theo định nghĩa trong self.mapping_lane). Giao dịch này được xem là điểm khởi đầu của lượt đi.
Kết thúc: Giao dịch vào sau đó phải thỏa mãn các điều kiện sau:
Xảy ra tại cùng trạm với giao dịch ra trước đó (tên trạm được xác định từ cột 'Làn chuẩn' thông qua self.mapping_lane).
Sử dụng đúng làn vào (được định nghĩa là 'vào' cho trạm đó trong self.mapping_lane).
Có 'Lỗi Antent' == False'.
Điều kiện hợp lệ: Cả giao dịch ra ban đầu và giao dịch vào sau đó đều phải có 'Lỗi Antent' == False' để lượt đi này được xác định là hợp lệ.
Trạng thái phí:
Nếu giao dịch khởi hành (làn ra đầu tiên) không bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị thiếu hay không.
Nếu giao dịch kết thúc (làn vào sau đó) bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị tính thừa hay không.
3. Lượt đi cơ bản (vào và ra):

Bắt đầu: Giao dịch vào đầu tiên ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'vào' (theo định nghĩa trong self.mapping_lane).
Kết thúc: Giao dịch ra tiếp theo ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'ra' (theo định nghĩa trong self.mapping_lane).
Kiểm tra đặc biệt cho làn 7: Tương tự như lượt đi một chiều, nếu làn kết thúc là làn số 7, cần kiểm tra các giao dịch tiếp theo (bên dưới) dựa trên loại vé chuẩn ("Miễn phí liên trạm" và 'Miễn phí quay đầu') để xác định giao dịch kết thúc chính xác.
Trạng thái phí:
Nếu giao dịch khởi hành (làn vào) không bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị thiếu hay không.
Nếu giao dịch kết thúc (làn ra) bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị tính thừa hay không.
4. Trường hợp xe chưa quay đầu:

Nếu trong một khoảng thời gian nhất định, hệ thống chỉ ghi nhận được giao dịch vào thỏa mãn điều kiện 'Lỗi Antent' == False' và là làn 'vào' (theo self.mapping_lane) cho một xe, mà không có giao dịch ra nào thỏa mãn điều kiện 'Lỗi Antent' == False' và là làn 'ra' (theo self.mapping_lane) cho cùng xe đó, thì trạng thái sẽ được ghi nhận là "xe chưa quay đầu".
5. Trường hợp xe đã ra mà chưa xác định điểm vào:

Nếu trong một khoảng thời gian nhất định, hệ thống chỉ ghi nhận được giao dịch ra thỏa mãn điều kiện 'Lỗi Antent' == False' và là làn 'ra' (theo self.mapping_lane) cho một xe, mà không có giao dịch vào nào thỏa mãn điều kiện 'Lỗi Antent' == False' và là làn 'vào' (theo self.mapping_lane) cho cùng xe đó trước đó, thì trạng thái sẽ được ghi nhận là "xe đã ra mà chưa xác định điểm vào".