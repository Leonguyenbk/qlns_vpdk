"""Model module Khảo sát – Đánh giá mức độ hài lòng.

Nguyên tắc bất biến dữ liệu lịch sử: khi một câu hỏi/phương án ĐÃ có câu trả lời,
sửa nội dung (question_text/question_type hoặc option_text/option_value) không
ghi đè bản ghi cũ — service tạo bản ghi mới và chuyển bản cũ sang `is_active=False`
(xem `app/services/survey_question_service.py`). Nhờ vậy `survey_answers` luôn trỏ
tới đúng nội dung câu hỏi/phương án tại thời điểm người dân trả lời.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin

SURVEY_STATUSES = {"draft", "active", "paused", "closed", "archived"}

QUESTION_TYPES = {
    "single_choice",
    "multiple_choice",
    "yes_no",
    "rating",
    "text",
    "textarea",
    "number",
    "date",
}

# Loại câu hỏi cần danh sách phương án trả lời (option) đi kèm.
QUESTION_TYPES_WITH_OPTIONS = {"single_choice", "multiple_choice"}


def _iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value else None


class Survey(TimestampMixin, db.Model):
    __tablename__ = "surveys"
    __table_args__ = (UniqueConstraint("slug", name="uq_surveys_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    # Lời chào hiển thị đầu trang khảo sát công khai, trước khi chọn chi
    # nhánh/nhập thông tin — khác với `description` (mô tả ngắn dưới tiêu đề).
    welcome_message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    questions: Mapped[list["SurveyQuestion"]] = relationship(
        "SurveyQuestion",
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="SurveyQuestion.sort_order",
    )
    creator = relationship("User")

    def to_dict(self, *, counts: dict | None = None) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "welcome_message": self.welcome_message,
            "status": self.status,
            "is_anonymous": self.is_anonymous,
            "start_at": _iso(self.start_at),
            "end_at": _iso(self.end_at),
            "created_by": self.created_by,
            "created_by_name": self.creator.full_name if self.creator else None,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if counts:
            data["question_count"] = counts.get("question_count", 0)
            data["response_count"] = counts.get("response_count", 0)
        return data


class SurveyQuestion(TimestampMixin, db.Model):
    __tablename__ = "survey_questions"
    __table_args__ = (
        Index("ix_survey_questions_survey_id", "survey_id"),
        Index("ix_survey_questions_sort_order", "survey_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    survey_id: Mapped[int] = mapped_column(
        ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    survey: Mapped["Survey"] = relationship("Survey", back_populates="questions")
    options: Mapped[list["SurveyOption"]] = relationship(
        "SurveyOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="SurveyOption.sort_order",
    )

    def to_dict(self, *, include_options: bool = True, only_active_options: bool = False) -> dict:
        data = {
            "id": self.id,
            "survey_id": self.survey_id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "is_required": self.is_required,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if include_options:
            opts = self.options
            if only_active_options:
                opts = [o for o in opts if o.is_active]
            data["options"] = [o.to_dict() for o in opts]
        return data


class SurveyOption(TimestampMixin, db.Model):
    __tablename__ = "survey_options"
    __table_args__ = (
        Index("ix_survey_options_question_id", "question_id"),
        Index("ix_survey_options_sort_order", "question_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("survey_questions.id", ondelete="CASCADE"), nullable=False
    )
    option_text: Mapped[str] = mapped_column(String(500), nullable=False)
    option_value: Mapped[str | None] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    question: Mapped["SurveyQuestion"] = relationship("SurveyQuestion", back_populates="options")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "option_text": self.option_text,
            "option_value": self.option_value,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }


class SurveyResponse(TimestampMixin, db.Model):
    __tablename__ = "survey_responses"
    __table_args__ = (
        UniqueConstraint("survey_id", "client_token", name="uq_survey_response_client_token"),
        Index("ix_survey_responses_survey_id", "survey_id"),
        Index("ix_survey_responses_submitted_at", "submitted_at"),
        Index("ix_survey_responses_branch_id", "branch_id"),
        Index("ix_survey_responses_service_id", "service_id"),
        Index("ix_survey_responses_employee_id", "employee_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    survey_id: Mapped[int] = mapped_column(
        ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    # Chuẩn bị tích hợp hệ thống lấy số/kiosk trong tương lai.
    branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True
    )
    service_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    counter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    respondent_name: Mapped[str | None] = mapped_column(String(255))
    respondent_phone: Mapped[str | None] = mapped_column(String(20))
    respondent_email: Mapped[str | None] = mapped_column(String(120))
    respondent_address: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    # Token do client sinh (UUID) để chống submit trùng do double-click/mất mạng.
    client_token: Mapped[str | None] = mapped_column(String(64))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    survey = relationship("Survey")
    branch = relationship("OrganizationUnit")
    employee = relationship("Employee")
    answers: Mapped[list["SurveyAnswer"]] = relationship(
        "SurveyAnswer", back_populates="response", cascade="all, delete-orphan"
    )

    def to_dict(self, *, include_answers: bool = False) -> dict:
        data = {
            "id": self.id,
            "survey_id": self.survey_id,
            "branch_id": self.branch_id,
            "branch_name": self.branch.name if self.branch else None,
            "service_id": self.service_id,
            "counter_id": self.counter_id,
            "employee_id": self.employee_id,
            "employee_name": self.employee.full_name if self.employee else None,
            "respondent_name": self.respondent_name,
            "respondent_phone": self.respondent_phone,
            "respondent_email": self.respondent_email,
            "respondent_address": self.respondent_address,
            "submitted_at": _iso(self.submitted_at),
        }
        if include_answers:
            data["answers"] = [a.to_dict() for a in self.answers]
        return data


class SurveyAnswer(TimestampMixin, db.Model):
    __tablename__ = "survey_answers"
    __table_args__ = (
        Index("ix_survey_answers_response_id", "response_id"),
        Index("ix_survey_answers_question_id", "question_id"),
        Index("ix_survey_answers_option_id", "option_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    response_id: Mapped[int] = mapped_column(
        ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("survey_questions.id", ondelete="RESTRICT"), nullable=False
    )
    option_id: Mapped[int | None] = mapped_column(
        ForeignKey("survey_options.id", ondelete="SET NULL"), nullable=True
    )
    answer_text: Mapped[str | None] = mapped_column(Text)
    answer_number: Mapped[float | None] = mapped_column(Float)

    response: Mapped["SurveyResponse"] = relationship("SurveyResponse", back_populates="answers")
    question = relationship("SurveyQuestion")
    option = relationship("SurveyOption")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "response_id": self.response_id,
            "question_id": self.question_id,
            "option_id": self.option_id,
            "option_text": self.option.option_text if self.option else None,
            "answer_text": self.answer_text,
            "answer_number": self.answer_number,
        }


class SurveyBranchLimit(TimestampMixin, db.Model):
    """Chỉ tiêu số lượt khảo sát tối đa cho một chi nhánh, trong MỘT khảo sát
    cụ thể (ví dụ BMT 1000, Buôn Đôn 500) — khi chi nhánh đủ số lượt, trang
    công khai khoá không nhận thêm phản hồi gán cho chi nhánh đó nữa."""

    __tablename__ = "survey_branch_limits"
    __table_args__ = (
        UniqueConstraint("survey_id", "branch_id", name="uq_survey_branch_limit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    survey_id: Mapped[int] = mapped_column(
        ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("organization_units.id", ondelete="CASCADE"), nullable=False
    )
    max_responses: Mapped[int] = mapped_column(Integer, nullable=False)

    branch = relationship("OrganizationUnit")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "branch_id": self.branch_id,
            "branch_name": self.branch.name if self.branch else None,
            "max_responses": self.max_responses,
        }
