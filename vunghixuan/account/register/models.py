from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Định nghĩa cơ sở
Base = declarative_base()

# Bảng trung gian User-Group
user_group_association = Table(
    'user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('group_id', Integer, ForeignKey('group.id'))
)

# Bảng trung gian Group-Roll
group_roll_association = Table(
    'group_roll', Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('roll_id', Integer, ForeignKey('roll.id'))
)

# Bảng trung gian Roll-Permission
roll_permission_association = Table('roll_permission', Base.metadata,
    Column('roll_id', Integer, ForeignKey('roll.id')),
    Column('permission_id', Integer, ForeignKey('permission.id')),
    Column('interface_id', Integer, ForeignKey('interface.id'))
)

# Bảng trung gian User-Roll
user_roll_association = Table(
    'user_roll', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('roll_id', Integer, ForeignKey('roll.id'))
)

# Bảng trung gian App-Permission
app_permission_association = Table(
    'app_permission', Base.metadata,
    Column('app_id', Integer, ForeignKey('app.id')),
    Column('permission_id', Integer, ForeignKey('permission.id'))
)

# Bảng trung gian Interface-Permission
interface_permission_association = Table(
    'interface_permission', Base.metadata,
    Column('interface_id', Integer, ForeignKey('interface.id')),
    Column('permission_id', Integer, ForeignKey('permission.id'))
)

# Bảng trung gian Roll-App
roll_app_association = Table(
    'roll_app', Base.metadata,
    Column('roll_id', Integer, ForeignKey('roll.id')),
    Column('app_id', Integer, ForeignKey('app.id'))
)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
    groups = relationship("Group", secondary=user_group_association, back_populates="users")
    rolls = relationship("Roll", secondary=user_roll_association, back_populates="users")

    def __repr__(self):
        return f"<User(username='{self.username}')>"

class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    users = relationship("User", secondary=user_group_association, back_populates="groups")
    rolls = relationship("Roll", secondary=group_roll_association, back_populates="groups")

    def __repr__(self):
        return f"<Group(name='{self.name}')>"

class Roll(Base):
    __tablename__ = 'roll'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    users = relationship("User", secondary=user_roll_association, back_populates="rolls")
    apps = relationship("App", secondary=roll_app_association, back_populates="rolls")
    permissions = relationship("Permission", secondary=roll_permission_association, back_populates="rolls")
    interfaces = relationship("Interface", secondary=roll_permission_association, back_populates="rolls", overlaps="permissions") # Thêm overlaps
    groups = relationship("Group", secondary=group_roll_association, back_populates="rolls")

    def __repr__(self):
        return f"<Roll(name='{self.name}')>"

class Permission(Base):
    __tablename__ = 'permission'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    rolls = relationship("Roll", secondary=roll_permission_association, back_populates="permissions", overlaps="interfaces") # Thêm overlaps
    apps = relationship("App", secondary=app_permission_association, back_populates="permissions")
    interfaces = relationship("Interface", secondary=interface_permission_association, back_populates="permissions")

    def __repr__(self):
        return f"<Permission(name='{self.name}')>"

class App(Base):
    __tablename__ = 'app'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    permissions = relationship("Permission", secondary=app_permission_association, back_populates="apps")
    interfaces = relationship("Interface", back_populates="app")
    rolls = relationship("Roll", secondary=roll_app_association, back_populates="apps")

    def __repr__(self):
        return f"<App(name='{self.name}')>"

class Interface(Base):
    __tablename__ = 'interface'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    app_id = Column(Integer, ForeignKey('app.id'), nullable=False)
    app = relationship("App", back_populates="interfaces")
    permissions = relationship("Permission", secondary=interface_permission_association, back_populates="interfaces")
    rolls = relationship("Roll", secondary=roll_permission_association, back_populates="interfaces", overlaps="permissions,rolls") # Sửa lại back_populates

    def __repr__(self):
        return f"<Interface(name='{self.name}')>"