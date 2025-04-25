Tuyệt vời! Để đảm bảo bạn có một bức tranh toàn diện và đầy đủ về quy trình đối soát, dưới đây là phiên bản tổng hợp và chi tiết hơn của toàn bộ nội dung chúng ta đã thảo luận:

Mô tả Vấn Đề:

Dữ liệu thu thập từ hai hệ thống FE (Front-End - hệ thống thu phí trực tiếp tại trạm) và BE (Back-End - hệ thống quản lý vé điện tử, tài khoản giao thông) cần được đối soát để phát hiện chênh lệch thu phí cho cùng một xe. Việc đối soát này dựa trên cột 'Số xe đăng ký'. Tuy nhiên, trong trường hợp cột 'Số xe đăng ký' bị trống, cần sử dụng cột 'BE_Biển số xe' để xác định xe.

Các Trường Hợp Cần Xử Lý:

FE thu phí, BE hoàn tiền: Trên cùng một xe ('Số xe đăng ký'), do có thể gắn nhiều 'BE_Số etag', hệ thống FE có thể quét và thu phí nhiều lần cho một lần xe qua trạm. Điều này được nhận diện khi có các dòng cùng 'Số xe đăng ký' với 'Phí thu' > 0 nhưng 'BE_Tiền bao gồm thuế' = 0, cho thấy BE đã hoàn lại tiền.

FE thu phí nhiều lần do quét trùng/nhiều làn: Một xe khi qua trạm (có nhiều làn với camera quét khác nhau) có thể bị nhiều camera đọc được, dẫn đến FE thu phí nhiều lần trong một khoảng thời gian ngắn. Thời gian đọc và truyền dữ liệu giữa các làn và giữa FE-BE có thể khác nhau.

Chênh lệch giá trị thu phí thông thường: Sự khác biệt về số tiền thu phí giữa FE và thông tin giao dịch tương ứng từ BE mà không thuộc hai trường hợp đặc biệt trên.

Giao dịch chỉ tồn tại ở một hệ thống: Có những giao dịch được ghi nhận ở FE nhưng không có thông tin tương ứng ở BE, hoặc ngược lại.

Sai lệch về thời gian giao dịch: Sự khác biệt đáng kể về thời gian ghi nhận giao dịch giữa FE và BE cho cùng một lần xe qua trạm.

Nhiệm Vụ:

Xây dựng một quy trình và giải pháp tổng hợp dữ liệu để đối soát chênh lệch thu phí giữa FE và BE, tạo ra một cột 'Ghi chú' để mô tả chi tiết các trường hợp sai lệch được phát hiện.

Quy Trình Chi Tiết:

Thu Thập và Load Dữ Liệu:

Đảm bảo dữ liệu từ cả hệ thống FE và BE được thu thập đầy đủ và chính xác.
Load dữ liệu vào cấu trúc dữ liệu phù hợp để xử lý (khuyến nghị sử dụng Pandas DataFrame trong Python).
Chuẩn Hóa Dữ Liệu:

Làm sạch cột biển số xe: Loại bỏ khoảng trắng thừa, ký tự đặc biệt (ví dụ: dấu nháy đơn) ở đầu và cuối chuỗi trong cả cột 'Số xe đăng ký' (FE) và 'BE_Biển số xe' (BE). Thay thế các giá trị chuỗi rỗng hoặc chỉ chứa khoảng trắng bằng NaN.
Chuyển đổi kiểu dữ liệu: Đảm bảo các cột số tiền ('Phí thu', 'BE_Tiền bao gồm thuế') được chuyển sang kiểu số (numeric). Các lỗi chuyển đổi nên được xử lý (ví dụ: thay thế bằng 0 hoặc NaN). Các cột thời gian ('Ngày giờ' của FE nếu có, 'BE_Thời gian qua trạm') nên được chuyển sang kiểu datetime.
Đổi tên cột: Đổi tên các cột trong DataFrame của BE để tránh trùng lặp với DataFrame của FE sau khi merge (ví dụ, thêm tiền tố 'BE_' vào trước tên các cột của BE, trừ cột biển số xe).
Tạo Cột Biển Số Xe Thống Nhất:

