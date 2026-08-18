from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User, Department, RoleEnum
from app.schemas.user_schema import (
    UserOut, UserCreate, UserUpdate, UserBatchRoleUpdate,
    DepartmentOut, DepartmentCreate, DepartmentUpdate
)
from app.services.oneauth_service import oneauth_service
from app.api.deps import require_teacher_or_admin, require_admin

router = APIRouter()

@router.get("/departments", response_model=List[DepartmentOut])
def get_departments(db: Session = Depends(get_db)):
    depts = db.query(Department).all()
    return depts

@router.get("", response_model=List[UserOut])
def get_users(
    department_id: Optional[int] = None,
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if role:
        query = query.filter(User.role == role)
    if keyword:
        query = query.filter((User.username.contains(keyword)) | (User.full_name.contains(keyword)))

    users = query.all()
    result = []
    for u in users:
        dept_name = None
        if u.department_id:
            dept = db.query(Department).filter(Department.id == u.department_id).first()
            if dept:
                dept_name = dept.name
        result.append(UserOut(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            email=u.email,
            role=u.role,
            department_id=u.department_id,
            department_name=dept_name,
            is_active=u.is_active,
            avatar=u.avatar,
            sso_user_id=u.sso_user_id,
            created_at=u.created_at
        ))
    return result

@router.post("/departments", response_model=DepartmentOut, dependencies=[Depends(require_admin)])
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    dept = Department(name=payload.name, parent_id=payload.parent_id, sso_dept_id=payload.sso_dept_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@router.put("/departments/{id}", response_model=DepartmentOut, dependencies=[Depends(require_admin)])
def update_department(id: int, payload: DepartmentUpdate, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    if payload.name is not None:
        dept.name = payload.name
    if payload.parent_id is not None:
        dept.parent_id = payload.parent_id if payload.parent_id > 0 else None
    db.commit()
    db.refresh(dept)
    return dept

def _get_all_sub_dept_ids(dept_id: int, all_depts: List[Department]) -> List[int]:
    """递归获取指定部门的所有子孙部门 ID 列表"""
    sub_ids = []
    for d in all_depts:
        if d.parent_id == dept_id:
            sub_ids.append(d.id)
            sub_ids.extend(_get_all_sub_dept_ids(d.id, all_depts))
    return sub_ids

@router.delete("/departments/{id}", dependencies=[Depends(require_admin)])
def delete_department(id: int, cascade: bool = Query(False, description="是否级联删除所有子部门"), db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    dept_name = str(dept.name)
    parent_id = dept.parent_id
    all_depts = db.query(Department).all()
    sub_dept_ids = _get_all_sub_dept_ids(id, all_depts)

    # 剥离当前会话内的对象，避免 commit 时 ORM 触发过期属性加载错误
    db.expunge_all()

    if cascade and sub_dept_ids:
        all_target_ids = [id] + sub_dept_ids
        # 1. 将所有被删除部门下的成员 department_id 清空
        db.query(User).filter(User.department_id.in_(all_target_ids)).update(
            {"department_id": None}, synchronize_session=False
        )
        # 2. 级联删除所有这些部门
        db.query(Department).filter(Department.id.in_(all_target_ids)).delete(
            synchronize_session=False
        )
        db.commit()
        return {"success": True, "message": f"已成功级联删除「{dept_name}」及 {len(sub_dept_ids)} 个子部门"}
    else:
        # 仅删除当前部门：将直属子部门的父级挂载到当前部门的原 parent_id（保留子部门架构）
        db.query(Department).filter(Department.parent_id == id).update(
            {"parent_id": parent_id}, synchronize_session=False
        )
        # 将当前部门员工部门清空
        db.query(User).filter(User.department_id == id).update(
            {"department_id": None}, synchronize_session=False
        )
        db.query(Department).filter(Department.id == id).delete(synchronize_session=False)
        db.commit()
        return {"success": True, "message": f"已成功删除部门「{dept_name}」"}

@router.post("", response_model=UserOut, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    exist = db.query(User).filter(User.username == payload.username).first()
    if exist:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    from app.core.security import get_password_hash
    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
        department_id=payload.department_id,
        is_active=payload.is_active,
        avatar=payload.avatar,
        hashed_password=get_password_hash(payload.password or "123456")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    dept_name = None
    if user.department_id:
        d = db.query(Department).filter(Department.id == user.department_id).first()
        if d:
            dept_name = d.name

    return UserOut(
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

@router.put("/{id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def update_user(id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. 保护内置 admin 账号
    if user.username == "admin":
        if payload.role is not None and payload.role != RoleEnum.SUPER_ADMIN.value:
            raise HTTPException(status_code=400, detail="内置管理员 (admin) 角色不可修改，必须保持超级管理员身份")
        if payload.is_active is not None and not payload.is_active:
            raise HTTPException(status_code=400, detail="内置管理员 (admin) 账号不可停用")

    # 2. 底线守护：如果修改角色为非超管或停用超管账号，检查系统中是否至少保留一位激活的超管
    if (payload.role is not None and payload.role != RoleEnum.SUPER_ADMIN.value and user.role == RoleEnum.SUPER_ADMIN.value) or \
       (payload.is_active is False and user.role == RoleEnum.SUPER_ADMIN.value):
        other_admins_count = db.query(User).filter(
            User.role == RoleEnum.SUPER_ADMIN.value,
            User.is_active == True,
            User.id != user.id
        ).count()
        if other_admins_count == 0:
            raise HTTPException(status_code=400, detail="操作被拦截：系统中至少需要保留一位处于激活状态的超级管理员")
    
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role
    if payload.department_id is not None:
        user.department_id = payload.department_id if payload.department_id > 0 else None
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        from app.core.security import get_password_hash
        user.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)

    dept_name = None
    if user.department_id:
        d = db.query(Department).filter(Department.id == user.department_id).first()
        if d:
            dept_name = d.name

    return UserOut(
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

@router.post("/batch-role", dependencies=[Depends(require_admin)])
def batch_update_user_role(payload: UserBatchRoleUpdate, db: Session = Depends(get_db)):
    """批量修改用户系统角色"""
    valid_roles = [RoleEnum.SUPER_ADMIN.value, RoleEnum.TEACHER.value, RoleEnum.STUDENT.value]
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail="不支持的角色类型")
    if not payload.user_ids:
        return {"success": True, "updated_count": 0, "message": "未指定需修改的用户"}
    
    target_users = db.query(User).filter(User.id.in_(payload.user_ids)).all()
    if not target_users:
        return {"success": True, "updated_count": 0, "message": "未找到指定的用户"}
    
    # 1. 保护内置 admin 账号：若批量目标角色非超管，则自动剔除 admin
    final_user_ids = []
    has_skipped_admin = False
    for u in target_users:
        if u.username == "admin" and payload.role != RoleEnum.SUPER_ADMIN.value:
            has_skipped_admin = True
            continue
        final_user_ids.append(u.id)

    if not final_user_ids:
        if has_skipped_admin:
            raise HTTPException(status_code=400, detail="内置管理员 (admin) 角色不可修改，必须保持超级管理员身份")
        return {"success": True, "updated_count": 0, "message": "无需修改的用户"}

    # 2. 底线守护：如果批量修改目标角色不是 super_admin，检查系统中是否至少保留一位激活的 super_admin
    if payload.role != RoleEnum.SUPER_ADMIN.value:
        remaining_admins_count = db.query(User).filter(
            User.role == RoleEnum.SUPER_ADMIN.value,
            User.is_active == True,
            ~User.id.in_(final_user_ids)
        ).count()
        if remaining_admins_count == 0:
            raise HTTPException(status_code=400, detail="操作被拦截：系统中至少需要保留一位处于激活状态的超级管理员")

    updated_count = db.query(User).filter(User.id.in_(final_user_ids)).update(
        {User.role: payload.role}, synchronize_session=False
    )
    db.commit()

    msg = f"成功将 {updated_count} 位成员角色更新为 {payload.role}"
    if has_skipped_admin:
        msg += "（已自动保护内置 admin 账号）"

    return {
        "success": True,
        "updated_count": updated_count,
        "role": payload.role,
        "message": msg
    }

@router.delete("/{id}", dependencies=[Depends(require_admin)])
def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. 保护内置 admin
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="内置管理员 (admin) 账号不可删除")
        
    # 2. 底线守护
    if user.role == RoleEnum.SUPER_ADMIN.value:
        remaining_admins = db.query(User).filter(
            User.role == RoleEnum.SUPER_ADMIN.value,
            User.is_active == True,
            User.id != user.id
        ).count()
        if remaining_admins == 0:
            raise HTTPException(status_code=400, detail="无法删除系统中唯一的超级管理员")

    db.delete(user)
    db.commit()
    return {"success": True, "message": "成员已删除"}

@router.get("/sso-config", dependencies=[Depends(require_admin)])
def get_sso_config():
    """获取企业身份源/SSO连接配置"""
    return oneauth_service.get_config()

@router.post("/sso-config", dependencies=[Depends(require_admin)])
def update_sso_config(payload: dict):
    """更新企业身份源/SSO连接配置（如服务器地址、同步账号等）"""
    oneauth_service.update_config(payload)
    return {"success": True, "message": "身份源连接配置已更新", "data": oneauth_service.get_config()}

@router.post("/sync-departments", dependencies=[Depends(require_admin)])
def sync_oneauth_departments(db: Session = Depends(get_db)):
    """仅同步部门树（幂等增量：已存在部门自动跳过，不重复同步）"""
    stats = oneauth_service.sync_departments_only(db)
    return {
        "success": True,
        "message": f"部门同步完成：新增 {stats['synced_departments']} 个部门，跳过已有 {stats['skipped_departments']} 个部门",
        "data": stats
    }

@router.get("/oneauth-candidates", dependencies=[Depends(require_admin)])
def get_oneauth_candidates(db: Session = Depends(get_db)):
    """拉取 OneAuth 待同步候选员工列表"""
    candidates = oneauth_service.get_candidate_users(db)
    return {"success": True, "data": candidates}

@router.post("/import-oneauth-users", dependencies=[Depends(require_admin)])
def import_selected_oneauth_users(payload: dict, db: Session = Depends(get_db)):
    """根据管理员勾选的候选员工精准批量导入"""
    selected_keys = payload.get("user_keys", [])
    if not selected_keys:
        raise HTTPException(status_code=400, detail="请至少勾选一位要同步的员工")
    
    stats = oneauth_service.import_selected_users(selected_keys, db)
    return {
        "success": True,
        "message": f"成功同步导入 {stats['imported_users']} 位员工",
        "data": stats
    }

@router.post("/sync-oneauth", dependencies=[Depends(require_admin)])
def sync_oneauth_organization(db: Session = Depends(get_db)):
    """全量一键同步"""
    stats = oneauth_service.sync_departments_and_users(db)
    return {
        "success": True,
        "message": f"同步成功：新增部门 {stats['synced_departments']} 个（跳过已有 {stats.get('skipped_departments', 0)} 个），同步员工 {stats['synced_users']} 位",
        "data": stats
    }
