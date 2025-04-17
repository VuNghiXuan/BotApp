from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker, joinedload, contains_eager
from sqlalchemy.orm.exc import NoResultFound
import hashlib
from vunghixuan.settings import DATABASE_URL, TABS_INFO, PERMISSIONS
from vunghixuan.account.register.models import (
    User,
    Roll,
    Permission,
    App,
    Group,
    Interface,
    Base,
    roll_permission_association,
    roll_app_association,
)
import os
from collections import defaultdict
import logging
import logging.handlers  # Import mô-đun handlers
import traceback
from vunghixuan.account.register.log_manager import LoggingConfig
from typing import List, Optional, Tuple, Union
from sqlalchemy.exc import SQLAlchemyError

# Khởi tạo logger từ LoggingConfig
logmanager = LoggingConfig.get_logger()


class RollManager:
    """Quản lý vai trò."""

    def __init__(self, session: sessionmaker):
        """Khởi tạo RollManager với phiên làm việc cơ sở dữ liệu."""
        self.session = session

    def _log_error(self, message: str, exc: Exception) -> None:
        """
        Log một lỗi với thông tin chi tiết.

        Args:
            message: Thông điệp lỗi.
            exc: Đối tượng Exception.
        """
        logmanager.error(f"{message}: {exc}\n{traceback.format_exc()}")

    def get_rolls(self) -> List[Roll]:
        """
        Lấy tất cả các role từ database.
        """
        try:
            # Sử dụng self.session thay vì self._session
            roles = self.session.query(Roll).all()
            return roles
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy danh sách role", e)
            return []

    def get_role_by_id(self, roll_id: int) -> Optional[Roll]:
        """
        Lấy một role theo ID.

        Args:
            roll_id: ID của role cần lấy.

        Returns:
            Roll object nếu tìm thấy, None nếu không.
        """
        try:
            # Sử dụng self.session thay vì self._session
            role = self.session.query(Roll).filter(Roll.id == roll_id).one_or_none()
            return role
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy role theo ID", e)
            return None

    def get_roles_by_group_id(self, group_id: int) -> List[Roll]:
        """
        Lấy danh sách các role thuộc một group cụ thể.

        Args:
            group_id: ID của group.

        Returns:
            Danh sách các Roll object thuộc group đó.
        """
        try:
            # Sử dụng eager loading để tối ưu hóa truy vấn
            group = (
                self.session.query(Group)
                .options(joinedload(Group.roles))  # Eager load roles
                .filter(Group.id == group_id)
                .one_or_none()
            )
            if group:
                return group.roles
            else:
                return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy các role của group", e)
            return []

    def get_all_rolls(self) -> List[Roll]:
        """Lấy danh sách tất cả các vai trò."""
        try:
            # Sử dụng self.session thay vì self._session
            return self.session.query(Roll).all()
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy danh sách vai trò", e)
            return []

    def add_roll_with_permissions(
        self, roll_name: str, selected_permissions_data: List[Tuple[str, int]]
    ) -> bool:
        """Thêm vai trò mới cùng với các quyền và ứng dụng."""
        try:
            if not roll_name:
                logmanager.error("Tên vai trò không được để trống.")
                return False

            if self._check_existing_roll(roll_name):
                logmanager.error(f"Vai trò '{roll_name}' đã tồn tại.")
                return False

            new_roll = Roll(name=roll_name)
            self.session.add(new_roll)
            self.session.flush()  # Flush để có ID của new_roll

            for permission_name, interface_id in selected_permissions_data:  # Unpack tuple
                # Lấy permission và interface
                permission = self.session.query(Permission).filter_by(
                    name=permission_name
                ).one_or_none()
                interface = self.session.get(Interface, interface_id)  # Dùng get cho nhanh
                if permission and interface:
                    # Thêm vào bảng trung gian roll_permission
                    self.session.execute(
                        roll_permission_association.insert().values(
                            roll_id=new_roll.id,
                            permission_id=permission.id,
                            interface_id=interface.id,  # Thêm interface
                        )
                    )

                    # Thêm vào bảng trung gian roll_app (nếu có)
                    if interface.app_id:
                        self.session.execute(
                            roll_app_association.insert().values(
                                roll_id=new_roll.id, app_id=interface.app_id
                            )
                        )

            self.session.commit()
            logmanager.info(f"Đã thêm vai trò '{roll_name}' thành công.")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi thêm vai trò", e)
            return False

    def _check_existing_roll(self, roll_name: str) -> bool:
        """Kiểm tra xem vai trò đã tồn tại trong cơ sở dữ liệu hay không."""
        return (
            self.session.query(Roll).filter_by(name=roll_name).one_or_none()
            is not None
        )

    def update_roll(
        self, roll_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> bool:
        """Cập nhật thông tin vai trò."""
        try:
            roll = self.session.get(Roll, roll_id)
            if roll:
                if name:
                    roll.name = name
                if description:
                    roll.description = description
                self.session.commit()
                logmanager.info(f"Đã cập nhật vai trò '{roll.name}' thành công.")
                return True
            logmanager.warning(f"Không tìm thấy vai trò có ID '{roll_id}'.")
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi cập nhật vai trò", e)
            return False

    def delete_roll(self, roll_id: int) -> bool:
        """Xóa vai trò khỏi cơ sở dữ liệu."""
        try:
            roll = self.session.get(Roll, roll_id)
            if roll:
                if self.is_roll_assigned_to_users(roll_id):  # Kiểm tra xem vai trò có người dùng nào chưa
                    logmanager.error(
                        f"Không thể xóa vai trò '{roll.name}' vì nó đã được gán cho người dùng."
                    )
                    return False

                # Xóa các liên kết trong bảng trung gian.  Sử dụng delete và commit ở cuối.
                self.session.query(roll_app_association).filter_by(
                    roll_id=roll_id
                ).delete()
                self.session.query(roll_permission_association).filter_by(
                    roll_id=roll_id
                ).delete()

                self.session.delete(roll)
                self.session.commit()
                logmanager.info(f"Đã xóa vai trò có ID '{roll_id}' thành công.")
                return True
            logmanager.warning(f"Không tìm thấy vai trò có ID '{roll_id}'.")
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi xóa vai trò", e)
            return False

    def is_roll_assigned_to_users(self, roll_id: int) -> bool:
        """Kiểm tra xem vai trò có được gán cho người dùng nào không."""
        return (
            self.session.query(User).filter(User.rolls.any(Roll.id == roll_id)).count()
            > 0
        )

    def is_roll_assigned_to_groups(self, roll_id: int) -> bool:
        """Kiểm tra xem vai trò có được gán cho nhóm nào không."""
        return (
            self.session.query(Group).filter(Group.rolls.any(Roll.id == roll_id)).count()
            > 0
        )

    def add_roll_to_group(self, group_id: int, roll_id: int) -> bool:
        """Thêm vai trò vào nhóm."""
        try:
            group = self.session.get(Group, group_id)
            roll = self.session.get(Roll, roll_id)
            if group and roll:
                if roll not in group.rolls:
                    group.rolls.append(roll)
                    self.session.commit()
                    logmanager.info(
                        f"Đã thêm vai trò '{roll.name}' vào nhóm '{group.name}' thành công."
                    )
                    return True
                else:
                    logmanager.warning(
                        f"Nhóm '{group.name}' đã có vai trò '{roll.name}'."
                    )
                    return False
            else:
                logmanager.error("Không tìm thấy nhóm hoặc vai trò!")
                return False
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi thêm vai trò vào nhóm", e)
            return False

    def remove_roll_from_group(self, group_id: int, roll_id: int) -> bool:
        """Xóa vai trò khỏi nhóm."""
        try:
            group = self.session.get(Group, group_id)
            roll = self.session.get(Roll, roll_id)
            if group and roll and roll in group.rolls:
                group.rolls.remove(roll)
                self.session.commit()
                logmanager.info(
                    f"Đã xóa vai trò '{roll.name}' khỏi nhóm '{group.name}' thành công."
                )
                return True
            else:
                logmanager.error(
                    "Nhóm không có vai trò này hoặc không tìm thấy nhóm/vai trò!"
                )
                return False
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi xóa vai trò khỏi nhóm", e)
            return False

    def remove_roll_from_all_users(self, roll_id: int) -> None:
        """Xóa vai trò khỏi tất cả người dùng."""
        try:
            roll = self.session.get(Roll, roll_id)  # Lấy đối tượng Roll
            if roll:
                # Sử dụng mối quan hệ `users` để xóa vai trò khỏi người dùng một cách hiệu quả
                for user in roll.users:
                    user.rolls.remove(roll)
                self.session.commit()
                logmanager.info(
                    f"Đã xóa vai trò có ID '{roll_id}' khỏi tất cả người dùng."
                )
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi xóa vai trò khỏi người dùng", e)
            raise  # Re-raise để thông báo cho hàm gọi biết lỗi

    def remove_roll_from_all_groups(self, roll_id: int) -> None:
        """Xóa vai trò khỏi tất cả các nhóm."""
        try:
            roll = self.session.get(Roll, roll_id)  # Lấy đối tượng Roll
            if roll:
                # Sử dụng mối quan hệ `groups` để xóa vai trò khỏi nhóm một cách hiệu quả
                for group in roll.groups:
                    group.rolls.remove(roll)
                self.session.commit()
                logmanager.info(f"Đã xóa vai trò có ID '{roll_id}' khỏi tất cả các nhóm.")
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi xóa vai trò khỏi các nhóm", e)
            raise  # Re-raise để thông báo cho hàm gọi biết lỗi

    def remove_roll_permissions(self, roll_id: int) -> None:
        """Xóa tất cả các quyền của một vai trò."""
        try:
            # Sử dụng trực tiếp câu lệnh delete để xóa các bản ghi trong bảng liên kết
            self.session.execute(
                roll_permission_association.delete().where(
                    roll_permission_association.c.roll_id == roll_id
                )
            )
            self.session.commit()
            logmanager.info(f"Đã xóa tất cả các quyền của vai trò có ID '{roll_id}'.")
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi xóa các quyền của vai trò", e)
            raise

    def remove_roll_apps(self, roll_id: int) -> None:
        """Xóa tất cả các ứng dụng của một vai trò."""
        try:
            # Sử dụng trực tiếp câu lệnh delete để xóa các bản ghi trong bảng liên kết
            self.session.execute(
                roll_app_association.delete().where(
                    roll_app_association.c.roll_id == roll_id
                )
            )
            self.session.commit()
            logmanager.info(f"Đã xóa tất cả các ứng dụng của vai trò có ID '{roll_id}'.")
        except SQLAlchemyError as e:
            self.session.rollback()
            self._log_error("Lỗi khi xóa các ứng dụng của vai trò", e)
            raise

    def get_groups_with_roll(self, roll_id: int) -> List[Group]:
        """Lấy danh sách các nhóm có vai trò."""
        try:
            roll = self.session.get(Roll, roll_id)
            if roll:
                return roll.groups  # Truy cập trực tiếp qua relationship
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy danh sách nhóm có vai trò", e)
            return []

    def get_permissions_with_roll(self, roll_id: int) -> List[Permission]:
        """Lấy danh sách các quyền của vai trò."""
        try:
            roll = self.session.get(Roll, roll_id)
            if roll:
                return roll.permissions  # Truy cập trực tiếp qua relationship
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy danh sách quyền của vai trò", e)
            return []

    def get_rolls_with_permission(self, permission_id: int) -> List[Roll]:
        """Lấy danh sách các vai trò có quyền."""
        try:
            permission = self.session.get(Permission, permission_id)
            if permission:
                return permission.rolls  # Truy cập trực tiếp qua relationship
            return []
        except SQLAlchemyError as e:
            self._log_error("Lỗi khi lấy danh sách vai trò có quyền", e)
            return []
