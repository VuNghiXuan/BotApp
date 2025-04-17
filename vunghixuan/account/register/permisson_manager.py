    
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
import hashlib
from vunghixuan.settings import DATABASE_URL, TABS_INFO, PERMISSIONS
from vunghixuan.account.register.models import User, Roll, Permission, App, Group, Interface, Base, roll_permission_association, roll_app_association
import os
from collections import defaultdict
import logging
import logging.handlers  # Import mô-đun handlers
import traceback

class PermissionManager:
    """Quản lý quyền."""
    def __init__(self, session):
        """Khởi tạo PermissionManager với phiên làm việc cơ sở dữ liệu."""
        self._session = session

    def get_all_permissions(self):
        """Lấy danh sách tất cả các quyền."""
        return self._session.query(Permission).options(joinedload(Permission.rolls)).all()

    def add_permission(self, name, description=None):
        """Thêm quyền mới vào cơ sở dữ liệu."""
        if self._session.query(Permission).filter_by(name=name).first():
            logging.error(f"Quyền hạn {name} đã tồn tại.")
            return False
        permission = Permission(name=name, description=description)
        self._session.add(permission)
        self._session.commit()
        return True

    def get_permissions(self):
        """Lấy danh sách tất cả các quyền."""
        return self._session.query(Permission).all()

    def update_permission(self, permission_id, name=None, description=None):
        """Cập nhật thông tin quyền."""
        permission = self._session.get(Permission, permission_id)
        if permission:
            if name:
                permission.name = name
            if description:
                permission.description = description
            self._session.commit()
            return True
        return False

    def delete_permission(self, permission_id):
        """Xóa quyền khỏi cơ sở dữ liệu."""
        permission = self._session.get(Permission, permission_id)
        if permission:
            self._session.delete(permission)
            self._session.commit()
            return True
        return False

    def add_permission_to_interface(self, interface_id, permission_id):
        """Thêm quyền vào giao diện."""
        interface = self._session.get(Interface, interface_id)
        permission = self._session.get(Permission, permission_id)
        if interface and permission:
            if permission not in interface.permissions:
                interface.permissions.append(permission)
                self._session.commit()
                return True
            else:
                logging.error("Quyền hạn đã tồn tại trong giao diện này!")
                return False
        else:
            logging.error("Không tìm thấy giao diện hoặc quyền hạn!")
            return False

    def remove_permission_from_interface(self, interface_id, permission_id):
        """Xóa quyền khỏi giao diện."""
        interface = self._session.get(Interface, interface_id)
        permission = self._session.get(Permission, permission_id)
        if interface and permission and permission in interface.permissions:
            interface.permissions.remove(permission)
            self._session.commit()
            return True
        else:
            logging.error("Giao diện không có quyền hạn này hoặc không tìm thấy giao diện/quyền hạn!")
            return False

    def add_permission_to_app(self, app_id, permission_id):
        """Thêm quyền vào ứng dụng."""
        app = self._session.get(App, app_id)
        permission = self._session.get(Permission, permission_id)
        if app and permission:
            if permission not in app.permissions:
                app.permissions.append(permission)
                self._session.commit()
                return True
            else:
                logging.error("Quyền hạn đã tồn tại trong ứng dụng này!")
                return False
        else:
            logging.error("Không tìm thấy ứng dụng hoặc quyền hạn!")
            return False

    def remove_permission_from_app(self, app_id, permission_id):
        """Xóa quyền khỏi ứng dụng."""
        app = self._session.get(App, app_id)
        permission = self._session.get(Permission, permission_id)
        if app and permission and permission in app.permissions:
            app.permissions.remove(permission)
            self._session.commit()
            return True
        else:
            logging.error("Ứng dụng không có quyền hạn này hoặc không tìm thấy ứng dụng/quyền hạn!")
            return False

    def get_permissions_in_interface(self, interface_id):
        """Lấy danh sách các quyền của giao diện."""
        interface = self._session.get(Interface, interface_id)
        if interface:
            return interface.permissions
        return []

    def get_permissions_in_app(self, app_id):
        """Lấy danh sách các quyền của ứng dụng."""
        app = self._session.get(App, app_id)
        if app:
            return app.permissions
        return []

    def get_interfaces_with_permission(self, permission_id):
        """Lấy danh sách các giao diện có quyền."""
        permission = self._session.get(Permission, permission_id)
        if permission:
            return permission.interfaces
        return []

    def get_apps_with_permission(self, permission_id):
        """Lấy danh sách các ứng dụng có quyền."""
        permission = self._session.get(Permission, permission_id)
        if permission:
            return permission.apps
        return []

    def get_permissions_with_app(self, app_id):
        """Lấy danh sách các quyền của ứng dụng."""
        app = self._session.get(App, app_id)
        if app:
            return app.permissions
        return []

    def get_permissions_with_interface(self, interface_id):
        """Lấy danh sách các quyền của giao diện."""
        interface = self._session.get(Interface, interface_id)
        if interface:
            return interface.permissions
        return []

    def get_groups_with_permission(self, permission_id):
        """Lấy danh sách các nhóm có quyền."""
        permission = self._session.get(Permission, permission_id)
        if permission:
            groups = []
            for roll in permission.rolls:
                groups.extend(roll.groups)
            return list(set(groups))
        return []

