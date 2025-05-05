from datetime import datetime, timedelta

class TramThuPhi:
    def __init__(self, ten_tram, tuyen_duong, lan_vao=None, lan_ra=None):
        """
        Khởi tạo một trạm thu phí với thông tin trạm, làn và các loại vé hỗ trợ.

        Args:
            ten_tram (str): Tên của trạm thu phí.
            tuyen_duong (str): Tên tuyến đường mà trạm thu phí này thuộc về.
            lan_vao (list, optional): Danh sách các làn xe vào. Defaults to None.
            lan_ra (list, optional): Danh sách các làn xe ra. Defaults to None.
        """
        self.ten_tram = ten_tram
        self.tuyen_duong = tuyen_duong
        self.lan_vao = lan_vao if lan_vao else []
        self.lan_ra = lan_ra if lan_ra else []
        self.luot_xe_da_qua = {}  # Lưu thông tin lượt xe đã qua trong ngày {bien_so_xe: [thoi_gian_vao, ten_tram_vao]}
        self.ve_thang = {}  # Lưu thông tin vé tháng {bien_so_xe: thoi_gian_het_han}
        self.mien_phi_khu_vuc = ["Trạm 2A", "Trạm 1A", "Trạm 3B"] # Các trạm được miễn giảm 100% cho đối tượng cụ thể
        self.cac_loai_ve = {
            "Giá thường": self._tinh_phi_gia_thuong,
            "UT toàn quốc": self._mien_phi,
            "Vé tháng thường": self._mien_phi,
            "Miễn phí quay đầu": self._mien_phi_quay_dau,
            f"Miễn giảm 100% trạm {self.ten_tram}": self._mien_phi_khu_vuc_cu_the,
            "Miễn phí liên trạm": self._mien_phi
        }

        # Khởi tạo mặc định làn nếu không được truyền vào
        if lan_vao is None and self.ten_tram == "Trạm 2A":
            self.lan_vao = [10, 11]
        elif lan_vao is None and self.ten_tram == "Trạm 1A":
            self.lan_vao = [1, 2]
        elif lan_vao is None and self.ten_tram == "Trạm 3B":
            self.lan_vao = [7, 8, 9]
        elif lan_vao is None and self.ten_tram == "Trạm 3A":
            self.lan_vao = [] # Trạm 3A chỉ có làn ra

        if lan_ra is None and self.ten_tram == "Trạm 2A":
            self.lan_ra = [12]
        elif lan_ra is None and self.ten_tram == "Trạm 1A":
            self.lan_ra = [3, 4]
        elif lan_ra is None and self.ten_tram == "Trạm 3B":
            self.lan_ra = [] # Trạm 3B chỉ có làn vào
        elif lan_ra is None and self.ten_tram == "Trạm 3A":
            self.lan_ra = [5, 6]

    def them_ve_thang(self, bien_so_xe, thoi_gian_het_han):
        """
        Thêm thông tin vé tháng cho một xe.

        Args:
            bien_so_xe (str): Biển số xe.
            thoi_gian_het_han (datetime): Thời điểm hết hạn của vé tháng.
        """
        self.ve_thang[bien_so_xe] = thoi_gian_het_han

    def _mien_phi(self, luot_di_trong_ngay, thoi_gian_hien_tai):
        """
        Hàm trả về phí là 0 cho các loại vé miễn phí.
        """
        return 0

    def _mien_phi_quay_dau(self, luot_di_trong_ngay, thoi_gian_hien_tai):
        """
        Hàm xác định phí cho vé miễn phí quay đầu (cần logic cụ thể hơn).
        """
        # Ví dụ logic đơn giản: Miễn phí nếu vào và ra cùng trạm trong vòng 15 phút
        if luot_di_trong_ngay and luot_di_trong_ngay["vao"] and luot_di_trong_ngay["ra"] and len(luot_di_trong_ngay["ra"]) == 1:
            thoi_gian_vao = luot_di_trong_ngay["vao"]["thoi_gian"]
            thoi_gian_ra = luot_di_trong_ngay["ra"][0]["thoi_gian"]
            if luot_di_trong_ngay["vao"]["tram"] == luot_di_trong_ngay["ra"][0]["tram"] and (thoi_gian_ra - thoi_gian_vao) < timedelta(minutes=15):
                return 0
        return 1 # Mặc định tính phí nếu không đủ điều kiện

    def _mien_phi_khu_vuc_cu_the(self, luot_di_trong_ngay, thoi_gian_hien_tai):
        """
        Hàm trả về phí là 0 cho vé miễn giảm 100% tại trạm cụ thể.
        """
        return 0

    def _tinh_phi_gia_thuong(self, luot_di_trong_ngay, thoi_gian_hien_tai):
        """
        Hàm tính phí cho vé giá thường.
        """
        if luot_di_trong_ngay and luot_di_trong_ngay["vao"]:
            tram_vao = luot_di_trong_ngay["vao"]["tram"]
            if tram_vao in ["Trạm 2A", "Trạm 1A", "Trạm 3B"] and self.ten_tram in ["Trạm 2A", "Trạm 1A", "Trạm 3B", "Trạm 3A"]:
                return 1 # Lần ra đầu tiên sau khi vào
            elif luot_di_trong_ngay["ra"] and len(luot_di_trong_ngay["ra"]) > 1 and thoi_gian_hien_tai.date() == luot_di_trong_ngay["vao"]["thoi_gian"].date():
                return 1 # Nếu đã có lượt ra trước đó trong ngày (khởi hành từ trong dự án)
            elif luot_di_trong_ngay["vao"]["tram"] == self.ten_tram and len(luot_di_trong_ngay["ra"]) == 1:
                return 1 # Vào ra cùng trạm
            elif luot_di_trong_ngay["vao"]["tram"] != self.ten_tram:
                return 1
            else:
                return 1
        else:
            return 1 # Nếu không ghi nhận lượt vào

