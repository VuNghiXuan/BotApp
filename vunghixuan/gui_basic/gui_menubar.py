
"4. Khai báo cho menu và actions"
# Định nghĩa Action và tên các sheét sử dụng trong Excel
class ACTION:
    def __init__(self, name, sheet_name_used=None):
        self.name = name
        self.isChoice = False

        # khai báo Sheet sử dụng cho hành động Action
        if sheet_name_used!=None:
            self.sheet_name_used = sheet_name_used
        else:
            self.sheet_name_used = ''


# Định nghĩa Menu
class MENU:
    def __init__(self, name, actions):
        self.name = name
        self.actions = actions
        self.isChoice = False #Menu đang đuọc chọn
        # sheet_names_used = sheet_names_used

    # Thay đổi isChoice
    # Lấy danh sách actions
    def get_action_names(self):
        action_names = []
        for act in self.actions:
            action_names.append(act.name)
        return action_names
    
    # Lấy danh sách sheets tương ứng actions
    def get_sheet_names(self):
        sheet_names = []
        for act in self.actions:
            sheet_names.append(act.sheet_name_used)
        return sheet_names


class MENU_BAR():
    def __init__(self, name, menus):
        self.name = name
        self.menus = menus
        
    # Lấy danh sách tên menus
    def get_menu_names(self):
        menus_names =[]
        for menu in self.menus:
            menus_names.append(menu.name)
        return menus_names
    
    
    

# Khởi tạo MenuBar
menubar_name = 'MenuBar cho phần Phân Kim'
dic_menus = {
    "Nhập dữ liệu":{
        'Đổi dẻ': 'Nhap_DoiDe',
        'Mua dẻ': 'Nhap_MuaDe',
        'Bán dẻ': 'Nhap_BanDe',
        'Giá vàng': 'GiaVang',
        'Loại vàng': 'LoaiVang'
    },
    "Báo cáo": {
        'Đổi dẻ': 'Nhap_DoiDe',
        'Mua dẻ': 'Nhap_MuaDe',
        'Bán dẻ': 'Nhap_BanDe',
        'Công nợ': 'Chưa có sheet'
    },
    "Phiếu xuất":{
        'Nhập kho': 'Chưa có sheet',
        'Xuất kho': 'Chưa có sheet',
    }
}

def create_menubar():    
    menu_objs = []
    for menu, actions in dic_menus.items():
        action_objs = []
        for act, sh in actions.items():
            action = ACTION(act, sh)
            action_objs.append(action)
        menu = MENU(menu, action_objs)
        menu_objs.append(menu)
    
    menubar = MENU_BAR(menubar_name,menu_objs)
    return menubar






if __name__ == "__main__":

    
    MENUBAR = create_menubar(menubar_name)

    print("Danh sách tên menu", MENUBAR.get_menu_names())
    
    for menu in MENUBAR.menus:
        print(f'Tên menu: {menu.name}, Danh mục actions{menu.get_action_names()}')
        print(f'Tên menu: {menu.name}, Danh mục sheets{menu.get_sheet_names()}')
    
    # print("Danh sách tên actions", MENUBAR.menus.get_action_names())
    # print("Danh sách tên sheet",MENUBAR.menus.get_sheet_names())
