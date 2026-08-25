from backend.config import AnalysisStatus, DB_PATH
from backend.database.database import (
    create_report,
    delete_report,
    get_report,
    init_db,
    list_reports,
    update_analysis,
)
from backend.models.report import ReportCreate, ReportStatus

print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)

print(f"Database : {DB_PATH}")

init_db(DB_PATH)

created = create_report(
    ReportCreate(
        image_path="data/uploads/test_001.jpg",
        description="Deep pothole on Main Street.",
        category="road",
        latitude=26.1,
        longitude=91.7,
    )
)

print(f"Created  : id={created.id} status={created.status.value} analysis={created.analysis_status.value}")

fetched = get_report(created.id)
assert fetched is not None
assert fetched.id == created.id
assert fetched.image_path == "data/uploads/test_001.jpg"
assert fetched.status == ReportStatus.SUBMITTED
assert fetched.analysis_status == AnalysisStatus.PENDING
assert fetched.issue_type is None
assert fetched.severity is None
print("Retrieved: pre-analysis report OK (AI fields null)")

updated = update_analysis(
    report_id=created.id,
    issue_type="pothole",
    severity="high",
    confidence=0.95,
    explanation="Deep hole in the roadway.",
    analysis_status=AnalysisStatus.COMPLETED.value,
)
assert updated is not None
assert updated.issue_type == "pothole"
assert updated.severity == "high"
assert updated.confidence == 0.95
assert updated.analysis_status == AnalysisStatus.COMPLETED
print("Updated  : analysis fields + status OK")

re_fetched = get_report(created.id)
assert re_fetched is not None
assert re_fetched.issue_type == "pothole"
assert re_fetched.analysis_status == AnalysisStatus.COMPLETED
print("Retrieved: post-analysis report OK")

listed = list_reports(DB_PATH, issue_type="pothole")
assert any(r.id == created.id for r in listed)
print(f"Listed   : {len(listed)} report(s) with issue_type=pothole")

deleted = delete_report(created.id)
assert deleted is True
assert get_report(created.id) is None
print("Cleaned  : test report deleted")

print()
print("ALL DATABASE VERIFICATION CHECKS PASSED")