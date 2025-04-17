import pandas as pd
from typing import List, Dict, Union
import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import unittest

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Định nghĩa base cho ORM
Base = declarative_base()

# Định nghĩa các model (ORM)
class LoaiVe(Base):
    __tablename__ = 'loai_ve'
    id = Column(Integer, primary_key=True)
    ten_loai_ve = Column(String(255), nullable=False)
    gia_ve = Column(Float, nullable=False)
    luot_vao = relationship('LuotVao', back_populates='loai_ve')

    def __init__(self, ten_loai_ve: str, gia_ve: float):
        if ten_loai_ve not in ["thang", "luot"]:
            raise ValueError(f"Loại vé không hợp lệ: {ten_loai_ve}. Chỉ chấp nhận 'thang' hoặc 'luot'.")
        if gia_ve < 0:
            raise ValueError(f"Giá vé không được âm: {gia_ve}")
        self.ten_loai_ve = ten_loai_ve
        self.gia_ve = gia_ve

    def __str__(self):
        return self.ten_loai_ve

    def __repr__(self):
        return f"LoaiVe(ten_loai_ve='{self.ten_loai_ve}', gia_ve={self.gia_ve})"
    
    def get_gia_ve(self):
        return self.gia_ve

class TramThuPhi(Base):
    __tablename__ = 'tram_thu_phi'
    id = Column(Integer, primary_key=True)
    ten_tram = Column(String(255), unique=True, nullable=False)
    luot_vao = relationship('LuotVao', back_populates='tram_thu_phi')
    luot_ra = relationship('LuotRa', back_populates='tram_thu_phi')

    def __init__(self, ten_tram: str):
        self.ten_tram = ten_tram

    def __repr__(self):
        return f"TramThuPhi(ten_tram='{self.ten_tram}')"

class LuotVao(Base):
    __tablename__ = 'luot_vao'
    id = Column(Integer, primary_key=True)
    bien_so = Column(String(255), nullable=False)
    thoi_gian = Column(DateTime, nullable=False)
    tram_thu_phi_id = Column(Integer, ForeignKey('tram_thu_phi.id'), nullable=False)
    tram_thu_phi = relationship('TramThuPhi', back_populates='luot_vao')
    loai_ve_id = Column(Integer, ForeignKey('loai_ve.id'), nullable=False)
    loai_ve = relationship('LoaiVe', back_populates='luot_vao')
    gia_ve = Column(Float, nullable=False)

class LuotRa(Base):
    __tablename__ = 'luot_ra'
    id = Column(Integer, primary_key=True)
    bien_so = Column(String(255), nullable=False)
    thoi_gian = Column(DateTime, nullable=False)
    tram_thu_phi_id = Column(Integer, ForeignKey('tram_thu_phi.id'), nullable=False)
    tram_thu_phi = relationship('TramThuPhi', back_populates='luot_ra')

