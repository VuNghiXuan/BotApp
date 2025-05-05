import pandas as pd
import numpy as np
import traceback

class Transaction:
    def __init__(self, transaction):
        """Khởi tạo đối tượng giao dịch."""
        self.duplicate_transactions_minutes = 5  # Thời gian trùng lặp (phút)

        self.time = None
        self.lane = None
        self.fee_fe = None
        self.fee_be = None
        self.diff_fee = None
        self.time_diff_antent = None
        self.antent_error = False
        self.station_in = None
        self.lane_in = None
        self.station_out = None
        self.lane_out = None
        self.trip_description = ''
        self.fee_status = ''
        self.is_first_transaction = False
        self.is_chargeable_in = False
        self.is_chargeable_out = False
        self.is_free_on_exit = False
        self.is_round_trip_valid = False
        self.is_new_trip_diff_station = False

        self.mapping_lane = {
            '2A': {'vào': ['Làn 10', 'Làn 11'], 'ra': ['Làn 12'], 'name': 'Đồng Khởi_2A'},
            '1A': {'vào': ['Làn 1', 'Làn 2'], 'ra': ['Làn 3', 'Làn 4'], 'name': 'ĐT768_1A'},
            '3B': {'vào': ['Làn 7', 'Làn 8', 'Làn 9'], 'ra': [], 'name': 'ĐT768_3B'},
            '3A': {'vào': [], 'ra': ['Làn 5', 'Làn 6'], 'name': 'ĐT768_3A'}}

        self._parse_transaction(transaction)

    def _parse_transaction(self, transaction):
        """Phân tích thông tin từ giao dịch."""
        try:
            self.time = pd.to_datetime(transaction['Thời gian chuẩn'])
            self.lane = str(transaction['Làn chuẩn']).strip()
            self.fee_fe = pd.to_numeric(transaction['Phí thu'], errors='coerce') or 0
            self.fee_be = pd.to_numeric(transaction['BE_Tiền bao gồm thuế'], errors='coerce') or 0
            self.diff_fee = self.fee_fe - self.fee_be

            for station, lanes in self.mapping_lane.items():
                if self.lane in [l.strip() for l in lanes.get('vào', [])]:
                    self.station_in = lanes['name']
                    self.lane_in = self.lane
                if self.lane in [l.strip() for l in lanes.get('ra', [])]:
                    self.station_out = lanes['name']
                    self.lane_out = self.lane

        except Exception:
            print(f"Lỗi parse transaction: {traceback.format_exc()}")

    def check_antent_error(self, prev_transaction):
        """Kiểm tra lỗi antent với giao dịch trước đó."""
        if prev_transaction and self.station_in == prev_transaction.station_in:
            time_diff = (self.time - prev_transaction.time).total_seconds() / 60
            if 0 < time_diff < self.duplicate_transactions_minutes:
                self.antent_error = True
                self.time_diff_antent = round(time_diff, 2)

class CarJourney:
    def __init__(self, car_license, journey_df):
        """Khởi tạo hành trình xe."""
        self.license_plate = car_license
        self.transactions = []
        self._process_transactions(journey_df)
        self._analyze_journey()
        self.trip_count = self._count_trips()

    def _process_transactions(self, df):
        """Tạo đối tượng Transaction và kiểm tra lỗi antent."""
        sorted_df = df.sort_values(by='Thời gian chuẩn').reset_index(drop=True)
        for index, row in sorted_df.iterrows():
            transaction = Transaction(row)
            if index > 0:
                transaction.check_antent_error(self.transactions[-1])
            transaction.is_first_transaction = (index == 0)
            self.transactions.append(transaction)

    def _analyze_journey(self):
        """Phân tích hành trình để xác định lượt và trạng thái phí."""
        for i, trans in enumerate(self.transactions):
            if trans.is_first_transaction:
                if trans.station_in and trans.fee_fe > 0:
                    trans.is_chargeable_in = True
                    trans.trip_description = 'Vào (thu phí)'
                elif trans.station_out and trans.fee_fe > 0:
                    trans.is_chargeable_out = True
                    trans.trip_description = 'Ra (thu phí - từ dự án)'
            elif i > 0:
                prev_trans = self.transactions[i-1]
                if prev_trans.is_chargeable_in and trans.station_out == prev_trans.station_in:
                    trans.is_free_on_exit = True
                    trans.trip_description = 'Ra (miễn phí - sau vào)'
                elif prev_trans.is_chargeable_out and trans.station_in == prev_trans.station_out:
                    trans.is_round_trip_valid = True
                    trans.trip_description = 'Vào lại cùng trạm (sau ra)'
                elif prev_trans.is_chargeable_out and trans.station_in and trans.station_in != prev_trans.station_out and trans.fee_fe > 0:
                    trans.is_new_trip_diff_station = True
                    trans.trip_description = 'Vào trạm khác (lượt mới)'

            if trans.fee_fe == trans.fee_be:
                trans.fee_status = 'FE=BE'
            elif trans.fee_fe > trans.fee_be:
                trans.fee_status = 'FE>BE'
            elif trans.fee_fe < trans.fee_be:
                trans.fee_status = 'FE<BE'

    def _count_trips(self):
        """Đếm số lượt đi đơn giản."""
        trips = 0
        first_chargeable_in = False
        first_chargeable_out = False
        for trans in self.transactions:
            if trans.is_chargeable_in and not first_chargeable_in:
                trips += 0.5
                first_chargeable_in = True
            elif trans.is_chargeable_out and not first_chargeable_out:
                trips += 0.5
                first_chargeable_out = True
            elif trans.is_free_on_exit and first_chargeable_in:
                trips += 0.5
                first_chargeable_in = False
            elif trans.is_round_trip_valid and first_chargeable_out:
                trips += 0.5
                first_chargeable_out = False
            elif trans.is_new_trip_diff_station and trans.is_chargeable_in:
                trips += 0.5
                first_chargeable_in = True
                first_chargeable_out = False
            elif trans.is_new_trip_diff_station and trans.is_chargeable_out:
                trips += 0.5
                first_chargeable_out = True
                first_chargeable_in = False
        return int(trips)

