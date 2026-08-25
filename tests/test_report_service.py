import tempfile
from pathlib import Path
from unittest.mock import patch

import backend.services.report_service as report_service
from backend.ai.schema import CivicIssueAnalysis, IssueType, Severity
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


print("=" * 60)
print("REPORT SERVICE TESTS")
print("=" * 60)

# ----------------------------------------------------------
# 1. Valid image upload + AI success
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = Path(tmp) / "civic.db"

    with patch("backend.services.ai_service.analyze", side_effect=success_analysis):
        r = report_service.submit_report(
            image_data=IMG_BYTES,
            filename="pothole.jpg",
            description="Deep pothole on Main Street.",
            content_type="image/jpeg",
            latitude=26.1,
            longitude=91.7,
            category="road",
        )

    report(
        "valid upload: report created, analysis completed",
        r is not None
        and r.analysis_status.value == "completed"
        and r.description == "Deep pothole on Main Street.",
    )
    report(
        "uploaded file exists on disk",
        Path(r.image_path).exists(),
    )

# ----------------------------------------------------------
# 2. Invalid file type
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"

    rejected = False
    try:
        report_service.save_image(
            image_data=IMG_BYTES,
            filename="notes.txt",
            content_type="text/plain",
        )
    except report_service.InvalidImageError:
        rejected = True

    report("invalid extension rejected", rejected)

    written = (
        list(report_service.UPLOAD_DIR.glob("*"))
        if report_service.UPLOAD_DIR.exists()
        else []
    )
    report("nothing written for invalid type", len(written) == 0)

    rejected_mime = False
    try:
        report_service.save_image(
            image_data=IMG_BYTES,
            filename="photo.png",
            content_type="text/plain",
        )
    except report_service.InvalidImageError:
        rejected_mime = True

    report("invalid mime type rejected", rejected_mime)

# ----------------------------------------------------------
# 3. Oversized file
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.MAX_UPLOAD_SIZE_BYTES = 100

    rejected = False
    try:
        report_service.save_image(
            image_data=IMG_BYTES,  # 512 bytes > 100 byte limit
            filename="big.jpg",
            content_type="image/jpeg",
        )
    except report_service.ImageTooLargeError:
        rejected = True

    report("oversized file rejected", rejected)

# ----------------------------------------------------------
# 4. Unique filename generation
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = Path(tmp) / "civic.db"
    report_service.MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

    with patch("backend.services.ai_service.analyze", side_effect=success_analysis):
        r1 = report_service.submit_report(
            IMG_BYTES, "a.jpg", "First", content_type="image/jpeg"
        )
        r2 = report_service.submit_report(
            IMG_BYTES, "b.jpg", "Second", content_type="image/jpeg"
        )

    report(
        "unique filenames generated",
        r1.image_path != r2.image_path
        and Path(r1.image_path).name != Path(r2.image_path).name,
    )

# ----------------------------------------------------------
# 5. Successful AI analysis using a stub
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = Path(tmp) / "civic.db"
    report_service.MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

    with patch("backend.services.ai_service.analyze", side_effect=success_analysis):
        r = report_service.submit_report(
            IMG_BYTES, "x.jpg", "Deep pothole", content_type="image/jpeg"
        )

    report(
        "AI success: fields persisted",
        r.analysis_status.value == "completed"
        and r.issue_type == "pothole"
        and r.severity == "high"
        and r.confidence == 0.95
        and r.explanation == "Stub analysis result.",
    )

# ----------------------------------------------------------
# 6. AI failure -> analysis_status=failed (no crash)
# ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    report_service.UPLOAD_DIR = Path(tmp) / "uploads"
    report_service.DB_PATH = Path(tmp) / "civic.db"
    report_service.MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

    with patch("backend.services.ai_service.analyze", side_effect=failing_analysis):
        r = report_service.submit_report(
            IMG_BYTES, "y.jpg", "Deep pothole", content_type="image/jpeg"
        )

    report("AI failure: analysis_status=failed", r.analysis_status.value == "failed")
    report(
        "AI failure: no fabricated AI fields",
        r.issue_type is None
        and r.severity is None
        and r.confidence is None
        and r.explanation is None,
    )

    persisted = report_service.get_report(r.id)
    report(
        "failed report persisted",
        persisted is not None
        and persisted.analysis_status.value == "failed",
    )

print("=" * 60)
print(f"Passed: {passed}/{passed + failed}")