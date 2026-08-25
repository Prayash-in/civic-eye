from backend.services.authority_service import route_issue, routing_metadata

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


print("=" * 60)
print("AUTHORITY ROUTING TESTS")
print("=" * 60)

# ----------------------------------------------------------
# 1. Every classified issue type routes deterministically
# ----------------------------------------------------------
expected = {
    "pothole": ("Roads & Infrastructure", "Guwahati Municipal Corporation"),
    "damaged_road": ("Roads & Infrastructure", "Guwahati Municipal Corporation"),
    "garbage_overflow": (
        "Solid Waste Management",
        "Guwahati Municipal Corporation",
    ),
    "illegal_dumping": (
        "Solid Waste Management",
        "Guwahati Municipal Corporation",
    ),
    "broken_streetlight": (
        "Street Lighting & Electrical",
        "Guwahati Municipal Corporation",
    ),
    "water_leakage": ("Water Supply", "Guwahati Jal Board"),
    "blocked_drain": ("Drainage & Stormwater", "Guwahati Municipal Corporation"),
    "open_drain": ("Drainage & Stormwater", "Guwahati Municipal Corporation"),
}

for issue_type, (dept, authority) in expected.items():
    result = route_issue(issue_type)
    report(
        f"{issue_type} -> {dept}",
        result["department"] == dept
        and result["authority"] == authority
        and result["routing_status"] == "routed"
        and bool(result["routing_reason"]),
    )

# ----------------------------------------------------------
# 2. Unknown issue type falls back instead of failing
# ----------------------------------------------------------
result = route_issue("meteor_strike")
report(
    "unknown type: fallback to general civic services",
    result["routing_status"] == "fallback"
    and result["authority"] == "Guwahati Municipal Corporation"
    and result["department"] == "General Civic Services"
    and "meteor_strike" in result["routing_reason"],
)

# ----------------------------------------------------------
# 3. Missing issue type falls back too
# ----------------------------------------------------------
result = route_issue(None)
report("None type: fallback", result["routing_status"] == "fallback")
report(
    "None type: still names an authority",
    bool(result["authority"]) and bool(result["department"]),
)

# ----------------------------------------------------------
# 4. Metadata marks the mapping as non-official demo data
# ----------------------------------------------------------
meta = routing_metadata()
report(
    "mapping flagged configurable / not officially verified",
    meta.get("verified_at") == "2026-08-22"
    and any("NOT been verified" in note for note in meta.get("notes", [])),
)

print("=" * 60)
print(f"Passed: {passed}/{passed + failed}")
assert failed == 0, f"{failed} authority tests failed"
