from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class OverviewStats(BaseModel):
    total_exams: int
    total_takers: int
    avg_score: float
    pass_rate: float # 0 - 100
    max_score: float = 0.0
    min_score: float = 0.0
    total_eligible: int = 0
    total_absent: int = 0

class DeptPassRateItem(BaseModel):
    dept_name: str
    total_count: int
    pass_count: int
    pass_rate: float
    avg_score: float

class WrongQuestionItem(BaseModel):
    question_title: str
    question_type: str
    knowledge_tag: str
    total_attempts: int
    wrong_count: int
    error_rate: float # 0 - 100

class KnowledgeRadarItem(BaseModel):
    tag: str
    mastery_rate: float # 掌握率 0 - 100
    wrong_count: int
    total_count: int

class ScoreDistributionItem(BaseModel):
    label: str # "90-100分 (优秀)", "80-89分 (良好)", "60-79分 (及格)", "<60分 (不及格)"
    count: int
    percentage: float

class CandidateRankItem(BaseModel):
    rank: int
    student_id: int
    student_name: str
    department_name: str
    total_score: float
    is_passed: bool
    duration_seconds: int
    submit_time: Optional[Any] = None

class ExamInfoBrief(BaseModel):
    id: Optional[int] = None
    title: str
    total_score: float
    pass_score: float

class AnalyticsReportOut(BaseModel):
    overview: OverviewStats
    exam_info: Optional[ExamInfoBrief] = None
    dept_stats: List[DeptPassRateItem]
    wrong_top_questions: List[WrongQuestionItem]
    knowledge_radar: List[KnowledgeRadarItem]
    score_distribution: List[ScoreDistributionItem] = []
    candidate_rankings: List[CandidateRankItem] = []
