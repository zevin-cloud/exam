import json
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.exam_record import ExamRecord, ExamAnswerDetail, ExamRecordStatus
from app.models.exam import ExamTask
from app.models.paper import Paper
from app.services.exam_record_service import is_latest_finished_record

class GradingService:
    @staticmethod
    def has_meaningful_answer(answer: Any) -> bool:
        if answer is None:
            return False
        if isinstance(answer, str):
            return bool(answer.strip())
        if isinstance(answer, dict):
            if answer.get("format") == "markdown":
                return bool(str(answer.get("content") or "").strip() or answer.get("attachments"))
            return bool(answer)
        if isinstance(answer, (list, tuple, set)):
            return bool(answer)
        return True

    @classmethod
    def repair_blank_subjective_answers(cls, db: Session) -> int:
        """幂等修复旧数据：空白主观题自动记 0，并完成已无需人工阅卷的答卷。"""
        details = db.query(ExamAnswerDetail).filter(
            ExamAnswerDetail.question_type.in_(["essay", "textarea", "Textarea", "Essay"]),
            ExamAnswerDetail.is_graded == False,
        ).all()
        repaired = 0
        affected_record_ids = set()
        for detail in details:
            try:
                answer = json.loads(detail.user_answer_json) if detail.user_answer_json else None
            except (TypeError, ValueError):
                answer = detail.user_answer_json
            if cls.has_meaningful_answer(answer):
                continue
            detail.actual_score = 0.0
            detail.is_graded = True
            affected_record_ids.add(detail.record_id)
            repaired += 1

        for record_id in affected_record_ids:
            record = db.query(ExamRecord).filter(ExamRecord.id == record_id).first()
            record_details = db.query(ExamAnswerDetail).filter(
                ExamAnswerDetail.record_id == record_id
            ).all()
            if not record or not record_details or not all(item.is_graded for item in record_details):
                continue
            task = db.query(ExamTask).filter(ExamTask.id == record.exam_task_id).first()
            record.subjective_score = sum(
                item.actual_score or 0.0
                for item in record_details
                if item.question_type.lower() in ("essay", "textarea")
            )
            record.total_score = (record.objective_score or 0.0) + record.subjective_score
            record.status = ExamRecordStatus.GRADED.value
            record.is_passed = bool(task and record.total_score >= task.pass_score)
            record.graded_time = record.graded_time or datetime.utcnow()

        if repaired:
            db.commit()
        return repaired

    @staticmethod
    def extract_paper_elements(schema_json: str) -> List[Dict[str, Any]]:
        """从 SurveyKing 试卷 Schema JSON 中提取所有题目定义"""
        try:
            data = json.loads(schema_json)
            elements = []
            pages = data.get("pages", [])
            for page in pages:
                for elem in page.get("elements", []):
                    elements.append(elem)
            return elements
        except Exception:
            return []

    @classmethod
    def grade_exam_submission(
        cls, 
        record: ExamRecord, 
        user_answers: Dict[str, Any], 
        db: Session
    ) -> ExamRecord:
        """考生交卷判分核心引擎"""
        exam_task = db.query(ExamTask).filter(ExamTask.id == record.exam_task_id).first()
        paper = db.query(Paper).filter(Paper.id == exam_task.paper_id).first()
        
        elements = cls.extract_paper_elements(paper.schema_json)
        
        objective_total = 0.0
        has_pending_subjective = False
        
        # 清除旧的答题明细（防止重考残留）
        db.query(ExamAnswerDetail).filter(ExamAnswerDetail.record_id == record.id).delete()

        for elem in elements:
            q_id = elem.get("id")
            q_type = elem.get("type", "Radio").lower() # radio, checkbox, truefalse, fillblank, textarea
            q_title = elem.get("title", "")
            exam_config = elem.get("exam_config", {})
            
            max_score = float(exam_config.get("score", 5.0))
            correct_ans = exam_config.get("correct_answer", [])
            knowledge_tag = exam_config.get("knowledge_tag", "通用知识")
            
            # 考生提交的答案
            user_ans = user_answers.get(q_id)
            
            actual_score = 0.0
            is_correct = False
            is_graded = True # 默认客观题为已评阅

            # 1. 单选
            if q_type in ["radio", "single_choice"]:
                u_val = str(user_ans).strip().upper() if user_ans is not None else ""
                c_vals = [str(x).strip().upper() for x in correct_ans]
                if u_val and (u_val in c_vals):
                    actual_score = max_score
                    is_correct = True
                objective_total += actual_score

            # 2. 多选
            elif q_type in ["checkbox", "multi_choice"]:
                u_set = set([str(x).strip().upper() for x in user_ans]) if isinstance(user_ans, list) else set()
                c_set = set([str(x).strip().upper() for x in correct_ans])
                if u_set and u_set == c_set:
                    actual_score = max_score
                    is_correct = True
                elif u_set and u_set.issubset(c_set):
                    # 漏选给一半分
                    actual_score = round(max_score / 2.0, 1)
                objective_total += actual_score

            # 3. 判断
            elif q_type in ["truefalse", "true_false"]:
                u_val = str(user_ans).lower() if user_ans is not None else ""
                c_val = str(correct_ans[0]).lower() if correct_ans else "true"
                # 统一为 true / false
                u_val = "true" if u_val in ["true", "1", "对", "正确"] else ("false" if u_val in ["false", "0", "错", "错误"] else u_val)
                c_val = "true" if c_val in ["true", "1", "对", "正确"] else "false"
                if u_val == c_val:
                    actual_score = max_score
                    is_correct = True
                objective_total += actual_score

            # 4. 填空
            elif q_type in ["fillblank", "fill_blank"]:
                u_text = str(user_ans).strip().lower() if user_ans is not None else ""
                # 只要命中任意一个预设标准答案关键字即得分
                matched = False
                for ca in correct_ans:
                    if str(ca).strip().lower() == u_text:
                        matched = True
                        break
                if matched and u_text != "":
                    actual_score = max_score
                    is_correct = True
                objective_total += actual_score

            # 5. 简答/问答（主观题）
            else:
                # 未作答主观题直接记 0 分，不进入人工阅卷池。
                is_graded = not cls.has_meaningful_answer(user_ans)
                has_pending_subjective = has_pending_subjective or not is_graded
                actual_score = 0.0 # 待考官打分

            # 创建单题明细
            detail = ExamAnswerDetail(
                record_id=record.id,
                question_id=q_id,
                question_type=q_type,
                question_title=q_title,
                knowledge_tag=knowledge_tag,
                max_score=max_score,
                actual_score=actual_score,
                user_answer_json=json.dumps(user_ans, ensure_ascii=False) if user_ans is not None else None,
                correct_answer_json=json.dumps(correct_ans, ensure_ascii=False),
                is_correct=is_correct,
                is_graded=is_graded
            )
            db.add(detail)

        # 更新记录总分与状态
        record.objective_score = objective_total
        record.submit_time = datetime.utcnow()
        record.submit_json = json.dumps(user_answers, ensure_ascii=False)

        if not has_pending_subjective:
            # 纯客观卷或主观题均未作答：直接完成判分归档。
            record.subjective_score = 0.0
            record.total_score = objective_total
            record.status = ExamRecordStatus.GRADED.value
            record.is_passed = (record.total_score >= exam_task.pass_score)
            record.graded_time = datetime.utcnow()
        else:
            # 含有主观题：进入待阅卷池
            record.total_score = objective_total
            record.status = ExamRecordStatus.SUBMITTED.value
            record.is_passed = False

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def grade_subjective_detail(
        cls, 
        detail_id: int, 
        grader_id: int, 
        score: float, 
        comment: str, 
        db: Session
    ) -> ExamAnswerDetail:
        """主观题流水阅卷打分"""
        detail = db.query(ExamAnswerDetail).filter(ExamAnswerDetail.id == detail_id).first()
        if not detail:
            raise ValueError("Detail item not found")
        
        detail.actual_score = min(max(score, 0.0), detail.max_score)
        detail.teacher_comment = comment
        detail.graded_by = grader_id
        detail.is_graded = True
        
        # 检查该试卷的所有主观题是否均已阅完
        record = db.query(ExamRecord).filter(ExamRecord.id == detail.record_id).first()
        if not record or not is_latest_finished_record(record, db):
            raise ValueError("该答卷不是考生本场考试最后一次有效答卷，不能继续计入最终成绩")
        all_details = db.query(ExamAnswerDetail).filter(ExamAnswerDetail.record_id == record.id).all()
        
        all_graded = all(d.is_graded for d in all_details)
        if all_graded:
            subj_total = sum(d.actual_score for d in all_details if d.question_type in ["essay", "textarea"])
            record.subjective_score = subj_total
            record.total_score = record.objective_score + subj_total
            record.status = ExamRecordStatus.GRADED.value
            
            exam_task = db.query(ExamTask).filter(ExamTask.id == record.exam_task_id).first()
            record.is_passed = (record.total_score >= exam_task.pass_score)
            record.graded_time = datetime.utcnow()
            record.graded_by = grader_id

        db.commit()
        db.refresh(detail)
        return detail

grading_service = GradingService()
