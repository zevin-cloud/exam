from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.core.database import get_db
from app.models.exam_record import ExamRecord, ExamAnswerDetail, ExamRecordStatus
from app.models.exam import ExamTask
from app.models.user import User, Department
from app.schemas.exam_schema import GradeItemSubmit
from app.services.grading_service import grading_service
from app.api.deps import require_teacher_or_admin, get_current_user

router = APIRouter()

@router.get("/pending-items", dependencies=[Depends(require_teacher_or_admin)])
def list_pending_grading_items(
    exam_task_id: Optional[int] = None,
    status: Optional[str] = "all", # pending(待阅), graded(已阅), all(全部)
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取主观题答卷列表（支持按考试、按批阅状态、按学员检索与指定查看）"""
    query = db.query(ExamAnswerDetail).join(ExamRecord).filter(
        ExamAnswerDetail.question_type.in_(["essay", "textarea", "Textarea", "Essay"])
    )
    
    if status == "pending":
        query = query.filter(ExamAnswerDetail.is_graded == False)
    elif status == "graded":
        query = query.filter(ExamAnswerDetail.is_graded == True)

    if exam_task_id:
        query = query.filter(ExamRecord.exam_task_id == exam_task_id)

    query = query.order_by(ExamAnswerDetail.id.desc())
    details = query.all()
    result = []
    
    for d in details:
        record = db.query(ExamRecord).filter(ExamRecord.id == d.record_id).first()
        task = db.query(ExamTask).filter(ExamTask.id == record.exam_task_id).first() if record else None
        student = db.query(User).filter(User.id == record.user_id).first() if record else None
        
        # 部门信息
        dept_name = "未分配部门"
        if student and student.department_id:
            dept = db.query(Department).filter(Department.id == student.department_id).first()
            if dept:
                dept_name = dept.name

        student_name = student.full_name if student else (f"考生 #{record.user_id}" if record else "未知考生")
        student_email = student.email if student else ""

        # 关键词匹配过滤 (考生姓名、工号、题干)
        if keyword:
            kw = keyword.strip().lower()
            if kw not in student_name.lower() and kw not in student_email.lower() and kw not in d.question_title.lower():
                continue

        u_ans = json.loads(d.user_answer_json) if d.user_answer_json else ""
        c_ans = json.loads(d.correct_answer_json) if d.correct_answer_json else []

        result.append({
            "detail_id": d.id,
            "record_id": d.record_id,
            "exam_task_id": record.exam_task_id if record else None,
            "exam_title": task.title if task else "未知考试",
            "student_id": student.id if student else None,
            "student_name": student_name,
            "student_email": student_email,
            "department_name": dept_name,
            "question_id": d.question_id,
            "question_title": d.question_title,
            "max_score": d.max_score,
            "actual_score": d.actual_score,
            "teacher_comment": d.teacher_comment or "",
            "is_graded": d.is_graded,
            "user_answer": u_ans if isinstance(u_ans, str) else json.dumps(u_ans, ensure_ascii=False),
            "reference_answer": c_ans[0] if c_ans else "请出题人按论述完整度与关键技术点酌情给分。",
            "knowledge_tag": d.knowledge_tag or "专业素养",
            "submit_time": record.submit_time if record else None
        })
    return result

@router.post("/grade-item", dependencies=[Depends(require_teacher_or_admin)])
def grade_subjective_item(
    payload: GradeItemSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """考官给主观题打分及写评语"""
    try:
        updated_detail = grading_service.grade_subjective_detail(
            detail_id=payload.detail_id,
            grader_id=current_user.id,
            score=payload.score,
            comment=payload.comment or "",
            db=db
        )
        return {
            "success": True,
            "message": f"批阅成功，得分：{updated_detail.actual_score}分"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
