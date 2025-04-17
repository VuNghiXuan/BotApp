from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
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
)
import os
from collections import defaultdict
import logging
import logging.handlers  # Import mô-đun handlers
import traceback
from vunghixuan.account.register.log_manager import LoggingConfig
from vunghixuan.account.register.models import Roll
from sqlalchemy.orm import joinedload, make_transient
from sqlalchemy import select
from PySide6.QtWidgets import ( QMessageBox,)


logger = LoggingConfig.get_logger()


class GroupManager:
    """
    Quản lý nhóm người dùng trong hệ thống.

    Lớp này cung cấp các phương thức để thêm, lấy, cập nhật và xóa nhóm người dùng,
    cũng như quản lý các mối quan hệ giữa người dùng, nhóm và vai trò (roll).
    """

    def __init__(self, session):
        """
        Khởi tạo GroupManager với phiên làm việc cơ sở dữ liệu.

        Args:
            session (sqlalchemy.orm.session.Session): Phiên làm việc SQLAlchemy
                được sử dụng để tương tác với cơ sở dữ liệu.
        """
        self._session = session

    def add_group(self, name, description=None):
        """
        Thêm một nhóm mới vào cơ sở dữ liệu.

        Args:
            name (str): Tên của nhóm mới.
            description (str, optional): Mô tả cho nhóm. Mặc định là None.

        Returns:
            bool: True nếu nhóm được thêm thành công, False nếu nhóm đã tồn tại.
        """
        if self._session.query(Group).filter_by(name=name).first():
            logger.error(f"Nhóm {name} đã tồn tại.")  # Ghi log lỗi
            return False
        group = Group(name=name, description=description)
        self._session.add(group)
        self._session.commit()
        return True

    def get_groups(self):
        """
        Lấy danh sách tất cả các nhóm từ cơ sở dữ liệu.

        Returns:
            list[Group]: Danh sách các đối tượng Group đại diện cho tất cả các nhóm.
        """
        return self._session.query(Group).all()

    def update_group(self, group_id, name=None, description=None):
        """
        Cập nhật thông tin của một nhóm.

        Args:
            group_id (int): ID của nhóm cần cập nhật.
            name (str, optional): Tên mới cho nhóm. Mặc định là None (không thay đổi).
            description (str, optional): Mô tả mới cho nhóm. Mặc định là None (không thay đổi).

        Returns:
            bool: True nếu nhóm được cập nhật thành công, False nếu không tìm thấy nhóm.
        """
        group = self._session.get(Group, group_id)
        if group:
            if name:
                group.name = name
            if description:
                group.description = description
            self._session.commit()
            return True
        else:
            logger.error(f"Không tìm thấy nhóm có ID {group_id}")  # Ghi log lỗi
            return False

    def delete_group(self, group_id, group_description=None):
        """
        Xóa một nhóm khỏi cơ sở dữ liệu.

        Args:
            group_id (int): ID của nhóm cần xóa.
            group_description (str, optional): Mô tả của nhóm.  Mặc định là None

        Returns:
            bool: True nếu nhóm được xóa thành công, False nếu không tìm thấy nhóm
                  hoặc nếu nhóm có người dùng liên quan.
        """
        try:
            group = self._session.get(Group, group_id)
            if group:
                # Check if the group has any associated users.
                if self.is_group_assigned_to_users(group_id):
                    logger.error(
                        f"Không thể xóa nhóm có ID {group_id} vì có người dùng đang thuộc nhóm này."
                    )
                    return False  # Return False to indicate deletion failure

                # Delete the group's relationships with rolls
                group.rolls = []
                group_name = group.name
                self._session.delete(group)
                self._session.commit()
                logger.info(f"Đã xóa nhóm có ID {group_id}")
                return group_name
            else:
                logger.error(f"Không tìm thấy nhóm có ID {group_id}")
                return False
        except Exception as e:
            error_message = f"Lỗi khi xóa nhóm có ID {group_id}: {e}\n"
            error_message += traceback.format_exc()
            logger.error(error_message)
            self._session.rollback()
            return False

    def add_user_to_group(self, user_id, group_id, group_description=None):
        """
        Thêm một người dùng vào một nhóm.

        Args:
            user_id (int): ID của người dùng cần thêm vào nhóm.
            group_id (int): ID của nhóm mà người dùng sẽ được thêm vào.
            group_description: (str, optional): Mô tả nhóm. Mặc định là None

        Returns:
            bool: True nếu người dùng được thêm vào nhóm thành công, False nếu
                  không tìm thấy người dùng hoặc nhóm, hoặc nếu người dùng đã ở trong nhóm.
        """
        user = self._session.get(User, user_id)
        group = self._session.get(Group, group_id)
        if user and group:
            if group not in user.groups:
                user.groups.append(group)
                self._session.commit()
                return True
            else:
                logger.error("Người dùng đã thuộc nhóm này!")  # Ghi log lỗi
                return False
        else:
            logger.error("Không tìm thấy người dùng hoặc nhóm!")  # Ghi log lỗi
            return False

    def remove_user_from_group(self, user_id, group_id, group_description=None):
        """
        Xóa một người dùng khỏi một nhóm.

        Args:
            user_id (int): ID của người dùng cần xóa khỏi nhóm.
            group_id (int): ID của nhóm mà người dùng sẽ bị xóa khỏi.
            group_description: (str, optional): Mô tả nhóm. Mặc định là None

        Returns:
            bool: True nếu người dùng được xóa khỏi nhóm thành công, False nếu
                  không tìm thấy người dùng hoặc nhóm, hoặc nếu người dùng không ở trong nhóm.
        """
        user = self._session.get(User, user_id)
        group = self._session.get(Group, group_id)
        if user and group and group in user.groups:
            user.groups.remove(group)
            self._session.commit()
            QMessageBox.information(
                    self, "Thành công", "Nhóm quyền đã được tạo thành công."
                )
            return True
        else:
            logger.error(
                "Người dùng không thuộc nhóm này hoặc không tìm thấy người dùng/nhóm!"
            )  # Ghi log lỗi
            return False

    def get_rolls_in_group(self, group_id, group_description=None):
        """
        Lấy danh sách các vai trò (roll) của một nhóm.

        Args:
            group_id (int): ID của nhóm.
            group_description: (str, optional): Mô tả nhóm. Mặc định là None

        Returns:
            list[Roll]: Danh sách các đối tượng Roll thuộc về nhóm. Trả về list rỗng nếu không tìm thấy nhóm.
        """
        group = self._session.get(Group, group_id)
        if group:
            return group.rolls
        else:
            logger.error(f"Không tìm thấy nhóm có ID {group_id}")  # Ghi log
            return []

    def get_groups_with_permission(self, permission_id, group_description=None):
        """
        Lấy danh sách các nhóm có một quyền cụ thể.

        Args:
            permission_id (int): ID của quyền.
            group_description: (str, optional): Mô tả nhóm. Mặc định là None

        Returns:
            list[Group]: Danh sách các đối tượng Group có quyền được chỉ định.
        """
        permission = self._session.get(Permission, permission_id)
        if permission:
            groups = []
            for roll in permission.rolls:
                groups.extend(roll.groups)
            return list(set(groups))
        else:
            logger.error(f"Không tìm thấy quyền có ID {permission_id}")  # Ghi log
            return []

    def get_groups_with_roll(self, roll_id, group_description=None):
        """
        Lấy danh sách các nhóm có một vai trò (roll) cụ thể.

        Args:
            roll_id (int): ID của vai trò (roll).
            group_description: (str, optional): Mô tả nhóm. Mặc định là None

        Returns:
            list[Group]: Danh sách các đối tượng Group có vai trò (roll) được chỉ định.
        """
        roll = self._session.get(Roll, roll_id)
        if roll:
            return roll.groups
        else:
            logger.error(f"Không tìm thấy roll có ID {roll_id}")  # Ghi log
            return []

    def add_group_with_rolls(self, group_name, roll_ids, group_description=None):
        """
        Thêm một nhóm mới (hoặc thêm vào nhóm đã tồn tại) và gán các vai trò cho nhóm đó.

        Args:
            group_name (str): Tên của nhóm.
            roll_ids (list[int]): Danh sách ID của các vai trò cần thêm vào nhóm.
            group_description (str, optional): Mô tả cho nhóm. Mặc định là None.

        Returns:
            bool: True nếu thành công, False nếu có lỗi.
        """
        try:
            # Fetch group first
            group = self._session.query(Group).filter_by(name=group_name).first()
            if not group:
                group = Group(name=group_name, description=group_description)
                self._session.add(group)
            
            # Fetch rolls in one query
            rolls = self._session.query(Roll).filter(Roll.id.in_(roll_ids)).all()
            
            if len(rolls) != len(roll_ids):
                logger.error(f"Not all rolls found. Expected {len(roll_ids)}, got {len(rolls)}")
                self._session.rollback()
                return False

            # Use set to optimize adding rolls.  Avoids duplicates.
            group.rolls.extend(rolls)
            self._session.commit()
            return True
        except Exception as e:
            error_message = (
                f"Lỗi khi thêm vai trò vào nhóm (group_name={group_name}, roll_ids={roll_ids}, group_description={group_description}): {e}\n"
            )
            error_message += traceback.format_exc()
            logger.error(error_message)
            self._session.rollback()  # Rollback giao dịch để tránh dữ liệu không nhất quán
            return False  # Trả về False để chỉ ra rằng đã có lỗi xảy ra

    def is_group_assigned_to_users(self, group_id, group_description=None):
        """Check if a group is assigned to any users."""
        group = self._session.get(Group, group_id)
        if not group:
            return False  # Group doesn't exist
        return len(group.users) > 0
