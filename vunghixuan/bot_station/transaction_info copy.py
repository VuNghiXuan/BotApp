import pandas as pd
import numpy as np
import traceback
import uuid

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
        self.standard_ticket_type = None # 'Loại vé chuẩn'

        self.mapping_lane = {
            '2A': {'vào': ['Làn 10', 'Làn 11'], 'ra': ['Làn 12'], 'trạm': 'Đồng Khởi_2A'},
            '1A': {'vào': ['Làn 1', 'Làn 2'], 'ra': ['Làn 3', 'Làn 4'], 'trạm': 'ĐT768_1A'},
            '3B': {'vào': ['Làn 7', 'Làn 8', 'Làn 9'], 'ra': [], 'trạm': 'ĐT768_3B'},
            '3A': {'vào': [], 'ra': ['Làn 5', 'Làn 6'], 'trạm': 'ĐT768_3A'}}

        # Các biến mới cho việc kiểm tra lượt đi
        self.is_chargeable = False # Xác định giao dịch có thu phí hay không
        self.is_entry = False # Xác định là giao dịch vào
        self.is_exit = False # Xác định là giao dịch ra
        self.trip_id = None # ID của lượt đi
        self.is_first_transaction_in_trip = False # Là giao dịch đầu tiên của lượt đi
        self.trip_description = '' # Mô tả hành trình của lượt đi
        self.has_matching_exit = False # Đã có giao dịch ra tương ứng
        self.fee_status = 'Chưa xác định' # Trạng thái phí BE/FE
        self.is_round_trip = False # Xác định là giao dịch quay đầu

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

            # Xác định giao dịch có thu phí
            if self.fee_of_fe > 0:
                self.is_chargeable = True

            self.is_entry = self._check_lane_type(self.lane, 'vào')
            self.is_exit = self._check_lane_type(self.lane, 'ra')

            self.journey_descripts = ''
        except Exception:
            print(f"Lỗi xảy ra trong hàm _parse_transaction:")
            traceback.print_exc()

    def _get_station_from_lane(self, lane):
        """Trích xuất tên trạm chuẩn hóa từ tên làn."""
        try:
            if pd.isna(lane):
                return None
            lane_str = str(lane).strip()
            if lane_str in ['Làn 7', 'Làn 8', 'Làn 9', 'Làn 5', 'Làn 6']:
                return 'ĐT768_3'
            elif lane_str in ['Làn 10', 'Làn 11', 'Làn 12']:
                return 'Đồng Khởi_2A'
            elif lane_str in ['Làn 1', 'Làn 2', 'Làn 3', 'Làn 4']:
                return 'ĐT768_1A'
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
            if lane_str in ['Làn 7', 'Làn 8', 'Làn 9']:
                return 'vào'
            elif lane_str in ['Làn 5', 'Làn 6']:
                return 'ra'
            elif lane_str in ['Làn 10', 'Làn 11']:
                return 'vào'
            elif lane_str == 'Làn 12':
                return 'ra'
            elif lane_str in ['Làn 1', 'Làn 2']:
                return 'vào'
            elif lane_str in ['Làn 3', 'Làn 4']:
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

    def transactions_only_has_FE_or_BE(self):
        "Thống kê các giao dịch chỉ có BE hoặc FE"
        if self.fee_of_fe != 0 and self.fee_of_be == 0:
            self.tran_only_fe_not_be = True
            self.fe_or_be_doubt ='Giao dịch có FE, không có BE'
        elif self.fee_of_fe == 0 and self.fee_of_be != 0:
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
                if self.diff_fee != 0:
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