"""Lead capture with email verification — gates results behind verified submission."""

from __future__ import annotations

import json
import os
import random
import string
from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

LEADS_FILE = Path(__file__).parent.parent.parent / "leads.json"

# In-memory verification store {session_id: {code, email, verified, report_data}}
_verifications: dict[str, dict] = {}


class LeadSubmission(BaseModel):
    session_id: str
    name: str
    email: str
    phone: str = ""
    restaurant_name: str
    address: str = ""
    top_concerns: list[str] = []
    estimated_leakage: float = 0.0


class VerifyRequest(BaseModel):
    session_id: str
    code: str


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))


# ───────────────────────────── email provider ─────────────────────────────
#
# Deliberately kept small. _send_email() is the only surface the rest of the
# module touches; swapping Resend for Brevo/SparkPost/Mailgun is ~15 LOC in
# one place.

EMAIL_FROM = os.getenv("EMAIL_FROM", "EightySix <noreply@quantumatiq.com>")
NOTIFY_EMAIL = "adam@ghostlogic.tech"


def _send_email(*, to: str, subject: str, html: str, text: str) -> bool:
    """Send one email. Returns True on success, False on any failure.

    Provider is Resend via HTTP. Key must be in RESEND_API_KEY env var.
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("Email error: RESEND_API_KEY not set")
        return False
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            },
            timeout=10,
        )
        if r.status_code >= 400:
            print(f"Resend error {r.status_code}: {r.text}")
            return False
        return True
    except requests.RequestException as e:
        print(f"Email error: {e}")
        return False


def _send_verification_email(email: str, code: str, restaurant_name: str) -> bool:
    """Send verification code via Resend."""
    html = f"""
<div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
    <div style="background: #f59e0b; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 24px;">
        <span style="color: white; font-weight: 900; font-size: 20px;">86</span>
    </div>
    <h2 style="margin: 0 0 8px; color: #111;">Your verification code</h2>
    <p style="color: #666; margin: 0 0 24px;">Enter this code to see your full leakage breakdown for {restaurant_name}.</p>
    <div style="background: #111; color: #f59e0b; font-size: 32px; font-weight: 900; letter-spacing: 8px; text-align: center; padding: 20px; border-radius: 12px; font-family: monospace;">
        {code}
    </div>
    <p style="color: #999; font-size: 13px; margin-top: 24px;">This code expires in 30 minutes. If you didn't request this, ignore this email.</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
    <p style="color: #bbb; font-size: 12px;">EightySix by Maelstrom LLC</p>
</div>
"""
    text = (
        f"Your EightySix verification code is: {code}\n\n"
        f"Enter this code to see your full leakage breakdown for {restaurant_name}.\n\n"
        f"This code expires in 30 minutes."
    )
    return _send_email(
        to=email,
        subject=f"Your EightySix verification code: {code}",
        html=html,
        text=text,
    )


@router.post("/leads")
async def capture_lead(lead: LeadSubmission):
    """Store lead info and send verification code to email."""
    session = _verifications.get(lead.session_id)
    if not session:
        # Create new verification entry (report_data will be set by upload flow)
        session = {}
        _verifications[lead.session_id] = session

    code = _generate_code()
    session.update({
        "code": code,
        "email": lead.email,
        "verified": False,
        "lead": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "restaurant_name": lead.restaurant_name,
            "address": lead.address,
            "top_concerns": lead.top_concerns,
            "estimated_leakage": lead.estimated_leakage,
        },
    })

    sent = _send_verification_email(lead.email, code, lead.restaurant_name)

    if not sent:
        raise HTTPException(500, "Failed to send verification email. Please try again.")

    return {"status": "code_sent", "message": f"Verification code sent to {lead.email}"}


@router.post("/verify-email")
async def verify_email(req: VerifyRequest):
    """Verify the email code. On success, persist the lead and return results."""
    session = _verifications.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session expired. Please start over.")

    if session.get("code") != req.code:
        raise HTTPException(400, "Incorrect code. Please try again.")

    # Mark verified
    session["verified"] = True

    # Persist the lead
    lead_data = session.get("lead", {})
    lead_data["email_verified"] = True
    _persist_lead(lead_data)

    # Notify Adam
    _notify_new_lead(lead_data)

    # Return stored report data
    report_data = session.get("report_data")
    if not report_data:
        raise HTTPException(404, "Analysis results expired. Please re-upload.")

    # Clean up session
    _verifications.pop(req.session_id, None)

    return {
        "status": "verified",
        "report": report_data.get("report"),
        "explanation": report_data.get("explanation"),
    }


def store_report_for_session(session_id: str, report_data: dict):
    """Called by upload flow to store results for later retrieval after verification."""
    if session_id not in _verifications:
        _verifications[session_id] = {}
    _verifications[session_id]["report_data"] = report_data


def _notify_new_lead(lead_data: dict):
    """Send Adam an email when a verified lead comes in. Best-effort, never raises."""
    name = lead_data.get("name", "Unknown")
    email = lead_data.get("email", "")
    phone = lead_data.get("phone", "")
    restaurant = lead_data.get("restaurant_name", "")
    address = lead_data.get("address", "")
    concerns = ", ".join(lead_data.get("top_concerns", []))
    leakage = lead_data.get("estimated_leakage", 0)

    html = f"""
<div style="font-family: -apple-system, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px;">
    <h2 style="margin: 0 0 16px; color: #111;">New verified lead</h2>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <tr><td style="padding: 8px 0; color: #888; width: 120px;">Name</td><td style="padding: 8px 0; font-weight: 600;">{name}</td></tr>
        <tr><td style="padding: 8px 0; color: #888;">Email</td><td style="padding: 8px 0;"><a href="mailto:{email}">{email}</a></td></tr>
        <tr><td style="padding: 8px 0; color: #888;">Phone</td><td style="padding: 8px 0;"><a href="tel:{phone}">{phone}</a></td></tr>
        <tr><td style="padding: 8px 0; color: #888;">Restaurant</td><td style="padding: 8px 0; font-weight: 600;">{restaurant}</td></tr>
        <tr><td style="padding: 8px 0; color: #888;">Address</td><td style="padding: 8px 0;">{address}</td></tr>
        <tr><td style="padding: 8px 0; color: #888;">Top concerns</td><td style="padding: 8px 0;">{concerns}</td></tr>
        <tr style="background: #fffbeb;"><td style="padding: 12px 8px; color: #888;">Est. leakage</td><td style="padding: 12px 8px; font-weight: 900; font-size: 18px; color: #d97706;">${leakage:,.0f}/yr</td></tr>
    </table>
    <p style="color: #999; font-size: 12px; margin-top: 16px;">Email verified. Lead is real. Follow up.</p>
</div>
"""
    text = (
        f"New EightySix lead (verified)\n\n"
        f"Name: {name}\nEmail: {email}\nPhone: {phone}\n"
        f"Restaurant: {restaurant}\nAddress: {address}\n"
        f"Concerns: {concerns}\n"
        f"Est. leakage: ${leakage:,.0f}/yr\n"
    )
    _send_email(
        to=NOTIFY_EMAIL,
        subject=f"New EightySix lead: {name} — {restaurant}",
        html=html,
        text=text,
    )


def _persist_lead(lead_data: dict):
    """Append verified lead to leads.json."""
    leads: list[dict] = []
    if LEADS_FILE.exists():
        try:
            leads = json.loads(LEADS_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            leads = []
    leads.append(lead_data)
    LEADS_FILE.write_text(json.dumps(leads, indent=2))


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
