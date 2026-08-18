from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.core.database import get_db
from app.models.question import Question, QuestionBank, QuestionType
from app.schemas.question_schema import (
    QuestionOut, QuestionCreate, QuestionUpdate, 
    QuestionBankOut, QuestionBankCreate
)
from app.services.excel_service import ExcelService
from app.api.deps import require_teacher_or_admin

router = APIRouter()

# ==================== 题库分类/题库池 ====================

@router.get("/banks", response_model=List[QuestionBankOut])
def list_question_banks(db: Session = Depends(get_db)):
    banks = db.query(QuestionBank).all()
    result = []
    for b in banks:
        count = db.query(Question).filter(Question.bank_id == b.id).count()
        result.append(QuestionBankOut(
            id=b.id,
            name=b.name,
            description=b.description,
            category=b.category,
            question_count=count,
            created_at=b.created_at
        ))
    return result

@router.post("/banks", response_model=QuestionBankOut, dependencies=[Depends(require_teacher_or_admin)])
def create_question_bank(payload: QuestionBankCreate, db: Session = Depends(get_db)):
    bank = QuestionBank(
        name=payload.name,
        description=payload.description,
        category=payload.category
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return QuestionBankOut(
        id=bank.id,
        name=bank.name,
        description=bank.description,
        category=bank.category,
        question_count=0,
        created_at=bank.created_at
    )

# ==================== 题目管理 ====================

def _format_question_out(q: Question) -> QuestionOut:
    options = json.loads(q.options_json) if q.options_json else []
    answer = json.loads(q.answer_json) if q.answer_json else []
    return QuestionOut(
        id=q.id,
        bank_id=q.bank_id,
        type=q.type,
        title=q.title,
        options=options,
        answer=answer,
        analysis=q.analysis or "",
        score=q.score,
        difficulty=q.difficulty,
        knowledge_tag=q.knowledge_tag or "通用",
        created_at=q.created_at
    )

@router.get("", response_model=List[QuestionOut])
def list_questions(
    bank_id: Optional[int] = None,
    type: Optional[str] = None,
    knowledge_tag: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Question)
    if bank_id:
        query = query.filter(Question.bank_id == bank_id)
    if type:
        query = query.filter(Question.type == type)
    if knowledge_tag:
        query = query.filter(Question.knowledge_tag == knowledge_tag)
    if keyword:
        query = query.filter(Question.title.contains(keyword))

    questions = query.order_by(Question.id.desc()).all()
    return [_format_question_out(q) for q in questions]

@router.post("", response_model=QuestionOut, dependencies=[Depends(require_teacher_or_admin)])
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    question = Question(
        bank_id=payload.bank_id,
        type=payload.type,
        title=payload.title,
        options_json=json.dumps([opt.dict() for opt in payload.options], ensure_ascii=False) if payload.options else None,
        answer_json=json.dumps(payload.answer, ensure_ascii=False),
        analysis=payload.analysis,
        score=payload.score,
        difficulty=payload.difficulty,
        knowledge_tag=payload.knowledge_tag
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return _format_question_out(question)

@router.put("/{id}", response_model=QuestionOut, dependencies=[Depends(require_teacher_or_admin)])
def update_question(id: int, payload: QuestionUpdate, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    q.bank_id = payload.bank_id
    q.type = payload.type
    q.title = payload.title
    q.options_json = json.dumps([opt.dict() for opt in payload.options], ensure_ascii=False) if payload.options else None
    q.answer_json = json.dumps(payload.answer, ensure_ascii=False)
    q.analysis = payload.analysis
    q.score = payload.score
    q.difficulty = payload.difficulty
    q.knowledge_tag = payload.knowledge_tag

    db.commit()
    db.refresh(q)
    return _format_question_out(q)

@router.delete("/{id}", dependencies=[Depends(require_teacher_or_admin)])
def delete_question(id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"success": True, "message": "题目已删除"}

# ==================== Excel 模板与批量导入导出 ====================

@router.get("/template/excel")
def download_excel_template():
    """下载题库批量导入 Excel 模板"""
    excel_bytes = ExcelService.generate_template_bytes()
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=question_import_template.xlsx"}
    )

@router.post("/import/excel", dependencies=[Depends(require_teacher_or_admin)])
async def import_questions_excel(
    file: UploadFile = File(...),
    bank_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """上传 Excel 批量导入题目"""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="请上传 .xlsx 或 .xls 格式的 Excel 文件")

    content = await file.read()
    try:
        success_count, errors = ExcelService.parse_and_import_excel(content, bank_id, db)
        return {
            "success": True,
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors,
            "message": f"成功导入 {success_count} 道题目" + (f"，有 {len(errors)} 条数据异常" if errors else "")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析 Excel 失败: {str(e)}")

@router.get("/export/excel")
def export_questions_excel(bank_id: Optional[int] = None, db: Session = Depends(get_db)):
    """导出题库为 Excel 文件"""
    query = db.query(Question)
    if bank_id:
        query = query.filter(Question.bank_id == bank_id)
    questions = query.all()
    
    excel_bytes = ExcelService.export_questions_to_excel(questions)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=question_bank_export.xlsx"}
    )
