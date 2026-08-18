from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import copy
from datetime import datetime
from app.core.database import get_db
from app.models.exam import ExamTask
from app.models.paper import Paper
from app.models.exam_record import ExamRecord, ExamAnswerDetail, ExamRecordStatus
from app.models.user import User, Department, RoleEnum
from app.schemas.exam_schema import (
    ExamTaskCreate, ExamTaskOut, ExamDraftSave, ExamSubmit
)
from app.services.grading_service import grading_service
from app.api.deps import get_current_user, require_teacher_or_admin

router = APIRouter()

# ==================== 考务管理 (HR/管理员) ====================

def check_user_authorized_for_task(user: User, task: ExamTask, db: Session) -> bool:
    """校验用户是否有权限参加该考试"""
    if user.role in [RoleEnum.SUPER_ADMIN.value, RoleEnum.TEACHER.value]:
        return True
    
    scope = task.scope_type or "ALL"
    if scope == "ALL":
        return True
    
    if scope == "USER":
        u_ids = json.loads(task.target_user_ids_json) if task.target_user_ids_json else []
        return user.id in u_ids
        
    if scope == "DEPT":
        if not user.department_id:
            return False
        d_ids = json.loads(task.target_dept_ids_json) if task.target_dept_ids_json else []
        # 收集用户当前部门及所有上级祖先部门 ID
        cur_dept_id = user.department_id
        ancestor_dept_ids = []
        while cur_dept_id:
            ancestor_dept_ids.append(cur_dept_id)
            d = db.query(Department).filter(Department.id == cur_dept_id).first()
            cur_dept_id = d.parent_id if d else None
            
        # 若用户的任意上级部门或当前部门在授权列表中，则有权限
        return any(aid in d_ids for aid in ancestor_dept_ids)
        
    return True

@router.get("", response_model=List[ExamTaskOut])
def list_exam_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = db.query(ExamTask).order_by(ExamTask.id.desc()).all()
    result = []
    
    # 部门与用户名称映射缓存
    all_depts_map = {d.id: d.name for d in db.query(Department).all()}
    all_users_map = {u.id: (u.full_name or u.username) for u in db.query(User).all()}

    for t in tasks:
        # 如果是普通考生，过滤掉未授权的考务
        if current_user.role == RoleEnum.STUDENT.value and not check_user_authorized_for_task(current_user, t, db):
            continue

        paper = db.query(Paper).filter(Paper.id == t.paper_id).first()
        
        # 查询当前考生的作答情况
        user_records = db.query(ExamRecord).filter(
            ExamRecord.exam_task_id == t.id,
            ExamRecord.user_id == current_user.id
        ).order_by(ExamRecord.id.desc()).all()

        attempt_count = len(user_records)
        latest_record = user_records[0] if user_records else None

        # 授权范围名称解析
        dept_ids = json.loads(t.target_dept_ids_json) if t.target_dept_ids_json else []
        user_ids = json.loads(t.target_user_ids_json) if t.target_user_ids_json else []
        dept_names = [all_depts_map[did] for did in dept_ids if did in all_depts_map]
        user_names = [all_users_map[uid] for uid in user_ids if uid in all_users_map]

        result.append(ExamTaskOut(
            id=t.id,
            title=t.title,
            paper_id=t.paper_id,
            paper_title=paper.title if paper else "未知试卷",
            total_score=paper.total_score if paper else 100.0,
            description=t.description,
            start_time=t.start_time,
            end_time=t.end_time,
            duration_minutes=t.duration_minutes,
            pass_score=t.pass_score,
            max_retries=t.max_retries,
            max_screen_switch=t.max_screen_switch,
            show_result_immediately=t.show_result_immediately,
            is_active=t.is_active,
            scope_type=t.scope_type or "ALL",
            target_dept_ids=dept_ids,
            target_user_ids=user_ids,
            target_dept_names=dept_names,
            target_user_names=user_names,
            user_attempt_count=attempt_count,
            latest_record_id=latest_record.id if latest_record else None,
            latest_record_status=latest_record.status if latest_record else None,
            latest_score=latest_record.total_score if latest_record else None,
            created_at=t.created_at
        ))
    return result

