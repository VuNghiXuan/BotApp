# coding=utf-8
#  vugnhixuan/update_setting_file.py


import os, site, shutil
import importlib.util as is_package

# Kiểm tra sự tồn tại file
def path_exists(path):
    return os.path.exists(path)

# Kiểm tra sự tồn tại gói 
def package_exists(package_name):
    return is_package.find_spec(package_name) is not None

# Chép file từ nguồn đến đích
def copy_file(source_file, destination):
    if path_exists(source_file):
        shutil.copy(source_file, destination)

# Kiểm tra gói VuNghiXuan đã cài đặt bằng pip chưa?
def chk_VuNghixuan_package():
    package_name = 'vunghixuan'
    package_folder = os.path.join(site.getsitepackages()[1], package_name)
        
    package_setting_file = os.path.join(package_folder, 'settings.py')
    
    # Kiểm tra gói VuNghiXuan đã cài đaetj chưa
    if os.path.exists(package_setting_file):
        # Tiếp tục kiểm tra sụe tồn tại 'settings/settings.py'
        return package_setting_file
    else:

        print(f'Chưa cài đặt gói "VuNghiXuan" hoặc không tồn tại "{package_setting_file}"')
        return False
    
# Tiếp tục kiểm tra sự tồn tại 'settings/settings.py'
def chk_file_setting_exits():
    setting_file = 'vunghixuan/settings.py'
    # Kiểm tra tồn tại file 
    if not os.path.exists(setting_file):
        print('Không tồn tại ', setting_file)
        return False
    else:
        return setting_file

# Update file settings from giao diện
def change_theme_for_setting_file(color_fnt_bg, setting_file):
    # color_fnt_bg = self.header.theme_selector.currentText()
    with open(setting_file, 'r', encoding='utf-8' ) as file:
        lines = file.readlines()

    with open(setting_file, 'w', encoding='utf-8') as file:
        for line in lines:
            if line.startswith('color_fnt_bg'):
                file.write(f"color_fnt_bg = COLOR_FONT_BACKGROUND['{color_fnt_bg}']\n")
            else:
                file.write(line)
        file.close()

# Cập nhật file setting
def update_setting_file():
    package_setting_file = chk_VuNghixuan_package()
    setting_file = chk_file_setting_exits()
    if package_setting_file and setting_file:        
        # Copy settings file vào gói VuNghiXuan
        copy_file(setting_file, package_setting_file)
        print('update setting file thành công!')


def update_theme(color_fnt_bg):
    # package_setting_file = chk_VuNghixuan_package()
    setting_file = chk_file_setting_exits()
    if setting_file:
        # Update file settings from giao diện
        change_theme_for_setting_file(color_fnt_bg, setting_file)
        # Copy settings file vào gói VuNghiXuan
        # copy_file(setting_file, package_setting_file)
        print('update setting file thành công!')
    
