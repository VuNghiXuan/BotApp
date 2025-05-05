# Quy trình kiểm tra phí thu giữa FE và BE

**Mục đích:** Đối soát phí thu giữa hệ thống Front-End (FE) và Back-End (BE) dựa trên DataFrame đã được gộp và chuẩn hóa, đồng thời kiểm tra tính hợp lý của các lượt đi, xử lý các trường hợp quét trùng/đọc đồng thời và xác định các trường hợp bất thường liên quan đến phí.

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
2. Kiểm tra lượt đi hợp lý và bất thường, xử lý quét trùng/đọc đồng thời: Xác định các lượt đi và các trường hợp quét trùng/đọc đồng thời dựa trên thời gian, làn giao dịch và thông tin phí.
3. Phân tích chênh lệch thu phí cho nhóm xe còn lại: Đối với nhóm xe còn lại, tìm hiểu lý do gây ra sự khác biệt về phí thu.
4. Xử lý kết quả và báo cáo.

## III. Mô tả chi tiết từng bước:

**Bước 1: Tách nhóm xe miễn phí/ưu tiên (Hàm `tach_nhom_xe_mien_phi_uu_tien`)**

* **Mục đích:** Lấy ra danh sách các xe thuộc diện miễn phí hoặc ưu tiên và đảm bảo rằng cả hệ thống FE và BE đều ghi nhận không thu phí cho các xe này.
* **Cách thực hiện:**
    * Xem xét cột `'Loại vé chuẩn'`. Nếu giá trị thuộc danh sách: `'Miễn giảm 100% trạm 2A 2B trạm 768'`, `'UT toàn quốc'`, `'Miễn phí quay đầu'`, `'Miễn phí liên trạm'`, `'Vé tháng thường'`, xe đó thuộc nhóm này.
    * Điều kiện quan trọng: Chọn xe miễn phí/ưu tiên mà cả cột `'Phí thu'` (FE) và `'BE_Tiền bao gồm thuế'` (BE) đều bằng `0` hoặc là `NaN`.
* **Kết quả:** Hai danh sách (DataFrame):
    * Danh sách xe miễn phí/ưu tiên không thu phí ở cả hai hệ thống.
    * Danh sách **còn lại** (xe trả phí hoặc có sự khác biệt).

**Bước 2: Kiểm tra lượt đi hợp lý và bất thường, xử lý quét trùng/đọc đồng thời (Hàm `kiem_tra_luot_di`)**

* **Mục đích:** Xác định các lượt đi hợp lý, các trường hợp quét trùng/đọc đồng thời và các lượt đi có dấu hiệu bất thường liên quan đến phí.
* **Cách thực hiện:**
    1. **Nhóm theo biển số** (`'Biển số chuẩn'`).
    2. **Sắp xếp** các giao dịch của mỗi xe theo `'Thời gian chuẩn'`.
    3. **Duyệt qua các cặp giao dịch liên tiếp:** Sử dụng một vòng lặp để xem xét từng cặp giao dịch kế tiếp của cùng một xe.
    4. **Xử lý quét trùng hoặc đọc đồng thời:**
        * Nếu hai giao dịch liên tiếp tại cùng một trạm (dựa vào `self._get_tram_from_lane()`):
            * Thời gian chênh lệch rất ngắn (<= 300 giây - `thoi_gian_quet_trung`).
            * **Và một trong các điều kiện sau:**
                * Thông tin phí (cả `'Phí thu'` và `'BE_Tiền bao gồm thuế'`) đều cùng là 0/NaN hoặc có giá trị bằng nhau.
                * Một giao dịch ở làn vào (`self._get_lane_type()` là 'in' hoặc None) và giao dịch kia ở làn ra ('out' hoặc None).
        * **Hành động:** Bỏ qua cả hai giao dịch này, không coi chúng là một lượt đi riêng biệt.
    5. **Xác định lượt đi và kiểm tra phí (cho các cặp không phải quét trùng):**
        * **Lượt đi hợp lý:** Cùng trạm, thời gian chênh lệch > 10 phút, loại làn vào-ra (hoặc ra-vào), và cả hai giao dịch đều có phí. Đánh dấu cột `'Lượt đi hợp lý'` là `True` cho cả hai giao dịch.
        * **Tính phí nhiều lần cho một lượt đi:** Nếu trong một khoảng thời gian được coi là một lượt đi hợp lý, hệ thống ghi nhận nhiều hơn một giao dịch có phí, đánh dấu là lượt đi bất thường và ghi chú.
        * **Thời gian chênh lệch ngắn (nghi vấn quay đầu có phí):** Thời gian <= 10 phút, cùng trạm, có phát sinh phí. Đánh dấu là lượt đi bất thường và ghi chú.
        * **Vào làn ra hoặc ra làn vào (nghi vấn lỗi làn có phí):** Giao dịch vào ở làn ra hoặc ra ở làn vào và có phí. Đánh dấu là lượt đi bất thường và ghi chú.
        * **Lượt đi đơn lẻ có phí:** Xe chỉ có một giao dịch duy nhất có phí trong ngày đối soát cần được xem xét thêm.
    6. **Đánh dấu và ghi chú:** Thêm cột `'Lượt đi bất thường'` (True/False) và ghi chú chi tiết vào cột `'Ghi chú xử lý'`.
