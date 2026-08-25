from backend.services.jurisdiction_service import (
    resolve_jurisdiction,
    representative_sources,
)

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
print("JURISDICTION SERVICE TESTS")
print("=" * 60)

# ----------------------------------------------------------
# 1. Point inside the Jalukbari polygon
# ----------------------------------------------------------
r = resolve_jurisdiction(26.17, 91.665)
report("Jalukbari: resolved", r["jurisdiction_status"] == "resolved")
report(
    "Jalukbari: assembly constituency AS-037",
    (r.get("assembly_constituency") or {}).get("id") == "AS-037"
    and (r.get("assembly_constituency") or {}).get("name") == "Jalukbari",
)
report(
    "Jalukbari: MLA is Himanta Biswa Sarma (BJP)",
    (r.get("mla") or {}).get("name") == "Himanta Biswa Sarma"
    and (r.get("mla") or {}).get("party") == "Bharatiya Janata Party",
)

# ----------------------------------------------------------
# 2. Point inside the Dispur polygon
# ----------------------------------------------------------
r = resolve_jurisdiction(26.12, 91.785)
report(
    "Dispur: AC + MLA",
    r["jurisdiction_status"] == "resolved"
    and (r.get("assembly_constituency") or {}).get("id") == "AS-033"
    and (r.get("mla") or {}).get("name") == "Pradyut Bordoloi",
)

# ----------------------------------------------------------
# 3. Point inside Dimoria -> AGP MLA
# ----------------------------------------------------------
r = resolve_jurisdiction(26.05, 91.88)
report(
    "Dimoria: Tapan Das (Asom Gana Parishad)",
    r["jurisdiction_status"] == "resolved"
    and (r.get("assembly_constituency") or {}).get("id") == "AS-034"
    and (r.get("mla") or {}).get("name") == "Tapan Das"
    and (r.get("mla") or {}).get("party") == "Asom Gana Parishad",
)

# ----------------------------------------------------------
# 4. Lok Sabha linkage for all supported segments
# ----------------------------------------------------------
for label, coords in [
    ("Guwahati Central", (26.167, 91.755)),
    ("New Guwahati", (26.195, 91.80)),
]:
    r = resolve_jurisdiction(*coords)
    ls = r.get("lok_sabha_constituency") or {}
    mp = r.get("mp") or {}
    report(
        f"{label}: Guwahati LS + MP Bijuli Kalita Medhi",
        ls.get("id") == "GUWAHATI"
        and mp.get("name") == "Bijuli Kalita Medhi"
        and mp.get("party") == "Bharatiya Janata Party",
    )

# ----------------------------------------------------------
# 5. Approximate-boundary disclosure present
# ----------------------------------------------------------
r = resolve_jurisdiction(26.12, 91.785)
report(
    "resolution_method is approximate_locality",
    r.get("resolution_method") == "approximate_locality",
)

# ----------------------------------------------------------
# 6. Missing coordinates
# ----------------------------------------------------------
r = resolve_jurisdiction(None, None)
report("no coordinates: unavailable", r["jurisdiction_status"] == "unavailable")
report("no coordinates: no representatives", r.get("mla") is None and r.get("mp") is None)

r = resolve_jurisdiction(26.1, None)
report("half coordinates: unavailable", r["jurisdiction_status"] == "unavailable")

# ----------------------------------------------------------
# 7. Coordinates far outside supported boundaries
# ----------------------------------------------------------
r = resolve_jurisdiction(12.9716, 77.5946)  # Bengaluru
report(
    "Bengaluru point: outside_supported_area",
    r["jurisdiction_status"] == "outside_supported_area",
)
report(
    "outside area: no constituency attached",
    r.get("assembly_constituency") is None,
)

# ----------------------------------------------------------
# 8. Source metadata available for disclosure
# ----------------------------------------------------------
meta = representative_sources()
report(
    "representative metadata has verified_at + sources",
    meta.get("verified_at") == "2026-08-22"
    and isinstance(meta.get("sources"), dict),
)

print("=" * 60)
print(f"Passed: {passed}/{passed + failed}")
assert failed == 0, f"{failed} jurisdiction tests failed"
