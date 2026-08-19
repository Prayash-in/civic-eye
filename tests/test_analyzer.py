from backend.ai.analyzer import analyze_report


IMAGE = "data/development/images/POT_001.jpeg"

DESCRIPTION = (
    "Road surface has numerous potholes and broken patches "
    "along a long stretch."
)


result = analyze_report(
    image_path=IMAGE,
    description=DESCRIPTION,
)

print("\nAI RESULT")
print("---------")
print(f"Issue type : {result.issue_type.value}")
print(f"Severity   : {result.severity.value}")
print(f"Confidence : {result.confidence}")
print(f"Explanation: {result.explanation}")