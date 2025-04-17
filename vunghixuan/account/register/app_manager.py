from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
import hashlib
from vunghixuan.settings import DATABASE_URL, TABS_INFO, PERMISSIONS
from vunghixuan.account.register.models import User, Roll, Permission, App, Group, Interface, Base, roll_permission_association
import os
from collections import defaultdict
import logging
import logging.handlers  # Import mô-đun handlers
import traceback



class AppManager:
    """Quản lý ứng dụng."""
    def __init__(self, session):
        """Khởi tạo AppManager với phiên làm việc cơ sở dữ liệu."""
        self._session = session

    def add_app(self, name, description=None):
        """Thêm ứng dụng mới vào cơ sở dữ liệu."""
        if self._session.query(App).filter_by(name=name).first():
            logging.error(f"Ứng dụng {name} đã tồn tại.")
            return False
        app = App(name=name, description=description)
        self._session.add(app)
        self._session.commit()
        return True

    def get_apps(self):
        """Lấy danh sách tất cả các ứng dụng."""
        return self._session.query(App).all()

    def update_app(self, app_id, name=None, description=None):
        """Cập nhật thông tin ứng dụng."""
        app = self._session.get(App, app_id)
        if app:
            if name:
                app.name = name
            if description:
                app.description = description
            self._session.commit()
            return True
        return False

    def delete_app(self, app_id):
        """Xóa ứng dụng khỏi cơ sở dữ liệu."""
        app = self._session.get(App, app_id)
        if app:
            self._session.delete(app)
            self._session.commit()
            return True
        return False

    def get_app_id_by_name(self, app_name):
        """Lấy ID ứng dụng theo tên ứng dụng."""
        app = self._session.query(App).filter_by(name=app_name).first()
        return app.id if app else None

    def get_all_apps(self):
        """Lấy danh sách tên của tất cả các ứng dụng."""
        return [app.name for app in self._session.query(App).all()]

    def get_all_app_names(self):
        """Lấy danh sách tên của tất cả các ứng dụng."""
        apps = self._session.query(App).all()
        return [app.name for app in apps]

