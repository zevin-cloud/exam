from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from app.core.database import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
