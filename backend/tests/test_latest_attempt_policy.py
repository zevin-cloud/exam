import json
import io
import unittest

import openpyxl
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all model metadata
from app.core.database import Base
from app.models.exam import ExamTask
from app.models.exam_attachment import ExamAttachment
from app.models.exam_record import ExamAnswerDetail, ExamRecord, ExamRecordStatus
from app.models.paper import Paper
from app.models.user import Department, User
from app.services.analytics_service import AnalyticsService
from app.services.excel_service import ExcelService
from app.services.exam_record_service import latest_finished_record_ids_subquery
from app.services.grading_service import GradingService
from app.services.exam_answer_service import normalize_markdown_answers


class LatestAttemptPolicyTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.user = User(username="candidate", full_name="考生", role="student", is_active=True)
        self.db.add(self.user)
        self.db.flush()

        schema = {
            "pages": [{
                "elements": [{
                    "id": "essay_1",
                    "type": "Textarea",
                    "title": "主观题",
                    "exam_config": {"score": 20, "correct_answer": ["参考答案"]},
                }]
            }]
        }
        self.paper = Paper(title="测试试卷", total_score=20, schema_json=json.dumps(schema))
        self.db.add(self.paper)
        self.db.flush()
        self.task = ExamTask(title="测试考试", paper_id=self.paper.id, pass_score=12, max_retries=3)
        self.db.add(self.task)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def add_record(self, score, status=ExamRecordStatus.GRADED.value):
        record = ExamRecord(
            exam_task_id=self.task.id,
            user_id=self.user.id,
            status=status,
            total_score=score,
            objective_score=score,
            is_passed=score >= self.task.pass_score,
        )
        self.db.add(record)
        self.db.commit()
        return record

    def test_latest_finished_attempt_is_the_only_effective_score(self):
        first = self.add_record(5)
        latest = self.add_record(18)
        latest_ids = latest_finished_record_ids_subquery(self.db, exam_task_id=self.task.id)
        records = self.db.query(ExamRecord).join(
            latest_ids, ExamRecord.id == latest_ids.c.record_id
        ).all()

        self.assertEqual([record.id for record in records], [latest.id])
        self.assertNotEqual(first.id, latest.id)

        report = AnalyticsService.get_exam_analytics(self.task.id, self.db)
        self.assertEqual(report.overview.total_takers, 1)
        self.assertEqual(report.overview.avg_score, 18)
        self.assertEqual(len(report.candidate_rankings), 1)
        self.assertEqual(report.candidate_rankings[0].total_score, 18)

    def test_in_progress_retry_does_not_replace_last_finished_score(self):
        finished = self.add_record(16)
        self.add_record(0, status=ExamRecordStatus.IN_PROGRESS.value)
        latest_ids = latest_finished_record_ids_subquery(self.db, exam_task_id=self.task.id)
        records = self.db.query(ExamRecord).join(
            latest_ids, ExamRecord.id == latest_ids.c.record_id
        ).all()
        self.assertEqual([record.id for record in records], [finished.id])

    def test_latest_pending_review_is_not_counted_as_a_final_score(self):
        self.add_record(16)
        self.add_record(7, status=ExamRecordStatus.SUBMITTED.value)
        report = AnalyticsService.get_exam_analytics(self.task.id, self.db)

        self.assertEqual(report.overview.total_takers, 1)
        self.assertEqual(report.overview.avg_score, 0)
        self.assertEqual(report.overview.pass_rate, 0)
        self.assertEqual(report.candidate_rankings, [])

    def test_blank_subjective_answer_is_auto_graded_zero(self):
        record = self.add_record(0, status=ExamRecordStatus.IN_PROGRESS.value)
        updated = GradingService.grade_exam_submission(record, {}, self.db)
        detail = self.db.query(ExamAnswerDetail).filter_by(record_id=record.id).one()

        self.assertEqual(updated.status, ExamRecordStatus.GRADED.value)
        self.assertTrue(detail.is_graded)
        self.assertEqual(detail.actual_score, 0)

    def test_answered_subjective_question_still_requires_review(self):
        record = self.add_record(0, status=ExamRecordStatus.IN_PROGRESS.value)
        updated = GradingService.grade_exam_submission(
            record, {"essay_1": "这是考生答案"}, self.db
        )
        detail = self.db.query(ExamAnswerDetail).filter_by(record_id=record.id).one()

        self.assertEqual(updated.status, ExamRecordStatus.SUBMITTED.value)
        self.assertFalse(detail.is_graded)

    def test_blank_markdown_subjective_answer_is_auto_graded_zero(self):
        record = self.add_record(0, status=ExamRecordStatus.IN_PROGRESS.value)
        answer = {"format": "markdown", "content": "  ", "attachments": []}
        updated = GradingService.grade_exam_submission(record, {"essay_1": answer}, self.db)
        detail = self.db.query(ExamAnswerDetail).filter_by(record_id=record.id).one()

        self.assertEqual(updated.status, ExamRecordStatus.GRADED.value)
        self.assertTrue(detail.is_graded)

    def test_markdown_attachment_is_validated_and_canonicalized(self):
        record = self.add_record(0, status=ExamRecordStatus.IN_PROGRESS.value)
        attachment = ExamAttachment(
            record_id=record.id,
            question_id="essay_1",
            uploader_id=self.user.id,
            original_name="diagram.png",
            stored_name=f"exam_attachments/{record.id}/diagram.png",
            content_type="image/png",
            size=128,
        )
        self.db.add(attachment)
        self.db.commit()

        normalized = normalize_markdown_answers(record, {
            "essay_1": {
                "format": "markdown",
                "content": f"![架构图](attachment:{attachment.id})",
                "attachments": [{"id": attachment.id, "name": "伪造名称.jpg"}],
            }
        }, self.db)
        saved = normalized["essay_1"]["attachments"][0]
        self.assertEqual(saved["name"], "diagram.png")
        self.assertEqual(saved["content_type"], "image/png")

        with self.assertRaises(HTTPException):
            normalize_markdown_answers(record, {
                "essay_1": {
                    "format": "markdown",
                    "content": "![无效图片](attachment:999999)",
                    "attachments": [],
                }
            }, self.db)

    def test_multidimensional_score_search_and_excel_export(self):
        region = Department(name="南区")
        self.db.add(region)
        self.db.flush()
        department = Department(name="信息安全部", parent_id=region.id)
        self.db.add(department)
        self.db.flush()
        team = Department(name="安全运营组", parent_id=department.id)
        self.db.add(team)
        self.db.flush()
        self.user.department_id = team.id
        self.db.add(self.user)

        self.add_record(5)
        latest = self.add_record(18)
        pending_user = User(
            username="pending-user",
            full_name="待阅员工",
            role="student",
            is_active=True,
            department_id=department.id,
        )
        self.db.add(pending_user)
        self.db.flush()
        pending = ExamRecord(
            exam_task_id=self.task.id,
            user_id=pending_user.id,
            status=ExamRecordStatus.SUBMITTED.value,
            objective_score=7,
            total_score=7,
        )
        self.db.add(pending)
        self.db.commit()

        result = AnalyticsService.search_score_records(
            self.db,
            exam_task_id=self.task.id,
            department_id=region.id,
            sort_by="score_desc",
        )
        self.assertEqual(result.total, 2)
        self.assertEqual(result.summary.scored_count, 1)
        self.assertEqual(result.summary.pending_count, 1)
        self.assertEqual(
            set(AnalyticsService.department_subtree_ids(self.db, region.id)),
            {region.id, department.id, team.id},
        )
        graded = next(item for item in result.items if item.status == ExamRecordStatus.GRADED.value)
        self.assertEqual(graded.record_id, latest.id)
        self.assertEqual(graded.attempt_no, 2)

        passed = AnalyticsService.search_score_records(
            self.db,
            result_status="passed",
            score_min=15,
            keyword="candidate",
        )
        self.assertEqual([item.record_id for item in passed.items], [latest.id])

        excel_bytes = ExcelService.export_exam_scores_to_excel(result.items, "测试成绩明细")
        workbook = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
        worksheet = workbook["成绩明细"]
        self.assertEqual(worksheet["A1"].value, "测试成绩明细")
        self.assertEqual(worksheet.max_row, 6)

    def test_historical_blank_subjective_answer_is_repaired(self):
        record = self.add_record(0, status=ExamRecordStatus.SUBMITTED.value)
        detail = ExamAnswerDetail(
            record_id=record.id,
            question_id="essay_1",
            question_type="textarea",
            question_title="主观题",
            max_score=20,
            actual_score=0,
            user_answer_json=None,
            is_graded=False,
        )
        self.db.add(detail)
        self.db.commit()

        repaired = GradingService.repair_blank_subjective_answers(self.db)
        self.db.refresh(record)
        self.db.refresh(detail)
        self.assertEqual(repaired, 1)
        self.assertTrue(detail.is_graded)
        self.assertEqual(record.status, ExamRecordStatus.GRADED.value)


if __name__ == "__main__":
    unittest.main()
