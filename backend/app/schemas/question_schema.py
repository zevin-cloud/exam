from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class QuestionOption(BaseModel):
    label: str # 选项文本，如 "A. Python"
    value: str # 选项值，如 "A"

class QuestionBase(BaseModel):
    bank_id: Optional[int] = None
    type: str # single_choice, multi_choice, true_false, fill_blank, essay
    title: str
    options: Optional[List[QuestionOption]] = []
    answer: List[str] # 正确答案，如 ["A"] 或 ["true"] 或 ["关键词1", "关键词2"]
    analysis: Optional[str] = ""
    score: float = 5.0
    difficulty: str = "medium"
    knowledge_tag: Optional[str] = "通用基础"

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(QuestionBase):
    pass

class QuestionOut(QuestionBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuestionBankBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = "默认分类"

class QuestionBankCreate(QuestionBankBase):
    pass

class QuestionBankOut(QuestionBankBase):
    id: int
    question_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
