from fastapi import APIRouter
from app.api.v1 import auth, users, questions, papers, exams, grading, analytics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["身份认证 & OneAuth SSO"])
api_router.include_router(users.router, prefix="/users", tags=["组织与用户管理"])
api_router.include_router(questions.router, prefix="/questions", tags=["题库与导入导出"])
api_router.include_router(papers.router, prefix="/papers", tags=["试卷管理 (SurveyKing)"])
api_router.include_router(exams.router, prefix="/exams", tags=["考务与在线考试"])
api_router.include_router(grading.router, prefix="/grading", tags=["主观题流水阅卷"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["数据报表与盲区分析"])
