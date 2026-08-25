import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.ai.schema import CivicIssueAnalysis, IssueType, Severity
from backend.api.app import app
from backend.services import report_service
from backend.services.ai_service import AIServiceError
from backend.services import notification_service

IMG_BYTES = bytes(range(256)) * 2  # 512 bytes

passed = 0
failed = 0


def report(name: str, ok: bool) -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}")


def success_analysis(image_path, description=""):
    return CivicIssueAnalysis(
        issue_type=IssueType.POTHOLE,
        severity=Severity.HIGH,
        confidence=0.95,
        explanation="Stub analysis result.",
    )


def failing_analysis(image_path, description=""):
    raise AIServiceError("Stub analysis failure.")


# Coordinates inside the approximate Jalukbari polygon.
JALUKBARI_LAT = 26.17
JALUKBARI_LON = 91.665


print("=" * 60)
print("CIVIC INTELLIGENCE FLOW TESTS")
print("=" * 60)

# ----------------------------------------------------------
# 1. Full happy path: AI success + jurisdiction + routing
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = Path(tmp) / "civic.db"

    with (
        patch("backend.services.ai_service.analyze", side_effect=success_analysis),
        patch.object(notification_service, "SMTP_HOST", None),
    ):
        r = report_service.submit_report(
            image_data=IMG_BYTES,
            filename="pothole.jpg",
            description="Deep pothole near the gate.",
            content_type="image/jpeg",
            latitude=JALUKBARI_LAT,
            longitude=JALUKBARI_LON,
        )

    report("flow: analysis completed", r.analysis_status.value == "completed")
    report(
        "flow: jurisdiction resolved",
        r.jurisdiction_status == "resolved",
    )
    report(
        "flow: resolution method disclosed as approximate_locality",
        r.resolution_method == "approximate_locality",
    )
    report(
        "flow: assembly constituency stored",
        r.assembly_constituency_id == "AS-037"
        and r.assembly_constituency_name == "Jalukbari",
    )
    report(
        "flow: MLA + MP persisted",
        r.mla_name == "Himanta Biswa Sarma"
        and r.mp_name == "Bijuli Kalita Medhi",
    )
    report(
        "flow: routed to Roads & Infrastructure / GMC",
        r.department == "Roads & Infrastructure"
        and r.authority_name == "Guwahati Municipal Corporation"
        and r.routing_reason,
    )
    report(
        "flow: notification recorded (not configured in tests)",
        r.notification_status == "not_configured",
    )

    notes = report_service.get_report_notifications(r.id)
    report(
        "flow: notification log row exists",
        len(notes) >= 1 and notes[0]["status"] == "not_configured",
    )

# ----------------------------------------------------------
# 2. AI failure: report still saved + jurisdiction still resolved,
#    but NO notification is attempted
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = Path(tmp) / "civic.db"

    with patch("backend.services.ai_service.analyze", side_effect=failing_analysis):
        r = report_service.submit_report(
            image_data=IMG_BYTES,
            filename="pothole.jpg",
            description="Unclassifiable image.",
            content_type="image/jpeg",
            latitude=JALUKBARI_LAT,
            longitude=JALUKBARI_LON,
        )

    report("AI failure: analysis failed", r.analysis_status.value == "failed")
    report(
        "AI failure: no fabricated issue fields",
        r.issue_type is None and r.severity is None and r.confidence is None,
    )
    report(
        "AI failure: jurisdiction still resolved deterministically",
        r.jurisdiction_status == "resolved"
        and r.mla_name == "Himanta Biswa Sarma",
    )
    report(
        "AI failure: notification not sent",
        r.notification_status in ("not_sent", None),
    )
    notes = report_service.get_report_notifications(r.id)
    report(
        "AI failure: log records not_sent",
        len(notes) >= 1 and notes[0]["status"] == "not_sent",
    )

# ----------------------------------------------------------
# 3. No coordinates: unavailable jurisdiction, no representatives
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = Path(tmp) / "civic.db"

    with patch("backend.services.ai_service.analyze", side_effect=success_analysis):
        r = report_service.submit_report(
            image_data=IMG_BYTES,
            filename="pothole.jpg",
            description="No GPS attached.",
            content_type="image/jpeg",
        )

    report(
        "no coords: unavailable",
        r.jurisdiction_status == "unavailable",
    )
    report(
        "no coords: no MLA/MP guessed",
        r.mla_name is None and r.mp_name is None,
    )
    report(
        "no coords: routing still falls back to general services",
        r.authority_name == "Guwahati Municipal Corporation",
    )

