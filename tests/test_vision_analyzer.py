from backend.ai.vision_analyzer import analyze_image


IMAGE = "data/development/images/POT_001.jpeg"


result = analyze_image(
    image_path=IMAGE,
    description=(
        "Road surface has numerous potholes and "
        "broken patches along a long stretch."
    ),
)


print("=" * 60)
print("STRUCTURED VISION TEST")
print("=" * 60)

print()
print("Issue type :", result.issue_type.value)
print("Confidence:", result.confidence)

print()
print("Visual facts:")
print(result.visual_facts.model_dump_json(indent=2))

print()
print("Explanation:")
print(result.explanation)