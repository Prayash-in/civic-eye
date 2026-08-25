import uuid
from pathlib import Path
from typing import Optional

from backend.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIME_TYPES,
    AnalysisStatus,
    DB_PATH,
    MAX_UPLOAD_SIZE_BYTES,
    NOTIFICATION_MIN_CONFIDENCE,
    PROJECT_ROOT,
    UPLOAD_DIR,
)
from backend.database.database import (
    create_report,
    get_notifications_for_report,
    get_recent_notifications as db_recent_notifications,
    get_report as db_get_report,
    list_reports as db_list_reports,
    record_notification,
    update_analysis,
    update_routing,
)
from backend.models.report import Report, ReportCreate
from backend.services import ai_service
from backend.services.authority_service import route_issue
from backend.services.jurisdiction_service import resolve_jurisdiction
from backend.services import notification_service


class ReportServiceError(Exception):
    pass


class InvalidImageError(ReportServiceError):
    pass


class ImageTooLargeError(ReportServiceError):
    pass


def validate_image(
    filename: str,
    content_type: Optional[str],
    size: int,
) -> None:
    name = Path(filename).name
    ext = Path(name).suffix.lower()

    if not ext or ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise InvalidImageError(
            "Unsupported image type. "
            "Allowed extensions: jpg, jpeg, png, webp."
        )

    if content_type and content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise InvalidImageError(
            f"Unsupported content type: {content_type}."
        )

    if size > MAX_UPLOAD_SIZE_BYTES:
        limit_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise ImageTooLargeError(
            f"Image exceeds the maximum size of {limit_mb} MB."
        )


def _unique_filename(ext: str) -> str:
    return f"{uuid.uuid4().hex}{ext}"


def save_image(
    image_data: bytes,
    filename: str,
    content_type: Optional[str],
) -> Path:
    validate_image(
        filename=filename,
        content_type=content_type,
        size=len(image_data),
    )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(filename).suffix.lower()
    stored = UPLOAD_DIR / _unique_filename(ext)

    stored.write_bytes(image_data)

    return stored


def _store_path(stored: Path) -> str:
    try:
        return str(stored.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(stored)


def _absolute(image_path: str) -> Path:
    path = Path(image_path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _route_and_notify(report: Report) -> Report:
    """Jurisdiction resolution + authority routing + demo notification.

    Deterministic data/rules only — the AI never picks authorities or
    representatives. Any failure here degrades gracefully and never breaks
    report creation.
    """
    jurisdiction = resolve_jurisdiction(report.latitude, report.longitude)
    # Debug logging for verification (temporary, low-noise)
    try:
        lat_dbg = report.latitude
        lng_dbg = report.longitude
        print(f"[Civic Eye] GPS coordinates received: latitude={lat_dbg}, longitude={lng_dbg}")
        print(f"[Civic Eye] Jurisdiction resolved: {jurisdiction.get('jurisdiction_status')} method={jurisdiction.get('resolution_method')} assembly={jurisdiction.get('assembly_constituency')} ls={jurisdiction.get('lok_sabha_constituency')} mla={jurisdiction.get('mla')} mp={jurisdiction.get('mp')}")
    except Exception:
        pass

    if report.issue_type:
        authority_info = route_issue(report.issue_type, jurisdiction)
    else:
        authority_info = route_issue(None, jurisdiction)

    try:
        print(f"[Civic Eye] Authority routed: {authority_info.get('authority')} / {authority_info.get('department')} reason={authority_info.get('routing_reason')}")
    except Exception:
        pass

    try:
        report = update_routing(
            report.id,
            {
                "assembly_constituency": jurisdiction.get("assembly_constituency"),
                "lok_sabha_constituency": jurisdiction.get("lok_sabha_constituency"),
                "mla": jurisdiction.get("mla"),
                "mp": jurisdiction.get("mp"),
                "jurisdiction_status": jurisdiction.get("jurisdiction_status"),
                "resolution_method": jurisdiction.get("resolution_method"),
                "authority": authority_info,
            },
            db_path=DB_PATH,
        )
    except Exception:  # noqa: BLE001 - routing persistence must not break flow
        pass

    if report is None:
        return report

    # Notifications require a classified issue AND AI confidence above the
    # threshold (>50%). Never claim a low-confidence or unclassified report
    # reached an authority.
    notification_result = {"status": "not_sent", "channel": None}
    if report.issue_type:
        confidence = report.confidence
        if confidence is None or confidence <= NOTIFICATION_MIN_CONFIDENCE:
            pct = f"{round(float(confidence) * 100)}%" if confidence is not None else "unknown"
            notification_result = {
                "status": "not_sent",
                "channel": "email",
                "error": (
                    f"AI confidence {pct} does not exceed the "
                    f"{round(NOTIFICATION_MIN_CONFIDENCE * 100)}% notification threshold."
                ),
            }
            try:
                print(f"[Civic Eye] Notification skipped: confidence {pct} <= {round(NOTIFICATION_MIN_CONFIDENCE * 100)}%")
            except Exception:
                pass
        else:
            try:
                notification_result = (
                    notification_service.send_authority_notification(
                        report, authority_info, jurisdiction
                    )
                )
            except Exception as error:  # noqa: BLE001 - defensive
                notification_result = {
                    "status": "failed",
                    "channel": "email",
                    "error": type(error).__name__,
                }

    try:
        record_notification(
            report.id,
            channel=notification_result.get("channel") or "email",
            recipients=notification_result.get("recipients", []),
            status=notification_result.get("status", "not_sent"),
            error=notification_result.get("error"),
            sent_at=notification_result.get("sent_at"),
            db_path=DB_PATH,
        )
    except Exception:  # noqa: BLE001
        pass

    return db_get_report(report.id, db_path=DB_PATH)


def submit_report(
    image_data: bytes,
    filename: str,
    description: str,
    content_type: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    category: str = "",
) -> Report:
    stored = save_image(
        image_data=image_data,
        filename=filename,
        content_type=content_type,
    )

    report = create_report(
        ReportCreate(
            image_path=_store_path(stored),
            description=description,
            category=category,
            latitude=latitude,
            longitude=longitude,
        ),
        db_path=DB_PATH,
    )

    try:
        result = ai_service.analyze(
            image_path=_absolute(report.image_path),
            description=description,
        )
    except ai_service.AIServiceError:
        failed_report = update_analysis(
            report_id=report.id,
            issue_type=None,
            severity=None,
            confidence=None,
            explanation=None,
            analysis_status=AnalysisStatus.FAILED.value,
            db_path=DB_PATH,
        )
        # Jurisdiction can still be resolved deterministically from the
        # coordinates, but no notification is attempted without a
        # classified issue.
        return _route_and_notify(failed_report)

    completed_report = update_analysis(
        report_id=report.id,
        issue_type=result.issue_type.value,
        severity=result.severity.value,
        confidence=result.confidence,
        explanation=result.explanation,
        analysis_status=AnalysisStatus.COMPLETED.value,
        db_path=DB_PATH,
    )

    return _route_and_notify(completed_report)


def get_report_notifications(report_id: int) -> list[dict]:
    return get_notifications_for_report(report_id, db_path=DB_PATH)


def recent_notifications(limit: int = 10) -> list[dict]:
    return db_recent_notifications(limit=limit, db_path=DB_PATH)


def get_report(report_id: int) -> Optional[Report]:
    return db_get_report(report_id, db_path=DB_PATH)


def list_reports(**filters) -> list[Report]:
    return db_list_reports(db_path=DB_PATH, **filters)