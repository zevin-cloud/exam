import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.exam_record import ExamRecord, ExamAnswerDetail, ExamRecordStatus
from app.models.exam import ExamTask
from app.models.user import User, Department
from app.schemas.analytics_schema import (
    AnalyticsReportOut, OverviewStats, DeptPassRateItem, 
    WrongQuestionItem, KnowledgeRadarItem, ScoreDistributionItem,
    CandidateRankItem, ExamInfoBrief
)

class AnalyticsService:
    @staticmethod
    def get_exam_analytics(exam_task_id: Optional[int], db: Session) -> AnalyticsReportOut:
        """生成考试分析大盘数据（支持全部或指定某场考试）"""
        record_query = db.query(ExamRecord).filter(ExamRecord.status.in_([ExamRecordStatus.GRADED.value, ExamRecordStatus.SUBMITTED.value]))
        current_task = None
        exam_info = None

        if exam_task_id:
            record_query = record_query.filter(ExamRecord.exam_task_id == exam_task_id)
            current_task = db.query(ExamTask).filter(ExamTask.id == exam_task_id).first()
            if current_task:
                exam_info = ExamInfoBrief(
                    id=current_task.id,
                    title=current_task.title,
                    total_score=current_task.paper.total_score if current_task.paper else 100.0,
                    pass_score=current_task.pass_score
                )

        graded_records = record_query.all()
        total_records_count = len(graded_records)

        # 1. 总体大盘数据
        total_exams = db.query(ExamTask).count() if not exam_task_id else 1
        total_takers = total_records_count
        all_scores = [r.total_score for r in graded_records] if graded_records else [0.0]
        avg_score = round(sum(all_scores) / max(total_records_count, 1), 1) if graded_records else 0.0
        max_score = max(all_scores) if graded_records else 0.0
        min_score = min(all_scores) if graded_records else 0.0
        passed_count = sum(1 for r in graded_records if r.is_passed)
        pass_rate = round((passed_count / max(total_records_count, 1)) * 100.0, 1) if graded_records else 0.0

        # 应考人数与缺考统计
        total_users_count = db.query(User).filter(User.username != "admin").count()
        total_eligible = total_users_count
        if current_task and current_task.scope_type == "USER" and current_task.target_user_ids_json:
            try:
                u_ids = json.loads(current_task.target_user_ids_json)
                total_eligible = len(u_ids)
            except Exception:
                pass
        total_absent = max(0, total_eligible - total_takers)

        overview = OverviewStats(
            total_exams=total_exams,
            total_takers=total_takers,
            avg_score=avg_score,
            pass_rate=pass_rate,
            max_score=max_score,
            min_score=min_score,
            total_eligible=total_eligible,
            total_absent=total_absent
        )

        # 2. 成绩分布区间 (四分段)
        dist_90_100 = sum(1 for s in all_scores if s >= 90) if graded_records else 0
        dist_80_89 = sum(1 for s in all_scores if 80 <= s < 90) if graded_records else 0
        dist_60_79 = sum(1 for s in all_scores if 60 <= s < 80) if graded_records else 0
        dist_under_60 = sum(1 for s in all_scores if s < 60) if graded_records else 0

        score_distribution = [
            ScoreDistributionItem(
                label="90-100分 (优秀)",
                count=dist_90_100,
                percentage=round((dist_90_100 / max(total_records_count, 1)) * 100.0, 1) if graded_records else 0.0
            ),
            ScoreDistributionItem(
                label="80-89分 (良好)",
                count=dist_80_89,
                percentage=round((dist_80_89 / max(total_records_count, 1)) * 100.0, 1) if graded_records else 0.0
            ),
            ScoreDistributionItem(
                label="60-79分 (合格)",
                count=dist_60_79,
                percentage=round((dist_60_79 / max(total_records_count, 1)) * 100.0, 1) if graded_records else 0.0
            ),
            ScoreDistributionItem(
                label="<60分 (待提升)",
                count=dist_under_60,
                percentage=round((dist_under_60 / max(total_records_count, 1)) * 100.0, 1) if graded_records else 0.0
            )
        ]

        # 3. 部门通过率与平均分对比
        all_depts_map = {d.id: d.name for d in db.query(Department).all()}
        all_users_dict = {u.id: u for u in db.query(User).all()}

        dept_stats_map = {} # dept_name -> {total, pass, scores: []}
        for r in graded_records:
            u = all_users_dict.get(r.user_id)
            dept_name = all_depts_map.get(u.department_id, "未分配部门") if u and u.department_id else "综合部门"
            if dept_name not in dept_stats_map:
                dept_stats_map[dept_name] = {"total": 0, "pass": 0, "scores": []}
            dept_stats_map[dept_name]["total"] += 1
            if r.is_passed:
                dept_stats_map[dept_name]["pass"] += 1
            dept_stats_map[dept_name]["scores"].append(r.total_score)

        dept_stats = []
        for d_name, stats in dept_stats_map.items():
            tot = stats["total"]
            pas = stats["pass"]
            p_rate = round((pas / max(tot, 1)) * 100.0, 1)
            d_avg = round(sum(stats["scores"]) / max(tot, 1), 1)
            dept_stats.append(DeptPassRateItem(
                dept_name=d_name,
                total_count=tot,
                pass_count=pas,
                pass_rate=p_rate,
                avg_score=d_avg
            ))
        dept_stats.sort(key=lambda x: (x.pass_rate, x.avg_score), reverse=True)

        # 4. 错题率 Top 排行榜
        detail_query = db.query(ExamAnswerDetail).join(ExamRecord).filter(
            ExamRecord.status.in_([ExamRecordStatus.GRADED.value, ExamRecordStatus.SUBMITTED.value])
        )
        if exam_task_id:
            detail_query = detail_query.filter(ExamRecord.exam_task_id == exam_task_id)

        all_details = detail_query.all()
        q_map = {} # question_id -> {title, type, tag, total, wrong}
        for d in all_details:
            qid = str(d.question_id)
            if qid not in q_map:
                q_map[qid] = {
                    "title": d.question_title,
                    "type": d.question_type,
                    "tag": d.knowledge_tag or "通用素养",
                    "total": 0,
                    "wrong": 0
                }
            q_map[qid]["total"] += 1
            if not d.is_correct and (d.actual_score or 0) < d.max_score:
                q_map[qid]["wrong"] += 1

        wrong_questions = []
        for qid, data in q_map.items():
            err_rate = round((data["wrong"] / max(data["total"], 1)) * 100.0, 1)
            wrong_questions.append(WrongQuestionItem(
                question_title=data["title"][:45] + ("..." if len(data["title"]) > 45 else ""),
                question_type=data["type"],
                knowledge_tag=data["tag"],
                total_attempts=data["total"],
                wrong_count=data["wrong"],
                error_rate=err_rate
            ))
        wrong_questions.sort(key=lambda x: (x.error_rate, x.wrong_count), reverse=True)
        top_wrong = wrong_questions[:8]

        # 5. 知识盲区与技能掌握度
        tag_map = {}
        for d in all_details:
            t = d.knowledge_tag or "专业素养"
            if t not in tag_map:
                tag_map[t] = {"total": 0, "wrong": 0}
            tag_map[t]["total"] += 1
            if not d.is_correct and (d.actual_score or 0) < d.max_score:
                tag_map[t]["wrong"] += 1

        knowledge_radar = []
        for tag, data in tag_map.items():
            tot = data["total"]
            wr = data["wrong"]
            err_r = (wr / max(tot, 1)) * 100.0
            mastery = round(max(0.0, 100.0 - err_r), 1)
            knowledge_radar.append(KnowledgeRadarItem(
                tag=tag,
                mastery_rate=mastery,
                wrong_count=wr,
                total_count=tot
            ))
        knowledge_radar.sort(key=lambda x: x.mastery_rate)

        # 6. 考生得分排名总榜
        sorted_records = sorted(graded_records, key=lambda x: (x.total_score, -x.duration_seconds), reverse=True)
        candidate_rankings = []
        for rank_idx, r in enumerate(sorted_records[:15]):
            u = all_users_dict.get(r.user_id)
            u_name = u.full_name if u else f"考生 #{r.user_id}"
            dept_name = all_depts_map.get(u.department_id, "未分配部门") if u and u.department_id else "综合部"
            candidate_rankings.append(CandidateRankItem(
                rank=rank_idx + 1,
                student_id=r.user_id,
                student_name=u_name,
                department_name=dept_name,
                total_score=r.total_score,
                is_passed=r.is_passed,
                duration_seconds=r.duration_seconds or 0,
                submit_time=r.submit_time
            ))

        return AnalyticsReportOut(
            overview=overview,
            exam_info=exam_info,
            dept_stats=dept_stats,
            wrong_top_questions=top_wrong,
            knowledge_radar=knowledge_radar,
            score_distribution=score_distribution,
            candidate_rankings=candidate_rankings
        )

analytics_service = AnalyticsService()
