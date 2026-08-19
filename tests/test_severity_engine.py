from backend.ai.severity_engine import determine_severity


tests = [
    {
        "name": "small pothole",
        "issue_type": "pothole",
        "model_severity": "medium",
        "description": "A small localized pothole.",
        "explanation": "",
        "expected": "low",
    },
    {
        "name": "deep potholes",
        "issue_type": "pothole",
        "model_severity": "medium",
        "description": "Several deep potholes on a busy road.",
        "explanation": "",
        "expected": "high",
    },
    {
        "name": "blocked drain with leaves",
        "issue_type": "blocked_drain",
        "model_severity": "medium",
        "description": "Drain grate covered with dry leaves.",
        "explanation": "",
        "expected": "low",
    },
    {
        "name": "blocked drain flooding",
        "issue_type": "blocked_drain",
        "model_severity": "medium",
        "description": "Water is backing up from the blocked drain.",
        "explanation": "",
        "expected": "high",
    },
    {
        "name": "fallen streetlight",
        "issue_type": "broken_streetlight",
        "model_severity": "medium",
        "description": "Streetlight pole has fallen.",
        "explanation": "",
        "expected": "high",
    },
    {
        "name": "localized water leak",
        "issue_type": "water_leakage",
        "model_severity": "medium",
        "description": "Water is bubbling and pooling locally.",
        "explanation": "",
        "expected": "low",
    },
    {
        "name": "major water burst",
        "issue_type": "water_leakage",
        "model_severity": "high",
        "description": "A major burst of water is spraying onto the street.",
        "explanation": "",
        "expected": "critical",
    },
]


print("=" * 60)
print("SEVERITY ENGINE TEST")
print("=" * 60)

passed = 0

for test in tests:

    result = determine_severity(
        issue_type=test["issue_type"],
        model_severity=test["model_severity"],
        description=test["description"],
        explanation=test["explanation"],
    )

    expected = test["expected"]

    status = "PASS" if result.value == expected else "FAIL"

    if status == "PASS":
        passed += 1

    print(
        f"{test['name']:<30}"
        f"Expected: {expected:<10}"
        f"Predicted: {result.value:<10}"
        f"{status}"
    )


print("=" * 60)
print(f"Passed: {passed}/{len(tests)}")