class TollDataProcessor:
    def __init__(self, df):
        """Khởi tạo bộ xử lý dữ liệu thu phí."""
        self.df = df
        self.car_journeys = self._create_car_journeys()

    def _create_car_journeys(self):
        """Tạo đối tượng CarJourney cho mỗi xe."""
        journeys = {}
        for license_plate, group in self.df.groupby('Biển số chuẩn'):
            journeys[license_plate] = CarJourney(license_plate, group)
        return journeys

    def get_simplified_transactions(self):
        """Lấy thông tin giao dịch đã đơn giản hóa."""
        simplified_data = []
        for journey in self.car_journeys.values():
            for trans in journey.transactions:
                simplified_data.append({
                    'Thời gian': trans.time,
                    'Biển số': journey.license_plate,
                    'Trạm vào (Làn)': f"{trans.station_in or ''} ({trans.lane_in or ''})",
                    'Trạm ra (Làn)': f"{trans.station_out or ''} ({trans.lane_out or ''})",
                    'Phí FE': trans.fee_fe,
                    'Phí BE': trans.fee_be,
                    'Chênh lệch phí': trans.diff_fee,
                    'Lỗi Antent': trans.antent_error,
                    'Thời gian lệch (phút)': trans.time_diff_antent,
                    'Mô tả lượt đi': trans.trip_description,
                    'Trạng thái phí': trans.fee_status,
                    'Tổng lượt đi/ngày': journey.trip_count
                })
        return pd.DataFrame(simplified_data)

if __name__ == '__main__':
    head = ['Mã giao dịch', 'Số xe đăng ký', 'Mã thẻ', 'Phí thu', 'Làn chuẩn', 'Ngày giờ', 'Loại vé', 'BE_Biển số xe', 'BE_Số etag', 'BE_Loại giá vé', 'BE_Tiền bao gồm thuế', 'BE_Thời gian qua trạm', 'BE_Làn', 'Mã giao dịch chuẩn', 'Biển số chuẩn', 'Làn', 'Loại vé chuẩn', 'Thời gian chuẩn', 'Xe không trả phí']
    val = [
        ["'1736121104", "'50H20700", "'3416214B8817620004936445", 20000, 'Làn 10', "'13-04-2025 00:02:37", 'Giá thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1736121104", "'50H20700", '10', 'Giá thường', '2025-04-13 00:02:37', False],
        ["'1736121105", "'50H20700", "'3416214B8817620004936445", 20000, 'Làn 10', "'13-04-2025 00:04:37", 'Giá thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1736121105", "'50H20700", '10', 'Giá thường', '2025-04-13 00:04:37', False], # Lỗi antent
        ["'1736765135", "'50H20700", "'3416214B8817620004936445", 0, 'Làn 12', "'13-04-2025 12:17:39", 'Giá thường', np.nan, np.nan, np.nan, 0, np.nan, np.nan, "'1736765135", "'50H20700", '12', 'Giá thường', '2025-04-13 12:17:39', False],
        ["'1736769963", "'50H20701", "'3416214B8817620004936446", 20000, 'Làn 3', "'13-04-2025 12:21:20", 'Giá thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1736769963", "'50H20701", '3', 'Giá thường', '2025-04-13 12:21:20', False],
        ["'1736852606", "'50H20701", "'3416214B8817620004936446", 20000, 'Làn 1', "'13-04-2025 13:25:32", 'Giá thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1736852606", "'50H20701", '1', 'Giá thường', '2025-04-13 13:25:32', False],
        ["'1736921436", "'50H20702", "'3416214B8817620004936447", 20000, 'Làn 10', "'13-04-2025 14:07:22", 'Giá thường', np.nan, np.nan, np.nan, 15000, np.nan, np.nan, "'1736921436", "'50H20702", '10', 'Giá thường', '2025-04-13 14:07:22', False], # Chênh lệch phí
        ["'1736957673", "'50H20702", "'3416214B8817620004936447", 20000, 'Làn 5', "'13-04-2025 14:31:02", 'Giá thường', np.nan, np.nan, np.nan, 20000, np.nan, np.nan, "'1736957673", "'50H20702", '5', 'Giá thường', '2025-04-13 14:31:02', False],
    ]

    df = pd.DataFrame(val, columns=head)
    df['Thời gian chuẩn'] = pd.to_datetime(df['Thời gian chuẩn'])

    processor = TollDataProcessor(df)
    simplified_df = processor.get_simplified_transactions()
    print(simplified_df)