* **Kết quả:** DataFrame đã được đánh dấu với cột `'Lượt đi hợp lý'`, `'Lượt đi bất thường'` và thông tin chi tiết trong cột `'Ghi chú xử lý'`.

**Bước 3: Phân tích chênh lệch thu phí cho nhóm xe còn lại (sau khi kiểm tra lượt đi)**

Xem xét danh sách xe còn lại (sau khi đã xác định các lượt đi bất thường và xử lý quét trùng) để xác định nguyên nhân gây ra sự khác biệt về phí thu.

* **Trường hợp 3.2: Chênh lệch do thu phí nguội (Cần viết hàm)**
    * Mục đích: BE có phí, FE không có giao dịch phí tương ứng.
    * Điều kiện nghi vấn:
        * `'BE_Tiền bao gồm thuế' > 0`.
        * `'Phí thu'` bằng 0 hoặc `NaN`.
        * Có thể không có dòng FE tương ứng.

* **Trường hợp 3.3: Chênh lệch do FE có giao dịch tính tiền và BE không có (Cần viết hàm)**
    * Mục đích: FE có phí, BE không có giao dịch phí tương ứng.
    * Điều kiện nghi vấn:
        * `'Phí thu' > 0`.
        * `'BE_Tiền bao gồm thuế'` bằng 0 hoặc `NaN`.
        * Có thể không có dòng BE tương ứng.

* **Trường hợp 3.4: Chênh lệch do khác phí thu giữa FE và BE (Cần viết hàm)**
    * Mục đích: Cả FE và BE đều có phí, nhưng số tiền khác nhau.
    * Điều kiện kiểm tra: `abs('Phí thu' - 'BE_Tiền bao gồm thuế')` lớn hơn một ngưỡng (ví dụ: 1000).

## IV. Lý do lọc nhóm có tối thiểu 2 dòng trở lên:**

Trong đối soát dữ liệu lớn hơn 24 giờ, mỗi xe thường có ít nhất 1 lượt vào và 1 lượt ra (2 dòng dữ liệu nếu cả hai hệ thống ghi nhận). Nhóm có nhiều hơn 2 dòng có khả năng cao là do các lượt đi phức tạp hoặc các trường hợp cần được phân tích kỹ hơn (sau khi đã xử lý quét trùng). Nhóm 1 dòng không đủ thông tin để xác định các vấn đề liên quan đến lượt đi.

## V. Xử lý kết quả và báo cáo:

