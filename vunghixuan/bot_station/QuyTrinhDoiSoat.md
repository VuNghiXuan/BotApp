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

1.  **Lọc và xem xét các trường hợp bất thường:** Tập trung vào các giao dịch được đánh dấu trong cột `'Lượt đi bất thường'` và các trường hợp có chênh lệch phí.
2.  **Điều tra nguyên nhân:** Thực hiện các nghiệp vụ cần thiết để xác định nguyên nhân gốc rễ của các trường hợp bất thường và chênh lệch.
3.  **Thực hiện điều chỉnh:** Dựa trên kết quả điều tra, thực hiện các điều chỉnh phí cần thiết.
4.  **Báo cáo:** Tổng hợp kết quả đối soát và các hành động điều chỉnh.
5.  **Cải tiến quy trình:** Dựa trên các vấn đề thường xuyên xảy ra, xem xét và cải tiến quy trình đối soát.

## VI. Quy trình kiểm tra lượt vé và phí thu

**Mục tiêu:** Xác định trạng thái thu phí (BE đúng, FE đúng, cả hai sai, hoặc cả hai đúng) và số lượt di chuyển trong ngày của một xe dựa trên dữ liệu thu phí và thông tin làn đường.

**Nguồn dữ liệu:**

* `self.mapping_lane`: Dữ liệu cấu hình ánh xạ làn đường, cho biết loại làn (vào, ra, khác).
* Dữ liệu giao dịch thu phí của xe (bao gồm thời điểm, trạm, làn đường, loại phí BE/FE).

**Logic kiểm tra lượt đi (đã điều chỉnh lần 2 + Làn 7):**

Khi phân tích các giao dịch để xác định lượt đi, chúng ta **chỉ xem xét** các giao dịch có `'Lỗi Antent' == False`, **bao gồm cả các giao dịch tại Làn 7**.

* **Quy tắc đặc biệt cho Làn 7:** Làn 7 được định nghĩa là làn kiểm soát thu phí cho xe đi từ các đường dân sinh vào dự án (và ngược lại). **Tất cả các giao dịch tại Làn 7 được xem xét phải có `'Lỗi Antent' == False`.**
    * Nếu một xe đi vào Làn 7 (`'Làn chuẩn' == 'Làn 7'`) và trước đó **không có giao dịch thu phí nào** (với `'Lỗi Antent' == False`) được ghi nhận cho xe đó tại bất kỳ làn vào nào khác của dự án (trong một khoảng thời gian hợp lý), thì giao dịch tại Làn 7 được xem như là **điểm khởi hành vào dự án**.
    * Tương tự, nếu một xe đi ra ở Làn 7 (`'Làn chuẩn' == 'Làn 7'`) và sau đó **không có giao dịch thu phí nào** (với `'Lỗi Antent' == False`) được ghi nhận cho xe đó tại bất kỳ làn ra nào khác của dự án, thì giao dịch tại Làn 7 được xem như là **điểm kết thúc ra khỏi dự án**.
    * Nếu xe đã thực hiện giao dịch thu phí ở các làn vào khác (với `'Lỗi Antent' == False'`), thì giao dịch ở Làn 7 (nếu có và `'Lỗi Antent' == False'`) sẽ không được tính là điểm khởi hành mới. Tương tự với chiều ra.
    * Giao dịch tại Làn 7 (với `'Lỗi Antent' == False'`) vẫn có thể là điểm kết thúc của một lượt đi từ ngoài vào hoặc điểm bắt đầu của một lượt đi từ trong ra, tương tự như các làn khác, nếu không có giao dịch thu phí nào khác (với `'Lỗi Antent' == False'`) trước đó theo chiều tương ứng.
    * **Nếu một giao dịch tại Làn 7 không phải là điểm khởi hành hoặc kết thúc của một lượt đi (dựa trên các quy tắc trên), thì bỏ qua giao dịch này và chuyển đến giao dịch kế tiếp của xe để tiếp tục tìm kiếm điểm khởi hành hoặc kết thúc lượt đi hợp lệ.**

* **1. Lượt đi từ ngoài vào:**
    * Giao dịch vào đầu tiên (với `'Lỗi Antent' == False'` và là làn được định nghĩa là 'vào' trong `self.mapping_lane`) được ghi nhận là điểm bắt đầu của lượt đi.
    * Giao dịch ra sau đó (với `'Lỗi Antent' == False'` và là làn được định nghĩa là 'ra' trong `self.mapping_lane`) sẽ kết thúc lượt đi này.

* **2. Lượt đi từ trong ra (dân sinh):**
    * Giao dịch ra đầu tiên (với `'Lỗi Antent' == False'` và là làn được định nghĩa là 'ra' trong `self.mapping_lane`) được ghi nhận là điểm bắt đầu của lượt đi.
    * Nếu sau đó có giao dịch vào lại **cùng trạm** (tên trạm được xác định từ 'Làn chuẩn' thông qua `self.mapping_lane`) và sử dụng **đúng làn vào** (được định nghĩa là 'vào' cho trạm đó trong `self.mapping_lane`), cả hai giao dịch này đều phải có `'Lỗi Antent' == False'` để lượt đi được xác định.

* **3. Lượt đi cơ bản:** Một lượt đi cơ bản hợp lệ bao gồm một giao dịch vào và một giao dịch ra (cả hai đều có `'Lỗi Antent' == False'`).

* **4. Xe chưa quay đầu:** Nếu chỉ có giao dịch vào (với `'Lỗi Antent' == False'` và là làn 'vào' theo `self.mapping_lane`) mà không có giao dịch ra (với `'Lỗi Antent' == False'` và là làn 'ra' theo `self.mapping_lane`) cho cùng một xe trong một khoảng thời gian nhất định, thì được ghi nhận là "xe chưa quay đầu".

