import pandas as pd
import numpy as np
import uuid
from vunghixuan.bot_station.transaction_info import Transaction
# from transaction_info import Transaction



class Car:
    def __init__(self, car_license, journey, mapping_lane):
        """
        Khởi tạo đối tượng Car: là tổng các lượt đi trong ngày (24h)
        """
        try:
            self.name = car_license
            self.journey = journey.sort_values(by='Thời gian chuẩn').reset_index(drop=True) # Giữ lại index sau khi sort
            self.total_journey = len(self.journey)
            self.transactions = []
            self.mapping_lane = mapping_lane
            self._create_transactions()
            self._update_time_diff_column_doubt_fix_antent() # Cập nhật cột sau khi tạo transactions
            self._analyze_trips() # Phân tích lượt đi
            self.trip_count = self._count_valid_trips() # Đếm số lượt đi hợp lệ
        except Exception as e:
            print(f'Lỗi hàm __init__ trong class Car: {e}')
            self.name = None
            self.journey = pd.DataFrame()
            self.total_journey = 0
            self.transactions = []
            self.mapping_lane = {}
            self.trip_count = 0

    def _create_transactions(self):
        """
        Tạo các đối tượng Transaction từ DataFrame.
        """
        try:
            for i in range(self.total_journey):
                transaction_row = self.journey.iloc[i]
                trans = Transaction(transaction_row, self.mapping_lane)
                if i > 0:
                    trans.calculate_the_time_difference_for_fix_from_antent(self.transactions[i-1])
                self.transactions.append(trans)
        except Exception as e:
            print(f'Lỗi hàm _create_transactions trong class Car: {e}')
            self.transactions = []

    def _update_time_diff_column_doubt_fix_antent(self):
        """
        Cập nhật thông tin về chênh lệch thời gian và nghi vấn lỗi antent.
        """
        try:
            time_diff_values = [tran.time_diff_to_previous for tran in self.transactions]
            # self.journey['T/gian 2 lượt (phút)'] = time_diff_values
        except Exception as e:
            print(f'Lỗi hàm _update_time_diff_column_doubt_fix_antent trong class Car: {e}')
            # if 'T/gian 2 lượt (phút)' in self.journey.columns:
            #     self.journey['T/gian 2 lượt (phút)'] = np.nan

    def get_journey_df(self):
        """
        Trả về DataFrame của hành trình xe.
        """
        try:
            return self.journey
        except Exception as e:
            print(f'Lỗi hàm get_journey_df trong class Car: {e}')
            return pd.DataFrame()

    def _check_fee_consistency(self, fe_fee, be_fee):
        """Kiểm tra sự nhất quán giữa phí FE và BE."""
        first_ticket_type = str(self.journey['Loại vé chuẩn'].iloc[0]).lower()
        if 'miễn phí' in first_ticket_type or 'quay đầu' in first_ticket_type:
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

    def _analyze_trips(self):
        """Phân tích các giao dịch để xác định lượt đi."""
        current_trip_id = None
        entry_transaction = None
        trip_index = 0
        has_lane_7 = False
        departure_lane = None
        end_lane = None
        previous_transaction = None
        exited_lane_5_6 = False # Biến theo dõi đã ra làn 5 hoặc 6 trong lượt đi hiện tại
        previous_exit_5_6_transaction = None # Lưu lại giao dịch ra ở làn 5 hoặc 6

        for i, trans in enumerate(self.transactions):
            if trans.fix_antent:
                continue

            if trans.is_lan7:
                has_lane_7 = True

            time_difference = None
            if previous_transaction and trans.time and previous_transaction.time:
                time_difference = (trans.time - previous_transaction.time).total_seconds()
                trans.time_difference_to_previous = time_difference
            else:
                trans.time_difference_to_previous = None

            if trans.is_entry and trans.is_lan7 and previous_transaction and previous_transaction.lane in ['Làn 8', 'Làn 9']:
                previous_transaction = trans
                continue

            # Nếu ra làn 5 hoặc 6 khi đang trong lượt đi, đánh dấu
            elif trans.is_exit and trans.lane in ['Làn 5', 'Làn 6'] and current_trip_id is not None:
                exited_lane_5_6 = True
                previous_exit_5_6_transaction = trans
                trans.trip_id = current_trip_id
                trans.trip_description = f"--Ra làn {trans.lane}--"
                previous_transaction = trans
                continue

            # Xử lý vào làn 8 hoặc 9 sau khi đã ra 5 hoặc 6
            elif trans.is_entry and trans.lane in ['Làn 8', 'Làn 9'] and exited_lane_5_6 and current_trip_id is not None:
                trans.trip_id = current_trip_id
                trans.trip_description = f"Lượt {trip_index}: Vào làn {trans.lane} (Quay đầu từ làn {previous_exit_5_6_transaction.lane if previous_exit_5_6_transaction else '?'})"
                if entry_transaction is None:
                    entry_transaction = trans
                exited_lane_5_6 = False # Reset trạng thái
                previous_exit_5_6_transaction = None # Reset
                previous_transaction = trans
                continue

            # Nếu vào một làn khác (không phải 8 hoặc 9) sau khi đã ra 5 hoặc 6,
            # kết thúc lượt đi tại giao dịch ra 5/6 và bắt đầu lượt mới
            elif trans.is_entry and trans.lane not in ['Làn 8', 'Làn 9'] and exited_lane_5_6 and current_trip_id is not None:
                # Kết thúc lượt đi tại giao dịch ra 5/6
                if previous_exit_5_6_transaction:
                    previous_exit_5_6_transaction.has_matching_exit = True
                    end_lane = previous_exit_5_6_transaction.lane
                    current_trip_id = None
                    entry_transaction = None
                    exited_lane_5_6 = False
                    previous_exit_5_6_transaction = None
                    # Bắt đầu lượt đi mới tại giao dịch vào hiện tại
                    trip_index += 1
                    current_trip_id = str(uuid.uuid4())
                    trans.trip_id = current_trip_id
                    trans.is_first_transaction_in_trip = True
                    trans.trip_description = f"Lượt {trip_index}: Vào trạm {trans.station} ({trans.lane})->Khởi hành (Làn 5/6 không quay đầu)"
                    entry_transaction = trans
                    departure_lane = trans.lane
                    trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
                    if trans.fee_of_fe == 0:
                        trans.fee_status = f"FE Không thu phí"
                    elif trans.fee_of_be == 0:
                        trans.fee_status = f"BE Không thu phí"
                    previous_transaction = trans
                    continue

            # Xử lý giao dịch ở làn 7 khi đang trong lượt đi
            elif trans.is_lan7 and current_trip_id is not None:
                trans.trip_id = current_trip_id
                trans.trip_description = f"--Làn kiểm soát--"
                previous_transaction = trans
                continue

            # XỬ LÝ KẾT THÚC LƯỢT ĐI THÔNG THƯỜNG (ĐIỀU CHỈNH QUAN TRỌNG)
            elif trans.is_exit and current_trip_id is not None and entry_transaction is not None and not (exited_lane_5_6 and trans.lane in ['Làn 5', 'Làn 6']):
                trans.trip_id = current_trip_id
                trans.trip_description = f"Lượt {trip_index}: Ra tại trạm {trans.station} ({trans.lane}) <- Kết thúc"
                trans.has_matching_exit = True
                entry_transaction.has_matching_exit = True
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
                end_lane = trans.lane
                current_trip_id = None
                entry_transaction = None
                exited_lane_5_6 = False # Reset trạng thái
                previous_exit_5_6_transaction = None # Reset
                previous_transaction = trans
                continue

            # 1. Lượt đi một chiều (từ ngoài vào)
            elif trans.is_entry and current_trip_id is None:
                trip_index += 1
                current_trip_id = str(uuid.uuid4())
                trans.trip_id = current_trip_id
                trans.is_first_transaction_in_trip = True
                trans.trip_description = f"Lượt {trip_index}: Vào trạm {trans.station} ({trans.lane})->Khởi hành"
                entry_transaction = trans
                departure_lane = trans.lane
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
                if trans.fee_of_fe == 0:
                    trans.fee_status = f"FE Không thu phí"
                elif trans.fee_of_be == 0:
                    trans.fee_status = f"BE Không thu phí"
                previous_transaction = trans
                continue

            # 2. Lượt đi dân sinh (từ trong ra, quay đầu tại trạm - logic này có thể cần xem xét lại)
            elif trans.is_exit and not trans.is_lan7 and current_trip_id is None:
                trip_index += 1
                current_trip_id = str(uuid.uuid4())
                trans.trip_id = current_trip_id
                trans.is_first_transaction_in_trip = True
                trans.trip_description = f"Lượt {trip_index}: Ra trạm {trans.station} ({trans.lane})-> Khởi hành"
                entry_transaction = trans
                departure_lane = trans.lane
                trans.has_matching_exit = False
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
                if trans.fee_of_fe > 0:
                    trans.fee_status = f"FE Thu phí sai (bắt đầu)"
                elif trans.fee_of_be > 0:
                    trans.fee_status = f"BE Thu phí sai (bắt đầu)"
                continue
            elif trans.is_entry and current_trip_id is not None and entry_transaction is not None and trans.station == entry_transaction.station:
                trans.trip_id = current_trip_id
                trans.trip_description = f"Lượt {trip_index}: Vào trạm {trans.station} ({trans.lane}) <- Kết thúc"
                trans.has_matching_exit = True
                entry_transaction.has_matching_exit = True
                trans.fee_status = self._check_fee_consistency(trans.fee_of_fe, trans.fee_of_be)
                if trans.fee_of_fe == 0:
                    trans.fee_status = f"FE Không thu phí (kết thúc)"
                elif trans.fee_of_be == 0:
                    trans.fee_status = f"BE Không thu phí (kết thúc)"
                end_lane = trans.lane
                current_trip_id = None
                entry_transaction = None
                exited_lane_5_6 = False # Reset trạng thái
                previous_exit_5_6_transaction = None # Reset
                continue

            previous_transaction = trans

        first_transaction = next((t for t in self.transactions if not t.fix_antent and not t.is_part_of_short_trip_89_to_7), None)
        if first_transaction and first_transaction.is_exit and first_transaction.trip_id is None:
            first_transaction.trip_description = f"Lượt 1: Ra trạm {first_transaction.station} ({first_transaction.lane}) - Chưa xác định điểm vào"
            first_transaction.is_first_transaction_in_trip = True
            first_transaction.has_matching_exit = True
            first_transaction.fee_status = self._check_fee_consistency(first_transaction.fee_of_fe, first_transaction.fee_of_be)
            if first_transaction.fee_of_fe > 0:
                first_transaction.fee_status = f"FE Thu phí sai (không vào)"
            elif first_transaction.fee_of_be > 0:
                first_transaction.fee_status = f"BE Thu phí sai (không vào)"

    def _count_valid_trips(self):
        """Đếm số lượt đi hợp lệ (có cả vào và ra)."""
        return sum(1 for trans in self.transactions if trans.has_matching_exit and trans.trip_id is not None and not trans.fix_antent)
    
