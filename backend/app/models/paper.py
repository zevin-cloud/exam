from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="综合")
    total_score = Column(Float, default=100.0)
    pass_score = Column(Float, default=60.0)
    suggest_duration = Column(Integer, default=60) # 建议作答时长（分钟）
    
    # 核心：完全兼容 SurveyKing 规范的完整 Schema JSON
    # 包含 elements（题目结构、题型、分值、标准答案、解析、知识点等）
    schema_json = Column(Text, nullable=False)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User")
    exam_tasks = relationship("ExamTask", back_populates="paper")
