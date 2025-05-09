import pandas as pd
import numpy as np
import uuid
from vunghixuan.bot_station.transaction_info import Transaction
# from transaction_info import Transaction



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
            self._analyze_trips() # Phân tích lượt đi
            self.trip_count = self._count_valid_trips() # Đếm số lượt đi hợp lệ
        except Exception as e:
            print(f'Lỗi hàm __init__ trong class Car: {e}')
            self.name = None
            self.journey = pd.DataFrame()
            self.total_journey = 0
            self.transactions = []
            self.trip_count = 0

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

    def _check_previous_paid_transaction(self, current_transaction_index, time_window_minutes=30):
        """
        Kiểm tra xem trong khoảng thời gian trước giao dịch hiện tại có giao dịch thu phí nào ở làn vào khác không.
        """
        current_time = self.transactions[current_transaction_index].time
        for i in range(current_transaction_index - 1, -1, -1):
            previous_tran = self.transactions[i]
            time_diff = (current_time - previous_tran.time).total_seconds() / 60
            if time_diff > time_window_minutes:
                break
            if previous_tran.is_chargeable and previous_tran.lane_type == 'vào' and previous_tran.lane != 'Làn 7':
                return True
        return False
    
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
        các thông tin kiểm tra lỗi và lượt đi.
        """
        try:
            all_transactions_data = []
            for car_license, car_obj in self.car_journeys.items():
                for trans in car_obj.transactions:
                    transaction_info = trans.info.copy()

                    transaction_info['Chênh lệch phí FE-BE'] = trans.diff_fee
                    # 1. Lỗi antent
                    transaction_info['Lỗi Antent'] = trans.fix_antent
                    transaction_info['T/gian 2 lượt (phút)'] = trans.time_diff_to_previous
                    transaction_info['Nghi vấn lỗi Antent'] = trans.antent_doubt

                    # 2. Lỗi giao dịch chỉ 1 phía BE hoặc FE
                    transaction_info['Giao dịch có FE hoặc BE'] = trans.tran_only_fe_not_be
                    transaction_info['Nghi vấn giao dịch 1 phía'] = trans.fe_or_be_doubt

                    # 3. Thông tin lượt đi
                    transaction_info['Mô tả hành trình'] = trans.trip_description
                    # transaction_info['ID Lượt đi'] = trans.trip_id
                    transaction_info['Trạng thái phí'] = trans.fee_status
                    transaction_info['Là giao dịch đầu lượt'] = trans.is_first_transaction_in_trip
                    transaction_info['Đã có giao dịch ra'] = trans.has_matching_exit

                    all_transactions_data.append(transaction_info)
            return pd.DataFrame(all_transactions_data)
        except Exception as e:
            print(f'Lỗi hàm get_transactions_info_df trong class Cars: {e}')
            return pd.DataFrame()


if __name__ == '__main__':
    head = ['Mã giao dịch', 'Số xe đăng ký', 'Mã thẻ', 'Phí thu', 'Làn', 'Ngày giờ', 'Loại vé', 'BE_Biển số xe', 'BE_Số etag', 'BE_Loại giá vé', 'BE_Tiền bao gồm thuế', 'BE_Thời gian qua trạm', 'BE_Làn', 'Mã giao dịch chuẩn', 'Biển số chuẩn', 'Làn chuẩn', 'Loại vé chuẩn', 'Thời gian chuẩn', 'Xe không trả phí']
    # val = [
    #     ["'1736121104", "'50H20700", "'3416214B8817620004936445", 0, '10', "'13-04-2025 00:02:37", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736121104", "'50H20700", 'Làn 10', 'Vé lượt miễn phí', '2025-04-13 00:02:37', False], # Vào miễn phí
    #     ["'1736765135", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 12:17:39", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736765135", "'50H20700", 'Làn 12', 'Vé lượt miễn phí', '2025-04-13 12:17:39', False], # Ra miễn phí
    #     ["'1736769963", "'50H20700", "'3416214B8817620004936445", 20000, '11', "'13-04-2025 12:21:20", 'Vé quý thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1736769963", "'50H20700", 'Làn 11', 'Vé quý thường', '2025-04-13 12:21:20', False], # Vào trả phí
    #     ["'1736852606", "'50H20700", "'3416214B8817620004936445", 0, '12', "'13-04-2025 13:25:32", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736852606", "'50H20700", 'Làn 12', 'Vé quý thường', '2025-04-13 13:25:32', False], # Ra trả phí
    #     ["'1736921436", "'50H20701", "'3416214B8817620004936447", 15000, '1', "'13-04-2025 14:07:22", 'Vé quý thường', np.nan, np.nan, np.nan, 15000, np.nan, np.nan, "'1736921436", "'50H20701", 'Làn 1', 'Vé quay đầu', '2025-04-13 14:07:22', False], # Vào quay đầu
    #     ["'1736957673", "'50H20701", "'3416214B8817620004936447", 0, '3', "'13-04-2025 14:31:02", 'Vé quý thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736957673", "'50H20701", 'Làn 3', 'Vé quay đầu', '2025-04-13 14:31:02', False], # Ra quay đầu
    #     ["'1737043660", "'50H20700", "'3416214B8817620004936445", 20000, '10', "'13-04-2025 15:16:20", 'Vé quý thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1737043660", "'50H20700", 'Làn 10', 'Vé quý thường', '2025-04-13 15:16:20', False], # Vào trả phí
    #     ["'173