# models_manage.py

from sqlalchemy import exists
# from vunghixuan.account.register.user_manager import User
from vunghixuan.account.register.models import User


class ModelsManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager

    def check_any_user_exists(self):
        """Kiểm tra xem có bất kỳ người dùng nào tồn tại trong cơ sở dữ liệu hay không."""
        return self.user_manager.session.query(exists().where(User.id != None)).scalar()
