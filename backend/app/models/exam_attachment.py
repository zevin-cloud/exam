from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExamAttachment(Base):
    __tablename__ = "exam_attachments"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("exam_records.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(64), nullable=False, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(50), nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    record = relationship("ExamRecord")
    uploader = relationship("User")

