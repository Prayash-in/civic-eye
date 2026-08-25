from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from backend.models.report import Report
from backend.services import report_service
from backend.services.report_service import (
    ImageTooLargeError,
    InvalidImageError,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _enrich_constituency(assembly_id: Optional[str], assembly_name: Optional[str]) -> Optional[dict]:
    """Lookup district/name from data file so API returns location-aware fields without DB migration."""
    if not assembly_id:
        return None
    try:
        # Lazy import to avoid cycle
        from backend.services.jurisdiction_service import _load_constituencies, _assembly_by_id

        entry = _assembly_by_id(assembly_id)
        if entry:
            return {
                "id": entry["id"],
                "name": entry["name"],
                "district": entry.get("district"),
            }
    except Exception:
        pass
    return {"id": assembly_id, "name": assembly_name}


def _enrich_lok_sabha(lok_sabha_id: Optional[str]) -> Optional[dict]:
    if not lok_sabha_id:
        return None
    try:
        from backend.services.jurisdiction_service import _load_constituencies

        for entry in _load_constituencies()["lok_sabha_constituencies"]:
            if entry["id"] == lok_sabha_id:
                return {
                    "id": entry["id"],
                    "name": entry["name"],
                    "alias": entry.get("alias"),
                }
    except Exception:
        pass
    return {"id": lok_sabha_id}


def _serialize(
    report: Report,
    notifications: Optional[list[dict]] = None,
) -> dict:
    data = report.model_dump(mode="json")
    data["image_url"] = f"/uploads/{Path(report.image_path).name}"

    # Structured civic-intelligence views over the same fields.
    # Existing flat keys are preserved for backward compatibility.
    # Assembly/district/Lok Sabha are enriched from the static constituency file
    # so Mangaldai (Darrang) reports correctly show district without a new DB column.
    assembly = _enrich_constituency(report.assembly_constituency_id, report.assembly_constituency_name)
    lok_sabha = _enrich_lok_sabha(report.lok_sabha_constituency_id)

    data["jurisdiction"] = {
        "status": report.jurisdiction_status or "pending",
        "method": report.resolution_method,
        "assembly_constituency": assembly,
        "lok_sabha_constituency": lok_sabha,
    }
    data["representatives"] = {
        "mla": {
            "name": report.mla_name,
            "party": report.mla_party,
        },
        "mp": {
            "name": report.mp_name,
            "party": report.mp_party,
        },
    }
    data["authority"] = {
        "name": report.authority_name,
        "department": report.department,
        "reason": report.routing_reason,
    }
    notification = {
        "status": report.notification_status or "not_sent",
        "channel": report.notification_channel,
        "sent_at": report.notification_sent_at,
    }
    if notifications is not None:
        notification["log"] = notifications
    data["notification"] = notification

    return data


@router.post("")
async def create_report(
    image: UploadFile = File(...),
    description: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    category: str = Form(""),
):
    if not description.strip():
        raise HTTPException(
            status_code=422,
            detail="Description is required.",
        )

    image_data = await image.read()

    try:
        report = report_service.submit_report(
            image_data=image_data,
            filename=image.filename or "",
            description=description.strip(),
            content_type=image.content_type,
            latitude=latitude,
            longitude=longitude,
            category=category,
        )
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ImageTooLargeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return _serialize(report)


@router.get("")
def list_reports(
    issue_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    analysis_status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    reports = report_service.list_reports(
        issue_type=issue_type,
        severity=severity,
        status=status,
        analysis_status=analysis_status,
        limit=limit,
        offset=offset,
    )
    return [_serialize(report) for report in reports]


@router.get("/stats")
def get_stats():
    reports = report_service.list_reports(limit=10000)

    by_issue_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_authority: dict[str, int] = {}
    notification_counts: dict[str, int] = {}
    jurisdiction_counts: dict[str, int] = {}

    for report in reports:
        issue_key = report.issue_type or "unknown"
        by_issue_type[issue_key] = by_issue_type.get(issue_key, 0) + 1

        severity_key = report.severity or "unknown"
        by_severity[severity_key] = by_severity.get(severity_key, 0) + 1

        status_key = report.status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1

        if report.authority_name:
            authority_key = report.authority_name
            by_authority[authority_key] = by_authority.get(authority_key, 0) + 1

        if report.notification_status:
            note_key = report.notification_status
            notification_counts[note_key] = (
                notification_counts.get(note_key, 0) + 1
            )

        if report.jurisdiction_status:
            juris_key = report.jurisdiction_status
            jurisdiction_counts[juris_key] = (
                jurisdiction_counts.get(juris_key, 0) + 1
            )

    routed = sum(by_authority.values())
    return {
        "total": len(reports),
        "by_issue_type": by_issue_type,
        "by_severity": by_severity,
        "by_status": by_status,
        "recent": [_serialize(report) for report in reports[:10]],
        "civic_response": {
            "routed": routed,
            "unrouted": len(reports) - routed,
            "by_authority": by_authority,
            "notifications": notification_counts,
            "jurisdiction": jurisdiction_counts,
            "recent_notifications": report_service.recent_notifications(limit=5),
        },
    }


@router.get("/{report_id}")
def get_report(report_id: int):
    report = report_service.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )
    notifications = report_service.get_report_notifications(report_id)
    return _serialize(report, notifications=notifications)