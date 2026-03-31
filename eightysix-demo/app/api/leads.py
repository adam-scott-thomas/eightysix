"""Lead capture endpoint — stores contact info from demo users."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter()

LEADS_FILE = Path(__file__).parent.parent.parent / "leads.json"


class LeadSubmission(BaseModel):
    name: str
    email: str
    phone: str = ""
    restaurant_name: str
    address: str = ""
    top_concerns: list[str] = []
    estimated_leakage: float = 0.0
    notes: str = ""


@router.post("/leads")
async def capture_lead(lead: LeadSubmission):
    """Store a lead from the demo funnel."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "restaurant_name": lead.restaurant_name,
        "address": lead.address,
        "top_concerns": lead.top_concerns,
        "estimated_leakage": lead.estimated_leakage,
        "notes": lead.notes,
    }

    # Append to JSON file
    leads: list[dict] = []
    if LEADS_FILE.exists():
        try:
            leads = json.loads(LEADS_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            leads = []

    leads.append(entry)
    LEADS_FILE.write_text(json.dumps(leads, indent=2))

    return {"status": "ok", "message": "Thanks — your full breakdown is ready."}


@router.get("/leads")
async def list_leads():
    """List all captured leads (internal use)."""
    if not LEADS_FILE.exists():
        return {"leads": [], "count": 0}

    try:
        leads = json.loads(LEADS_FILE.read_text())
    except (json.JSONDecodeError, Exception):
        return {"leads": [], "count": 0}

    return {"leads": leads, "count": len(leads)}
