from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.exam_record import ExamRecord, ExamRecordStatus


FINISHED_RECORD_STATUSES = (
    ExamRecordStatus.SUBMITTED.value,
    ExamRecordStatus.GRADED.value,
)


def latest_finished_record_ids_subquery(
    db: Session,
    exam_task_id: Optional[int] = None,
):
    """每位考生每场考试最后一次已交卷记录 ID。进行中的重考不替换已有成绩。"""
    query = db.query(func.max(ExamRecord.id).label("record_id")).filter(
        ExamRecord.status.in_(FINISHED_RECORD_STATUSES)
    )
    if exam_task_id is not None:
        query = query.filter(ExamRecord.exam_task_id == exam_task_id)
    return query.group_by(ExamRecord.exam_task_id, ExamRecord.user_id).subquery()


def is_latest_finished_record(record: ExamRecord, db: Session) -> bool:
    latest_id = db.query(func.max(ExamRecord.id)).filter(
        ExamRecord.exam_task_id == record.exam_task_id,
        ExamRecord.user_id == record.user_id,
        ExamRecord.status.in_(FINISHED_RECORD_STATUSES),
    ).scalar()
    return latest_id == record.id

