from backend.ai.vision_analyzer import analyze_image
from backend.ai.severity_engine import determine_severity_from_facts


TESTS = [
    (
        "OD-003",
        "data/evaluation/images/OD_003.jpeg",
        "A large uncovered drain is immediately beside a busy roadway with moving traffic.",
        "critical",
    ),

    (
        "SL-004",
        "data/evaluation/images/SL_004.jpeg",
        "A streetlight pole has fallen onto the roadside grass area.",
        "high",
    ),

    (
        "WL-003",
        "data/evaluation/images/WL_003.jpeg",
        "A major burst of water is spraying onto a city street from a damaged water line.",
        "critical",
    ),

    (
        "GO-003",
        "data/evaluation/images/GO_003.jpeg",
        "Garbage is scattered around a collection bin, with waste extending onto the ground.",
        "low",
    ),
]


print("=" * 70)
print("STRUCTURED SEVERITY TEST")
print("=" * 70)


for test_id, image, description, expected in TESTS:

    print("\n" + "-" * 70)
    print(test_id)

    result = analyze_image(
        image_path=image,
        description=description,
    )

    severity = determine_severity_from_facts(
        issue_type=result.issue_type.value,
        facts=result.visual_facts,
    )

    print("Issue type :", result.issue_type.value)
    print("Facts      :", result.visual_facts.model_dump())
    print("Expected   :", expected)
    print("Predicted  :", severity.value)

    if severity.value == expected:
        print("Result     : PASS")
    else:
        print("Result     : FAIL")