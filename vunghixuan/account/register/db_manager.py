

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




class DatabaseManager:
    """Quản lý kết nối cơ sở dữ liệu."""
    def __init__(self, database_url):
        """Khởi tạo DatabaseManager với URL cơ sở dữ liệu."""
        self._engine = create_engine(database_url)
        SessionMaker = sessionmaker(bind=self._engine)
        self._session = SessionMaker()

    def get_session(self):
        """Trả về phiên làm việc cơ sở dữ liệu."""
        return self._session

    def commit(self):
        """Lưu các thay đổi vào cơ sở dữ liệu."""
        self._session.commit()

    def close(self):
        """Đóng phiên làm việc cơ sở dữ liệu."""
        self._session.close()

class DefaultSetup:
    """Thiết lập các giá trị mặc định cho cơ sở dữ liệu."""
    def __init__(self, session):
        """Khởi tạo DefaultSetup với phiên làm việc cơ sở dữ liệu."""
        self._session = session

    def setup_defaults(self):
        """Thiết lập các giá trị mặc định (bảng, ứng dụng, giao diện, quyền)."""
        self.create_tables_if_not_exists()
        if not self._check_app_exists():
            self._add_default_apps_interfaces_permissions()

    def create_tables_if_not_exists(self):
        """Tạo bảng nếu cơ sở dữ liệu chưa tồn tại."""
        engine = create_engine(DATABASE_URL)
        if not os.path.exists(DATABASE_URL.split("///")[1]):
            Base.metadata.create_all(engine)
            print("Cơ sở dữ liệu đã được tạo thành công.")
        else:
            print("Cơ sở dữ liệu đã tồn tại.")

    def _check_app_exists(self):
        """Kiểm tra xem ứng dụng có tồn tại trong cơ sở dữ liệu hay không."""
        return self._session.query(App).first() is not None

    def _add_default_apps_interfaces_permissions(self):
        """Thêm các ứng dụng, giao diện và quyền mặc định vào cơ sở dữ liệu."""
        added_permissions = {}
        for permission_name in PERMISSIONS:
            existing_permission = self._session.query(Permission).filter_by(name=permission_name).first()
            if not existing_permission:
                permission = Permission(name=permission_name)
                self._session.add(permission)
                self._session.commit()
                added_permissions[permission_name] = permission
            else:
                added_permissions[permission_name] = existing_permission

        for app_name, interfaces in TABS_INFO.items():
            app = App(name=app_name)
            self._session.add(app)
            self._session.commit()

            for interface_name, _ in interfaces.items():
                interface = Interface(name=interface_name, app_id=app.id)
                self._session.add(interface)
                self._session.commit()

                for permission_name in PERMISSIONS:
                    permission = added_permissions[permission_name]
                    app.permissions.append(permission)
                    interface.permissions.append(permission)
                self._session.commit()

