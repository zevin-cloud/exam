from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class RoleEnum(str, enum.Enum):
    SUPER_ADMIN = "super_admin"  # 超级管理员（系统配置、SSO配置）
    TEACHER = "teacher"          # 出题/阅卷人（HR / 业务主管）
    STUDENT = "student"          # 考生（普通员工）

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    sso_dept_id = Column(String(64), unique=True, index=True, nullable=True) # OneAuth 外部部门ID
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("Department", remote_side=[id], backref="children")
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    sso_user_id = Column(String(64), unique=True, index=True, nullable=True) # OneAuth 外部员工ID
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True)
    role = Column(String(20), default=RoleEnum.STUDENT.value, nullable=False) # super_admin, teacher, student
    is_active = Column(Boolean, default=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="users")
    records = relationship("ExamRecord", back_populates="user", foreign_keys="[ExamRecord.user_id]")
