import csv
from pathlib import Path

from backend.ai.vision_analyzer import analyze_image
from backend.ai.severity_engine import determine_severity_from_facts


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# IMPORTANT:
# Use the SAME CSV path that your existing evaluation benchmark uses.
EVAL_CSV = PROJECT_ROOT / "data" / "evaluation" / "reports.csv"
IMAGE_DIR = PROJECT_ROOT / "data" / "evaluation" / "images"


def main():

    with open(EVAL_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)

    issue_correct = 0
    severity_correct = 0
    successful = 0

    print("=" * 70)
    print("CIVIC AI — STRUCTURED AI EVALUATION")
    print("=" * 70)

    for index, row in enumerate(rows, start=1):

        image_path = IMAGE_DIR / row["image"].strip()

        expected_issue = row["issue_type"].strip()
        expected_severity = row["severity"].strip()

        print("\n" + "-" * 70)
        print(f"[{index}/{total}] {row['id']}")
        print(f"Image      : {image_path.name}")
        print(f"Expected   : {expected_issue} / {expected_severity}")

        if not image_path.exists():

            print(f"ERROR: Image not found: {image_path}")

            continue

        try:

            vision = analyze_image(
                image_path=str(image_path),
                description=row["description"],
            )

            final_severity = determine_severity_from_facts(
                issue_type=vision.issue_type.value,
                facts=vision.visual_facts,
            )

            predicted_issue = vision.issue_type.value
            predicted_severity = final_severity.value

            issue_pass = predicted_issue == expected_issue
            severity_pass = predicted_severity == expected_severity

            successful += 1

            if issue_pass:
                issue_correct += 1

            if severity_pass:
                severity_correct += 1

            print(
                f"Predicted  : "
                f"{predicted_issue} / {predicted_severity}"
            )

            print(
                f"Confidence : {vision.confidence:.2f}"
            )

            print(
                f"Issue      : "
                f"{'PASS' if issue_pass else 'FAIL'}"
            )

            print(
                f"Severity   : "
                f"{'PASS' if severity_pass else 'FAIL'}"
            )

            print(
                f"Facts      : "
                f"{vision.visual_facts.model_dump()}"
            )

        except Exception as e:

            print(f"ERROR: {e}")


    issue_accuracy = (
        issue_correct / successful * 100
        if successful
        else 0
    )

    severity_accuracy = (
        severity_correct / successful * 100
        if successful
        else 0
    )

    print("\n")
    print("=" * 70)
    print("STRUCTURED EVALUATION SUMMARY")
    print("=" * 70)

    print(f"Dataset images          : {total}")
    print(f"Successfully analyzed   : {successful}")

    print(
        f"Issue classification    : "
        f"{issue_correct}/{successful} "
        f"({issue_accuracy:.1f}%)"
    )

    print(
        f"Severity classification : "
        f"{severity_correct}/{successful} "
        f"({severity_accuracy:.1f}%)"
    )


if __name__ == "__main__":
    main()