from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.exam import ExamTask
from app.schemas.analytics_schema import AnalyticsReportOut, ScoreSearchOut
from app.services.analytics_service import analytics_service
from app.services.excel_service import ExcelService
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


@router.get("/scores", response_model=ScoreSearchOut, dependencies=[Depends(require_teacher_or_admin)])
def search_exam_scores(
    exam_task_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None, max_length=100),
    result_status: Literal["all", "passed", "failed", "pending"] = Query("all"),
    score_min: Optional[float] = Query(None, ge=0),
    score_max: Optional[float] = Query(None, ge=0),
    submitted_from: Optional[datetime] = Query(None),
    submitted_to: Optional[datetime] = Query(None),
    sort_by: Literal[
        "submit_desc", "submit_asc", "score_desc", "score_asc", "duration_asc", "duration_desc"
    ] = Query("submit_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=10, le=100),
    db: Session = Depends(get_db),
):
    """多维检索考试成绩；每人每场考试只取最后一次有效答卷。"""
    if score_min is not None and score_max is not None and score_min > score_max:
        raise HTTPException(status_code=400, detail="最低分不能高于最高分")
    return analytics_service.search_score_records(
        db=db,
        exam_task_id=exam_task_id,
        department_id=department_id,
        keyword=keyword,
        result_status=result_status,
        score_min=score_min,
        score_max=score_max,
        submitted_from=submitted_from,
        submitted_to=submitted_to,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.get("/scores/export", dependencies=[Depends(require_teacher_or_admin)])
def export_exam_scores(
    exam_task_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None, max_length=100),
    result_status: Literal["all", "passed", "failed", "pending"] = Query("all"),
    score_min: Optional[float] = Query(None, ge=0),
    score_max: Optional[float] = Query(None, ge=0),
    submitted_from: Optional[datetime] = Query(None),
    submitted_to: Optional[datetime] = Query(None),
    sort_by: Literal[
        "submit_desc", "submit_asc", "score_desc", "score_asc", "duration_asc", "duration_desc"
    ] = Query("submit_desc"),
    db: Session = Depends(get_db),
):
    """按当前检索条件导出完整成绩明细 Excel。"""
    if score_min is not None and score_max is not None and score_min > score_max:
        raise HTTPException(status_code=400, detail="最低分不能高于最高分")
    result = analytics_service.search_score_records(
        db=db,
        exam_task_id=exam_task_id,
        department_id=department_id,
        keyword=keyword,
        result_status=result_status,
        score_min=score_min,
        score_max=score_max,
        submitted_from=submitted_from,
        submitted_to=submitted_to,
        sort_by=sort_by,
        export_all=True,
    )
    task = db.query(ExamTask).filter(ExamTask.id == exam_task_id).first() if exam_task_id else None
    report_title = f"{task.title} - 成绩明细" if task else "全部考务 - 成绩明细"
    excel_bytes = ExcelService.export_exam_scores_to_excel(result.items, report_title)
    filename = f"exam_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
