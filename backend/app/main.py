from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, Department, RoleEnum
from app.models.question import QuestionBank, Question, QuestionType, Difficulty
from app.models.paper import Paper
from app.models.exam import ExamTask
from app.models.exam_record import ExamRecord, ExamAnswerDetail, ExamRecordStatus
from app.api.v1 import api_router

# 自动创建表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 挂载本地文件存储静态目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
def root():
    return {
        "message": "Welcome to Enterprise Exam System API",
        "docs": "/docs",
        "version": "1.0.0"
    }

def init_seed_data():
    """初始化预置种子数据（开箱即用，提供完整演示与测试环境）"""
    db = SessionLocal()
    try:
        # 1. 检查是否存在超管
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # 部门
            dept_tech = Department(sso_dept_id="dept_tech", name="技术研发中心")
            dept_tech_fe = Department(sso_dept_id="dept_tech_fe", name="前端研发组", parent=dept_tech)
            dept_tech_be = Department(sso_dept_id="dept_tech_be", name="后端研发组", parent=dept_tech)
            dept_hr = Department(sso_dept_id="dept_hr", name="人力资源与企业大学")
            dept_ops = Department(sso_dept_id="dept_ops", name="运营与市场部")
            db.add_all([dept_tech, dept_tech_fe, dept_tech_be, dept_hr, dept_ops])
            db.flush()

            # 用户（超管、出题人、考生）
            u_admin = User(
                sso_user_id="emp_001",
                username="admin",
                full_name="系统超级管理员",
                email="admin@company.com",
                role=RoleEnum.SUPER_ADMIN.value,
                department_id=dept_tech.id,
                hashed_password=get_password_hash("admin123"),
                is_active=True
            )
            u_teacher = User(
                sso_user_id="emp_002",
                username="hr_teacher",
                full_name="林主管(HR/出题考官)",
                email="hr@company.com",
                role=RoleEnum.TEACHER.value,
                department_id=dept_hr.id,
                hashed_password=get_password_hash("teacher123"),
                is_active=True
            )
            u_stu1 = User(
                sso_user_id="emp_003",
                username="student_zhang",
                full_name="张小明(后端员工)",
                email="zhang@company.com",
                role=RoleEnum.STUDENT.value,
                department_id=dept_tech_be.id,
                hashed_password=get_password_hash("123456"),
                is_active=True
            )
            u_stu2 = User(
                sso_user_id="emp_004",
                username="student_li",
                full_name="李雅琪(前端员工)",
                email="li@company.com",
                role=RoleEnum.STUDENT.value,
                department_id=dept_tech_fe.id,
                hashed_password=get_password_hash("123456"),
                is_active=True
            )
            u_stu3 = User(
                sso_user_id="emp_005",
                username="student_wang",
                full_name="王小华(运营员工)",
                email="wang@company.com",
                role=RoleEnum.STUDENT.value,
                department_id=dept_ops.id,
                hashed_password=get_password_hash("123456"),
                is_active=True
            )
            db.add_all([u_admin, u_teacher, u_stu1, u_stu2, u_stu3])
            db.flush()

            # 2. 预置题库
            bank = QuestionBank(
                name="2026 企业通用能力与安全规范题库",
                description="涵盖企业信息安全、编码规范、协同沟通及企业文化常识",
                category="入职与合规",
                created_by=u_teacher.id
            )
            db.add(bank)
            db.flush()

            # 预置 5 大题型题目
            q1 = Question(
                bank_id=bank.id,
                type=QuestionType.SINGLE_CHOICE.value,
                title="员工在离开工位或下班时，电脑操作系统的安全要求是？",
                options_json=json.dumps([
                    {"label": "保持开机常亮便于远程", "value": "A"},
                    {"label": "必须锁定屏幕 (Win+L / Cmd+Ctrl+Q)", "value": "B"},
                    {"label": "只关闭显示器电源", "value": "C"},
                    {"label": "让同事帮忙看管", "value": "D"}
                ], ensure_ascii=False),
                answer_json=json.dumps(["B"]),
                analysis="根据公司《信息安全管理条例》，离开工位必须锁屏以防敏感数据泄露。",
                score=10.0,
                difficulty=Difficulty.EASY.value,
                knowledge_tag="信息安全规范"
            )

            q2 = Question(
                bank_id=bank.id,
                type=QuestionType.MULTI_CHOICE.value,
                title="关于公司代码仓库与数据资产保护，以下做法正确的是？",
                options_json=json.dumps([
                    {"label": "严禁将内部业务代码或 Token 上传至公开开源社区", "value": "A"},
                    {"label": "生产环境数据库密码需统一使用配置中心加密管理", "value": "B"},
                    {"label": "离职交接时需清理本地开发环境中的公司敏感数据", "value": "C"},
                    {"label": "为了方便居家办公可以把未脱敏客户数据拷到私有网盘", "value": "D"}
                ], ensure_ascii=False),
                answer_json=json.dumps(["A", "B", "C"]),
                analysis="选项 D 违反《数据安全出境与存储规范》，属于严重违规行为。",
                score=15.0,
                difficulty=Difficulty.MEDIUM.value,
                knowledge_tag="数据安全"
            )

            q3 = Question(
                bank_id=bank.id,
                type=QuestionType.TRUE_FALSE.value,
                title="FastAPI 框架基于 Python 异步协程标准 ASGI 构建，天然支持高性能并发接口开发。",
                answer_json=json.dumps(["true"]),
                analysis="FastAPI 基于 Starlette 与 Pydantic，底层遵循标准 ASGI 异步网关接口。",
                score=10.0,
                difficulty=Difficulty.EASY.value,
                knowledge_tag="技术常识"
            )

            q4 = Question(
                bank_id=bank.id,
                type=QuestionType.FILL_BLANK.value,
                title="在敏捷开发流程中，每天早晨召开的 15 分钟站立会议通常被称为 ____ 会议。",
                answer_json=json.dumps(["Standup", "standup", "站会", "晨会", "Scrum站会"]),
                analysis="Scrum 敏捷站立会议（Daily Standup）用于同步今日计划、昨日进展与阻碍点。",
                score=15.0,
                difficulty=Difficulty.EASY.value,
                knowledge_tag="敏捷开发流程"
            )

            q5 = Question(
                bank_id=bank.id,
                type=QuestionType.ESSAY.value,
                title="请简要阐述：当线上生产环境发生突发故障（P1/P2故障）时，你的标准应急响应与汇报步骤是什么？",
                answer_json=json.dumps(["1. 立即通报故障群；2. 优先止血（降级/回滚/限流）；3. 排查根因修复；4. 复盘复盘报告"]),
                analysis="考核重点：止血优先原则、通报机制、回滚策略及后续复盘文档产出。",
                score=20.0,
                difficulty=Difficulty.HARD.value,
                knowledge_tag="运维应急与流程"
            )

            db.add_all([q1, q2, q3, q4, q5])
            db.flush()

            # 3. 预置 SurveyKing Schema 格式试卷
            schema_data = {
                "pages": [
                    {
                        "id": "page_1",
                        "title": "企业综合能力与安全规范考核试卷",
                        "elements": [
                            {
                                "id": "q_1",
                                "type": "Radio",
                                "title": q1.title,
                                "options": json.loads(q1.options_json),
                                "required": True,
                                "exam_config": {
                                    "score": 10.0,
                                    "correct_answer": ["B"],
                                    "analysis": q1.analysis,
                                    "knowledge_tag": "信息安全规范",
                                    "difficulty": "easy"
                                }
                            },
                            {
                                "id": "q_2",
                                "type": "Checkbox",
                                "title": q2.title,
                                "options": json.loads(q2.options_json),
                                "required": True,
                                "exam_config": {
                                    "score": 15.0,
                                    "correct_answer": ["A", "B", "C"],
                                    "analysis": q2.analysis,
                                    "knowledge_tag": "数据安全",
                                    "difficulty": "medium"
                                }
                            },
                            {
                                "id": "q_3",
                                "type": "TrueFalse",
                                "title": q3.title,
                                "options": [
                                    {"label": "正确", "value": "true"},
                                    {"label": "错误", "value": "false"}
                                ],
                                "required": True,
                                "exam_config": {
                                    "score": 10.0,
                                    "correct_answer": ["true"],
                                    "analysis": q3.analysis,
                                    "knowledge_tag": "技术常识",
                                    "difficulty": "easy"
                                }
                            },
                            {
                                "id": "q_4",
                                "type": "FillBlank",
                                "title": q4.title,
                                "options": [],
                                "required": True,
                                "exam_config": {
                                    "score": 15.0,
                                    "correct_answer": ["Standup", "standup", "站会", "晨会"],
                                    "analysis": q4.analysis,
                                    "knowledge_tag": "敏捷开发流程",
                                    "difficulty": "easy"
                                }
                            },
                            {
                                "id": "q_5",
                                "type": "Textarea",
                                "title": q5.title,
                                "options": [],
                                "required": True,
                                "exam_config": {
                                    "score": 20.0,
                                    "correct_answer": ["1. 立即通报；2. 优先止血降级；3. 排查根因；4. 复盘"],
                                    "analysis": q5.analysis,
                                    "knowledge_tag": "运维应急与流程",
                                    "difficulty": "hard"
                                }
                            }
                        ]
                    }
                ]
            }

            paper = Paper(
                title="2026年企业信息安全与综合业务考核试卷",
                description="本试卷用于全体员工季度合规考核，总分70分，45分及格，作答限时30分钟。",
                category="合规与安全",
                total_score=70.0,
                pass_score=45.0,
                suggest_duration=30,
                schema_json=json.dumps(schema_data, ensure_ascii=False),
                created_by=u_teacher.id,
                is_published=True
            )
            db.add(paper)
            db.flush()

            # 4. 发布考务
            exam_task = ExamTask(
                title="2026 Q1 员工信息安全与规范季度统一考试",
                paper_id=paper.id,
                description="请各位同事在指定时间内完成作答，答题过程中请勿频繁切换屏幕窗口。",
                start_time=datetime.utcnow() - timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=30),
                duration_minutes=30,
                pass_score=45.0,
                max_retries=2,
                max_screen_switch=3,
                show_result_immediately=True,
                created_by=u_teacher.id,
                is_active=True
            )
            db.add(exam_task)
            db.flush()

            # 5. 预置两位考生的作答记录（一份已判分，一份主观题待流水阅卷）
            # 考生1：张小明（已阅完）
            rec1 = ExamRecord(
                exam_task_id=exam_task.id,
                user_id=u_stu1.id,
                status=ExamRecordStatus.GRADED.value,
                objective_score=50.0,
                subjective_score=18.0,
                total_score=68.0,
                is_passed=True,
                duration_seconds=520,
                screen_switch_count=0,
                start_time=datetime.utcnow() - timedelta(hours=3),
                submit_time=datetime.utcnow() - timedelta(hours=2, minutes=50),
                graded_time=datetime.utcnow() - timedelta(hours=2),
                graded_by=u_teacher.id
            )
            db.add(rec1)
            db.flush()

            db.add_all([
                ExamAnswerDetail(
                    record_id=rec1.id, question_id="q_1", question_type="radio",
                    question_title=q1.title, knowledge_tag="信息安全规范", max_score=10.0,
                    actual_score=10.0, user_answer_json=json.dumps("B"), correct_answer_json=json.dumps(["B"]),
                    is_correct=True, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec1.id, question_id="q_2", question_type="checkbox",
                    question_title=q2.title, knowledge_tag="数据安全", max_score=15.0,
                    actual_score=15.0, user_answer_json=json.dumps(["A", "B", "C"]), correct_answer_json=json.dumps(["A", "B", "C"]),
                    is_correct=True, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec1.id, question_id="q_3", question_type="truefalse",
                    question_title=q3.title, knowledge_tag="技术常识", max_score=10.0,
                    actual_score=10.0, user_answer_json=json.dumps("true"), correct_answer_json=json.dumps(["true"]),
                    is_correct=True, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec1.id, question_id="q_4", question_type="fillblank",
                    question_title=q4.title, knowledge_tag="敏捷开发流程", max_score=15.0,
                    actual_score=15.0, user_answer_json=json.dumps("站会"), correct_answer_json=json.dumps(["Standup", "standup", "站会"]),
                    is_correct=True, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec1.id, question_id="q_5", question_type="textarea",
                    question_title=q5.title, knowledge_tag="运维应急与流程", max_score=20.0,
                    actual_score=18.0, user_answer_json=json.dumps("1. 立即通报群内相关责任人\n2. 启动降级与流量限流预案，快速止血\n3. 配合研发定位排查根因并修复\n4. 产出复盘报告"),
                    correct_answer_json=json.dumps(["1. 立即通报；2. 优先止血；3. 排查修复；4. 复盘"]),
                    is_correct=False, is_graded=True, graded_by=u_teacher.id, teacher_comment="应急步骤清晰，止血优先原则表述准确！"
                )
            ])

            # 考生2：王小华（待流水阅卷）
            rec2 = ExamRecord(
                exam_task_id=exam_task.id,
                user_id=u_stu3.id,
                status=ExamRecordStatus.SUBMITTED.value,
                objective_score=35.0,
                subjective_score=0.0,
                total_score=35.0,
                is_passed=False,
                duration_seconds=780,
                screen_switch_count=1,
                start_time=datetime.utcnow() - timedelta(hours=1),
                submit_time=datetime.utcnow() - timedelta(minutes=45)
            )
            db.add(rec2)
            db.flush()

            db.add_all([
                ExamAnswerDetail(
                    record_id=rec2.id, question_id="q_1", question_type="radio",
                    question_title=q1.title, knowledge_tag="信息安全规范", max_score=10.0,
                    actual_score=10.0, user_answer_json=json.dumps("B"), correct_answer_json=json.dumps(["B"]),
                    is_correct=True, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec2.id, question_id="q_2", question_type="checkbox",
                    question_title=q2.title, knowledge_tag="数据安全", max_score=15.0,
                    actual_score=7.5, user_answer_json=json.dumps(["A", "B"]), correct_answer_json=json.dumps(["A", "B", "C"]),
                    is_correct=False, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec2.id, question_id="q_3", question_type="truefalse",
                    question_title=q3.title, knowledge_tag="技术常识", max_score=10.0,
                    actual_score=0.0, user_answer_json=json.dumps("false"), correct_answer_json=json.dumps(["true"]),
                    is_correct=False, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec2.id, question_id="q_4", question_type="fillblank",
                    question_title=q4.title, knowledge_tag="敏捷开发流程", max_score=15.0,
                    actual_score=15.0, user_answer_json=json.dumps("standup"), correct_answer_json=json.dumps(["Standup", "standup", "站会"]),
                    is_correct=True, is_graded=True
                ),
                ExamAnswerDetail(
                    record_id=rec2.id, question_id="q_5", question_type="textarea",
                    question_title=q5.title, knowledge_tag="运维应急与流程", max_score=20.0,
                    actual_score=0.0, user_answer_json=json.dumps("先在工作群里喊一声，然后联系运维人员看日志重启服务。"),
                    correct_answer_json=json.dumps(["1. 立即通报；2. 优先止血；3. 排查修复；4. 复盘"]),
                    is_correct=False, is_graded=False
                )
            ])

            db.commit()
            print("[Init] 数据库种子数据初始化完毕：包含超管、出题人、考生账号及演示考卷！")
    except Exception as e:
        db.rollback()
        print(f"[Init] 种子数据初始化异常: {e}")
    finally:
        db.close()

# 启动时执行数据初始化
init_seed_data()

# =========================================================
# 前端一体化静态托管 (SPA 模式，无需 Nginx)
# =========================================================
from fastapi.responses import FileResponse

candidates = [
    os.getenv("FRONTEND_DIST_DIR", ""),
    "/app/frontend_dist",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
]
frontend_dist = next((p for p in candidates if p and os.path.exists(os.path.join(p, "index.html"))), None)

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # 排除 API 与静态文档
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return None
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
    
    print(f"[SPA] 已成功挂载前端生产资源: {frontend_dist}")

