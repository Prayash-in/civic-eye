from pathlib import Path
import csv

from backend.ai.analyzer import analyze_report


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EVAL_CSV = PROJECT_ROOT / "data" / "evaluation" / "reports.csv"
IMAGE_DIR = PROJECT_ROOT / "data" / "evaluation" / "images"


# ---------------------------------------------------------
# LOAD DATASET
# ---------------------------------------------------------

def load_evaluation_dataset():
    with open(EVAL_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------
# MAIN BENCHMARK
# ---------------------------------------------------------

def main():

    rows = load_evaluation_dataset()

    print("=" * 70)
    print("CIVIC AI — FINAL EVALUATION BENCHMARK")
    print("=" * 70)

    total = len(rows)

    issue_correct = 0
    severity_correct = 0

    results = []

    for index, row in enumerate(rows, start=1):

        image_path = IMAGE_DIR / row["image"]

        expected_issue = row["issue_type"]
        expected_severity = row["severity"]

        print("\n" + "-" * 70)
        print(f"[{index}/{total}] {row['id']}")
        print(f"Image      : {row['image']}")
        print(f"Expected   : {expected_issue} / {expected_severity}")

        try:

            result = analyze_report(
                image_path=str(image_path),
                description=row["description"],
            )

            predicted_issue = result.issue_type.value
            predicted_severity = result.severity.value

            issue_pass = predicted_issue == expected_issue
            severity_pass = predicted_severity == expected_severity

            if issue_pass:
                issue_correct += 1

            if severity_pass:
                severity_correct += 1

            print(f"Predicted  : {predicted_issue} / {predicted_severity}")
            print(f"Confidence : {result.confidence:.2f}")

            print(
                f"Issue      : {'PASS' if issue_pass else 'FAIL'}"
            )

            print(
                f"Severity   : {'PASS' if severity_pass else 'FAIL'}"
            )

            print(f"Explanation: {result.explanation}")

            results.append({
                "id": row["id"],
                "expected_issue": expected_issue,
                "predicted_issue": predicted_issue,
                "expected_severity": expected_severity,
                "predicted_severity": predicted_severity,
                "confidence": result.confidence,
                "issue_correct": issue_pass,
                "severity_correct": severity_pass,
            })

        except Exception as e:

            print(f"ERROR: {e}")

            results.append({
                "id": row["id"],
                "expected_issue": expected_issue,
                "predicted_issue": "ERROR",
                "expected_severity": expected_severity,
                "predicted_severity": "ERROR",
                "confidence": 0,
                "issue_correct": False,
                "severity_correct": False,
            })


    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    issue_accuracy = (
        issue_correct / total * 100
        if total else 0
    )

    severity_accuracy = (
        severity_correct / total * 100
        if total else 0
    )

    print("\n")
    print("=" * 70)
    print("FINAL EVALUATION SUMMARY")
    print("=" * 70)

    print(f"Images tested          : {total}")
    print(
        f"Issue classification   : "
        f"{issue_correct}/{total} ({issue_accuracy:.1f}%)"
    )

    print(
        f"Severity classification: "
        f"{severity_correct}/{total} ({severity_accuracy:.1f}%)"
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

    for r in results:

        expected = (
            f"{r['expected_issue']}"
            f" / "
            f"{r['expected_severity']}"
        )

        predicted = (
            f"{r['predicted_issue']}"
            f" / "
            f"{r['predicted_severity']}"
        )

        issue_status = "PASS" if r["issue_correct"] else "FAIL"
        severity_status = (
            "PASS" if r["severity_correct"] else "FAIL"
        )

        print(
            f"{r['id']:<10}"
            f"{expected:<22}"
            f"{predicted:<22}"
            f"{issue_status:<8}"
            f"{severity_status:<10}"
        )


if __name__ == "__main__":
    main()