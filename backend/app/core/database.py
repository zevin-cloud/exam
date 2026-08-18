from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    connect_args = {"check_same_thread": False, "timeout": 30}
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=False
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        except Exception:
            pass
else:
    # 生产 MySQL / PostgreSQL 高性能连接池配置
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
