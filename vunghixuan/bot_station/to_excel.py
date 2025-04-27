
import pandas as pd
import xlwings as xw
import os




class ExcelWithTOC:
    def __init__(self, output_path, sheets_and_data):
        self.output_path = output_path
        self.app = xw.App(visible=False)
        self.wb = self.app.books.add()
        self.toc_sheet_name = "Mục Lục"
        self.toc_sheet = self.wb.sheets.add(self.toc_sheet_name)
        self.sheets_and_data = sheets_and_data
        self.add_sheet_with_data()
        

    def __enter__(self):
        "with ExcelWithTOC(self.output_dir, sheets_and_data) as excel_toc: "
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):#
        if self.wb:
            try:
                self.wb.save(self.output_path)
            finally:
                self.wb.close()
        if self.app:
            self.app.quit()
    
    def format_worksheet(self, ws):
        # Tự động điều chỉnh kích thước cột và hàng
        ws.autofit('columns')
        ws.autofit('rows')
        
        # DÒng hyperlink
        hyper_row = ws.used_range.rows[0]
        hyper_row.font.color = (255, 0, 0)  # Màu chứ đỏ

        # Lấy dòng đầu tiên
        first_row = ws.used_range.rows[1]
        first_row.api.WrapText = True

        # # Bọc văn bản cho các ô có độ dài lớn hơn 30 ký tự
        # for col in ws.used_range.columns:
        #     for cell in col:
        #         if len(str(cell.value)) > 30:
        #             cell.api.WrapText = True

        # Định dạng dòng đầu tiên
        first_row.color = (0, 139, 0)  # Màu nền xanh lá cây đậm
        first_row.font.color = (255, 255, 255)  # Màu chữ trắng
        first_row.font.bold = True  # In đậm
        # Canh giữa theo chiều ngang
        first_row.api.HorizontalAlignment = xw.constants.HAlign.xlHAlignCenter

        # Canh giữa theo chiều dọc
        first_row.api.VerticalAlignment = xw.constants.VAlign.xlVAlignCenter

        

    def add_sheet_with_data(self):
        """Thêm các sheet mới với dữ liệu từ DataFrame và hyperlink quay về Mục Lục."""
        for sheet_name, data in self.sheets_and_data.items():
            try:
                if not isinstance(data, pd.DataFrame):
                    if isinstance(data, list) and all(isinstance(item, list) for item in data):
                        df = pd.DataFrame(data)
                    elif isinstance(data, dict):
                        df = pd.DataFrame(data)
                    else:
                        print(f"Cảnh báo: Dữ liệu cho sheet '{sheet_name}' không phải là DataFrame, list of lists hoặc dict. Bỏ qua sheet này.")
                        continue
                else:
                    df = data

                ws = self.wb.sheets.add(sheet_name, after=self.toc_sheet.name)
                ws.range('A1').value = 'Quay về Mục Lục'
                sub_address_back = f"'{self.toc_sheet_name}'!A1"
                print(f"Đang tạo hyperlink quay về: #{sub_address_back} trên sheet '{sheet_name}'")
                ws.range('A1').add_hyperlink(
                    f'#{sub_address_back}',
                    'Quay về Mục Lục'
                )
                if not df.empty:
                    ws.range('A2').options(index=False).value = df
                else:
                    ws.range('A2').value = f'Không tìm thấy dữ liệu cho: "{sheet_name}"'
                
                # Định dạng sheets
                self.format_worksheet(ws)

                ws.used_range.rows[0]
            except Exception as e:
                print(f"Lỗi khi thêm sheet '{sheet_name}': {e}")

        self._update_toc()

    def _update_toc(self):
        """Cập nhật sheet Mục Lục với danh sách các sheet và hyperlink."""
        self.toc_sheet.clear_contents()
        self.toc_sheet.range('B1').value = 'Danh Mục Sheets'
        for i, sheet in enumerate(self.wb.sheets):
            if sheet.name != self.toc_sheet_name:
                # Điều chỉnh chỉ số hàng để bỏ qua hàng tiêu đề 'Danh Mục Sheets'
                row_index_in_toc = i + 1
                self.toc_sheet.range(f'A{row_index_in_toc + 1}').value =  row_index_in_toc-1# Bắt đầu từ hàng 2
                cell = self.toc_sheet.range(f'B{row_index_in_toc + 1}') # Bắt đầu từ hàng 2

                # Thêm số thứ tự vào giá trị của cell
                cell.value = sheet.name

                sub_address_forward = f"'{sheet.name}'!A1"
                print(f"Đang tạo hyperlink đến: #{sub_address_forward} trên sheet '{self.toc_sheet_name}'")
                cell.add_hyperlink(
                    f'#{sub_address_forward}',
                    sheet.name
                )