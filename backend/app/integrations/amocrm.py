from typing import Any, Mapping

from app.hr.models import Candidate

CandidateInput = Candidate | Mapping[str, Any]


def create_lead_from_candidate(
    candidate: CandidateInput, source: str
) -> dict[str, Any]:
    return {
        "provider": "amocrm",
        "action": "create_lead_from_candidate",
        "candidate": dict(candidate)
        if isinstance(candidate, Mapping)
        else getattr(candidate, "__dict__", {}),
        "source": source,
        "status": "ok",
    }


def update_lead_status(candidate_id: int, status: str) -> dict[str, Any]:
    return {
        "provider": "amocrm",
        "action": "update_lead_status",
        "candidate_id": candidate_id,
        "status_value": status,
        "status": "ok",
    }


def attach_note(candidate_id: int, text: str) -> dict[str, Any]:
    return {
        "provider": "amocrm",
        "action": "attach_note",
        "candidate_id": candidate_id,
        "text": text,
        "status": "ok",
    }
