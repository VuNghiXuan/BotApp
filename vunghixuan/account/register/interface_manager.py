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
from vunghixuan.account.register.log_manager import LoggingConfig   

class InterfaceManager:
    """Quản lý giao diện."""
    def __init__(self, session):
        """Khởi tạo InterfaceManager với phiên làm việc cơ sở dữ liệu."""
        self._session = session

    def add_interface(self, name, app_id, description=None):
        """Thêm giao diện mới vào cơ sở dữ liệu."""
        if self._session.query(Interface).filter_by(name=name, app_id=app_id).first():
            logging.error(f"Giao diện {name} đã tồn tại trong ứng dụng {app_id}.")
            return False
        interface = Interface(name=name, app_id=app_id, description=description)
        self._session.add(interface)
        self._session.commit()
        return True

    def get_interfaces(self):
        """Lấy danh sách tất cả các giao diện."""
        return self._session.query(Interface).all()

    def update_interface(self, interface_id, name=None, app_id=None, description=None):
        """Cập nhật thông tin giao diện."""
        interface = self._session.get(Interface, interface_id)
        if interface:
            if name:
                interface.name = name
            if app_id:
                interface.app_id = app_id
            if description:
                interface.description = description
            self._session.commit()
            return True
        return False

    def delete_interface(self, interface_id):
        """Xóa giao diện khỏi cơ sở dữ liệu."""
        interface = self._session.get(Interface, interface_id)
        if interface:
            self._session.delete(interface)
            self._session.commit()
            return True
        return False

    def get_permissions_in_interface(self, interface_id):
        """Lấy danh sách các quyền của giao diện."""
        interface = self._session.get(Interface, interface_id)
        if interface:
            return interface.permissions
        return []

    def get_interfaces_with_permission(self, permission_id):
        """Lấy danh sách các giao diện có quyền."""
        permission = self._session.get(Permission, permission_id)
        if permission:
            return permission.interfaces
        return []
    