Tạo một cột mới trong DataFrame đã merge (hoặc trước khi merge nếu cần), ví dụ 'Biển số xe chuẩn'.
Áp dụng logic: Nếu giá trị ở cột 'Số xe đăng ký' không phải là NaN hoặc không trống, sử dụng giá trị đó. Ngược lại, nếu 'Số xe đăng ký' là NaN hoặc trống, sử dụng giá trị từ cột 'BE_Biển số xe'.
Merge Dữ Liệu FE và BE:

Sử dụng hàm merge của Pandas để kết hợp hai DataFrame dựa trên cột 'Biển số xe chuẩn'. Sử dụng how='outer' để giữ lại tất cả các giao dịch từ cả hai hệ thống.
Tính Toán Chênh Lệch:

Tạo cột 'Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)' bằng cách lấy giá trị cột 'Phí thu' trừ đi cột 'BE_Tiền bao gồm thuế'.
Tạo Cột 'Ghi chú' và Xác Định Các Trường Hợp:

Khởi tạo một cột mới tên 'Ghi chú' với giá trị ban đầu là chuỗi rỗng.
Trường hợp 1: FE thu phí, BE hoàn tiền: Lọc các dòng mà 'Phí thu' > 0 và 'BE_Tiền bao gồm thuế' == 0. Gán 'Ghi chú' là "FE thu phí, BE hoàn tiền".
Trường hợp 2: Nghi vấn quét trùng/nhiều làn:
Nhóm dữ liệu theo 'Biển số xe chuẩn'.
Đối với mỗi nhóm, nếu có thông tin thời gian ('Ngày giờ' và/hoặc 'BE_Thời gian qua trạm'), sắp xếp các giao dịch theo thời gian.
Xác định các giao dịch FE hoặc BE xảy ra trong một khoảng thời gian rất ngắn (ví dụ: vài phút) cho cùng một biển số xe.
Gán 'Ghi chú' là "Nghi vấn quét trùng/nhiều làn".
Trường hợp 3: Chênh lệch giá trị thu phí thông thường: Lọc các dòng có 'Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)' khác 0 và không thuộc trường hợp 1. Gán 'Ghi chú' là "Chênh lệch giá trị: [giá trị chênh lệch]".
Trường hợp 4: Chỉ có giao dịch ở FE: Lọc các dòng mà thông tin BE (ví dụ: 'BE_Mã giao dịch', 'BE_Thời gian qua trạm') là NaN. Gán 'Ghi chú' là "Chỉ có giao dịch ở FE".
Trường hợp 5: Chỉ có giao dịch ở BE: Lọc các dòng mà thông tin FE (ví dụ: 'Mã giao dịch', 'Phí thu') là NaN. Gán 'Ghi chú' là "Chỉ có giao dịch ở BE".
Trường hợp 6: Sai lệch thời gian: Nếu có cả 'Ngày giờ' và 'BE_Thời gian qua trạm', tính toán sự khác biệt thời gian. Nếu vượt quá một ngưỡng nhất định, gán 'Ghi chú' là "Sai lệch thời gian lớn".
Trường hợp 7: Đối soát khớp: Lọc các dòng có 'Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)' == 0 và 'Ghi chú' vẫn là rỗng. Gán 'Ghi chú' là "Đối soát khớp".
Sắp Xếp và Hiển Thị Kết Quả:

Sắp xếp DataFrame kết quả theo 'Biển số xe chuẩn' và sau đó theo thời gian giao dịch (nếu có) để dễ dàng theo dõi.
Hiển thị các cột quan trọng như 'Mã giao dịch' (FE), 'BE_Mã giao dịch', 'Biển số xe chuẩn', 'Phí thu', 'BE_Tiền bao gồm thuế', 'Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)', và 'Ghi chú'.
Giải pháp (Python và Pandas):

import pandas as pd
import numpy as np

