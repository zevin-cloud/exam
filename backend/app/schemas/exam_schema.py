from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ExamTaskCreate(BaseModel):
    title: str
    paper_id: int
    description: Optional[str] = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: int = 60
    pass_score: float = 60.0
    max_retries: int = 1
    max_screen_switch: int = 3
    shuffle_options: bool = False
    show_result_immediately: bool = True
    scope_type: str = "ALL" # ALL, DEPT, USER
    target_dept_ids: Optional[List[int]] = []
    target_user_ids: Optional[List[int]] = []

class ExamTaskOut(BaseModel):
    id: int
    title: str
    paper_id: int
    paper_title: Optional[str] = None
    total_score: Optional[float] = 100.0
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: int
    pass_score: float
    max_retries: int
    max_screen_switch: int
    show_result_immediately: bool
    is_active: bool
    scope_type: Optional[str] = "ALL"
    target_dept_ids: Optional[List[int]] = []
    target_user_ids: Optional[List[int]] = []
    target_dept_names: Optional[List[str]] = []
    target_user_names: Optional[List[str]] = []
    user_attempt_count: Optional[int] = 0
    latest_record_id: Optional[int] = None
    latest_record_status: Optional[str] = None
    latest_score: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 考生答题交互 Schemas
class ExamDraftSave(BaseModel):
    answers: Dict[str, Any] # {"q_1": ["A"], "q_2": "文本内容"}
    screen_switch_count: int = 0
    duration_seconds: int = 0

class ExamSubmit(BaseModel):
    answers: Dict[str, Any] # 最终提交答案
    screen_switch_count: int = 0
    duration_seconds: int = 0

class GradeItemSubmit(BaseModel):
    detail_id: int
    score: float
    comment: Optional[str] = ""
