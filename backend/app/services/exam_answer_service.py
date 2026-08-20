import copy
import re
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.exam_attachment import ExamAttachment
from app.models.exam_record import ExamRecord


def normalize_markdown_answers(record: ExamRecord, answers: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """校验附件归属，并以服务端附件信息重建 Markdown 答案快照。"""
    normalized = copy.deepcopy(answers)
    for question_id, answer in list(normalized.items()):
        if not isinstance(answer, dict) or answer.get("format") != "markdown":
            continue
        content = str(answer.get("content") or "")
        attachment_ids = []
        for item in answer.get("attachments") or []:
            raw_id = item.get("id") if isinstance(item, dict) else item
            if str(raw_id).isdigit():
                attachment_ids.append(int(raw_id))
        attachment_ids.extend(int(value) for value in re.findall(r"attachment:(\d+)", content))
        attachment_ids = list(dict.fromkeys(attachment_ids))

        attachments = []
        if attachment_ids:
            rows = db.query(ExamAttachment).filter(ExamAttachment.id.in_(attachment_ids)).all()
            row_map = {row.id: row for row in rows}
            for attachment_id in attachment_ids:
                row = row_map.get(attachment_id)
                if not row or row.record_id != record.id or str(row.question_id) != str(question_id):
                    raise HTTPException(status_code=400, detail="答案中包含无效或不属于本题的图片附件")
                attachments.append({
                    "id": row.id,
                    "name": row.original_name,
                    "content_type": row.content_type,
                    "size": row.size,
                })
        normalized[question_id] = {
            "format": "markdown",
            "content": content,
            "attachments": attachments,
        }
    return normalized