def doi_soat_thu_phi_v3(df_fe, df_be):
    """
    Đối soát chênh lệch thu phí giữa FE và BE, xử lý trường hợp 'Số xe đăng ký' trống và các trường hợp sai lệch.

    Args:
        df_fe (pd.DataFrame): DataFrame chứa dữ liệu từ hệ thống FE.
        df_be (pd.DataFrame): DataFrame chứa dữ liệu từ hệ thống BE.

    Returns:
        pd.DataFrame: DataFrame kết quả đối soát với cột 'Ghi chú'.
    """

    # 1. Chuẩn hóa dữ liệu
    df_fe['Số xe đăng ký'] = df_fe['Số xe đăng ký'].str.strip("' ").replace('', np.nan)
    df_be['Biển số xe'] = df_be['Biển số xe'].str.strip("' ")
    df_fe['Phí thu'] = pd.to_numeric(df_fe['Phí thu'], errors='coerce').fillna(0)
    df_be['BE_Tiền bao gồm thuế'] = pd.to_numeric(df_be['Tiền bao gồm thuế'], errors='coerce').fillna(0)

    # Đổi tên cột BE
    be_cols = {col: f'BE_{col}' for col in df_be.columns if col != 'Biển số xe'}
    df_be = df_be.rename(columns=be_cols)

    # 2. Tạo cột biển số xe thống nhất
    merged_df = pd.merge(df_fe, df_be, left_on='Số xe đăng ký', right_on='BE_Biển số xe', how='outer')
    merged_df['Biển số xe chuẩn'] = merged_df['Số xe đăng ký'].fillna(merged_df['BE_Biển số xe'])

    # 3. Tính toán chênh lệch
    merged_df['Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)'] = merged_df['Phí thu'] - merged_df['BE_Tiền bao gồm thuế']
    merged_df['Ghi chú'] = ''

    # 4. Xác định các trường hợp chênh lệch và tạo cột ghi chú

    # Trường hợp 1: FE thu phí, BE hoàn tiền
    condition_fe_thu_be_hoan = (merged_df['Phí thu'] > 0) & (merged_df['BE_Tiền bao gồm thuế'] == 0)
    merged_df.loc[condition_fe_thu_be_hoan, 'Ghi chú'] = 'FE thu phí, BE hoàn tiền'

    # Trường hợp 3: Chênh lệch giá trị thu phí
    condition_chenh_lech_gia_tri = (merged_df['Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)'] != 0) & ~condition_fe_thu_be_hoan
    merged_df.loc[condition_chenh_lech_gia_tri, 'Ghi chú'] = 'Chênh lệch giá trị: ' + merged_df['Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)'].astype(str)

    # Trường hợp 4: Chỉ có giao dịch ở FE
    condition_only_fe = merged_df['BE_Biển số xe'].isnull()
    merged_df.loc[condition_only_fe, 'Ghi chú'] = 'Chỉ có giao dịch ở FE'

    # Trường hợp 5: Chỉ có giao dịch ở BE
    condition_only_be = merged_df['Số xe đăng ký'].isnull()
    merged_df.loc[condition_only_be, 'Ghi chú'] = 'Chỉ có giao dịch ở BE'

    # Trường hợp 6: Sai lệch thời gian (cần ngưỡng cụ thể)
    if 'Ngày giờ' in merged_df.columns and 'BE_Thời gian qua trạm' in merged_df.columns:
        merged_df['Ngày giờ'] = pd.to_datetime(merged_df['Ngày giờ'], errors='coerce')
        merged_df['BE_Thời gian qua trạm'] = pd.to_datetime(merged_df['BE_Thời gian qua trạm'], errors='coerce')
        time_diff_threshold = pd.Timedelta(minutes=15)  # Ví dụ: ngưỡng 15 phút
        time_diff = np.abs(merged_df['Ngày giờ'] - merged_df['BE_Thời gian qua trạm'])
        merged_df.loc[time_diff > time_diff_threshold, 'Ghi chú'] = merged_df.loc[time_diff > time_diff_threshold, 'Ghi chú'].apply(lambda x: f'{x}; Sai lệch thời gian lớn' if x else 'Sai lệch thời gian lớn')

    # Trường hợp 2: Nghi vấn quét trùng/nhiều làn (cần ngưỡng thời gian)
    def detect_multiple_transactions(group):
        fe_times = pd.to_datetime(group['Ngày giờ'], errors='coerce').dropna().sort_values()
        be_times = pd.to_datetime(group['BE_Thời gian qua trạm'], errors='coerce').dropna().sort_values()
        time_threshold = pd.Timedelta(minutes=5)
        ghi_chu = ''
        if len(fe_times) > 1:
            for i in range(len(fe_times) - 1):
                if (fe_times.iloc[i+1] - fe_times.iloc[i]) < time_threshold:
                    ghi_chu = f'{ghi_chu}; Nghi vấn FE quét trùng/nhiều làn' if ghi_chu else 'Nghi vấn FE quét trùng/nhiều làn'
                    break
        if len(be_times) > 1:
            for i in range(len(be_times) - 1):
                if (be_times.iloc[i+1] - be_times.iloc[i]) < time_threshold:
                    ghi_chu = f'{ghi_chu}; Nghi vấn BE ghi trùng' if ghi_chu else 'Nghi vấn BE ghi trùng'
                    break
        return ghi_chu.lstrip('; ')

    grouped = merged_df.groupby('Biển số xe chuẩn')
    merged_df['Ghi chú_quet_trung'] = grouped.apply(detect_multiple_transactions).fillna('')
    merged_df['Ghi chú'] = merged_df.apply(lambda row: f"{row['Ghi chú']}; {row['Ghi chú_quet_trung']}".lstrip('; ') if row['Ghi chú_quet_trung'] else row['Ghi chú'], axis=1)
    merged_df = merged_df.drop(columns=['Ghi chú_quet_trung'])


    # Trường hợp 7: Đối soát khớp
    condition_khop = (merged_df['Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)'] == 0) & (merged_df['Ghi chú'] == '')
    merged_df.loc[condition_khop, 'Ghi chú'] = 'Đối soát khớp'

    # 5. Sắp xếp kết quả
    merged_df = merged_df.sort_values(by=['Biển số xe chuẩn', 'Ngày giờ', 'BE_Thời gian qua trạm'])

    return merged_df[['Mã giao dịch', 'Số xe đăng ký', 'BE_Biển số xe', 'Biển số xe chuẩn', 'Mã thẻ', 'Phí thu',
                       'BE_Thời gian qua trạm', 'BE_Làn', 'BE_Tổng tiền bao gồm thuế',
                       'Chênh lệch (Phí thu - BE_Tiền bao gồm thuế)', 'Ghi chú']]