Sau khi thực hiện các bước đối soát, DataFrame kết quả sẽ chứa thông tin chi tiết về các trường hợp chênh lệch và các lượt đi bất thường.

1.  **Lọc và xem xét các trường hợp bất thường:** Tập trung vào các giao dịch được đánh dấu trong cột `'Lượt đi bất thường'` và các trường hợp có chênh lệch phí.
2.  **Điều tra nguyên nhân:** Thực hiện các nghiệp vụ cần thiết để xác định nguyên nhân gốc rễ của các trường hợp bất thường và chênh lệch.
3.  **Thực hiện điều chỉnh:** Dựa trên kết quả điều tra, thực hiện các điều chỉnh phí cần thiết.
4.  **Báo cáo:** Tổng hợp kết quả đối soát và các hành động điều chỉnh.
5.  **Cải tiến quy trình:** Dựa trên các vấn đề thường xuyên xảy ra, xem xét và cải tiến quy trình đối soát.

## Quy trình kiểm tra lượt vé và phí thu

**Mục tiêu:** Xác định trạng thái thu phí (BE đúng, FE đúng, cả hai sai, hoặc cả hai đúng) và số lượt di chuyển trong ngày của một xe dựa trên dữ liệu thu phí và thông tin làn đường.

**Nguồn dữ liệu:**

* `self.mapping_lane`: Dữ liệu cấu hình ánh xạ làn đường, cho biết loại làn (vào, ra, khác).
* Dữ liệu giao dịch thu phí của xe (bao gồm thời điểm, trạm, làn đường, loại phí BE/FE).

**Logic kiểm tra:**

1.  **Xác định lượt di chuyển:**
    * Một lượt di chuyển được xác định dựa trên trình tự các giao dịch thu phí của một xe trong một khoảng thời gian nhất định (ví dụ: trong một ngày).
    * **Trường hợp xe khởi hành từ ngoài dự án vào:**
        * Lượt thu phí đầu tiên tại một trạm được xem là lượt vào và bị tính phí.
        * Các giao dịch thu phí tiếp theo tại các **làn ra** của cùng trạm trong cùng lượt di chuyển được miễn phí.
        * Nếu xe đi qua các làn không phải làn ra sau lượt vào có phí, đó có thể là lỗi quét trùng antenna.
    * **Trường hợp xe khởi hành từ dự án đi ra:**
        * Giao dịch thu phí đầu tiên tại một **làn ra** được xem là lượt ra và bị tính phí (áp dụng cho cư dân sinh sống trong khu vực dự án).
        * Nếu xe sau đó đi vào **cùng trạm** và đúng **làn vào**, giao dịch này được xem là một phần của lượt di chuyển hợp lệ (không tính là lượt đi mới).
        * Nếu xe sau đó đi vào một **trạm khác**, giao dịch này được xem là một lượt đi mới và sẽ bị tính phí.

2.  **Kiểm tra trạng thái thu phí (BE/FE) cho mỗi lượt di chuyển:**
    * Đối với mỗi lượt di chuyển đã xác định, kiểm tra thông tin thu phí BE (Backend) và FE (Frontend).
    * Xác định trạng thái:
        * **BE đúng, FE sai:** Phí ở hệ thống backend chính xác nhưng có lỗi ở frontend (ví dụ: không hiển thị, hiển thị sai).
        * **FE đúng, BE sai:** Phí ở frontend chính xác nhưng có lỗi ở backend (ví dụ: tính sai tiền).
        * **Cả hai sai:** Cả backend và frontend đều có lỗi thu phí.
        * **Cả hai đúng:** Cả backend và frontend đều thu phí chính xác.

3.  **Đếm số lượt di chuyển trong ngày:**
    * Dựa trên các lượt di chuyển đã được xác định trong bước 1, đếm tổng số lượt di chuyển của xe trong ngày.

**Hàm kiểm tra (pseudocode):**
