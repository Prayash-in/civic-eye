import time
import csv
from pathlib import Path

from backend.ai.analyzer import analyze_report


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_PATH = PROJECT_ROOT / "data" / "development" / "reports.csv"
IMAGE_DIR = PROJECT_ROOT / "data" / "development" / "images"


# --------------------------------------------------
# Development test IDs
# These are ONLY development images.
# --------------------------------------------------

TEST_IDS = [
    "POT-001",
    "POT-002",
    "POT-003",
    "BD-001",
    "BD-004",
    "OD-001",
    "GO-002",
    "IDP-001",
    "SL-001",
    "WL-001",
]


# --------------------------------------------------
# Load development CSV
# --------------------------------------------------

def load_reports():
    reports = {}

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            reports[row["id"]] = row

    return reports


# --------------------------------------------------
# Main benchmark
# --------------------------------------------------

def main():

    reports = load_reports()

    results = []

    issue_correct = 0
    severity_correct = 0

    print("\n" + "=" * 70)
    print("CIVIC AI — DEVELOPMENT BENCHMARK")
    print("=" * 70)

    for number, report_id in enumerate(TEST_IDS, start=1):

        if report_id not in reports:
            print(f"\n[{number}/10] {report_id}")
            print("ERROR: ID not found in development/reports.csv")
            continue

        report = reports[report_id]

        image_path = IMAGE_DIR / report["image"]

        expected_issue = report["issue_type"]
        expected_severity = report["severity"]

        print("\n" + "-" * 70)
        print(f"[{number}/10] {report_id}")
        print(f"Image      : {report['image']}")
        print(f"Expected   : {expected_issue} / {expected_severity}")

        try:

            max_retries = 3
            result = None

            for attempt in range(max_retries):
                try:
                    result = analyze_report(
                        image_path=image_path,
                        description=report["description"],
                    )
                    break

                except Exception as error:
                    error_text = str(error)

                    if "503" in error_text or "UNAVAILABLE" in error_text:
                        if attempt < max_retries - 1:
                            wait_time = 5 * (attempt + 1)

                            print(
                                f"Temporary Gemini availability error. "
                                f"Retrying in {wait_time}s..."
                            )

                            time.sleep(wait_time)
                        else:
                            raise

                    else:
                        raise

            predicted_issue = result.issue_type.value
            predicted_severity = result.severity.value
            confidence = result.confidence

            issue_ok = predicted_issue == expected_issue
            severity_ok = predicted_severity == expected_severity

            if issue_ok:
                issue_correct += 1

            if severity_ok:
                severity_correct += 1

            results.append({
                "id": report_id,
                "expected_issue": expected_issue,
                "predicted_issue": predicted_issue,
                "expected_severity": expected_severity,
                "predicted_severity": predicted_severity,
                "confidence": confidence,
                "issue_correct": issue_ok,
                "severity_correct": severity_ok,
            })

            print(f"Predicted  : {predicted_issue} / {predicted_severity}")
            print(f"Confidence : {confidence:.2f}")

            print(
                "Issue      : "
                + ("PASS" if issue_ok else "FAIL")
            )

            print(
                "Severity   : "
                + ("PASS" if severity_ok else "FAIL")
            )

            print(f"Explanation: {result.explanation}")

        except Exception as error:

            print(f"ERROR: {error}")

            results.append({
                "id": report_id,
                "expected_issue": expected_issue,
                "predicted_issue": "ERROR",
                "expected_severity": expected_severity,
                "predicted_severity": "ERROR",
                "confidence": 0,
                "issue_correct": False,
                "severity_correct": False,
            })

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    total = len(results)

    if total == 0:
        print("\nNo results generated.")
        return

    issue_accuracy = issue_correct / total
    severity_accuracy = severity_correct / total

    print("\n")
    print("=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    print(f"Images tested          : {total}")
    print(
        f"Issue classification   : "
        f"{issue_correct}/{total} "
        f"({issue_accuracy * 100:.1f}%)"
    )

    print(
        f"Severity classification: "
        f"{severity_correct}/{total} "
        f"({severity_accuracy * 100:.1f}%)"
    )

    print("\nDetailed Results")
    print("-" * 70)

    print(
        f"{'ID':<10}"
        f"{'Expected':<22}"
        f"{'Predicted':<22}"
        f"{'Issue':<8}"
        f"{'Severity':<10}"
    )

    print("-" * 70)

    for result in results:

        expected = result["expected_issue"]
        predicted = result["predicted_issue"]

        issue_status = (
            "PASS"
            if result["issue_correct"]
            else "FAIL"
        )

        severity_status = (
            "PASS"
            if result["severity_correct"]
            else "FAIL"
        )

        print(
            f"{result['id']:<10}"
            f"{expected:<22}"
            f"{predicted:<22}"
            f"{issue_status:<8}"
            f"{severity_status:<10}"
        )


if __name__ == "__main__":
    main()