# Giả sử bạn đã load dữ liệu FE và BE vào các DataFrame df_fe và df_be
# df_fe = pd.read_csv('fe_data.csv')
# df_be = pd.read_csv('be_data.csv')

# result_df = doi_soat_thu_phi_v3(df_fe.copy(), df_be.copy())
# print(result_df)

Lưu ý quan trọng:

Ngưỡng thời gian: Việc xác định ngưỡng thời gian cho trường hợp quét trùng/nhiều làn (ví dụ: pd.Timedelta(minutes=5)) và sai lệch thời gian lớn (pd.Timedelta(minutes=15)) là rất quan trọng và cần được điều chỉnh dựa trên đặc thù hệ thống và nghiệp vụ của bạn.
Thông tin thời gian: Code giả định rằng bạn có cột thời gian giao dịch ở cả hai hệ thống ('Ngày giờ' cho FE và 'BE_Thời gian qua trạm' cho BE). Nếu thiếu một trong hai, bạn cần điều chỉnh logic cho phù hợp.
Xử lý dữ liệu NaN: Các thao tác với dữ liệu NaN cần được xem xét kỹ để tránh gây ra lỗi hoặc kết quả không chính xác.
Tên cột: Đảm bảo tên cột trong code khớp với tên cột thực tế trong dữ liệu của bạn.
Bằng việc triển khai quy trình và giải pháp chi tiết này, bạn sẽ có khả năng đối soát dữ liệu thu phí một cách toàn diện hơn, xử lý được trường hợp thiếu 'Số xe đăng ký' và phát hiện các loại sai lệch khác nhau, từ đó nâng cao hiệu quả quản lý và đối soát dữ liệu.