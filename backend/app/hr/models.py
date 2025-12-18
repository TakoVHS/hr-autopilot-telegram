import enum
from datetime import datetime

from app.core.db import Base
from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Source(str, enum.Enum):
    AVITO = "avito"
    YANDEX = "yandex"
    TELEGRAM = "telegram"
    OTHER = "other"


class CandidateStatus(str, enum.Enum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    NO_RESPONSE = "no_response"
    DOCS_PENDING = "docs_pending"


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    candidates: Mapped[list["Candidate"]] = relationship(
        "Candidate", back_populates="vacancy", cascade="all,delete"
    )
    interview_slots: Mapped[list["InterviewSlot"]] = relationship(
        "InterviewSlot", back_populates="vacancy", cascade="all,delete"
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[Source] = mapped_column(
        Enum(Source), nullable=False, default=Source.OTHER
    )
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus), nullable=False, default=CandidateStatus.NEW
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    vacancy_id: Mapped[int | None] = mapped_column(
        ForeignKey("vacancies.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    vacancy: Mapped[Vacancy | None] = relationship(
        "Vacancy", back_populates="candidates"
    )
    interview_slots: Mapped[list["InterviewSlot"]] = relationship(
        "InterviewSlot", back_populates="candidate", cascade="all,delete"
    )
    followups: Mapped[list["FollowUpTask"]] = relationship(
        "FollowUpTask", back_populates="candidate", cascade="all,delete"
    )


class InterviewSlot(Base):
    __tablename__ = "interview_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    vacancy_id: Mapped[int | None] = mapped_column(
        ForeignKey("vacancies.id", ondelete="SET NULL"), nullable=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate: Mapped[Candidate] = relationship(
        "Candidate", back_populates="interview_slots"
    )
    vacancy: Mapped[Vacancy | None] = relationship(
        "Vacancy", back_populates="interview_slots"
    )


class FollowUpTask(Base):
    __tablename__ = "followup_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="followups")
