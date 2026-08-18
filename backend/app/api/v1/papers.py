from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from app.core.database import get_db
from app.models.paper import Paper
from app.models.question import Question
from app.models.user import User
from app.schemas.paper_schema import PaperOut, PaperCreate, PaperUpdate
from app.api.deps import require_teacher_or_admin, get_current_user
from pydantic import BaseModel

router = APIRouter()

class GenerateFromBankRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "综合"
    suggest_duration: int = 60
    pass_score: float = 60.0
    question_ids: List[int]

def _format_paper_out(p: Paper) -> PaperOut:
    schema_data = json.loads(p.schema_json) if p.schema_json else {"pages": []}
    return PaperOut(
        id=p.id,
        title=p.title,
        description=p.description,
        category=p.category,
        total_score=p.total_score,
        pass_score=p.pass_score,
        suggest_duration=p.suggest_duration,
        schema_data=schema_data,
        created_by=p.created_by,
        is_published=p.is_published,
        created_at=p.created_at
    )

@router.get("", response_model=List[PaperOut])
def list_papers(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Paper)
    if category:
        query = query.filter(Paper.category == category)
    papers = query.order_by(Paper.id.desc()).all()
    return [_format_paper_out(p) for p in papers]

@router.get("/{id}", response_model=PaperOut)
def get_paper(id: int, db: Session = Depends(get_db)):
    p = db.query(Paper).filter(Paper.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    return _format_paper_out(p)

@router.post("", response_model=PaperOut, dependencies=[Depends(require_teacher_or_admin)])
def create_paper(payload: PaperCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    schema_str = json.dumps(payload.schema_data.dict(), ensure_ascii=False)
    
    # 自动汇总计算试卷总分
    calculated_total = 0.0
    for page in payload.schema_data.pages:
        for elem in page.elements:
            calculated_total += elem.exam_config.score
    
    paper = Paper(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        total_score=calculated_total if calculated_total > 0 else payload.total_score,
        pass_score=payload.pass_score,
        suggest_duration=payload.suggest_duration,
        schema_json=schema_str,
        created_by=current_user.id,
        is_published=True
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return _format_paper_out(paper)

@router.put("/{id}", response_model=PaperOut, dependencies=[Depends(require_teacher_or_admin)])
def update_paper(id: int, payload: PaperUpdate, db: Session = Depends(get_db)):
    p = db.query(Paper).filter(Paper.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")

    if payload.title is not None: p.title = payload.title
    if payload.description is not None: p.description = payload.description
    if payload.category is not None: p.category = payload.category
    if payload.suggest_duration is not None: p.suggest_duration = payload.suggest_duration
    if payload.pass_score is not None: p.pass_score = payload.pass_score
    if payload.schema_data is not None:
        p.schema_json = json.dumps(payload.schema_data.dict(), ensure_ascii=False)
        calculated_total = 0.0
        for page in payload.schema_data.pages:
            for elem in page.elements:
                calculated_total += elem.exam_config.score
        p.total_score = calculated_total if calculated_total > 0 else (payload.total_score or p.total_score)

    db.commit()
    db.refresh(p)
    return _format_paper_out(p)

@router.post("/generate-from-bank", response_model=PaperOut, dependencies=[Depends(require_teacher_or_admin)])
def generate_paper_from_bank(
    payload: GenerateFromBankRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从题库选题一键生成 SurveyKing 规范的试卷"""
    questions = db.query(Question).filter(Question.id.in_(payload.question_ids)).all()
    if not questions:
        raise HTTPException(status_code=400, detail="未找到选中的题目")

    type_to_elem_type = {
        "single_choice": "Radio",
        "multi_choice": "Checkbox",
        "true_false": "TrueFalse",
        "fill_blank": "FillBlank",
        "essay": "Textarea",
    }

    elements = []
    total_score = 0.0
    for idx, q in enumerate(questions, 1):
        total_score += q.score
        opts = json.loads(q.options_json) if q.options_json else []
        ans = json.loads(q.answer_json) if q.answer_json else []
        
        elem_options = []
        for o in opts:
            elem_options.append({"label": o.get("label"), "value": o.get("value")})

        elements.append({
            "id": f"q_{q.id}_{idx}",
            "type": type_to_elem_type.get(q.type, "Radio"),
            "title": q.title,
            "options": elem_options,
            "required": True,
            "exam_config": {
                "score": q.score,
                "correct_answer": ans,
                "analysis": q.analysis or "",
                "knowledge_tag": q.knowledge_tag or "通用知识",
                "difficulty": q.difficulty
            }
        })

    schema_data = {
        "pages": [
            {
                "id": "page_1",
                "title": payload.title,
                "elements": elements
            }
        ]
    }

    paper = Paper(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        total_score=total_score,
        pass_score=payload.pass_score,
        suggest_duration=payload.suggest_duration,
        schema_json=json.dumps(schema_data, ensure_ascii=False),
        created_by=current_user.id,
        is_published=True
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return _format_paper_out(paper)

@router.delete("/{id}", dependencies=[Depends(require_teacher_or_admin)])
def delete_paper(id: int, db: Session = Depends(get_db)):
    p = db.query(Paper).filter(Paper.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Paper not found")
    db.delete(p)
    db.commit()
    return {"success": True, "message": "试卷已删除"}
