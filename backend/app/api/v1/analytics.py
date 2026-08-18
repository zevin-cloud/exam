from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.analytics_schema import AnalyticsReportOut
from app.services.analytics_service import analytics_service
from app.api.deps import require_teacher_or_admin

router = APIRouter()

@router.get("/dashboard", response_model=AnalyticsReportOut, dependencies=[Depends(require_teacher_or_admin)])
def get_analytics_dashboard(
    exam_task_id: Optional[int] = Query(None, description="指定考试ID，不传则统计全员"),
    db: Session = Depends(get_db)
):
    """获取数据报表：部门及格率/通过率分布、平均分、错题率排行、知识盲区雷达"""
    report = analytics_service.get_exam_analytics(exam_task_id=exam_task_id, db=db)
    return report
