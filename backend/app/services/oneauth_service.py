import httpx
import json
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User, Department, RoleEnum
from app.models.system_config import SystemConfig
from app.core.security import get_password_hash

class OneAuthSyncError(RuntimeError):
    """OneAuth 连接或鉴权失败。"""


class OneAuthService:
    """
    对接 OneAuth (https://github.com/zjl111/OneAuth.git)
    实现 OAuth2 授权码模式登录及部门/员工定时同步（配置持久化存储于数据库 SystemConfig 表中）
    """
    def _get_db_session(self, db: Optional[Session] = None):
        if db is not None:
            return db, False
        return SessionLocal(), True

    def get_config(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """获取当前配置（优先读取数据库持久化配置，若无则使用 .env 默认值）"""
        session, should_close = self._get_db_session(db)
        try:
            configs = session.query(SystemConfig).all()
            config_map = {c.key: c.value for c in configs}
            return {
                "server_url": config_map.get("oneauth_server_url") or settings.ONEAUTH_SERVER_URL.rstrip("/"),
                "sync_username": config_map.get("oneauth_sync_username") or "",
                "sync_password": config_map.get("oneauth_sync_password") or "",
                "client_id": config_map.get("oneauth_client_id") or settings.ONEAUTH_CLIENT_ID,
                "client_secret": config_map.get("oneauth_client_secret") or settings.ONEAUTH_CLIENT_SECRET,
                "redirect_uri": config_map.get("oneauth_redirect_uri") or settings.ONEAUTH_REDIRECT_URI,
            }
        finally:
            if should_close:
                session.close()

    def update_config(self, config: Dict[str, Any], db: Optional[Session] = None):
        """持久化保存 OneAuth 配置到数据库中（重启、多 Worker 间均即时生效）"""
        session, should_close = self._get_db_session(db)
        try:
            key_mapping = {
                "server_url": "oneauth_server_url",
                "sync_username": "oneauth_sync_username",
                "sync_password": "oneauth_sync_password",
                "client_id": "oneauth_client_id",
                "client_secret": "oneauth_client_secret",
                "redirect_uri": "oneauth_redirect_uri",
            }
            for req_key, db_key in key_mapping.items():
                if req_key in config and config[req_key] is not None:
                    val = str(config[req_key]).strip()
                    if req_key == "server_url":
                        val = val.rstrip("/")
                    item = session.query(SystemConfig).filter(SystemConfig.key == db_key).first()
                    if not item:
                        item = SystemConfig(key=db_key, value=val)
                        session.add(item)
                    else:
                        item.value = val
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if should_close:
                session.close()

    def get_authorize_url(self, redirect_uri: Optional[str] = None, state: str = "exam_auth", db: Optional[Session] = None) -> str:
        """生成跳转 OneAuth 统一认证授权地址（支持动态传入当前真实访问的回调地址）"""
        cfg = self.get_config(db)
        r_uri = redirect_uri or cfg.get("redirect_uri") or settings.ONEAUTH_REDIRECT_URI
        server_url = cfg.get("server_url")
        client_id = cfg.get("client_id")
        return f"{server_url}/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={r_uri}&scope=openid%20profile%20email&state={state}"

    async def exchange_token_and_get_user(self, code: str, redirect_uri: Optional[str] = None, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """使用 authorization_code 向 OneAuth 换取 Access Token 并拉取用户信息"""
        cfg = self.get_config(db)
        server_url = cfg.get("server_url")
        client_id = cfg.get("client_id")
        client_secret = cfg.get("client_secret")
        r_uri = redirect_uri or cfg.get("redirect_uri") or settings.ONEAUTH_REDIRECT_URI
        token_endpoints = [
            f"{server_url}/oauth/token",
            "http://127.0.0.1:8080/oauth/token",
            f"{server_url}/api/v1/oauth/token"
        ]
        userinfo_endpoints = [
            f"{server_url}/oauth/userinfo",
            "http://127.0.0.1:8080/oauth/userinfo",
            f"{server_url}/userinfo",
            f"{server_url}/api/v1/userinfo"
        ]

        access_token = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. 换取 access_token
                for t_url in token_endpoints:
                    try:
                        token_resp = await client.post(t_url, data={
                            "grant_type": "authorization_code",
                            "code": code,
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "redirect_uri": r_uri,
                        })
                        if token_resp.status_code == 200:
                            token_data = token_resp.json()
                            access_token = token_data.get("access_token")
                            if access_token:
                                break
                        basic_resp = await client.post(
                            t_url,
                            data={
                                "grant_type": "authorization_code",
                                "code": code,
                                "redirect_uri": r_uri,
                            },
                            auth=(client_id, client_secret)
                        )
                        if basic_resp.status_code == 200:
                            token_data = basic_resp.json()
                            access_token = token_data.get("access_token")
                            if access_token:
                                break
                    except Exception as e:
                        print(f"[OneAuthService] Attempt token endpoint {t_url} error: {e}")

                if not access_token:
                    print(f"[OneAuthService] Failed to obtain access_token for code: {code}")
                    return None

                # 2. 拉取员工详细信息
                for u_url in userinfo_endpoints:
                    try:
                        user_resp = await client.get(u_url, headers={"Authorization": f"Bearer {access_token}"})
                        if user_resp.status_code == 200:
                            raw_user = user_resp.json()
                            if isinstance(raw_user, dict) and "data" in raw_user and isinstance(raw_user["data"], dict):
                                raw_user = raw_user["data"]
                            
                            # 提取统一字段
                            username = raw_user.get("preferred_username") or raw_user.get("username") or raw_user.get("sub") or raw_user.get("name")
                            full_name = raw_user.get("name") or raw_user.get("full_name") or raw_user.get("preferred_username") or username
                            email = raw_user.get("email") or f"{username}@fit2cloud.com"
                            sso_id = str(raw_user.get("sub") or raw_user.get("id") or username)

                            return {
                                "sso_user_id": sso_id,
                                "username": username,
                                "full_name": full_name,
                                "email": email,
                                "raw": raw_user
                            }
                    except Exception as e:
                        print(f"[OneAuthService] Attempt userinfo endpoint {u_url} error: {e}")

        except Exception as e:
            print(f"[OneAuthService] SSO exchange error: {e}")
        return None

    def fetch_remote_organization_data(
        self,
        db: Optional[Session] = None,
        config_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """通过 OneAuth HTTP API 鉴权后拉取组织数据，不允许绕过密码直读数据库。"""
        cfg = self.get_config(db)
        if config_override:
            cfg.update({k: v for k, v in config_override.items() if v is not None})

        server_url = str(cfg.get("server_url") or "").strip().rstrip("/")
        username = str(cfg.get("sync_username") or "").strip()
        password = str(cfg.get("sync_password") or "")
        if not server_url:
            raise OneAuthSyncError("请先填写 OneAuth 服务地址")
        if not username or not password:
            raise OneAuthSyncError("请先填写组织同步用户名和密码")

        candidate_urls = [server_url]
        api_server_url = re.sub(r':5174$', ':8080', server_url)
        if api_server_url != server_url:
            candidate_urls.append(api_server_url)

        auth_failed = False
        connection_errors = []
        for base_url in candidate_urls:
            try:
                with httpx.Client(timeout=6.0, trust_env=False) as client:
                    login_resp = client.post(
                        f"{base_url}/api/v1/auth/login",
                        json={"username": username, "password": password},
                    )
                    if login_resp.status_code in (400, 401, 403):
                        auth_failed = True
                        continue
                    if login_resp.status_code != 200:
                        connection_errors.append(f"{base_url} 登录接口返回 HTTP {login_resp.status_code}")
                        continue

                    login_data = login_resp.json()
                    token = (login_data.get("data") or {}).get("access_token") or login_data.get("access_token")
                    if not token:
                        connection_errors.append(f"{base_url} 登录成功但未返回 access_token")
                        continue

                    headers = {"Authorization": f"Bearer {token}"}
                    dept_resp = client.get(f"{base_url}/api/v1/departments/tree", headers=headers)
                    user_resp = client.get(f"{base_url}/api/v1/users?page_size=500", headers=headers)
                    if dept_resp.status_code != 200 or user_resp.status_code != 200:
                        raise OneAuthSyncError(
                            f"OneAuth 数据接口异常：部门 HTTP {dept_resp.status_code}，用户 HTTP {user_resp.status_code}"
                        )

                    tree_data = dept_resp.json().get("data", [])
                    all_depts = []

                    def traverse(nodes, parent_id=None):
                        for node in nodes:
                            all_depts.append({
                                "id": str(node["id"]),
                                "name": node["name"],
                                "parent_id": str(parent_id) if parent_id else None,
                            })
                            if node.get("children"):
                                traverse(node["children"], node["id"])

                    traverse(tree_data)
                    user_data = user_resp.json().get("data", {})
                    raw_items = user_data.get("items", []) if isinstance(user_data, dict) else user_data
                    items = [{
                        "sso_user_id": str(item.get("id") or item.get("username")),
                        "username": item.get("username"),
                        "full_name": item.get("name") or item.get("nickname") or item.get("username"),
                        "email": item.get("email") or f"{item.get('username')}@fit2cloud.com",
                        "role": RoleEnum.SUPER_ADMIN.value if item.get("username") == "admin" else RoleEnum.STUDENT.value,
                        "dept_sso_id": str(item.get("department_id") or item.get("dept_id") or ""),
                    } for item in raw_items]
                    return {"departments": all_depts, "users": items, "source": f"remote ({base_url})"}
            except OneAuthSyncError:
                raise
            except (httpx.RequestError, ValueError) as exc:
                connection_errors.append(f"{base_url}: {exc}")

        if auth_failed:
            raise OneAuthSyncError("OneAuth 同步账号或密码错误")
        detail = connection_errors[-1] if connection_errors else "未知连接错误"
        raise OneAuthSyncError(f"无法连接 OneAuth：{detail}")

    def test_connection(self, config: Dict[str, Any], db: Session) -> Dict[str, Any]:
        org_data = self.fetch_remote_organization_data(db=db, config_override=config)
        return {
            "source": org_data["source"],
            "departments": len(org_data["departments"]),
            "users": len(org_data["users"]),
        }

    def sync_departments_only(self, db: Session, org_data: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        同步部门树（幂等：如果部门已存在则跳过，不重复同步）
        """
        org_data = org_data or self.fetch_remote_organization_data(db=db)
        synced_depts = 0
        skipped_depts = 0

        dept_map = {} # sso_dept_id -> db_id
        for d in org_data.get("departments", []):
            d_id = str(d.get("id") or d.get("dept_id"))
            d_name = d.get("name") or d.get("dept_name")
            dept = db.query(Department).filter(
                (Department.sso_dept_id == d_id) | (Department.name == d_name)
            ).first()
            if not dept:
                dept = Department(sso_dept_id=d_id, name=d_name)
                db.add(dept)
                db.flush()
                synced_depts += 1
            else:
                skipped_depts += 1
            dept_map[d_id] = dept.id

        # 更新新加入部门的父子层级
        for d in org_data.get("departments", []):
            d_id = str(d.get("id") or d.get("dept_id"))
            p_id = str(d.get("parent_id")) if d.get("parent_id") else None
            if p_id and p_id in dept_map and d_id in dept_map:
                dept = db.query(Department).filter(Department.id == dept_map[d_id]).first()
                if dept and not dept.parent_id:
                    dept.parent_id = dept_map[p_id]

        db.commit()
        return {"synced_departments": synced_depts, "skipped_departments": skipped_depts}

    def get_candidate_users(self, db: Session) -> List[Dict[str, Any]]:
        """
        拉取 OneAuth 候选员工列表并标注是否已同步
        """
        org_data = self.fetch_remote_organization_data(db=db)
        remote_users = org_data.get("users", [])
        remote_depts = {str(d.get("id") or d.get("dept_id")): (d.get("name") or d.get("dept_name")) for d in org_data.get("departments", [])}

        existing_users = {u.username: u for u in db.query(User).all()}
        existing_sso_map = {u.sso_user_id: u for u in db.query(User).filter(User.sso_user_id.isnot(None)).all()}

        candidates = []
        for u in remote_users:
            sso_uid = str(u.get("sso_user_id") or u.get("id") or u.get("username"))
            uname = u.get("username") or f"user_{sso_uid}"
            full_name = u.get("full_name") or u.get("name") or uname
            email = u.get("email") or f"{uname}@fit2cloud.com"
            dept_sso = str(u.get("dept_sso_id") or u.get("department_id") or "")
            dept_name = remote_depts.get(dept_sso, "未分配部门")

            # 检查本地是否已存在
            is_synced = (uname in existing_users) or (sso_uid in existing_sso_map)
            local_user = existing_users.get(uname) or existing_sso_map.get(sso_uid)

            candidates.append({
                "key": uname,
                "sso_user_id": sso_uid,
                "username": uname,
                "full_name": full_name,
                "email": email,
                "dept_name": dept_name,
                "dept_sso_id": dept_sso,
                "role": u.get("role") or RoleEnum.STUDENT.value,
                "is_synced": is_synced,
                "local_user_id": local_user.id if local_user else None
            })
        return candidates

    def import_selected_users(self, selected_keys: List[str], db: Session, org_data: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        精准导入用户勾选的员工列表
        """
        org_data = org_data or self.fetch_remote_organization_data(db=db)
        remote_users = org_data.get("users", [])
        
        # 确保部门已映射
        dept_sso_map = {d.sso_dept_id: d.id for d in db.query(Department).filter(Department.sso_dept_id.isnot(None)).all()}
        dept_name_map = {d.name: d.id for d in db.query(Department).all()}
        remote_depts_name = {str(d.get("id") or d.get("dept_id")): (d.get("name") or d.get("dept_name")) for d in org_data.get("departments", [])}

        imported_count = 0
        selected_set = set(selected_keys)

        for u in remote_users:
            sso_uid = str(u.get("sso_user_id") or u.get("id") or u.get("username"))
            username = u.get("username") or f"user_{sso_uid}"
            if username not in selected_set and sso_uid not in selected_set:
                continue

            full_name = u.get("full_name") or u.get("name") or username
            email = u.get("email") or f"{username}@fit2cloud.com"
            role = u.get("role") or RoleEnum.STUDENT.value
            dept_sso = str(u.get("dept_sso_id") or u.get("department_id") or "")
            dept_name = remote_depts_name.get(dept_sso)

            dept_id = dept_sso_map.get(dept_sso) or dept_name_map.get(dept_name)

            user = db.query(User).filter(
                (User.sso_user_id == sso_uid) | (User.username == username)
            ).first()

            if not user:
                user = User(
                    sso_user_id=sso_uid,
                    username=username,
                    full_name=full_name,
                    email=email,
                    role=role,
                    department_id=dept_id,
                    hashed_password=get_password_hash("123456"),
                    is_active=True
                )
                db.add(user)
            else:
                user.sso_user_id = sso_uid
                user.full_name = full_name
                user.email = email
                if dept_id:
                    user.department_id = dept_id

            imported_count += 1

        db.commit()
        return {"imported_users": imported_count}

    def sync_departments_and_users(self, db: Session, org_data: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """保留全量同步快捷入口"""
        org_data = org_data or self.fetch_remote_organization_data(db=db)
        dept_stats = self.sync_departments_only(db, org_data=org_data)
        remote_users = org_data.get("users", [])
        all_keys = [str(u.get("username") or u.get("sso_user_id") or u.get("id")) for u in remote_users]
        user_stats = self.import_selected_users(all_keys, db, org_data=org_data)
        return {
            "synced_departments": dept_stats["synced_departments"],
            "skipped_departments": dept_stats["skipped_departments"],
            "synced_users": user_stats["imported_users"]
        }

oneauth_service = OneAuthService()