class KiemTraThuPhi:
    def __init__(self, cac_tram=None):
        """
        Khởi tạo class kiểm tra thu phí.

        Args:
            cac_tram (dict, optional): Dictionary chứa thông tin các trạm thu phí {ten_tram: TramThuPhi}.
                                      Nếu None, sẽ khởi tạo mặc định các trạm.
        """
        if cac_tram is None:
            self.cac_tram = {
                "Trạm 2A": TramThuPhi("Trạm 2A", "Đường Đồng Khởi"),
                "Trạm 1A": TramThuPhi("Trạm 1A", "Đường ĐT768"),
                "Trạm 3B": TramThuPhi("Trạm 3B", "Đường ĐT768"),
                "Trạm 3A": TramThuPhi("Trạm 3A", "Đường ĐT768"),
            }
        else:
            self.cac_tram = cac_tram

    def so_sanh_phi_thu(self, bien_so_xe, loai_ve, danh_sach_lan, danh_sach_thoi_gian, phi_thu_be, phi_thu_fe):
        """
        Kiểm tra và so sánh phí thu giữa BE và FE.

        Args:
            bien_so_xe (str): Biển số xe.
            loai_ve (str): Loại vé của xe.
            danh_sach_lan (list): List các làn xe mà xe đã đi qua theo thứ tự thời gian.
            danh_sach_thoi_gian (list): List các thời điểm xe qua làn tương ứng trong danh_sach_lan.
            phi_thu_be (list): List phí thu được ghi nhận từ hệ thống BE tương ứng với các lần qua trạm.
            phi_thu_fe (list): List phí thu được ghi nhận từ hệ thống FE tương ứng với các lần qua trạm.

        Returns:
            dict: Dictionary chứa kết quả so sánh cho từng lần qua trạm.
                  Ví dụ: {
                      0: "BE tính đúng",
                      1: "FE tính sai, BE tính đúng",
                      2: "BE tính sai, FE tính đúng",
                      ...
                  }
        """
        ket_qua_so_sanh = {}
        luot_di_trong_ngay = {}  # Theo dõi lượt đi trong ngày để áp dụng quy tắc giá thường

        if bien_so_xe not in luot_di_trong_ngay:
            luot_di_trong_ngay[bien_so_xe] = {"vao": None, "ra": []}

        for i in range(len(danh_sach_lan)):
            lan = danh_sach_lan[i]
            thoi_gian = self._parse_thoi_gian(danh_sach_thoi_gian[i])
            tram_hien_tai = self._tim_tram_theo_lan(lan)
            phi_be = phi_thu_be[i] if i < len(phi_thu_be) else None
            phi_fe = phi_thu_fe[i] if i < len(phi_thu_fe) else None
            phi_ly_thuyet = 1 # Mặc định phí là 1, sẽ được cập nhật nếu miễn phí

            if not tram_hien_tai:
                ket_qua_so_sanh[i] = f"Không xác định được trạm cho làn '{lan}'"
                continue

            ten_tram = tram_hien_tai.ten_tram

            # Theo dõi lượt vào
            if lan in tram_hien_tai.lan_vao and luot_di_trong_ngay[bien_so_xe]["vao"] is None:
                luot_di_trong_ngay[bien_so_xe]["vao"] = {"thoi_gian": thoi_gian, "tram": ten_tram}

            # Theo dõi lượt ra
            if lan in tram_hien_tai.lan_ra:
                luot_di_trong_ngay[bien_so_xe]["ra"].append({"thoi_gian": thoi_gian, "tram": ten_tram})

            # Tính phí lý thuyết dựa trên loại vé và quy tắc của trạm
            if loai_ve in tram_hien_tai.cac_loai_ve:
                phi_ly_thuyet = tram_hien_tai.cac_loai_ve[loai_ve](luot_di_trong_ngay[bien_so_xe], thoi_gian)

            so_sanh = self._thuc_hien_so_sanh(phi_be, phi_fe, phi_ly_thuyet)
            ket_qua_so_sanh[i] = so_sanh

        return ket_qua_so_sanh

    def _tim_tram_theo_lan(self, ma_lan):
        """
        Tìm trạm thu phí dựa trên mã làn.

        Args:
            ma_lan (int): Mã làn xe.

        Returns:
            TramThuPhi or None: Đối tượng TramThuPhi nếu tìm thấy, None nếu không.
        """
        for tram in self.cac_tram.values():
            if ma_lan in tram.lan_vao or ma_lan in tram.lan_ra:
                return tram
        return None

    def _parse_thoi_gian(self, thoi_gian_str):
        """
        Chuyển đổi chuỗi thời gian thành đối tượng datetime (nếu cần).

        Args:
            thoi_gian_str (str): Chuỗi biểu diễn thời gian.

        Returns:
            datetime or None: Đối tượng datetime nếu chuyển đổi thành công, None nếu không.
        """
        if isinstance(thoi_gian_str, datetime):
            return thoi_gian_str
        try:
            return datetime.strptime(thoi_gian_str, '%Y-%m-%d %H:%M:%S') # Thử một định dạng phổ biến
        except (ValueError, TypeError):
            return None

    def _thuc_hien_so_sanh(self, phi_be, phi_fe, phi_ly_thuyet):
        """
        Thực hiện so sánh giữa phí thu BE, FE và phí lý thuyết.

        Args:
            phi_be (float or int or None): Phí thu từ BE.
            phi_fe (float or int or None): Phí thu từ FE.
            phi_ly_thuyet (float or int): Phí thu lý thuyết.

        Returns:
            str: Kết quả so sánh.
        """
        be_dung = (phi_be == phi_ly_thuyet)
        fe_dung = (phi_fe == phi_ly_thuyet)

        if be_dung and fe_dung:
            return "BE tính đúng, FE tính đúng"
        elif be_dung and not fe_dung:
            return "BE tính đúng, FE tính sai"
        elif not be_dung and fe_dung:
            return "BE tính sai, FE tính đúng"
        else:
            return "BE tính sai, FE tính sai"

