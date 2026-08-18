from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice" # 单选题
    MULTI_CHOICE = "multi_choice"   # 多选题
    TRUE_FALSE = "true_false"       # 判断题
    FILL_BLANK = "fill_blank"       # 填空题
    ESSAY = "essay"                 # 问答/简答题

class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionBank(Base):
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="默认分类")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    questions = relationship("Question", back_populates="bank", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=True)
    type = Column(String(30), nullable=False) # single_choice, multi_choice, true_false, fill_blank, essay
    title = Column(Text, nullable=False)     # 题干
    options_json = Column(Text, nullable=True) # 选项 JSON，如 [{"label": "A. xxx", "value": "A"}]
    answer_json = Column(Text, nullable=False) # 正确答案 JSON，如 ["A"] 或 ["true"] 或 ["关键词1", "关键词2"]
    analysis = Column(Text, nullable=True)   # 答案解析
    score = Column(Float, default=5.0)       # 默认分值
    difficulty = Column(String(20), default=Difficulty.MEDIUM.value)
    knowledge_tag = Column(String(100), nullable=True) # 知识点标签（用于知识盲区统计）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bank = relationship("QuestionBank", back_populates="questions")
