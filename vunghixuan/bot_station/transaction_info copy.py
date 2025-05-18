import pandas as pd
import numpy as np
import traceback
import uuid

class Transaction:
    def __init__(self, transaction, mapping_lane):
        """
        Khởi tạo đối tượng ThongTinGiaoDich từ một giao dịch.
        """
        self.tran_reasonable_time_minutes = 10  # Thời gian hợp lý (phút)
        self.tran_unusual_time_minutes = 10     # Thời gian chuyến đi bất thường (phút)
        self.duplicate_transactions_minutes = 5 # Giao dịch xảy ra trùng lặp do Antent (phút)

        self.time = None
        self.station = None
        self.lane_type = None
        self.fee_of_fe = None
        self.fee_of_be = None
        self.diff_fee = None             # Chênh lệch phí giữa FE và BE
        self.time_diff_to_previous = None
        self.index_in_df = None          # Lưu trữ index của giao dịch trong DataFrame
        self.lane = None
        self.info = {}                 # Dictionary để lưu trữ thông tin đầy đủ của giao dịch
        self.standard_ticket_type = None # 'Loại vé chuẩn'
        self.mapping_lane = mapping_lane

        # Các biến mới cho việc kiểm tra lượt đi
        self.is_chargeable = False      # Xác định giao dịch có thu phí hay không
        self.is_entry = False           # Xác định là giao dịch vào
        self.is_exit = False            # Xác định là giao dịch ra
        self.is_lan7 = False            # Xác định là làn số 7
        self.trip_id = None             # ID của lượt đi
        self.is_first_transaction_in_trip = False # Là giao dịch đầu tiên của lượt đi
        self.trip_description = ''      # Mô tả hành trình của lượt đi
        self.has_matching_exit = False  # Đã có giao dịch ra tương ứng
        self.fee_status = '' # Trạng thái phí BE/FE
        self.is_round_trip = False      # Xác định là giao dịch quay đầu
        self.fix_antent = False         # Xác định giao dịch bị lỗi antent
        self.antent_doubt = ''          # Nghi vấn lỗi antent
        self.is_part_of_short_trip_89_to_7 = False # Khắc phục lỗi xe đi vào làn 8,9 đi ra làn 7 bị lỗi Antent

        # Phân tích biến đổi kiểu dữ liệu
        self._parse_transaction(transaction)

    def _parse_transaction(self, transaction):
        """Phân tích thông tin từ giao dịch."""
        try:
            self.info = transaction.to_dict() # Lưu trữ toàn bộ giao dịch dưới dạng dictionary
            self.car_name = transaction['Biển số chuẩn']
            self.name = transaction['Mã giao dịch']
            self.time = pd.to_datetime(transaction['Thời gian chuẩn'])
            self.standard_ticket_type = transaction['Loại vé chuẩn']
            # Xử lý 'Phí thu'
            phi_thu = pd.to_numeric(transaction['Phí thu'], errors='coerce')
            self.fee_of_fe = phi_thu if pd.notna(phi_thu) else 0

            # Xử lý 'BE_Tiền bao gồm thuế'
            be_tien = pd.to_numeric(transaction['BE_Tiền bao gồm thuế'], errors='coerce')
            self.fee_of_be = be_tien if pd.notna(be_tien) else 0

            self.lane = str(transaction['Làn chuẩn'])
            self.station = self._get_station_from_lane(self.lane)
            self.lane_type = self._get_lane_type(self.lane)
            self.diff_fee = self.fee_of_fe - self.fee_of_be
            self.index_in_df = transaction.name # Lấy index từ Series
            self.is_lan7 = self.lane.strip() == 'Làn 7'

            # 1. Nghi vấn lỗi antent
            self.time_diff_to_previous = None
            self.antent_doubt = '' # NGhi vấn lỗi antent

            # 2. Lỗi chênh lệch phí do chỉ có FE hoặc BE
            self.tran_only_fe_not_be = False
            self.fe_or_be_doubt = '' # Nghi vấn chênh lệch BE hoặc FE
            self._check_fee_one_sided()

            # Xác định giao dịch có thu phí
            if self.fee_of_fe > 0:
                self.is_chargeable = True

            self.is_entry = self._check_lane_type(self.lane, 'vào')
            self.is_exit = self._check_lane_type(self.lane, 'ra')

        except Exception:
            print(f"Lỗi xảy ra trong hàm _parse_transaction:")
            traceback.print_exc()

    def _get_station_from_lane(self, lane):
        """Trích xuất tên trạm chuẩn hóa từ tên làn."""
        try:
            if pd.isna(lane):
                return None
            lane_str = str(lane).strip()
            for station, lane_info in self.mapping_lane.items():
                if lane_str in [l.strip() for l in lane_info.get('vào', [])] or \
                   lane_str in [l.strip() for l in lane_info.get('ra', [])]:
                    return station
            return None
        except Exception:
            print(f"Lỗi xảy ra trong hàm _get_station_from_lane:")
            traceback.print_exc()
            return None

    def _get_lane_type(self, lane):
        """Xác định loại làn (in/out) từ tên làn dựa trên mapping chuẩn hóa."""
        try:
            if pd.isna(lane):
                return None
            lane_str = str(lane).strip()
            for station, lane_info in self.mapping_lane.items():
                if lane_str in [l.strip() for l in lane_info.get('vào', [])]:
                    return 'vào'
                elif lane_str in [l.strip() for l in lane_info.get('ra', [])]:
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
            for station, lane_info in self.mapping_lane.items():
                if lane_str in [l.strip() for l in lane_info.get(type, [])]:
                    return True
            return False
        except Exception:
            print(f"Lỗi xảy ra trong hàm _check_lane_type:")
            traceback.print_exc()
            return False

    def _check_fee_one_sided(self):
        """Thống kê các giao dịch chỉ có BE hoặc FE."""
        if self.fee_of_fe != 0 and self.fee_of_be == 0:
            self.tran_only_fe_not_be = True
            self.fe_or_be_doubt = 'GD FE có, BE không'
        elif self.fee_of_fe == 0 and self.fee_of_be != 0:
            self.fe_or_be_doubt = 'Nghi vấn thu phí nguội'
        elif self.diff_fee == 0:
            self.fe_or_be_doubt = 'Khớp GD'

    def calculate_the_time_difference_for_fix_from_antent(self, other_transaction):
        """Tính chênh lệch thời gian với giao dịch trước đó (phút) và xác định nghi vấn lỗi Antent, bỏ qua làn 7."""
        try:
            # Kiểm tra nếu giao dịch hiện tại HOẶC giao dịch trước đó là ở làn 7, thì bỏ qua
            if self.is_lan7 or (other_transaction and hasattr(other_transaction, 'is_lan7') and other_transaction.is_lan7):
                self.time_diff_to_previous = None
                self.fix_antent = False
                self.antent_doubt = None
                return  # Thoát khỏi hàm mà không thực hiện kiểm tra lỗi Antent

            other_time = other_transaction.time
            time_diff_seconds = (self.time - other_time).total_seconds()
            time_diff_minutes = time_diff_seconds / 60

            if time_diff_minutes < self.duplicate_transactions_minutes:
                doubt_note = 'Nghi vấn lỗi Antent'

                # Đánh dấu giao dịch hiện tại
                self.time_diff_to_previous = round(time_diff_minutes, 3)
                self.fix_antent = True
                self.antent_doubt = doubt_note
                # if self.diff_fee != 0:
                #     self.antent_doubt += ' (có chênh lệch phí FE-BE)'
                # else:
                #     self.antent_doubt += ' (phí FE-BE khớp)'

                # # Đánh dấu giao dịch trước đó (tùy thuộc vào logic bạn muốn)
                # # other_transaction.time_diff_to_previous = round(time_diff_minutes, 3)
                # # other_transaction.fix_antent = True
                # # other_transaction.antent_doubt = doubt_note
                # # if other_transaction.diff_fee != 0:
                # #     other_transaction.antent_doubt += ' (có chênh lệch phí FE-BE)'
                # # else:
                # #     other_transaction.antent_doubt += ' (phí FE-BE khớp)'
            # else:
            #     self.time_diff_to_previous = round(time_diff_minutes, 3)

        except Exception:
            print(f"Lỗi xảy ra trong hàm calculate_the_time_difference_for_fix_from_antent:")
            traceback.print_exc()
            self.time_diff_to_previous = None