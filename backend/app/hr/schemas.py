from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class Source(str, Enum):
    AVITO = "avito"
    YANDEX = "yandex"
    TELEGRAM = "telegram"
    OTHER = "other"


class CandidateStatus(str, Enum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    NO_RESPONSE = "no_response"
    DOCS_PENDING = "docs_pending"


class VacancyBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_open: bool = True


class VacancyCreate(VacancyBase):
    pass


class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_open: Optional[bool] = None


class VacancyRead(VacancyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: Source = Source.OTHER
    status: CandidateStatus = CandidateStatus.NEW
    notes: Optional[str] = None
    vacancy_id: Optional[int] = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: Optional[Source] = None
    status: Optional[CandidateStatus] = None
    notes: Optional[str] = None
    vacancy_id: Optional[int] = None


class CandidateRead(CandidateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewSlotBase(BaseModel):
    candidate_id: int
    vacancy_id: Optional[int] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    notes: Optional[str] = None


class InterviewSlotCreate(InterviewSlotBase):
    pass


class InterviewSlotUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class InterviewSlotRead(InterviewSlotBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class FollowUpTaskBase(BaseModel):
    candidate_id: int
    title: str
    due_at: Optional[datetime] = None
    completed: bool = False
    notes: Optional[str] = None


class FollowUpTaskCreate(FollowUpTaskBase):
    pass


class FollowUpTaskUpdate(BaseModel):
    title: Optional[str] = None
    due_at: Optional[datetime] = None
    completed: Optional[bool] = None
    notes: Optional[str] = None


class FollowUpTaskRead(FollowUpTaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
