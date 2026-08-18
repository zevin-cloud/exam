from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ExamTask(Base):
    __tablename__ = "exam_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    description = Column(Text, nullable=True)
    
    # 考务配置
    start_time = Column(DateTime, nullable=True) # 开放起始时间
    end_time = Column(DateTime, nullable=True)   # 开放截止时间
    duration_minutes = Column(Integer, default=60) # 答题限时（分钟）
    pass_score = Column(Float, default=60.0)      # 及格线
    max_retries = Column(Integer, default=1)      # 允许重考次数
    
    # 防作弊配置
    max_screen_switch = Column(Integer, default=3) # 允许切屏最大次数，超过强制交卷
    shuffle_options = Column(Boolean, default=False) # 选项乱序
    show_result_immediately = Column(Boolean, default=True) # 客观题交卷后是否立即展示成绩与解析
    
    # 目标参考人员授权范围
    scope_type = Column(String(20), default="ALL") # ALL(全员公开), DEPT(指定部门), USER(指定人员)
    target_dept_ids_json = Column(Text, nullable=True) # 部门ID数组 JSON
    target_user_ids_json = Column(Text, nullable=True) # 用户ID数组 JSON
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    paper = relationship("Paper", back_populates="exam_tasks")
    creator = relationship("User")
    records = relationship("ExamRecord", back_populates="exam_task", cascade="all, delete-orphan")