* **5. Xe đã ra mà chưa xác định điểm vào:** Nếu chỉ có giao dịch ra (với `'Lỗi Antent' == False'` và là làn 'ra' theo `self.mapping_lane`) mà không có giao dịch vào (với `'Lỗi Antent' == False'` và là làn 'vào' theo `self.mapping_lane`) trước đó cho cùng một xe trong một khoảng thời gian nhất định, thì được ghi nhận là "xe đã ra mà chưa xác định điểm vào".

**Hàm kiểm tra (pseudocode):**


VI. Quy tắc xác định lượt đi và trạng thái phí:
Lượt đi một chiều (từ ngoài vào):

Bắt đầu: Giao dịch đầu tiên ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'vào' (theo định nghĩa trong self.mapping_lane). Giao dịch này được xem là điểm khởi đầu của lượt đi.
Kết thúc: Giao dịch tiếp theo ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'ra' (theo định nghĩa trong self.mapping_lane).
Kiểm tra đặc biệt cho làn 7: Nếu làn kết thúc là làn số 7, cần kiểm tra các giao dịch tiếp theo (bên dưới) để xác định giao dịch kết thúc lượt đi chính xác hơn dựa trên loại vé chuẩn:
Nếu tồn tại giao dịch ở làn 7 có cột loại vé chuẩn là "Miễn phí liên trạm" và phí thu bằng 0, thì giao dịch này được xem là làn kiểm soát, chưa phải là giao dịch kết thúc cuối cùng của lượt đi. Cần tiếp tục tìm giao dịch ra hợp lệ sau đó.
Nếu tồn tại giao dịch ở làn 7 có cột loại vé chuẩn là 'Miễn phí quay đầu', thì giao dịch này chính là giao dịch kết thúc của lượt đi.
Nếu không có các trường hợp đặc biệt trên, giao dịch ra đầu tiên ở làn 'ra' (bao gồm cả làn 7 nếu không thuộc trường hợp "Miễn phí liên trạm") được xem là kết thúc lượt đi.
Trạng thái phí:
Nếu giao dịch khởi hành (làn vào) không bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị thiếu hay không.
Nếu giao dịch kết thúc (làn ra) bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị tính thừa hay không.
Lượt đi dân sinh (từ trong ra, quay đầu tại trạm):

Bắt đầu: Giao dịch ra đầu tiên ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'ra' (theo định nghĩa trong self.mapping_lane). Giao dịch này được xem là điểm khởi đầu của lượt đi.
Kết thúc: Giao dịch vào sau đó phải thỏa mãn các điều kiện sau:
Xảy ra tại cùng trạm với giao dịch ra trước đó (tên trạm được xác định từ cột 'Làn chuẩn' thông qua self.mapping_lane).
Sử dụng đúng làn vào (được định nghĩa là 'vào' cho trạm đó trong self.mapping_lane).
Có 'Lỗi Antent' == False'.
Điều kiện hợp lệ: Cả giao dịch ra ban đầu và giao dịch vào sau đó đều phải có 'Lỗi Antent' == False' để lượt đi này được xác định là hợp lệ.
Trạng thái phí:
Nếu giao dịch khởi hành (làn ra đầu tiên) không bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị thiếu hay không.
Nếu giao dịch kết thúc (làn vào sau đó) bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị tính thừa hay không.
Lượt đi cơ bản (vào và ra):

Bắt đầu: Giao dịch vào đầu tiên ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'vào' (theo định nghĩa trong self.mapping_lane).
Kết thúc: Giao dịch ra tiếp theo ghi nhận được phải thỏa mãn đồng thời hai điều kiện: 'Lỗi Antent' == False' và làn giao dịch là làn 'ra' (theo định nghĩa trong self.mapping_lane).
Kiểm tra đặc biệt cho làn 7: Tương tự như lượt đi một chiều, nếu làn kết thúc là làn số 7, cần kiểm tra các giao dịch tiếp theo (bên dưới) dựa trên loại vé chuẩn ("Miễn phí liên trạm" và 'Miễn phí quay đầu') để xác định giao dịch kết thúc chính xác.
Trạng thái phí:
Nếu giao dịch khởi hành (làn vào) không bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị thiếu hay không.
Nếu giao dịch kết thúc (làn ra) bị tính phí, hãy kiểm tra xem phí thu BE hoặc FE có bị tính thừa hay không.
Trường hợp xe chưa quay đầu:

Nếu hệ thống ghi nhận một giao dịch khởi hành hợp lệ (làn 'vào', 'Lỗi Antent' == False') cho một lượt đi nhưng không tìm thấy giao dịch kết thúc hợp lệ (làn 'ra', 'Lỗi Antent' == False') tương ứng cho lượt đi đó trong chuỗi giao dịch của xe, thì giao dịch cuối cùng của lượt đi đó sẽ được ghi nhận với trạng thái "(Xe chưa quay đầu)" trong mô tả hành trình.
Trường hợp xe đã ra mà chưa xác định điểm vào:

Nếu hệ thống ghi nhận một giao dịch ra hợp lệ (làn 'ra', 'Lỗi Antent' == False') và không tìm thấy giao dịch vào hợp lệ (làn 'vào', 'Lỗi Antent' == False') nào được xác định là điểm khởi hành cho lượt đi đó trong chuỗi giao dịch của xe trước giao dịch ra này, thì giao dịch ra đầu tiên đó sẽ được ghi nhận với mô tả "... - Xe đã ra mà chưa xác định điểm vào trước đó".