# ----------------------------------------------------------
# 4. API serialization: nested objects + backward compatibility
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    with (
        patch.object(report_service, "UPLOAD_DIR", Path(tmp) / "uploads"),
        patch.object(report_service, "DB_PATH", Path(tmp) / "civic.db"),
        patch(
            "backend.services.ai_service.analyze",
            side_effect=success_analysis,
        ),
        patch.object(notification_service, "SMTP_HOST", None),
    ):
        client = TestClient(app)

        resp = client.post(
            "/api/reports",
            files={"image": ("p.jpg", IMG_BYTES, "image/jpeg")},
            data={
                "description": "Deep pothole near the gate.",
                "latitude": str(JALUKBARI_LAT),
                "longitude": str(JALUKBARI_LON),
            },
        )
        body = resp.json()

        report("api: create returns 200", resp.status_code == 200)
        report(
            "api: legacy flat keys preserved",
            body["analysis_status"] == "completed"
            and body["issue_type"] == "pothole"
            and body["severity"] == "high"
            and "image_url" in body,
        )
        report(
            "api: nested jurisdiction object",
            body["jurisdiction"]["status"] == "resolved"
            and body["jurisdiction"]["assembly_constituency"]["id"] == "AS-037",
        )
        report(
            "api: nested representatives object",
            body["representatives"]["mla"]["name"] == "Himanta Biswa Sarma"
            and body["representatives"]["mp"]["name"] == "Bijuli Kalita Medhi",
        )
        report(
            "api: nested authority object",
            body["authority"]["department"] == "Roads & Infrastructure"
            and body["authority"]["name"] == "Guwahati Municipal Corporation",
        )
        report(
            "api: nested notification object",
            body["notification"]["status"] == "not_configured",
        )

        detail = client.get(f"/api/reports/{body['id']}")
        detail_body = detail.json()
        report(
            "api: detail includes notification log",
            isinstance(detail_body["notification"].get("log"), list)
            and len(detail_body["notification"]["log"]) >= 1,
        )

        stats = client.get("/api/reports/stats")
        stats_body = stats.json()
        civic = stats_body.get("civic_response") or {}
        report(
            "api: stats civic_response section present",
            resp.status_code == 200
            and "routed" in civic
            and "by_authority" in civic
            and "notifications" in civic
            and "jurisdiction" in civic,
        )
        report(
            "api: stats counts routed reports",
            civic.get("routed") == 1
            and civic.get("by_authority", {}).get(
                "Guwahati Municipal Corporation"
            )
            == 1,
        )
        report(
            "api: legacy stats keys intact",
            stats_body["total"] == 1
            and "by_issue_type" in stats_body
            and "by_severity" in stats_body
            and "by_status" in stats_body
            and "recent" in stats_body,
        )

# ----------------------------------------------------------
# 5. Existing DB keeps working after migration (ALTER TABLE path)
# ----------------------------------------------------------
import sqlite3

with tempfile.TemporaryDirectory() as tmp:
    db_path = Path(tmp) / "civic.db"
    # Simulate a pre-existing old database without the new columns.
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            issue_type TEXT,
            severity TEXT,
            confidence REAL,
            explanation TEXT,
            latitude REAL,
            longitude REAL,
            status TEXT NOT NULL DEFAULT 'submitted',
            analysis_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO reports (image_path, description, created_at)"
        " VALUES ('old/legacy.jpg', 'Legacy row', '2025-01-01T00:00:00+00:00')"
    )
    conn.commit()
    conn.close()

    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = db_path

    migrated = report_service.list_reports()
    report(
        "migration: legacy rows readable",
        len(migrated) == 1
        and migrated[0].description == "Legacy row"
        and migrated[0].jurisdiction_status is None,
    )

    with (
        patch("backend.services.ai_service.analyze", side_effect=success_analysis),
        patch.object(notification_service, "SMTP_HOST", None),
    ):
        r = report_service.submit_report(
            image_data=IMG_BYTES,
            filename="new.jpg",
            description="New report on migrated DB.",
            content_type="image/jpeg",
            latitude=JALUKBARI_LAT,
            longitude=JALUKBARI_LON,
        )
    report(
        "migration: new flow works on migrated DB",
        r.analysis_status.value == "completed"
        and r.jurisdiction_status == "resolved",
    )

print("=" * 60)
print(f"Passed: {passed}/{passed + failed}")
assert failed == 0, f"{failed} civic flow tests failed"
