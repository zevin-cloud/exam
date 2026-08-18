from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class ExamRecordStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS" # 作答中
    SUBMITTED = "SUBMITTED"     # 已交卷（客观题已秒判，若有主观题待阅卷）
    GRADED = "GRADED"           # 已完成阅卷并归档出分

class ExamRecord(Base):
    __tablename__ = "exam_records"

    id = Column(Integer, primary_key=True, index=True)
    exam_task_id = Column(Integer, ForeignKey("exam_tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 考试状态与得分
    status = Column(String(20), default=ExamRecordStatus.IN_PROGRESS.value)
    objective_score = Column(Float, default=0.0) # 客观题得分
    subjective_score = Column(Float, default=0.0) # 主观题得分
    total_score = Column(Float, default=0.0)     # 试卷最终总得分
    is_passed = Column(Boolean, default=False)
    
    # 答题过程监控
    screen_switch_count = Column(Integer, default=0) # 切屏作弊违规次数
    duration_seconds = Column(Integer, default=0)    # 实际答题耗时（秒）
    start_time = Column(DateTime, default=datetime.utcnow)
    submit_time = Column(DateTime, nullable=True)
    graded_time = Column(DateTime, nullable=True)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 答卷快照与草稿暂存（无 Redis 方案：直接在此字段实现秒级/心跳草稿保存）
    draft_json = Column(Text, nullable=True)   # 暂存未交卷答案
    submit_json = Column(Text, nullable=True)  # 最终交卷答案快照
    
    # Relationships
    exam_task = relationship("ExamTask", back_populates="records")
    user = relationship("User", back_populates="records", foreign_keys=[user_id])
    grader = relationship("User", foreign_keys=[graded_by])
    details = relationship("ExamAnswerDetail", back_populates="record", cascade="all, delete-orphan")

class ExamAnswerDetail(Base):
    __tablename__ = "exam_answer_details"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("exam_records.id"), nullable=False)
    question_id = Column(String(64), nullable=False) # 试卷内部题目唯一标识 (如 q_1, q_2)
    question_type = Column(String(30), nullable=False)
    question_title = Column(Text, nullable=False)
    knowledge_tag = Column(String(100), nullable=True)
    
    max_score = Column(Float, default=0.0) # 题目满分
    actual_score = Column(Float, default=0.0) # 考生实际得分
    
    user_answer_json = Column(Text, nullable=True) # 考生提交答案
    correct_answer_json = Column(Text, nullable=True) # 正确答案
    is_correct = Column(Boolean, default=False) # 客观题是否完全正确
    
    # 主观题阅卷字段
    is_graded = Column(Boolean, default=True) # 客观题默认为 True，主观题初始为 False
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    teacher_comment = Column(Text, nullable=True) # 考官评语

    # Relationships
    record = relationship("ExamRecord", back_populates="details")
