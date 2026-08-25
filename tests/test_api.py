import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.ai.schema import CivicIssueAnalysis, IssueType, Severity
from backend.api.app import app
from backend.services.ai_service import AIServiceError

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


def _post(
    client,
    name="pothole.jpg",
    content_type="image/jpeg",
    data_bytes=IMG_BYTES,
    description="Deep pothole on Main Street.",
    extra=None,
):
    files = {"image": (name, data_bytes, content_type)}
    data = {"description": description}
    if extra:
        data.update(extra)
    return client.post("/api/reports", files=files, data=data)


print("=" * 60)
print("API TESTS")
print("=" * 60)

# ----------------------------------------------------------
# Successful AI analysis + create (POST /api/reports)
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    with (
        patch(
            "backend.services.report_service.UPLOAD_DIR",
            Path(tmp) / "uploads",
        ),
        patch(
            "backend.services.report_service.DB_PATH",
            Path(tmp) / "civic.db",
        ),
        patch(
            "backend.services.ai_service.analyze",
            side_effect=success_analysis,
        ),
    ):
        client = TestClient(app)

        resp = _post(
            client,
            extra={
                "latitude": "26.1",
                "longitude": "91.7",
                "category": "road",
            },
        )
        report("POST success: status 200", resp.status_code == 200)
        body = resp.json()
        created_id = body.get("id")
        report(
            "POST success: analysis completed + fields",
            body.get("analysis_status") == "completed"
            and body.get("issue_type") == "pothole"
            and body.get("severity") == "high"
            and body.get("confidence") == 0.95,
        )
        report(
            "POST success: image_url present",
            str(body.get("image_url", "")).startswith("/uploads/"),
        )

        # Invalid image (bad extension + mime)
        resp = _post(client, name="notes.txt", content_type="text/plain")
        report("POST invalid image: status 400", resp.status_code == 400)

        # Oversized image
        with patch("backend.services.report_service.MAX_UPLOAD_SIZE_BYTES", 100):
            resp = _post(client, data_bytes=IMG_BYTES)
        report("POST oversized image: status 400", resp.status_code == 400)

        # Missing description
        resp = client.post(
            "/api/reports",
            files={"image": ("x.jpg", IMG_BYTES, "image/jpeg")},
            data={},
        )
        report("POST missing description: status 422", resp.status_code == 422)

        # Missing image
        resp = client.post(
            "/api/reports",
            data={"description": "No image here."},
        )
        report("POST missing image: status 422", resp.status_code == 422)

        # AI failure -> report stored with analysis_status=failed
        with patch(
            "backend.services.ai_service.analyze",
            side_effect=failing_analysis,
        ):
            resp = _post(client, description="Deep pothole on Main Street.")
        report(
            "POST AI failure: status 200 + analysis failed",
            resp.status_code == 200
            and resp.json().get("analysis_status") == "failed",
        )
        report(
            "POST AI failure: no fabricated AI fields",
            resp.json().get("issue_type") is None
            and resp.json().get("severity") is None
            and resp.json().get("confidence") is None,
        )

        # GET /api/reports
        resp = client.get("/api/reports")
        report(
            "GET list: 200 + contains created report",
            resp.status_code == 200
            and any(r["id"] == created_id for r in resp.json()),
        )

        # GET /api/reports with filter
        resp = client.get("/api/reports", params={"issue_type": "pothole"})
        report(
            "GET list filter issue_type: includes report",
            resp.status_code == 200
            and any(r["id"] == created_id for r in resp.json()),
        )

        # GET /api/reports/{id}
        resp = client.get(f"/api/reports/{created_id}")
        report(
            "GET detail: 200 + matches",
            resp.status_code == 200 and resp.json()["id"] == created_id,
        )

        resp = client.get("/api/reports/999999")
        report("GET detail unknown id: status 404", resp.status_code == 404)

        # GET /api/reports/stats
        resp = client.get("/api/reports/stats")
        report(
            "GET stats: 200 + total >= 2",
            resp.status_code == 200 and resp.json()["total"] >= 2,
        )

print("=" * 60)
print(f"Passed: {passed}/{passed + failed}")