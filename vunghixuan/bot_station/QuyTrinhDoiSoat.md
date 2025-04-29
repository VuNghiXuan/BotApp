# Quy trình kiểm tra phí thu giữa FE và BE

**Mục đích:** Đối soát phí thu giữa hệ thống Front-End (FE) và Back-End (BE) dựa trên DataFrame đã được gộp và chuẩn hóa.

## I. Mô tả trạm, làn và loại vé:

* Trạm và làn:
    1. Đường Đồng Khởi (Trạm 2A):
        * Làn vào: 10, 11
        * Làn ra: 12
    2. Đường ĐT768:
        * Trạm 1A:
            * Làn vào: 1, 2
            * Làn ra: 3, 4
        * Trạm 3B:
            * Làn vào: 7, 8, 9
        * Trạm 3A:
            * Làn ra: 5, 6
* Loại vé:
    * Miễn phí: UT toàn quốc
    * Giá thường: Tính phí khi xe khởi đầu vào dự án và ra một trong các làn ra (1 lần), hoặc ngược lại (khởi hành từ trong dự án đi ra và vào trong ngày - 1 lần).
    * UT toàn quốc: Không tính phí.
    * Vé tháng thường: Đã thanh toán theo tháng, qua trạm không tính phí.
    * Miễn phí quay đầu: Kiểm soát việc quay đầu, không tính phí.
    * Miễn giảm 100% trạm 2A 2B trạm 768: Dành cho quân đội trong khu vực dự án, không tính phí.
    * Miễn phí liên trạm: Qua các trạm đều không tính phí.

## II. Quy trình tổng quan:

1. Phân loại ban đầu: Tách riêng nhóm xe được miễn phí/ưu tiên mà không phát sinh phí.
2. Xác định nguyên nhân chênh lệch cho xe trả phí: Đối với nhóm xe còn lại (xe trả phí), tìm hiểu lý do gây ra sự khác biệt về phí thu.

## III. Mô tả chi tiết từng bước:

**Bước 1: Tách nhóm xe miễn phí/ưu tiên (Hàm `tach_nhom_xe_mien_phi_uu_tien`)**

* Mục đích: Lấy ra danh sách các xe thuộc diện miễn phí hoặc ưu tiên và đảm bảo rằng cả hệ thống FE và BE đều ghi nhận không thu phí cho các xe này.
* Cách thực hiện:
    * Xem xét cột `'Loại vé chuẩn'`. Nếu giá trị thuộc danh sách: `'Miễn giảm 100% trạm 2A 2B trạm 768'`, `'UT toàn quốc'`, `'Miễn phí quay đầu'`, `'Miễn phí liên trạm'`, `'Vé tháng thường'`, xe đó thuộc nhóm này.
    * Điều kiện quan trọng: Chọn xe miễn phí/ưu tiên mà cả cột `'Phí thu'` (FE) và `'BE_Tiền bao gồm thuế'` (BE) đều bằng `0` hoặc là `NaN`.
* Kết quả: Hai danh sách (DataFrame):
    * Danh sách xe miễn phí/ưu tiên không thu phí ở cả hai hệ thống.
    * Danh sách **còn lại** (xe trả phí hoặc có sự khác biệt).

**Bước 2: Phân tích chênh lệch thu phí cho nhóm xe còn lại (xe trả phí)**

Xem xét danh sách xe còn lại để xác định nguyên nhân gây ra sự khác biệt về phí thu.

* Trường hợp 2.1: Chênh lệch do anten đọc nhiều lượt (Cần viết hàm)
    * Mục đích: Xác định xe có thể bị đọc thẻ/biển số nhiều lần trong thời gian ngắn.
    * Cách thực hiện:
        1. Nhóm theo biển số (`'Biển số chuẩn'`).
        2. Lọc nhóm có tối thiểu 2 giao dịch trở lên.
        3. Kiểm tra cặp giao dịch: Nếu **hai dòng** của cùng biển số thỏa mãn:
            * Cùng trạm: Dựa vào `self.mapping_lane` (cần khai báo và định nghĩa cấu trúc ánh xạ làn về trạm) để kiểm tra.
            * Thời gian chênh lệch <= 5 phút.
            * Cả hai đều tính phí: `'BE_Tiền bao gồm thuế' > 0` hoặc `'Phí thu' > 0`.
    * Kết luận: Nghi vấn anten đọc trùng.

* Trường hợp 2.2: Chênh lệch do thu phí nguội (Cần viết hàm)
    * Mục đích: BE có phí, FE không có giao dịch phí tương ứng.
    * Điều kiện nghi vấn:
        * `'BE_Tiền bao gồm thuế' > 0`.
        * `'Phí thu'` bằng 0 hoặc `NaN`.
        * Có thể không có dòng FE tương ứng.

* Trường hợp 2.3: Chênh lệch do FE có giao dịch tính tiền và BE không có (Cần viết hàm)
    * Mục đích: FE có phí, BE không có giao dịch phí tương ứng.
    * Điều kiện nghi vấn:
        * `'Phí thu' > 0`.
        * `'BE_Tiền bao gồm thuế'` bằng 0 hoặc `NaN`.
        * Có thể không có dòng BE tương ứng.

* Trường hợp 2.4: Chênh lệch do khác phí thu giữa FE và BE (Cần viết hàm)
    * Mục đích: Cả FE và BE đều có phí, nhưng số tiền khác nhau.
    * Điều kiện kiểm tra: `abs('Phí thu' - 'BE_Tiền bao gồm thuế')` lớn hơn một ngưỡng (ví dụ: 1000).

## IV. Lý do lọc nhóm có tối thiểu 2 dòng trở lên:**

Trong đối soát dữ liệu lớn hơn 24 giờ, mỗi xe thường có ít nhất 1 lượt vào và 1 lượt ra (2 dòng dữ liệu nếu cả hai hệ thống ghi nhận). Nhóm có nhiều hơn 2 dòng có khả năng cao là do đọc trùng lặp. Nhóm 1 dòng không đủ thông tin để xác định trùng lặp.