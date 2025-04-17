# -*- coding: utf-8 -*-
# add_new_roll_per_form.py


from PySide6.QtGui import Qt, QFont
from PySide6.QtCore import Signal, Slot

from sqlalchemy import create_engine, func, select, and_, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
import os
from collections import defaultdict
import logging
import logging.handlers  # Import mô-đun handlers
import traceback
import hashlib
from typing import List, Optional, Dict, Union

# Assuming these are in the same file or you have correct import paths
from vunghixuan.account.register.models import (
    User,
    Roll,
    Permission,
    App,
    Group,
    Interface,
    Base,
    roll_permission_association,
    roll_app_association # Import thêm roll_app_association
)
from vunghixuan.settings import DATABASE_URL  # Assuming this is available
from vunghixuan.account.register.permisson_manager import PermissionManager
from vunghixuan.account.register.models import user_roll_association


        
class UserManager:
    """Quản lý người dùng."""

    def __init__(self, session: sessionmaker):
        """Khởi tạo UserManager với phiên làm việc cơ sở dữ liệu."""
        self.session = session  # Đổi tên thành self.session
        self.permission_manager = PermissionManager(session) # Thêm PermissionManager

    def _log_error(self, message: str, exc: Exception) -> None:
        """
        Log một lỗi với thông tin chi tiết.

        Args:
            message: Thông điệp lỗi.
            exc: Đối tượng Exception.
        """
        logging.error(f"{message}: {exc}\n{traceback.format_exc()}")

    def add_user(
        self,
        username: str,
        password: str,
        re_password: str,
        group_ids: List[int],
        roll_ids: Optional[List[int]] = None,
    ) -> bool:
        """
        Thêm người dùng mới vào database.
        """
        if password != re_password:
            raise ValueError("Mật khẩu và xác nhận mật khẩu không khớp.")

        if self._check_existing_user(username):
            raise ValueError("Tên người dùng đã tồn tại.")

        try:
            # Mã hóa mật khẩu trước khi lưu
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            new_user = User(username=username, password=hashed_password)
            self.session.add(new_user)

            # Lấy groups và rolls bằng một truy vấn duy nhất
            groups = self.session.query(Group).filter(Group.id.in_(group_ids)).all()
            if len(groups) != len(group_ids):
                self.session.rollback()
                raise ValueError("Một hoặc nhiều Group không tồn tại")
            new_user.groups.extend(groups)  # Thêm groups

            if roll_ids:
                rolls = self.session.query(Roll).filter(Roll.id.in_(roll_ids)).all()
                if len(rolls) != len(roll_ids):
                    self.session.rollback()
                    raise ValueError("Một hoặc nhiều Roll không tồn tại")
                new_user.rolls.extend(rolls)  # Thêm rolls

            self.session.commit()
            return True
        except (ValueError, SQLAlchemyError) as e:
            self.session.rollback()
            self._log_error("Lỗi khi thêm người dùng", e)
            return False

    def _validate_input(self, username: str, password: str, re_password: str) -> bool:
        """Kiểm tra tính hợp lệ của dữ liệu đầu vào."""
        if not username or not password or not re_password:
            logging.error("Tên, Mật khẩu, hoặc Xác thực chưa được nhập đầy đủ")
            return False
        if password != re_password:
            logging.error("Mật khẩu và Xác thực không khớp")
            return False
        return True

    def _check_existing_user(self, username: str) -> bool:
        """Kiểm tra xem người dùng đã tồn tại trong cơ sở dữ liệu hay không."""
        return (
            self.session.query(User).filter_by(username=username).one_or_none()
            is not None
        )

    def verify_user(self, username: str, password: str) -> bool:
        """Xác minh thông tin đăng nhập người dùng."""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return (
            self.session.query(User)
            .filter_by(username=username, password=hashed_password)
            .one_or_none()
            is not None
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Lấy thông tin người dùng theo tên người dùng."""
        try:
            return (
                self.session.query(User).filter_by(username=username).one_or_none()
            )
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy thông tin người dùng", e)
            return None
        
    def get_user_permissions(
        self, username: str
    ) -> Optional[Dict[str, List[Dict[str, Union[int, str]]]]]:
        """Lấy danh sách quyền của người dùng theo tên người dùng."""
        try:
            user = self.session.query(User).filter_by(username=username).one_or_none()
            if not user:
                return None

            app_permissions = defaultdict(list)

            # Lấy thông tin quyền một cách rõ ràng
            for group in user.groups:
                for roll in group.rolls:
                    # Fetch permissions for each roll
                    permissions = self.session.query(Permission).join(
                        roll_permission_association
                    ).filter(roll_permission_association.c.roll_id == roll.id).all()

                    for permission in permissions:
                        app_permissions[permission.name].append(
                            {"id": permission.id, "name": permission.name}
                        )
            return dict(app_permissions)
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy quyền của người dùng", e)
            return None

    def get_all_users_with_rolls_and_permissions(
        self,
    ) -> List[Dict[str, List[Dict[str, List[Dict[str, str]]]]]]:
        """Lấy danh sách tất cả người dùng cùng với vai trò và quyền của họ."""
        try:
            users = self.session.query(User).all()
            user_data = []
            for user in users:
                user_info = {"username": user.username, "rolls": []}
                for group in user.groups:
                    for roll in group.rolls:
                        # Fetch permissions for each roll.
                        permissions = self.session.query(Permission).join(
                            roll_permission_association
                        ).filter(roll_permission_association.c.roll_id == roll.id).all()
                        roll_info = {"name": roll.name, "permissions": []}
                        for permission in permissions:
                            roll_info["permissions"].append(
                                {"name": permission.name, "roll_id": roll.id}
                            )
                        user_info["rolls"].append(roll_info)
                user_data.append(user_info)
            return user_data
        except SQLAlchemyError as e:
            self._log_error(
                "Lỗi khi lấy thông tin người dùng, vai trò và quyền", e
            )
            return []
    
    def get_users_in_group(self, group_id: int) -> List[User]:
        """Lấy danh sách người dùng thuộc nhóm theo ID nhóm."""
        try:
            group = self.session.query(Group).filter(Group.id == group_id).one_or_none()
            if group:
                return group.users
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy người dùng trong nhóm", e)
            return []
        
    def get_users_with_permission(self, permission_id: int) -> List[User]:
        """Lấy danh sách người dùng có quyền theo ID quyền."""
        try:
            permission = self.session.query(Permission).filter(Permission.id == permission_id).one_or_none()
            if permission:
                users = set()
                # Lấy danh sách các roll có quyền này
                rolls = self.session.query(Roll).join(roll_permission_association).filter(roll_permission_association.c.permission_id == permission.id).all()
                for roll in rolls:
                  # Lấy danh sách user của từng roll
                  users.update(roll.users)
                return list(users)
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy người dùng có quyền", e)
            return []
    
    def get_users_in_app(self, app_id: int) -> List[User]:
        """Lấy danh sách người dùng có quyền trong ứng dụng theo ID ứng dụng."""
        try:
            app = self.session.query(App).filter(App.id == app_id).one_or_none()
            if app:
                users = set()
                # Lấy danh sách các roll liên kết với app qua bảng trung gian roll_app_association
                rolls = self.session.query(Roll).join(roll_app_association).filter(roll_app_association.c.app_id == app.id).all()
                for roll in rolls:
                    users.update(roll.users)
                return list(users)
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy người dùng trong ứng dụng", e)
            return []

    def get_users_in_interface(self, interface_id: int) -> List[User]:
        """Lấy danh sách người dùng có quyền trong giao diện theo ID giao diện."""
        try:
            interface = self.session.query(Interface).filter(Interface.id == interface_id).one_or_none()
            if interface:
                users = set()
                permissions = self.session.query(Permission).filter(Permission.interface_id == interface.id).all()
                for permission in permissions:
                  rolls = self.session.query(Roll).join(roll_permission_association).filter(roll_permission_association.c.permission_id == permission.id).all()
                  for roll in rolls:
                    users.update(roll.users)
                return list(users)
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy người dùng trong giao diện", e)
            return []
    
    def get_users_with_group(self, group_id: int) -> List[User]:
        """Lấy danh sách người dùng thuộc nhóm theo ID nhóm."""
        try:
            group = self.session.get(Group, group_id)
            if group:
                return group.users
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy người dùng với nhóm", e)
            return []

    def get_users_with_roll(self, roll_id: int) -> List[User]:
        """Lấy danh sách người dùng có vai trò theo ID vai trò."""
        try:
            roll = self.session.query(Roll).filter(Roll.id == roll_id).one_or_none()
            if roll:
                return roll.users
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy người dùng với vai trò", e)
            return []
    


    def delete_user(self, username: str) -> bool:
        try:
            user_to_delete = self.session.query(User).filter(User.username == username).first()
            if not user_to_delete:
                raise ValueError(f"Không tìm thấy người dùng với username: {username}")

            user_to_delete.groups.clear()
            
            # print(f"Với cột user_id là: {user_roll_association.c.user_id.name}")
            # print(f"ID người dùng cần xóa: {user_to_delete.id}")
            # count = self.session.query(user_roll_association).filter(user_roll_association.c.user_id == user_to_delete.id).count()
            # print(f"Số lượng liên kết vai trò tìm thấy: {count}")
            self.session.execute(
                delete(user_roll_association).where(
                    user_roll_association.c.user_id == user_to_delete.id
                )
            )

            self.session.delete(user_to_delete)
            self.session.commit()
            return True

        except (ValueError, SQLAlchemyError) as e:
            self.session.rollback()
            self._log_error(f"Lỗi khi xóa người dùng {username}", e)
            return False
        
    'Đoạn này lấy thông tin users và các apps, interfaces permissons ----------------'
    # Lấy group từ user
    def get_groups_data(self, user):
        groups_data = []
        for group in user.groups:
            # print (f'Tên Group là: {group.name}. Mô tả nhóm:{group.description}')            
            group_data = {
                "name": group.name,
                "description": group.description, 
                "rolls": [],               
            }
            rolls_data = self.get_rolls_data(group)

            group_data['rolls'].append(rolls_data)

            # print('Group trước thêm', group_data)
            groups_data.append(group_data)
            # print('Group sau thêm', group_data)

        return groups_data

   
    # Lấy roll từ group
    def get_rolls_data(self, group):
        rolls_data = []
        for roll in group.rolls:
            roll_data = {
                "name": roll.name,
                "apps": [app.name for app in roll.apps],
                "interfaces": [],
            }
            interfaces_data = self.get_interfaces_data(roll)
            roll_data['interfaces'].extend(interfaces_data)  # Sử dụng extend để thêm danh sách interfaces
                       
            
            
            rolls_data.append(roll_data)
        return rolls_data

    
    

    # Lấy Interfaces từ roll
    def get_interfaces_data(self, roll):
        interfaces_data = []
        seen_interface_names = set()

        # 1. Lấy tất cả các interface ID liên quan đến roll cụ thể từ bảng roll_permission_association.
        interface_ids_query = select(roll_permission_association.c.interface_id).where(
            roll_permission_association.c.roll_id == roll.id
        )
        interface_ids = [
            interface_id for (interface_id,) in self.session.execute(interface_ids_query)
        ]

        if not interface_ids:
            return []  # Nếu không có interface nào liên quan đến roll, trả về danh sách rỗng

        # 2. Lấy các interface từ bảng Interface dựa trên các ID đã lấy ở trên.
        interfaces_query = select(Interface).where(Interface.id.in_(interface_ids))
        interfaces = self.session.execute(interfaces_query).scalars().all()

        # 3. Lấy tất cả các bản ghi permission NAME liên quan ĐẾN ROLL CỤ THỂ và các interface đã lấy
        permission_query = select(roll_permission_association.c.interface_id, Permission.name).join(
            Permission, roll_permission_association.c.permission_id == Permission.id
        ).where(
            (roll_permission_association.c.interface_id.in_(interface_ids)) &
            (roll_permission_association.c.roll_id == roll.id)  # Thêm điều kiện lọc theo roll_id
        )

        permissions_result = self.session.execute(permission_query).all()
        # Tạo một dictionary để lưu trữ permissions cho mỗi interface_id
        interface_permissions = {}
        for interface_id, permission_name in permissions_result:
            if interface_id not in interface_permissions:
                interface_permissions[interface_id] = [permission_name]
            else:
                interface_permissions[interface_id].append(permission_name)

        for interface in interfaces:
            interface_name = interface.name
            # Lấy danh sách permission_name từ dictionary
            permissions_data = interface_permissions.get(interface.id, [])

            if interface_name not in seen_interface_names:
                interface_data = {
                    "name": interface_name,
                    "permissions": permissions_data,
                }
                interfaces_data.append(interface_data)
                seen_interface_names.add(interface_name)
            else:
                # Nếu interface name đã tồn tại, tìm interface trước đó và cập nhật permissions
                for existing_interface in interfaces_data:
                    if existing_interface["name"] == interface_name:
                        existing_permissions = set(existing_interface["permissions"])
                        for permission_name in permissions_data:
                            if permission_name not in existing_permissions:
                                existing_interface["permissions"].append(
                                    permission_name
                                )
                                existing_permissions.add(permission_name)
                        break  # Đã cập nhật, không cần tìm tiếp
        return interfaces_data
   
   
    # Lấy thông tin truy cập của tất cả người dùng
    def get_all_users_with_details(self) :
        
        try:
            users = self.session.query(User).all()
           
            users_data = []
            for user in users:
                # print (f'Tên User là: {user.username}')
                user_data = {
                    "username": user.username,
                    "groups": [],
                }

                # group_data = self.get_groups_data(user)
                groups_data = self.get_groups_data(user)
                user_data["groups"].append(groups_data)
                users_data.append(user_data)

            return users_data
        except SQLAlchemyError as e:
            print(f"Lỗi khi lấy chi tiết tất cả người dùng: {e}")
            return []


                        
                        


    def convert_users_data_for_table(self, users_data):
        """
        Chuyển đổi dữ liệu người dùng từ định dạng chi tiết sang định dạng phù hợp với QTableWidget.
        """
        table_data = []

        for user in users_data:
            groups_data = []

            for groups in user["groups"]:
                rolls_data = []

                for group in groups:
                    for rolls in group["rolls"]:
                        apps_data = []
                        for roll in rolls:
                            apps_data.extend(roll['apps'])
                            interfaces_data = []
                            for interface in roll["interfaces"]:
                                face_per = f"{interface['name']} ({', '.join(interface.get('permissions', ['No Permissions']))})"
                                interfaces_data.append(face_per)

                            rolls_data.append(
                                f"{roll['name']} "
                            )

                    groups_data.append(
                        f"{group['name']} "#(Roles: {', '.join(rolls_data)})
                    )

            user_data = {
                "Tên người dùng (Users)": user["username"],
                "Thuộc nhóm (Groups)": ", ".join(groups_data),
                "Vai trò / Nhóm quyền (Rolls)": ", ".join(rolls_data),
                "Các ứng dụng (Apps)": ", ".join(apps_data),
                "Giao diện (Interfaces)": ", ".join(interfaces_data),
            }

            table_data.append(user_data)

        return table_data


    # Hàm lấy thông tin tên app, interface và quyền của một user dựa trên username
    def get_user_access_info(self, username: str):
        try:
            user = self.session.query(User).filter(User.username == username).first()
            if not user:
                return f"Không tìm thấy người dùng với username: {username}"

            groups_data = self.get_groups_data(user)
            user_access_info = {
                "username": user.username,
                "apps": set(),
                "interfaces": [],
                "permissions": set()
            }

            for group_info in groups_data:
                for rolls_info in group_info['rolls']:
                    for roll_info in rolls_info:
                        user_access_info["apps"].update(roll_info['apps'])
                        for interface_info in roll_info['interfaces']:
                            user_access_info["interfaces"].append({
                                "name": interface_info["name"],
                                "permissions": interface_info["permissions"]
                            })
                            user_access_info["permissions"].update(interface_info["permissions"])

            return {
                "username": user_access_info["username"],
                "apps": list(user_access_info["apps"]),
                "interfaces": user_access_info["interfaces"],
                # "permissions": list(user_access_info["permissions"])
            }

        except Exception as e:
            return f"Lỗi khi lấy thông tin truy cập của người dùng {username}: {e}"