# Khởi tạo đối tượng kiểm tra (sẽ tự động tạo các trạm mặc định)
kiem_tra = KiemTraThuPhi()

# Dữ liệu kiểm tra (ví dụ)
bien_so = "XE9999"
loai_ve_xe = "Giá thường"
lan_xe_qua = [1, 5, 10, 12]
thoi_gian_qua = ["2025-04-29 08:00:00", "2025-04-29 08:15:00", "2025-04-29 08:30:00", "2025-04-29 08:45:00"]
phi_be_thu = [1, 1, 0, 0]
phi_fe_thu = [1, 0, 1, 0]

# Thực hiện kiểm tra
ket_qua = kiem_tra.so_sanh_phi_thu(bien_so, loai_ve_xe, lan_xe_qua, thoi_gian_qua, phi_be_thu, phi_fe_thu)

# In kết quả
print(f"Kết quả so sánh phí thu cho xe '{bien_so}':")
for lan_idx, trang_thai in ket_qua.items():
    tram = kiem_tra._tim_tram_theo_lan(lan_xe_qua[lan_idx])
    ten_tram = tram.ten_tram if tram else "Không xác định"
    print(f"  Lần qua làn '{lan_xe_qua[lan_idx]}' tại trạm '{ten_tram}' ({thoi_gian_qua[lan_idx]}): {trang_thai} (BE: {phi_be_thu[lan_idx]}, FE: {phi_fe_thu[lan_idx]})")

bien_so2 = "XE8888"
loai_ve_xe2 = "UT toàn quốc"
lan_xe_qua2 = [10, 12]
thoi_gian_qua2 = ["2025-04-29 09:00:00", "2025-04-29 09:10:00"]
phi_be_thu2 = [0, 0]
phi_fe_thu2 = [0, 0]

ket_qua2 = kiem_tra.so_sanh_phi_thu(bien_so2, loai_ve_xe2, lan_xe_qua2, thoi_gian_qua2, phi_be_thu2, phi_fe_thu2)
print(f"\nKết quả so sánh phí thu cho xe '{bien_so2}':")
for lan_idx, trang_thai in ket_qua2.items():
    tram = kiem_tra._tim_tram_theo_lan(lan_xe_qua2[lan_idx])
    ten_tram = tram.ten_tram if tram else "Không xác định"
    print(f"  Lần qua làn '{lan_xe_qua[lan_idx]}' tại trạm '{ten_tram}' ({thoi_gian_qua[lan_idx]}): {trang_thai} (BE: {phi_be_thu[lan_idx]}, FE: {phi_fe_thu[lan_idx]})")