# Class quản lý dữ liệu và logic
class DuLieuXeRaVao:
    def __init__(self, db_url: str = 'sqlite:///:memory:'):  # Sử dụng in-memory SQLite để đơn giản
        """
        Khởi tạo đối tượng DuLieuXeRaVao.

        Args:
            db_url (str, optional): URL của database. Mặc định là 'sqlite:///:memory:' (in-memory SQLite).
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.tram_thu_phi = {}  # Dictionary để lưu trữ các trạm thu phí (key là tên trạm, value là đối tượng TramThuPhi)
        self.loai_ve_mapping = {}  # Dictionary để lưu trữ các loại vé

    def them_loai_ve(self, ten_loai_ve: str, gia_ve: float) -> LoaiVe:
        """
        Thêm một loại vé mới vào hệ thống.

        Args:
            ten_loai_ve (str): Tên loại vé ("thang" hoặc "luot").
            gia_ve (float): Giá vé.

        Returns:
            LoaiVe: Đối tượng LoaiVe đã được tạo và thêm vào session.
        """
        try:
            if ten_loai_ve in self.loai_ve_mapping:
                raise ValueError(f"Loại vé '{ten_loai_ve}' đã tồn tại.")
            loai_ve = LoaiVe(ten_loai_ve, gia_ve)
            self.session.add(loai_ve)
            self.session.commit()
            self.loai_ve_mapping[ten_loai_ve] = loai_ve
            logger.info(f"Đã thêm loại vé: {loai_ve}")
            return loai_ve
        except ValueError as e:
            logger.error(f"Lỗi khi thêm loại vé: {e}")
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            logger.error(f"Lỗi database khi thêm loại vé: {e}")
            self.session.rollback()
            raise

    def doc_du_lieu_tu_excel(self, file_path: str):
        """
        Đọc dữ liệu xe ra vào từ file Excel.

        Args:
            file_path (str): Đường dẫn đến file Excel.
        """
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.lower().str.strip()
            required_columns = ["bien_so", "thoi_gian", "tram_vao", "tram_ra", "loai_ve", "gia_ve"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"File Excel thiếu các cột sau: {', '.join(missing_columns)}")

            for _, row in df.iterrows():
                bien_so = row["bien_so"]
                thoi_gian = pd.to_datetime(row["thoi_gian"])  # Chuyển sang kiểu datetime
                tram_vao = row["tram_vao"]
                tram_ra = row["tram_ra"]
                loai_ve_str = row["loai_ve"]
                gia_ve = row["gia_ve"]

                # Kiểm tra và thêm loại vé nếu cần
                if loai_ve_str not in self.loai_ve_mapping:
                    try:
                        self.them_loai_ve(loai_ve_str, gia_ve)
                    except ValueError:
                        logger.warning(f"Loại vé '{loai_ve_str}' không hợp lệ trong file Excel, bỏ qua dòng này.")
                        continue  # Bỏ qua dòng nếu loại vé không hợp lệ

                loai_ve = self.loai_ve_mapping[loai_ve_str]

                # Tạo trạm nếu chưa tồn tại
                if tram_vao not in self.tram_thu_phi:
                    tram_vao_obj = TramThuPhi(tram_vao)
                    self.session.add(tram_vao_obj)
                    self.session.commit()  # Commit ngay để có ID cho trạm
                    self.tram_thu_phi[tram_vao] = tram_vao_obj
                if tram_ra not in self.tram_thu_phi:
                    tram_ra_obj = TramThuPhi(tram_ra)
                    self.session.add(tram_ra_obj)
                    self.session.commit()
                    self.tram_thu_phi[tram_ra] = tram_ra_obj

                # Ghi nhận lượt vào
                luot_vao = LuotVao(
                    bien_so=bien_so,
                    thoi_gian=thoi_gian,
                    tram_thu_phi=self.tram_thu_phi[tram_vao],
                    loai_ve=loai_ve,
                    gia_ve=gia_ve
                )
                self.session.add(luot_vao)

                # Ghi nhận lượt ra
                luot_ra = LuotRa(
                    bien_so=bien_so,
                    thoi_gian=thoi_gian,
                    tram_thu_phi=self.tram_thu_phi[tram_ra],
                )
                self.session.add(luot_ra)
            self.session.commit()
            logger.info("Đã đọc dữ liệu thành công từ file Excel.")
        except FileNotFoundError:
            error_msg = f"Không tìm thấy file Excel tại đường dẫn: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except ValueError as e:
            error_msg = f"Lỗi đọc file Excel: {e}"
            logger.error(error_msg)
            self.session.rollback()
            raise ValueError(error_msg)
        except SQLAlchemyError as e:
            error_msg = f"Lỗi database khi đọc file Excel: {e}"
            logger.error(error_msg)
            self.session.rollback()
            raise SQLAlchemyError(error_msg)
        except Exception as e:
            error_msg = f"Lỗi không xác định khi đọc file Excel: {e}"
            logger.error(error_msg)
            self.session.rollback()
            raise Exception(error_msg)

    def doi_chieu_du_lieu(self) -> Dict[str, Dict]:
        """
        Thực hiện đối chiếu dữ liệu xe ra vào giữa các trạm.

        Returns:
            Dict[str, Dict]: Kết quả đối chiếu, với key là tên trạm và value là thông tin đối chiếu.
        """
        ket_qua_doi_chieu = {}
        for ten_tram, tram in self.tram_thu_phi.items():
            ket_qua_doi_chieu[ten_tram] = {
                "ten_tram": ten_tram,
                "luot_vao": self.session.query(LuotVao).filter(LuotVao.tram_thu_phi == tram).count(),
                "luot_ra": self.session.query(LuotRa).filter(LuotRa.tram_thu_phi == tram).count(),
                "chi_tiet_xe_vao": {},
                "chi_tiet_xe_ra": {},
                "xe_khong_xac_dinh": [],
            }

            # Lấy chi tiết xe vào
            luot_vao_list = self.session.query(LuotVao).filter(LuotVao.tram_thu_phi == tram).all()
            for luot_vao in luot_vao_list:
                bien_so = luot_vao.bien_so
                if bien_so not in ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_vao"]:
                    ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_vao"][bien_so] = []
                ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_vao"][bien_so].append(luot_vao)

            # Lấy chi tiết xe ra
            luot_ra_list = self.session.query(LuotRa).filter(LuotRa.tram_thu_phi == tram).all()
            for luot_ra in luot_ra_list:
                bien_so = luot_ra.bien_so
                if bien_so not in ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_ra"]:
                    ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_ra"][bien_so] = []
                ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_ra"][bien_so].append(luot_ra)
            
            # Tìm xe không xác định
            bien_so_vao = set(ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_vao"].keys())
            bien_so_ra = set(ket_qua_doi_chieu[ten_tram]["chi_tiet_xe_ra"].keys())
            xe_khong_xac_dinh = bien_so_ra - bien_so_vao
            ket_qua_doi_chieu[ten_tram]["xe_khong_xac_dinh"] = list(xe_khong_xac_dinh)
        return ket_qua_doi_chieu
    
    def thong_ke_theo_loai_ve(self, ket_qua_doi_chieu: Dict[str, Dict]) -> Dict[str, Dict[str, int]]:
        """
        Thống kê số lượng xe theo loại vé cho từng trạm.

        Args:
            ket_qua_doi_chieu (Dict[str, Dict]): Kết quả đối chiếu từ hàm doi_chieu_du_lieu.

        Returns:
            Dict[str, Dict[str, int]]: Thống kê số lượng xe theo loại vé cho từng trạm.
        """
        thong_ke_ve = {}
        for ten_tram, du_lieu_tram in ket_qua_doi_chieu.items():
            thong_ke_ve[ten_tram] = {"thang": 0, "luot": 0}
            for bien_so, danh_sach_luot_vao in du_lieu_tram["chi_tiet_xe_vao"].items():
                for luot_vao in danh_sach_luot_vao:
                    if luot_vao.loai_ve.ten_loai_ve == "thang":
                        thong_ke_ve[ten_tram]["thang"] += 1
                    elif luot_vao.loai_ve.ten_loai_ve == "luot":
                        thong_ke_ve[ten_tram]["luot"] += 1
        return thong_ke_ve

    def xuat_ket_qua_excel(self, ket_qua_doi_chieu: Dict[str, Dict], file_path: str):
        """
        Xuất kết quả đối chiếu ra file Excel.

        Args:
            ket_qua_doi_chieu (Dict[str, Dict]): Kết quả đối chiếu từ hàm doi_chieu_du_lieu.
            file_path (str): Đường dẫn để lưu file Excel.
        """
        try:
            writer = pd.ExcelWriter(file_path, engine="xlsxwriter")

            # Xuất thông tin chung của từng trạm
            df_tram = pd.DataFrame([
                {
                    "Tên trạm": tram["ten_tram"],
                    "Lượt xe vào": tram["luot_vao"],
                    "Lượt xe ra": tram["luot_ra"],
                    "Xe không xác định": len(tram["xe_khong_xac_dinh"]),
                }
                for tram in ket_qua_doi_chieu.values()
            ])
            df_tram.to_excel(writer, sheet_name="Thống kê trạm", index=False)

            # Xuất chi tiết xe vào của từng trạm
            for ten_tram, du_lieu_tram in ket_qua_doi_chieu.items():
                data_vao = []
                for bien_so, danh_sach_luot_vao in du_lieu_tram["chi_tiet_xe_vao"].items():
                    for luot_vao in danh_sach_luot_vao:
                        data_vao.append({
                            "Tên trạm": ten_tram,
                            "Biển số": bien_so,
                            "Thời gian vào": luot_vao.thoi_gian,
                            "Loại vé": luot_vao.loai_ve.ten_loai_ve,
                            "Giá vé": luot_vao.gia_ve,
                        })
                if data_vao:
                    df_vao = pd.DataFrame(data_vao)
                    df_vao.to_excel(writer, sheet_name=f"Xe vào - {ten_tram}", index=False)

            # Xuất chi tiết xe ra của từng trạm
            for ten_tram, du_lieu_tram in ket_qua_doi_chieu.items():
                data_ra = []
                for bien_so, danh_sach_luot_ra in du_lieu_tram["chi_tiet_xe_ra"].items():
                    for luot_ra in danh_sach_luot_ra:
                        data_ra.append({
                            "Tên trạm": ten_tram,
                            "Biển số": bien_so,
                            "Thời gian ra": luot_ra.thoi_gian,
                        })
                if data_ra:
                    df_ra = pd.DataFrame(data_ra)
                    df_ra.to_excel(writer, sheet_name=f"Xe ra - {ten_tram}", index=False)
            
             # Xuất danh sách xe không xác định
            df_khong_xac_dinh = pd.DataFrame()
            for ten_tram, du_lieu_tram in ket_qua_doi_chieu.items():
                if du_lieu_tram["xe_khong_xac_dinh"]:  # Kiểm tra danh sách có rỗng không
                    df_temp = pd.DataFrame({
                        "Tên trạm": ten_tram,
                        "Biển số": du_lieu_tram["xe_khong_xac_dinh"],
                    })
                    df_khong_xac_dinh = pd.concat([df_khong_xac_dinh, df_temp])
            if not df_khong_xac_dinh.empty:
                df_khong_xac_dinh.to_excel(writer, sheet_name="Xe không xác định", index=False)

            writer.close()
            logger.info(f"Đã xuất kết quả ra file Excel: {file_path}")
        except Exception as e:
            error_msg = f"Lỗi khi xuất file Excel: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def loc_du_lieu(self, ket_qua_doi_chieu: Dict[str, Dict], bien_so_filter: str = None, tram_vao_filter: str = None,
                    tram_ra_filter: str = None, loai_ve_filter: str = None) -> Dict[str, Dict]:
        """
        Lọc dữ liệu dựa trên các tiêu chí.

        Args:
            ket_qua_doi_chieu (Dict[str, Dict]): Kết quả đối chiếu từ hàm doi_chieu_du_lieu.
            bien_so_filter (str, optional): Biển số xe cần lọc. Mặc định là None (không lọc).
            tram_vao_filter (str, optional): Tên trạm vào cần lọc. Mặc định là None (không lọc).
            tram_ra_filter (str, optional): Tên trạm ra cần lọc. Mặc định là None (không lọc).
            loai_ve_filter (str, optional): Loại vé cần lọc ("thang" hoặc "luot"). Mặc định là None (không lọc).

        Returns:
            Dict[str, Dict]: Kết quả lọc.
        """
        ket_qua_loc = {}
        for ten_tram, du_lieu_tram in ket_qua_doi_chieu.items():
            # Lọc theo trạm vào hoặc trạm ra
            if (tram_vao_filter and ten_tram != tram_vao_filter) and (
                    tram_ra_filter and ten_tram != tram_ra_filter):
                continue

            ket_qua_loc[ten_tram] = {
                "ten_tram": ten_tram,
                "luot_vao": 0,
                "luot_ra": 0,
                "chi_tiet_xe_vao": {},
                "chi_tiet_xe_ra": {},
                "xe_khong_xac_dinh": du_lieu_tram["xe_khong_xac_dinh"],
            }

            # Lọc chi tiết xe vào
            for bien_so, danh_sach_luot_vao in du_lieu_tram["chi_tiet_xe_vao"].items():
                for luot_vao in danh_sach_luot_vao:
                    if (not bien_so_filter or luot_vao.bien_so == bien_so_filter) and \
                            (not loai_ve_filter or luot_vao.loai_ve.ten_loai_ve == loai_ve_filter):
                        ket_qua_loc[ten_tram]["luot_vao"] += 1
                        if bien_so not in ket_qua_loc[ten_tram]["chi_tiet_xe_vao"]:
                            ket_qua_loc[ten_tram]["chi_tiet_xe_vao"][bien_so] = []
                        ket_qua_loc[ten_tram]["chi_tiet_xe_vao"][bien_so].append(luot_vao)

            # Lọc chi tiết xe ra
            for bien_so, danh_sach_luot_ra in du_lieu_tram["chi_tiet_xe_ra"].items():
                for luot_ra in danh_sach_luot_ra:
                    if not bien_so_filter or luot_ra.bien_so == bien_so_filter:
                        ket_qua_loc[ten_tram]["luot_ra"] += 1
                        if bien_so not in ket_qua_loc[ten_tram]["chi_tiet_xe_ra"]:
                            ket_qua_loc[ten_tram]["chi_tiet_xe_ra"][bien_so] = []
                        ket_qua_loc[ten_tram]["chi_tiet_xe_ra"][bien_so].append(luot_ra)
        return ket_qua_loc

# Unit test cho class DuLieuXeRaVao
class TestDuLieuXeRaVao(unittest.TestCase):
    def setUp(self):
        # Sử dụng database tạm thời cho các bài test
        self.du_lieu = DuLieuXeRaVao('sqlite:///:memory:')
        self.du_lieu.session = self.du_lieu.Session()  # Tạo một session mới cho mỗi test
        self.du_lieu.them_loai_ve("thang", 100000)
        self.du_lieu.them_loai_ve("luot", 10000)
    
    def tearDown(self):
        self.du_lieu.session.close()

    def test_them_loai_ve(self):
        loai_ve_moi = self.du_lieu.them_loai_ve("ngay", 50000)
        self.assertIsNotNone(loai_ve_moi)
        self.assertEqual(loai_ve_moi.ten_loai_ve, "ngay")
        self.assertEqual(loai_ve_moi.gia_ve, 50000)
        self.assertIn("ngay", self.du_lieu.loai_ve_mapping)

        with self.assertRaises(ValueError):
            self.du_lieu.them_loai_ve("thang", 120000)  # Thêm trùng loại vé

    def test_doc_du_lieu_tu_excel(self):
        # Tạo một file Excel giả lập cho việc test
        data = {
            "bien_so": ["29A12345", "30B54321", "29A12345", "30B54321"],
            "thoi_gian": ["2024-01-15 08:00:00", "2024-01-15 09:00:00", "2024-01-15 10:00:00", "2024-01-15 11:00:00"],
            "tram_vao": ["Trạm A", "Trạm B", "Trạm A", "Trạm B"],
            "tram_ra": ["Trạm B", "Trạm A", "Trạm B", "Trạm A"],
            "loai_ve": ["thang", "luot", "thang", "luot"],
            "gia_ve": [100000, 10000, 100000, 10000],
        }
        df = pd.DataFrame(data)
        test_file_path = "test_data.xlsx"
        df.to_excel(test_file_path, index=False)

        self.du_lieu.doc_du_lieu_tu_excel(test_file_path)
        # Kiểm tra xem dữ liệu có được đọc vào đúng không (số lượng bản ghi, v.v.)
        self.assertEqual(self.du_lieu.session.query(LuotVao).count(), 4)
        self.assertEqual(self.du_lieu.session.query(LuotRa).count(), 4)
        self.assertEqual(len(self.du_lieu.tram_thu_phi), 2)
        self.assertIn("Trạm A", self.du_lieu.tram_thu_phi)
        self.assertIn("Trạm B", self.du_lieu.tram_thu_phi)
        #cleanup
        import os
        os.remove(test_file_path)

    def test_doi_chieu_du_lieu(self):
        # Tạo dữ liệu giả lập trong database
        tram_a = TramThuPhi(ten_tram="Trạm A")
        tram_b = TramThuPhi(ten_tram="Trạm B")
        self.du_lieu.session.add_all([tram_a, tram_b])
        self.du_lieu.session.commit()
        
        loai_ve_thang = self.du_lieu.loai_ve_mapping["thang"]
        loai_ve_luot = self.du_lieu.loai_ve_mapping["luot"]

        luot_vao_1 = LuotVao(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 8, 0, 0), tram_thu_phi=tram_a, loai_ve=loai_ve_thang, gia_ve=100000)
        luot_ra_1 = LuotRa(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=tram_b)
        luot_vao_2 = LuotVao(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 10, 0, 0), tram_thu_phi=tram_b, loai_ve=loai_ve_luot, gia_ve=10000)
        luot_ra_2 = LuotRa(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 11, 0, 0), tram_thu_phi=tram_a)
        self.du_lieu.session.add_all([luot_vao_1, luot_ra_1, luot_vao_2, luot_ra_2])
        self.du_lieu.session.commit()

        ket_qua = self.du_lieu.doi_chieu_du_lieu()
        self.assertEqual(ket_qua["Trạm A"]["luot_vao"], 1)
        self.assertEqual(ket_qua["Trạm A"]["luot_ra"], 1)
        self.assertEqual(ket_qua["Trạm B"]["luot_vao"], 1)
        self.assertEqual(ket_qua["Trạm B"]["luot_ra"], 1)
        self.assertEqual(len(ket_qua["Trạm A"]["chi_tiet_xe_vao"]), 1)
        self.assertEqual(len(ket_qua["Trạm A"]["chi_tiet_xe_ra"]), 1)
        self.assertEqual(len(ket_qua["Trạm B"]["chi_tiet_xe_vao"]), 1)
        self.assertEqual(len(ket_qua["Trạm B"]["chi_tiet_xe_ra"]), 1)
        self.assertEqual(len(ket_qua["Trạm A"]["xe_khong_xac_dinh"]), 0)
        self.assertEqual(len(ket_qua["Trạm B"]["xe_khong_xac_dinh"]), 0)

    def test_thong_ke_theo_loai_ve(self):
        # Tạo dữ liệu giả lập
        ket_qua_doi_chieu = {
            "Trạm A": {
                "ten_tram": "Trạm A",
                "chi_tiet_xe_vao": {
                    "29A12345": [
                        LuotVao(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 8, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="thang", gia_ve=100000), gia_ve=100000),
                        LuotVao(bien_so="29A12346", thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
            },
            "Trạm B": {
                "ten_tram": "Trạm B",
                "chi_tiet_xe_vao": {
                    "30B54321": [
                        LuotVao(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 10, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm B"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
            },
        }
        thong_ke = self.du_lieu.thong_ke_theo_loai_ve(ket_qua_doi_chieu)
        self.assertEqual(thong_ke["Trạm A"]["thang"], 1)
        self.assertEqual(thong_ke["Trạm A"]["luot"], 1)
        self.assertEqual(thong_ke["Trạm B"]["thang"], 0)
        self.assertEqual(thong_ke["Trạm B"]["luot"], 1)

    def test_xuat_ket_qua_excel(self):
        # Tạo dữ liệu giả lập
        ket_qua_doi_chieu = {
            "Trạm A": {
                "ten_tram": "Trạm A",
                "luot_vao": 2,
                "luot_ra": 1,
                "chi_tiet_xe_vao": {
                    "29A12345": [
                        LuotVao(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 8, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="thang", gia_ve=100000), gia_ve=100000),
                        LuotVao(bien_so="29A12346", thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
                "chi_tiet_xe_ra": {
                    "29A12345": [
                        LuotRa(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A")),
                    ],
                },
                "xe_khong_xac_dinh": ["29A12347"],
            },
            "Trạm B": {
                "ten_tram": "Trạm B",
                "luot_vao": 1,
                "luot_ra": 1,
                "chi_tiet_xe_vao": {
                    "30B54321": [
                        LuotVao(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 10, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm B"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
                "chi_tiet_xe_ra": {
                    "30B54321": [
                        LuotRa(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 11, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm B")),
                    ],
                },
                "xe_khong_xac_dinh": [],
            },
        }
        output_file = "test_output.xlsx"
        self.du_lieu.xuat_ket_qua_excel(ket_qua_doi_chieu, output_file)
        # Kiểm tra sự tồn tại của file và một vài nội dung cơ bản
        import os
        self.assertTrue(os.path.exists(output_file))
        #cleanup
        os.remove(output_file)

    def test_loc_du_lieu(self):
        # Tạo dữ liệu giả lập
        ket_qua_doi_chieu = {
            "Trạm A": {
                "ten_tram": "Trạm A",
                "luot_vao": 2,
                "luot_ra": 1,
                "chi_tiet_xe_vao": {
                    "29A12345": [
                        LuotVao(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 8, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="thang", gia_ve=100000), gia_ve=100000),
                        LuotVao(bien_so="29A12346", thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
                "chi_tiet_xe_ra": {
                    "29A12345": [
                        LuotRa(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A")),
                    ],
                },
                "xe_khong_xac_dinh": ["29A12347"],
            },
            "Trạm B": {
                "ten_tram": "Trạm B",
                "luot_vao": 1,
                "luot_ra": 1,
                "chi_tiet_xe_vao": {
                    "30B54321": [
                        LuotVao(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 10, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm B"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
                "chi_tiet_xe_ra": {
                    "30B54321": [
                        LuotRa(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 11, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm B")),
                    ],
                },
                "xe_khong_xac_dinh": [],
            },
        }
        # Lọc theo biển số
        ket_qua_loc_bien_so = self.du_lieu.loc_du_lieu(ket_qua_doi_chieu, bien_so_filter="29A12345")
        self.assertEqual(ket_qua_loc_bien_so["Trạm A"]["luot_vao"], 1)
        self.assertEqual(ket_qua_loc_bien_so["Trạm A"]["luot_ra"], 1)
        self.assertEqual(ket_qua_loc_bien_so["Trạm B"]["luot_vao"], 0)
        self.assertEqual(ket_qua_loc_bien_so["Trạm B"]["luot_ra"], 0)

        # Lọc theo trạm vào
        ket_qua_loc_tram_vao = self.du_lieu.loc_du_lieu(ket_qua_doi_chieu, tram_vao_filter="Trạm A")
        self.assertEqual(ket_qua_loc_tram_vao["Trạm A"]["luot_vao"], 2)
        self.assertEqual(ket_qua_loc_tram_vao["Trạm A"]["luot_ra"], 1)
        self.assertNotIn("Trạm B", ket_qua_loc_tram_vao)

        # Lọc theo loại vé
        ket_qua_loc_loai_ve = self.du_lieu.loc_du_lieu(ket_qua_doi_chieu, loai_ve_filter="luot")
        self.assertEqual(ket_qua_loc_loai_ve["Trạm A"]["luot_vao"], 1)
        self.assertEqual(ket_qua_loc_loai_ve["Trạm A"]["luot_ra"], 0) #Xe ra không có loại vé nên không lọc được
        self.assertEqual(ket_qua_loc_loai_ve["Trạm B"]["luot_vao"], 1)
        self.assertEqual(ket_qua_loc_loai_ve["Trạm B"]["luot_ra"], 0) #Xe ra không có loại vé nên không lọc được
    
    def test_loc_du_lieu_tram_ra(self):
        # Tạo dữ liệu giả lập
        ket_qua_doi_chieu = {
            "Trạm A": {
                "ten_tram": "Trạm A",
                "luot_vao": 2,
                "luot_ra": 1,
                "chi_tiet_xe_vao": {
                    "29A12345": [
                        LuotVao(bien_so="29A12345",  thoi_gian=datetime.datetime(2024, 1, 15, 8, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="thang", gia_ve=100000), gia_ve=100000),
                        LuotVao(bien_so="29A12346",  thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
                "chi_tiet_xe_ra": {
                    "29A12345": [
                        LuotRa(bien_so="29A12345", thoi_gian=datetime.datetime(2024, 1, 15, 9, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm A")),
                    ],
                },
                "xe_khong_xac_dinh": ["29A12347"],
            },
            "Trạm B": {
                "ten_tram": "Trạm B",
                "luot_vao": 1,
                "luot_ra": 1,
                "chi_tiet_xe_vao": {
                    "30B54321": [
                         LuotVao(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 10, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm B"), loai_ve=LoaiVe(ten_loai_ve="luot", gia_ve=10000), gia_ve=10000),
                    ],
                },
                "chi_tiet_xe_ra": {
                    "30B54321": [
                        LuotRa(bien_so="30B54321", thoi_gian=datetime.datetime(2024, 1, 15, 11, 0, 0), tram_thu_phi=TramThuPhi(ten_tram="Trạm B")),
                    ],
                },
                "xe_khong_xac_dinh": [],
            },
        }

        # Lọc theo trạm ra
        ket_qua_loc_tram_ra = self.du_lieu.loc_du_lieu(ket_qua_doi_chieu, tram_ra_filter="Trạm B")
        self.assertEqual(ket_qua_loc_tram_ra["Trạm A"]["luot_vao"], 0)
        self.assertEqual(ket_qua_loc_tram_ra["Trạm A"]["luot_ra"], 1)
        self.assertEqual(ket_qua_loc_tram_ra["Trạm B"]["luot_vao"], 1)
        self.assertEqual(ket_qua_loc_tram_ra["Trạm B"]["luot_ra"], 1)
        self.assertNotIn("Trạm A", ket_qua_loc_tram_ra["chi_tiet_xe_vao"])

if __name__ == "__main__":
    # Khởi tạo đối tượng quản lý dữ liệu
    # Thay đổi chuỗi kết nối để sử dụng một file database
    db_url = 'sqlite:///./xe_ra_vao.db'  # Lưu vào file xe_ra_vao.db
    du_lieu = DuLieuXeRaVao(db_url)

    # Thêm các loại vé (chỉ cần chạy một lần)
    try:
        du_lieu.them_loai_ve("thang", 100000)  # Ví dụ giá vé tháng là 100,000
        du_lieu.them_loai_ve("luot", 10000)  # Ví dụ giá vé lượt là 10,000
    except ValueError as e:
        logger.warning(f"Loại vé đã tồn tại hoặc giá vé không hợp lệ: {e}")

    # Đường dẫn đến file Excel (thay đổi cho phù hợp)
    file_path = "du_lieu_xe_ra_vao.xlsx"  # Đặt đường dẫn file Excel của bạn

    # Đọc dữ liệu từ file Excel
    try:
        du_lieu.doc_du_lieu_tu_excel(file_path)
    except (FileNotFoundError, ValueError, SQLAlchemyError, Exception) as e:
        logger.error(f"Chương trình dừng do lỗi: {e}")
        exit()

    # Thực hiện đối chiếu dữ liệu
    ket_qua_doi_chieu = du_lieu.doi_chieu_du_lieu()

    # In kết quả đối chiếu ra màn hình
    print("Kết quả đối chiếu dữ liệu:")
    print(ket_qua_doi_chieu)

    # Thống kê số lượng xe theo loại vé
    thong_ke_ve = du_lieu.thong_ke_theo_loai_ve(ket_qua_doi_chieu)
    print("\nThống kê số lượng xe theo loại vé:")
    print(thong_ke_ve)

    # Xuất kết quả ra file Excel
    output_file = "ket_qua_doi_chieu.xlsx"
    du_lieu.xuat_ket_qua_excel(ket_qua_doi_chieu, output_file)

    # Lọc dữ liệu
    bien_so_loc = "29A12345"  # Biển số cần lọc, để trống "" nếu không lọc
    tram_vao_loc = "Trạm A"
    tram_ra_loc = None
    loai_ve_loc = "luot"
    ket_qua_loc = du_lieu.loc_du_lieu(ket_qua_doi_chieu, bien_so_loc, tram_vao_loc, tram_ra_loc,
                                    loai_ve_loc)
    print(f"\nKết quả lọc với biển số '{bien_so_loc}', trạm vào '{tram_vao_loc}', loại vé '{loai_ve_loc}':")
    print(ket_qua_loc)
    
    #Chạy Unit test
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
