import os
import shutil
import importlib.util as is_package
import site

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


def copy_file_from_vunghixuan_package(settings_path, requirements_path):    
    source_file = 'vunghixuan/settings.py'
    copy_file(source_file, settings_path)
    copy_file('vunghixuan/requirements.txt', requirements_path)

def create_file():    
    base_dir = os.getcwd()   
    settings_path = os.path.join('settings', 'settings.py')
    requirements_path = os.path.join(base_dir, 'requirements.txt')
    
    if not path_exists(settings_path):
        package_name = 'vunghixuan'
        source_file = 'vunghixuan/settings.py'
        
        if package_exists(package_name):
            source_folder = os.path.join(site.getsitepackages()[1], package_name)
            setting_file = os.path.join(source_folder, 'settings.py')
            requirement_file = os.path.join(source_folder, 'requirements.txt')

            # Kiểm tra file do có sự tòn tại cả cache
            if path_exists(setting_file):
                copy_file(setting_file, settings_path)
                copy_file(requirement_file, requirements_path)
            else:
                copy_file_from_vunghixuan_package(settings_path, requirements_path)
        else:
            copy_file_from_vunghixuan_package(settings_path, requirements_path)

create_file()
