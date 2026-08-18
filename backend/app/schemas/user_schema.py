from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class DepartmentBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    sso_dept_id: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None

class DepartmentOut(DepartmentBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    full_name: str
    email: Optional[str] = None
    role: str = "student"
    department_id: Optional[int] = None
    is_active: bool = True
    avatar: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = "123456"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserBatchRoleUpdate(BaseModel):
    user_ids: List[int]
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(UserBase):
    id: int
    sso_user_id: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

Token.model_rebuild()
