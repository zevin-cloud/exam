import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Exam System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "exam_secret_key_antigravity_2026_super_secure_token")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database: Default SQLite for zero-config run, easily switchable to MySQL/Postgres
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./exam.db")

    # Local Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads")))

    # OneAuth SSO Configuration (https://github.com/zjl111/OneAuth.git)
    ONEAUTH_ENABLED: bool = True
    ONEAUTH_SERVER_URL: str = os.getenv("ONEAUTH_SERVER_URL", "http://192.168.123.233:5174")
    ONEAUTH_CLIENT_ID: str = os.getenv("ONEAUTH_CLIENT_ID", "app_52a0a477a52301c3")
    ONEAUTH_CLIENT_SECRET: str = os.getenv("ONEAUTH_CLIENT_SECRET", "XHmyUn7U90JzTEha_bL_WcMr3NQbkFIgcF75TomhYX65eNwDm3nqP8TLKB-eXeY7")
    ONEAUTH_REDIRECT_URI: str = os.getenv("ONEAUTH_REDIRECT_URI", "http://192.168.123.233:5173/auth/callback")

    class Config:
        case_sensitive = True
        extra = "allow"

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