@router.post("", response_model=ExamTaskOut, dependencies=[Depends(require_teacher_or_admin)])
def create_exam_task(
    payload: ExamTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == payload.paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    dept_json = json.dumps(payload.target_dept_ids) if payload.target_dept_ids else None
    user_json = json.dumps(payload.target_user_ids) if payload.target_user_ids else None

    task = ExamTask(
        title=payload.title,
        paper_id=payload.paper_id,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_minutes=payload.duration_minutes,
        pass_score=payload.pass_score,
        max_retries=payload.max_retries,
        max_screen_switch=payload.max_screen_switch,
        shuffle_options=payload.shuffle_options,
        show_result_immediately=payload.show_result_immediately,
        scope_type=payload.scope_type or "ALL",
        target_dept_ids_json=dept_json,
        target_user_ids_json=user_json,
        created_by=current_user.id,
        is_active=True
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    all_depts_map = {d.id: d.name for d in db.query(Department).all()}
    all_users_map = {u.id: (u.full_name or u.username) for u in db.query(User).all()}
    dept_names = [all_depts_map[did] for did in (payload.target_dept_ids or []) if did in all_depts_map]
    user_names = [all_users_map[uid] for uid in (payload.target_user_ids or []) if uid in all_users_map]

    return ExamTaskOut(
        id=task.id,
        title=task.title,
        paper_id=task.paper_id,
        paper_title=paper.title,
        total_score=paper.total_score,
        description=task.description,
        start_time=task.start_time,
        end_time=task.end_time,
        duration_minutes=task.duration_minutes,
        pass_score=task.pass_score,
        max_retries=task.max_retries,
        max_screen_switch=task.max_screen_switch,
        show_result_immediately=task.show_result_immediately,
        is_active=task.is_active,
        scope_type=task.scope_type or "ALL",
        target_dept_ids=payload.target_dept_ids or [],
        target_user_ids=payload.target_user_ids or [],
        target_dept_names=dept_names,
        target_user_names=user_names,
        created_at=task.created_at
    )

@router.put("/{id}", response_model=ExamTaskOut, dependencies=[Depends(require_teacher_or_admin)])
def update_exam_task(
    id: int,
    payload: ExamTaskCreate,
    db: Session = Depends(get_db)
):
    """更新考试任务设置（包括时间段调整、授权范围等）"""
    task = db.query(ExamTask).filter(ExamTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Exam task not found")

    paper = db.query(Paper).filter(Paper.id == payload.paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    dept_json = json.dumps(payload.target_dept_ids) if payload.target_dept_ids else None
    user_json = json.dumps(payload.target_user_ids) if payload.target_user_ids else None

    task.title = payload.title
    task.paper_id = payload.paper_id
    task.description = payload.description
    task.start_time = payload.start_time
    task.end_time = payload.end_time
    task.duration_minutes = payload.duration_minutes
    task.pass_score = payload.pass_score
    task.max_retries = payload.max_retries
    task.max_screen_switch = payload.max_screen_switch
    task.shuffle_options = payload.shuffle_options
    task.show_result_immediately = payload.show_result_immediately
    task.scope_type = payload.scope_type or "ALL"
    task.target_dept_ids_json = dept_json
    task.target_user_ids_json = user_json

    db.commit()
    db.refresh(task)

    all_depts_map = {d.id: d.name for d in db.query(Department).all()}
    all_users_map = {u.id: (u.full_name or u.username) for u in db.query(User).all()}
    dept_names = [all_depts_map[did] for did in (payload.target_dept_ids or []) if did in all_depts_map]
    user_names = [all_users_map[uid] for uid in (payload.target_user_ids or []) if uid in all_users_map]

    return ExamTaskOut(
        id=task.id,
        title=task.title,
        paper_id=task.paper_id,
        paper_title=paper.title,
        total_score=paper.total_score,
        description=task.description,
        start_time=task.start_time,
        end_time=task.end_time,
        duration_minutes=task.duration_minutes,
        pass_score=task.pass_score,
        max_retries=task.max_retries,
        max_screen_switch=task.max_screen_switch,
        show_result_immediately=task.show_result_immediately,
        is_active=task.is_active,
        scope_type=task.scope_type or "ALL",
        target_dept_ids=payload.target_dept_ids or [],
        target_user_ids=payload.target_user_ids or [],
        target_dept_names=dept_names,
        target_user_names=user_names,
        created_at=task.created_at
    )

@router.post("/{id}/extend", dependencies=[Depends(require_teacher_or_admin)])
def extend_exam_deadline(
    id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    """为考试延期（调整截止时间）"""
    task = db.query(ExamTask).filter(ExamTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Exam task not found")

    new_end_time = payload.get("end_time")
    if new_end_time:
        if isinstance(new_end_time, str):
            task.end_time = datetime.fromisoformat(new_end_time.replace("Z", "+00:00"))
        else:
            task.end_time = new_end_time
    
    db.commit()
    return {"success": True, "message": "考试时间已成功延长", "end_time": task.end_time}

@router.get("/{id}/absentees", dependencies=[Depends(require_teacher_or_admin)])
def get_exam_absentees(id: int, db: Session = Depends(get_db)):
    """获取该考试任务的应考与缺考名单统计"""
    task = db.query(ExamTask).filter(ExamTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Exam task not found")

    # 1. 查询所有应考人员
    all_users = db.query(User).filter(User.is_active == True, User.role == RoleEnum.STUDENT.value).all()
    eligible_users = []
    for u in all_users:
        if check_user_authorized_for_task(u, task, db):
            dept = db.query(Department).filter(Department.id == u.department_id).first() if u.department_id else None
            eligible_users.append({
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "department_name": dept.name if dept else "未分配"
            })

    # 2. 查询已参加的人员 ID
    submitted_user_ids = set(
        r.user_id for r in db.query(ExamRecord.user_id).filter(ExamRecord.exam_task_id == task.id).all()
    )

    # 3. 统计缺考人员
    absentees = [u for u in eligible_users if u["id"] not in submitted_user_ids]
    attendees = [u for u in eligible_users if u["id"] in submitted_user_ids]

    return {
        "total_eligible": len(eligible_users),
        "total_attended": len(attendees),
        "total_absent": len(absentees),
        "absentees": absentees,
        "attendees": attendees
    }

@router.delete("/{id}", dependencies=[Depends(require_teacher_or_admin)])
def delete_exam_task(id: int, db: Session = Depends(get_db)):
    """删除考试任务"""
    task = db.query(ExamTask).filter(ExamTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Exam task not found")
    db.delete(task)
    db.commit()
    return {"success": True, "message": "考务任务已删除"}

# ==================== 考生在线答题流程 ====================

@router.post("/{id}/start")
def start_or_resume_exam(
    id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """考生进入/恢复考试，返回脱敏试卷 Schema 与草稿进度"""
    task = db.query(ExamTask).filter(ExamTask.id == id, ExamTask.is_active == True).first()
    if not task:
        raise HTTPException(status_code=404, detail="Exam task not found or disabled")

    # 校验参考授权
    if not check_user_authorized_for_task(current_user, task, db):
        raise HTTPException(status_code=403, detail="您暂无权限参加本场考试（不在指定部门或人员授权名单中）")

    # 检查开放时间
    now = datetime.utcnow()
    if task.start_time and now < task.start_time:
        raise HTTPException(status_code=400, detail="考试尚未开始")
    if task.end_time and now > task.end_time:
        raise HTTPException(status_code=400, detail="考试已结束")

    paper = db.query(Paper).filter(Paper.id == task.paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # 检查当前考生的记录
    user_records = db.query(ExamRecord).filter(
        ExamRecord.exam_task_id == task.id,
        ExamRecord.user_id == current_user.id
    ).order_by(ExamRecord.id.desc()).all()

    # 查找是否有作答中 (IN_PROGRESS) 的记录
    in_progress_record = next((r for r in user_records if r.status == ExamRecordStatus.IN_PROGRESS.value), None)

    if not in_progress_record:
        # 检查重考次数限制
        finished_count = sum(1 for r in user_records if r.status != ExamRecordStatus.IN_PROGRESS.value)
        if finished_count >= task.max_retries:
            raise HTTPException(status_code=400, detail=f"已达到最大允许考试次数 ({task.max_retries} 次)")

        # 新建考试记录
        in_progress_record = ExamRecord(
            exam_task_id=task.id,
            user_id=current_user.id,
            status=ExamRecordStatus.IN_PROGRESS.value,
            start_time=datetime.utcnow()
        )
        db.add(in_progress_record)
        db.commit()
        db.refresh(in_progress_record)

    # 试卷 Schema 安全脱敏（剥离标准答案和解析）
    raw_schema = json.loads(paper.schema_json)
    sanitized_schema = copy.deepcopy(raw_schema)
    for page in sanitized_schema.get("pages", []):
        for elem in page.get("elements", []):
            cfg = elem.get("exam_config", {})
            cfg.pop("correct_answer", None)
            cfg.pop("analysis", None)

    draft_answers = json.loads(in_progress_record.draft_json) if in_progress_record.draft_json else {}

    return {
        "record_id": in_progress_record.id,
        "exam_task": {
            "id": task.id,
            "title": task.title,
            "duration_minutes": task.duration_minutes,
            "max_screen_switch": task.max_screen_switch,
            "pass_score": task.pass_score,
            "total_score": paper.total_score
        },
        "schema": sanitized_schema,
        "draft_answers": draft_answers,
        "screen_switch_count": in_progress_record.screen_switch_count,
        "duration_seconds": in_progress_record.duration_seconds
    }

@router.put("/records/{record_id}/draft")
def save_exam_draft(
    record_id: int, 
    payload: ExamDraftSave, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """答题心跳与草稿自动暂存（无 Redis 本地落库）"""
    record = db.query(ExamRecord).filter(
        ExamRecord.id == record_id, 
        ExamRecord.user_id == current_user.id
    ).first()
    if not record or record.status != ExamRecordStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=400, detail="Invalid exam record or already submitted")

    record.draft_json = json.dumps(payload.answers, ensure_ascii=False)
    record.screen_switch_count = payload.screen_switch_count
    record.duration_seconds = payload.duration_seconds
    db.commit()
    return {"success": True}

@router.post("/records/{record_id}/submit")
def submit_exam(
    record_id: int, 
    payload: ExamSubmit, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """考生交卷并执行自动判分引擎"""
    record = db.query(ExamRecord).filter(
        ExamRecord.id == record_id, 
        ExamRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.status != ExamRecordStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=400, detail="This exam has already been submitted")

    record.screen_switch_count = payload.screen_switch_count
    record.duration_seconds = payload.duration_seconds

    # 执行判分
    updated_record = grading_service.grade_exam_submission(record, payload.answers, db)
    
    return {
        "success": True,
        "record_id": updated_record.id,
        "status": updated_record.status,
        "objective_score": updated_record.objective_score,
        "total_score": updated_record.total_score,
        "is_passed": updated_record.is_passed,
        "message": "交卷成功！" + ("客观题已完成判分" if updated_record.status == ExamRecordStatus.GRADED.value else "主观题已进入阅卷池，待考官批阅")
    }

@router.get("/records/{record_id}/result")
def get_exam_result(
    record_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """获取考试结果与答卷错题明细解析"""
    record = db.query(ExamRecord).filter(ExamRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    # 仅允许本人、老师或超管查看
    if record.user_id != current_user.id and current_user.role not in ["super_admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    task = db.query(ExamTask).filter(ExamTask.id == record.exam_task_id).first()
    paper = db.query(Paper).filter(Paper.id == task.paper_id).first()
    details = db.query(ExamAnswerDetail).filter(ExamAnswerDetail.record_id == record.id).all()

    # 检查是否允许查看答卷详情与试题解析
    # 超管或出题人始终可见；普通考生由考务设置 show_result_immediately 控制
    allow_view_details = True
    if current_user.role == "student" and task:
        allow_view_details = bool(task.show_result_immediately)

    # 提取试卷结构中的 options 与 analysis
    paper_elements_map = {}
    if paper and paper.schema_json:
        try:
            s_data = json.loads(paper.schema_json) if isinstance(paper.schema_json, str) else paper.schema_json
            for page in s_data.get("pages", []):
                for elem in page.get("elements", []):
                    paper_elements_map[str(elem.get("id"))] = elem
        except Exception:
            pass

    # 组装明细列表
    detail_list = []
    if allow_view_details:
        for d in details:
            u_ans = json.loads(d.user_answer_json) if d.user_answer_json else None
            c_ans = json.loads(d.correct_answer_json) if d.correct_answer_json else []
            elem_data = paper_elements_map.get(str(d.question_id), {})
            options = elem_data.get("options", [])
            analysis = elem_data.get("exam_config", {}).get("analysis", "") or ""

            detail_list.append({
                "id": d.id,
                "question_id": d.question_id,
                "question_type": d.question_type,
                "question_title": d.question_title,
                "knowledge_tag": d.knowledge_tag,
                "max_score": d.max_score,
                "actual_score": d.actual_score,
                "user_answer": u_ans,
                "correct_answer": c_ans,
                "is_correct": d.is_correct,
                "is_graded": d.is_graded,
                "teacher_comment": d.teacher_comment,
                "options": options,
                "analysis": analysis
            })

    return {
        "record": {
            "id": record.id,
            "exam_title": task.title if task else "考试结果",
            "paper_title": paper.title if paper else "试卷",
            "total_paper_score": paper.total_score if paper else 100,
            "pass_score": task.pass_score if task else 60,
            "total_score": record.total_score,
            "objective_score": record.objective_score,
            "subjective_score": record.subjective_score,
            "is_passed": record.is_passed,
            "status": record.status,
            "duration_seconds": record.duration_seconds,
            "screen_switch_count": record.screen_switch_count,
            "submit_time": record.submit_time,
            "allow_view_details": allow_view_details
        },
        "details": detail_list
    }
