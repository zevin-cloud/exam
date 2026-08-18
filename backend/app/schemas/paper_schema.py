from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SurveyKingExamConfig(BaseModel):
    score: float = 5.0
    correct_answer: List[str] = [] # 题目标准答案
    analysis: Optional[str] = ""    # 题目解析
    knowledge_tag: Optional[str] = "通用知识"
    difficulty: Optional[str] = "medium"

class SurveyKingOption(BaseModel):
    label: str
    value: str

class SurveyKingElement(BaseModel):
    id: str # 如 "q_1", "q_2"
    type: str # "Radio", "Checkbox", "TrueFalse", "FillBlank", "Textarea"
    title: str
    options: Optional[List[SurveyKingOption]] = []
    required: bool = True
    exam_config: SurveyKingExamConfig = Field(default_factory=SurveyKingExamConfig)

class SurveyKingPage(BaseModel):
    id: str = "page_1"
    title: Optional[str] = "第一部分"
    elements: List[SurveyKingElement] = []

class SurveyKingSchema(BaseModel):
    pages: List[SurveyKingPage] = []

class PaperCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "综合"
    suggest_duration: int = 60
    total_score: float = 100.0
    pass_score: float = 60.0
    schema_data: SurveyKingSchema # 完整的 SurveyKing JSON Schema

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    suggest_duration: Optional[int] = None
    total_score: Optional[float] = None
    pass_score: Optional[float] = None
    schema_data: Optional[SurveyKingSchema] = None

class PaperOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    total_score: float
    pass_score: float
    suggest_duration: int
    schema_data: Dict[str, Any]
    created_by: Optional[int] = None
    is_published: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
