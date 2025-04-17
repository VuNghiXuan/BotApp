
# src/vunghixuan/create_project.py
import os 
from pathlib import Path

class Project:
    def __init__(self):       
        # self.root_path = Path(__file__).parent
        self.root_path = Path(os.getcwd())  # Lấy đường dẫn hiện tại
   
    # Tạo ra folder cần thiết cho dự án
    def create_folder(self, folder_path, name):
        folder_path = os.path.join(folder_path, name)
        os.makedirs(folder_path, exist_ok=True) 
    
    

    # Tạo ra folder apps
    def create_project(self):
        # Tạo ra các app
        list_folder = ['apps', 'settings']
        for folder in list_folder:
            self.create_folder(self.root_path, folder)

        # Tạo ra file settings
        from . import project_create_files_and_app
        project_create_files_and_app.create_file()

    

    def create_app(self, app_name):
        folder_path = os.path.join(self.root_path, 'apps')
        
        if not os.path.exists(folder_path):
            self.create_project()
            self.create_app(app_name)
        else:
            self.create_folder(folder_path, app_name)
            app_folder_path = os.path.join(self.root_path, 'apps', app_name)

            # list_folder = ['models', 'views', 'tests.py', f'{app_name}.py']
            # for folder in list_folder:
            #     self.create_folder(folder_path, folder)

            list_files = ['models', 'views', 'tests', app_name]

            for file in list_files:

                # Tạo các file cần thiết cho ứng dụng
                with open(os.path.join(app_folder_path, file), 'w', encoding='utf-8') as f:
                    f.write("# Đây là file chính của ứng dụng\n")
            
            


    
    
        
        


if __name__=="__main__":
    
    project = Project()

    # 1. Tạo ra project
    # project.create_project()

    # 2. Tạo app
    project.create_app('app1')
        