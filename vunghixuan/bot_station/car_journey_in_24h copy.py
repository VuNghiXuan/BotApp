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

    def check_turn(self):
        """
        Kiểm tra lượt vé đi, xác định trạng thái phí thu (BE/FE),
        và đếm số lượt đi trong ngày cho mỗi xe.
        """
        ket_qua_kiem_tra = {}
        so_luot_di_ngay = {}

        for car_license, car_obj in self.car_journeys.items():
            transactions = car_obj.transactions
            num_transactions = len(transactions)
            luot_di = []
            trang_thai_phi = []

            if num_transactions > 0:
                # Phân tích lượt đi và trạng thái phí
                i = 0
                while i < num_transactions:
                    tran1 = transactions[i]
                    i += 1
                    if i < num_transactions:
                        tran2 = transactions[i]

                        # Kiểm tra lượt đi hợp lệ (cùng trạm, vào-ra hoặc ra-vào, thời gian hợp lý)
                        if (tran1.station == tran2.station and
                            ((tran1.is_in_lane and tran2.is_out_lane) or (tran1.is_out_lane and tran2.is_in_lane)) and
                            (tran2.time - tran1.time).total_seconds() / 60 > tran1.tran_reasonable_time_minutes and
                            not tran1.fix_antent and not tran2.fix_antent):
                            luot_di.append((tran1.info['Mã giao dịch'], tran2.info['Mã giao dịch']))
                            i += 1 # Bỏ qua giao dịch thứ hai của lượt đi
                        else:
                            luot_di.append((tran1.info['Mã giao dịch'], None)) # Giao dịch đơn lẻ hoặc không tạo thành lượt hợp lệ

                    else:
                        luot_di.append((tran1.info['Mã giao dịch'], None)) # Giao dịch cuối cùng

                # Xác định trạng thái phí cho từng giao dịch
                for tran in transactions:
                    if tran.fee_of_be == tran.fee_of_fe:
                        trang_thai = "Cả hai đúng"
                    elif tran.fee_of_be != 0 and tran.fee_of_fe == 0:
                        trang_thai = "BE đúng, FE sai"
                    elif tran.fee_of_be == 0 and tran.fee_of_fe != 0:
                        trang_thai = "FE đúng, BE sai"
                    else:
                        trang_thai = "Cả hai sai"
                    trang_thai_phi.append(trang_thai)

                ket_qua_kiem_tra[car_license] = list(zip([tran.info['Mã giao dịch'] for tran in transactions], trang_thai_phi, luot_di))
                so_luot_di_ngay[car_license] = len([ld for ld in luot_di if ld[1] is not None])

        return ket_qua_kiem_tra, so_luot_di_ngay


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