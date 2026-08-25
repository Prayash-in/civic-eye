"""Deterministic issue-type to department/authority routing.

The mapping lives in backend/data/authorities.json and is configurable data,
NOT an officially verified government routing table (see the metadata block
in that file). The AI never determines authorities; only this rule-based
router does.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class AuthorityRoutingError(Exception):
    """Raised when routing cannot be completed at all."""


@lru_cache(maxsize=1)
def _load_authorities() -> dict:
    with open(_DATA_DIR / "authorities.json", encoding="utf-8") as file:
        return json.load(file)


def _authority_for_district(
    base_authority: Optional[str],
    department: Optional[str],
    district: Optional[str],
    issue_type: Optional[str],
    data: dict,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Override base authority with district-specific authority when available.

    Returns (authority, department, extra_reason_suffix).
    """
    if not district:
        return base_authority, department, None

    district_defaults = data.get("district_defaults", {})
    water_authorities = data.get("district_water_authorities", {})

    # Water supply has a separate per-district utility mapping
    if issue_type == "water_leakage" and district in water_authorities:
        return water_authorities[district], department, f" Routed to {district} district water authority."

    if district in district_defaults:
        district_auth = district_defaults[district]
        # Only override if base is the generic Guwahati authority
        if base_authority == "Guwahati Municipal Corporation":
            return district_auth, department, f" Jurisdiction: {district} district."

    return base_authority, department, None


def route_issue(
    issue_type: Optional[str], jurisdiction: Optional[dict] = None
) -> dict:
    """Route an AI-detected issue type to a responsible authority.

    Unknown or missing issue types fall back to a generic civic-services
    route so reports are never silently dropped, and the response states so.

    When `jurisdiction` is provided (must contain assembly_constituency
    district or lok sabha info), the authority is localized to that
    district — e.g. Darrang reports go to Mangaldai Municipal Board,
    not Guwahati Municipal Corporation. This ensures Mangaldai GPS
    reports never incorrectly claim Guwahati as the authority.
    """
    data = _load_authorities()
    fallback = data.get("default_authority", {})

    # Extract district from jurisdiction if available
    district = None
    if jurisdiction:
        assembly = jurisdiction.get("assembly_constituency") or {}
        district = assembly.get("district")
        # Fallback: infer from Lok Sabha if district missing but LS is Darrang-Udalguri -> Darrang
        if not district:
            ls = jurisdiction.get("lok_sabha_constituency") or {}
            if ls.get("id") == "DARRANG_UDALGURI":
                district = "Darrang"

    if not issue_type:
        base_auth = fallback.get("authority")
        base_dept = fallback.get("department")
        auth, dept, suffix = _authority_for_district(
            base_auth, base_dept, district, issue_type, data
        )
        reason = "No classified issue type available; routed to general civic services."
        if suffix:
            reason += suffix
        return {
            "authority": auth,
            "department": dept,
            "routing_reason": reason,
            "routing_status": "fallback",
        }

    entry = data.get("issue_routing", {}).get(issue_type)
    if entry is None:
        base_auth = fallback.get("authority")
        base_dept = fallback.get("department")
        auth, dept, suffix = _authority_for_district(
            base_auth, base_dept, district, issue_type, data
        )
        reason = (
            f"Issue type '{issue_type}' has no specific route yet; "
            "routed to general civic services."
        )
        if suffix:
            reason += suffix
        return {
            "authority": auth,
            "department": dept,
            "routing_reason": reason,
            "routing_status": "fallback",
        }

    base_auth = entry["authority"]
    base_dept = entry["department"]
    auth, dept, suffix = _authority_for_district(
        base_auth, base_dept, district, issue_type, data
    )
    reason = entry["routing_reason"]
    if suffix:
        reason = reason + suffix

    return {
        "authority": auth,
        "department": dept,
        "routing_reason": reason,
        "routing_status": "routed",
    }


def routing_metadata() -> dict:
    return _load_authorities().get("metadata", {})
