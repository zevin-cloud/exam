from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User, Department, RoleEnum
from app.schemas.user_schema import UserLogin, Token, UserOut
from app.services.oneauth_service import oneauth_service
from app.api.deps import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class SSOCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None
    redirect_uri: Optional[str] = None

class QuickSwitchRequest(BaseModel):
    username: str

@router.post("/login", response_model=Token)
def login_for_access_token(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")

    access_token = create_access_token(subject=user.id, role=user.role)
    
    dept_name = None
    if user.department_id:
        dept = db.query(Department).filter(Department.id == user.department_id).first()
        if dept:
            dept_name = dept.name
            
    user_out = UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        department_id=user.department_id,
        department_name=dept_name,
        is_active=user.is_active,
        avatar=user.avatar,
        sso_user_id=user.sso_user_id,
        created_at=user.created_at
    )
    return Token(access_token=access_token, token_type="bearer", user=user_out)

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dept_name = None
    if current_user.department_id:
        dept = db.query(Department).filter(Department.id == current_user.department_id).first()
        if dept:
            dept_name = dept.name
            
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        department_id=current_user.department_id,
        department_name=dept_name,
        is_active=current_user.is_active,
        avatar=current_user.avatar,
        sso_user_id=current_user.sso_user_id,
        created_at=current_user.created_at
    )

@router.get("/oneauth/url")
def get_oneauth_authorize_url(redirect_uri: Optional[str] = None, db: Session = Depends(get_db)):
    """获取 OneAuth SSO 认证跳转链接（动态支持前端当前域名/端口的回调地址）"""
    url = oneauth_service.get_authorize_url(redirect_uri=redirect_uri, db=db)
    return {"authorize_url": url}

@router.post("/oneauth/callback", response_model=Token)
async def oneauth_callback(payload: SSOCallbackRequest, db: Session = Depends(get_db)):
    """OneAuth OAuth2 授权码回调换取登录凭据"""
    user_info = await oneauth_service.exchange_token_and_get_user(payload.code, redirect_uri=payload.redirect_uri, db=db)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Failed to authenticate with OneAuth server"
        )
    
    # 查找或新建该 SSO 用户
    sso_id = user_info.get("id") or user_info.get("sso_user_id") or user_info.get("username")
    user = db.query(User).filter((User.sso_user_id == sso_id) | (User.username == user_info.get("username"))).first()
    
    if not user:
        user = User(
            sso_user_id=sso_id,
            username=user_info.get("username", f"sso_{sso_id}"),
            full_name=user_info.get("full_name") or user_info.get("name") or "SSO用户",
            email=user_info.get("email"),
            role=user_info.get("role", RoleEnum.STUDENT.value),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(subject=user.id, role=user.role)
    dept_name = None
    if user.department_id:
        dept = db.query(Department).filter(Department.id == user.department_id).first()
        if dept:
            dept_name = dept.name
            
    user_out = UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        department_id=user.department_id,
        department_name=dept_name,
        is_active=user.is_active,
        avatar=user.avatar,
        sso_user_id=user.sso_user_id,
        created_at=user.created_at
    )
    return Token(access_token=access_token, token_type="bearer", user=user_out)

@router.post("/quick-switch", response_model=Token)
def quick_switch_account(payload: QuickSwitchRequest, db: Session = Depends(get_db)):
    """快捷切换内置演示身份（超管/HR出题人/考生）"""
    target = payload.username
    user = None

    # 1. 尝试直接按用户名匹配
    user = db.query(User).filter(User.username == target).first()

    # 2. 若未找到，按角色意图智能匹配现有真实员工
    if not user:
        if target in ["admin", "super_admin"]:
            user = db.query(User).filter((User.username == "admin") | (User.role == RoleEnum.SUPER_ADMIN.value)).first()
        elif target in ["hr_teacher", "teacher"]:
            user = db.query(User).filter(User.role == RoleEnum.TEACHER.value).first()
            if not user:
                # 挑选一位真实员工临时设为出题人角色
                candidate = db.query(User).filter(User.username != "admin").first()
                if candidate:
                    candidate.role = RoleEnum.TEACHER.value
                    db.commit()
                    db.refresh(candidate)
                    user = candidate
        elif target in ["student_zw", "student", "zw"]:
            user = db.query(User).filter(User.role == RoleEnum.STUDENT.value).first()
            if not user:
                user = db.query(User).filter(User.username != "admin").first()

    if not user:
        user = db.query(User).first()

    if not user:
        raise HTTPException(status_code=404, detail="系统中暂无可用用户")

    access_token = create_access_token(subject=user.id, role=user.role)
    dept_name = None
    if user.department_id:
        dept = db.query(Department).filter(Department.id == user.department_id).first()
        if dept:
            dept_name = dept.name
            
    user_out = UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        department_id=user.department_id,
        department_name=dept_name,
        is_active=user.is_active,
        avatar=user.avatar,
        sso_user_id=user.sso_user_id,
        created_at=user.created_at
    )
    return Token(access_token=access_token, token_type="bearer", user=user_out)