class Cars():
    def __init__(self, df_has_fee, mapping_lane):
        try:
            self.df_has_fee = df_has_fee
            self.name = 'Xe trả phí'
            self.car_journeys = {} # Dictionary để lưu trữ các đối tượng Car
            self.mapping_lane = mapping_lane

            # Thêm hành trình xe và giao dịch vào dự án
            self._create_car_journeys()
        except Exception as e:
            print(f'Lỗi hàm __init__ trong class Cars: {e}')
            self.df_has_fee = pd.DataFrame()
            self.car_journeys = {}
            self.mapping_lane = {}

    def _create_car_journeys(self):
        try:
            for name, group in self.df_has_fee.groupby('Biển số chuẩn'):
                group_sorted = group.sort_values('Thời gian chuẩn').reset_index(drop=True)
                car = Car(name, group_sorted, self.mapping_lane)
                self.car_journeys[name] = car # Lưu trữ đối tượng Car
        except Exception as e:
            print(f'Lỗi hàm _create_car_journeys trong class Cars: {e}')
            self.car_journeys = {}

    def get_all_journeys_df(self):
        """
        Trả về một DataFrame chứa thông tin của tất cả các hành trình xe.
        """
        try:
            all_journeys = []
            for car_license, car_obj in self.car_journeys.items():
                journey_df = car_obj.get_journey_df()
                if not journey_df.empty:
                    journey_df['Biển số chuẩn'] = car_license
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
        Trả về DataFrame chứa thông tin giao dịch từ tất cả các xe.
        """
        try:
            all_transactions_data = []
            for car_license, car_obj in self.car_journeys.items():
                for trans in car_obj.transactions:
                    transaction_info = trans.info.copy()
                    transaction_info['Chênh lệch phí FE-BE'] = trans.diff_fee
                    transaction_info['Lỗi Antent'] = trans.fix_antent
                    transaction_info['T/gian 2 lượt (phút)'] = trans.time_diff_to_previous
                    transaction_info['Nghi vấn lỗi Antent'] = trans.antent_doubt
                    transaction_info['GD có FE hoặc BE'] = trans.tran_only_fe_not_be
                    transaction_info['Nghi vấn GD 1 phía'] = trans.fe_or_be_doubt
                    transaction_info['Mô tả hành trình'] = trans.trip_description
                    transaction_info['Trạng thái phí'] = trans.fee_status
                    transaction_info['Là GD đầu lượt'] = trans.is_first_transaction_in_trip
                    transaction_info['Đã có GD ra'] = trans.has_matching_exit
                    # transaction_info['ID Lượt đi'] = trans.trip_id
                    transaction_info['Biển số chuẩn'] = car_license
                    all_transactions_data.append(transaction_info)
            return pd.DataFrame(all_transactions_data)
        except Exception as e:
            print(f'Lỗi hàm get_transactions_info_df trong class Cars: {e}')
            return pd.DataFrame()

if __name__ == '__main__':
    head = ['Mã giao dịch', 'Số xe đăng ký', 'Mã thẻ', 'Phí thu', 'Làn', 'Ngày giờ', 'Loại vé', 'BE_Biển số xe', 'BE_Số etag', 'BE_Loại giá vé', 'BE_Tiền bao gồm thuế', 'BE_Thời gian qua trạm', 'BE_Làn', 'Mã giao dịch chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Loại vé chuẩn', 'Thời gian chuẩn', 'Xe không trả phí']
    val = [
        ["'1736121104", "'50H20700", "'3416214B8817620004936445", 0, '10', "'13-04-2025 00:02:37", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736121104", "'50H20700", 'Làn 10', 'Vé lượt miễn phí', '2025-04-13 00:02:37', False], # Vào miễn phí
        ["'1736765135", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 12:17:39", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736765135", "'50H20700", 'Làn 12', 'Vé lượt miễn phí', '2025-04-13 12:17:39', False], # Ra miễn phí
        ["'1736769963", "'50H20700", "'3416214B8817620004936445", 20000, '11', "'13-04-2025 12:21:20", 'Vé quý thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1736769963", "'50H20700", 'Làn 11', 'Vé quý thường', '2025-04-13 12:21:20', False], # Vào trả phí
        ["'1736852606", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 13:25:32", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736852606", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 13:25:32', False], # Ra trả phí
        ["'1736921436", "'50H20701", "'3416214B8817620004936447", 15000, '1', "'13-04-2025 14:07:22", 'Vé quý thường', np.nan, np.nan, np.nan, 15000, np.nan, np.nan, "'1736921436", "'50H20701", 'Làn 1', 'Vé quay đầu', '2025-04-13 14:07:22', False], # Vào quay đầu
        ["'1736957673", "'50H20701", "'3416214B8817620004936447", 0, '3', "'13-04-2025 14:31:02", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736957673", "'50H20701", 'Làn 3', 'Vé quay đầu', '2025-04-13 14:31:02', False], # Ra quay đầu
        ["'1737043660", "'50H20700", "'3416214B8817620004936445", 20000, '10', "'13-04-2025 15:16:20", 'Vé quý thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1737043660", "'50H20700", 'Làn 10', 'Vé quý thường', '2025-04-13 15:16:20', False], # Vào trả phí
        ["'1737123456", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 16:01:30", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1737123456", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 16:01:30', False], # Ra trả phí
        ["'1737156789", "'50H20702", "'3416214B8817620004936449", 10000, '7', "'13-04-2025 16:30:45", 'Vé lượt miễn phí', np.nan, np.nan, np.nan, 10000, np.nan, np.nan, "'1737156789", "'50H20702", 'Làn 7', 'Vé lượt miễn phí', '2025-04-13 16:30:45', False], # Vào Làn 7
        ["'1737200000", "'50H20702", "'3416214B8817620004936449", 0, '5', "'13-04-2025 17:05:00", 'Vé lượt miễn phí', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1737200000", "'50H20702", 'Làn 5', 'Vé lượt miễn phí', '2025-04-13 17:05:00', False], # Ra Làn 5
    ]
    df = pd.DataFrame(val, columns=head)

    mapping_lane_config = {
        'Đồng Khởi_2A': {'vào': ['Làn 10', 'Làn 11'], 'ra': ['Làn 12']},
        'ĐT768_1A': {'vào': ['Làn 1', 'Làn 2'], 'ra': ['Làn 3', 'Làn 4']},
        'ĐT768_3': {'vào': ['Làn 7', 'Làn 8', 'Làn 9'], 'ra': ['Làn 5', 'Làn 6']}
    }

    cars_manager = Cars(df, mapping_lane_config)
    all_transactions_info = cars_manager.get_transactions_info_df()
    print(all_transactions_info[['Thời gian chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Mô tả hành trình', 'Trạng thái phí', 'Đã có giao dịch ra', 'ID Lượt đi']])