from datetime import datetime
from typing import Optional

from app.hr.schemas import CandidateStatus, Source
from app.integrations import amocrm, avito, seller_gpt
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tools", tags=["tools"])


class CreateCandidatePayload(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: Source = Source.OTHER
    vacancy_id: Optional[int] = None
    notes: Optional[str] = None


class UpdateCandidateStatusPayload(BaseModel):
    candidate_id: int
    status: CandidateStatus = Field(default=CandidateStatus.NEW)
    notes: Optional[str] = None


class ScheduleInterviewPayload(BaseModel):
    candidate_id: int
    vacancy_id: Optional[int] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    notes: Optional[str] = None


class EscalateToHumanPayload(BaseModel):
    candidate_id: int
    reason: str
    priority: str = Field(default="normal")  # could be: low|normal|high|urgent


@router.post("/create_candidate_in_crm")
async def create_candidate_in_crm(payload: CreateCandidatePayload) -> dict:
    data = payload.model_dump()
    return {
        "status": "ok",
        "action": "create_candidate_in_crm",
        "results": [
            seller_gpt.create_lead_from_candidate(data, source=payload.source.value),
            amocrm.create_lead_from_candidate(data, source=payload.source.value),
            avito.create_lead_from_candidate(data, source=payload.source.value),
        ],
    }


@router.post("/update_candidate_status")
async def update_candidate_status(payload: UpdateCandidateStatusPayload) -> dict:
    return {
        "status": "ok",
        "action": "update_candidate_status",
        "results": [
            seller_gpt.update_lead_status(payload.candidate_id, payload.status.value),
            amocrm.update_lead_status(payload.candidate_id, payload.status.value),
            avito.update_lead_status(payload.candidate_id, payload.status.value),
        ],
    }


@router.get("/get_vacancy_details")
async def get_vacancy_details(vacancy_id: int) -> dict:
    return {
        "status": "ok",
        "action": "get_vacancy_details",
        "vacancy_id": vacancy_id,
        "note": "TODO: fetch vacancy details from DB/CRM",
    }


@router.post("/schedule_interview")
async def schedule_interview(payload: ScheduleInterviewPayload) -> dict:
    return {
        "status": "ok",
        "action": "schedule_interview",
        "payload": payload.model_dump(),
        "note": "TODO: create interview slot and notify stakeholders",
    }


@router.post("/escalate_to_human")
async def escalate_to_human(payload: EscalateToHumanPayload) -> dict:
    note_text = f"Escalation ({payload.priority}): {payload.reason}"
    return {
        "status": "ok",
        "action": "escalate_to_human",
        "payload": payload.model_dump(),
        "results": [
            seller_gpt.attach_note(payload.candidate_id, note_text),
            amocrm.attach_note(payload.candidate_id, note_text),
            avito.attach_note(payload.candidate_id, note_text),
        ],
    }
