from pathlib import Path
import csv


# -----------------------------
# Paths
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = PROJECT_ROOT / "data" / "development" / "reports.csv"
IMAGE_DIR = PROJECT_ROOT / "data" / "development" / "images"


# -----------------------------
# Allowed labels
# -----------------------------

ALLOWED_CATEGORIES = {
    "road",
    "waste_management",
    "electricity",
    "water",
    "drainage",
}

ALLOWED_ISSUE_TYPES = {
    "pothole",
    "damaged_road",
    "garbage_overflow",
    "illegal_dumping",
    "broken_streetlight",
    "water_leakage",
    "blocked_drain",
    "open_drain",
}

ALLOWED_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


# -----------------------------
# Load CSV
# -----------------------------

if not CSV_PATH.exists():
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

if not IMAGE_DIR.exists():
    raise FileNotFoundError(f"Image directory not found: {IMAGE_DIR}")


with open(CSV_PATH, "r", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))


print(f"Loaded {len(rows)} reports.")
print()


# -----------------------------
# Validate IDs
# -----------------------------

ids = [row["id"] for row in rows]

duplicate_ids = {
    report_id
    for report_id in ids
    if ids.count(report_id) > 1
}

if duplicate_ids:
    print(f"❌ Duplicate report IDs: {duplicate_ids}")
else:
    print("✅ Report IDs are unique.")


# -----------------------------
# Validate image references
# -----------------------------

referenced_images = {row["image"] for row in rows}

missing_images = [
    image
    for image in referenced_images
    if not (IMAGE_DIR / image).exists()
]

if missing_images:
    print("❌ Missing images:")
    for image in missing_images:
        print(f"   - {image}")
else:
    print("✅ All CSV images exist.")


# -----------------------------
# Find unreferenced images
# -----------------------------

actual_images = {
    image.name
    for image in IMAGE_DIR.iterdir()
    if image.is_file()
}

unreferenced_images = actual_images - referenced_images

if unreferenced_images:
    print("⚠️ Unreferenced images:")
    for image in sorted(unreferenced_images):
        print(f"   - {image}")
else:
    print("✅ No unreferenced images.")


# -----------------------------
# Validate labels
# -----------------------------

label_errors = []

for row in rows:

    if row["category"] not in ALLOWED_CATEGORIES:
        label_errors.append(
            f'{row["id"]}: invalid category "{row["category"]}"'
        )

    if row["issue_type"] not in ALLOWED_ISSUE_TYPES:
        label_errors.append(
            f'{row["id"]}: invalid issue_type "{row["issue_type"]}"'
        )

    if row["severity"] not in ALLOWED_SEVERITIES:
        label_errors.append(
            f'{row["id"]}: invalid severity "{row["severity"]}"'
        )


if label_errors:
    print("❌ Label errors:")

    for error in label_errors:
        print(f"   - {error}")

else:
    print("✅ All labels are valid.")


# -----------------------------
# Summary
# -----------------------------

print()
print("=" * 40)
print("DATASET VALIDATION SUMMARY")
print("=" * 40)

print(f"Reports: {len(rows)}")
print(f"Images:  {len(actual_images)}")
print(f"Missing: {len(missing_images)}")
print(f"Extra:   {len(unreferenced_images)}")
print(f"Label errors: {len(label_errors)}")

print("=" * 40)