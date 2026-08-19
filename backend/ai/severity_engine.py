from enum import Enum

from backend.ai.vision_analyzer import VisualFacts


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def determine_severity_from_facts(
    issue_type: str,
    facts: VisualFacts,
) -> Severity:

    issue_type = issue_type.lower().strip()

    # =========================================================
    # POTHOLE
    # =========================================================

    if issue_type == "pothole":

        if (
            facts.immediate_hazard
            and facts.extent == "widespread"
            and facts.depth == "deep"
        ):
            return Severity.HIGH

        if (
            facts.size == "large"
            or facts.depth == "deep"
            or facts.extent == "widespread"
        ):
            return Severity.HIGH

        if (
            facts.size == "moderate"
            or facts.depth == "moderate"
        ):
            return Severity.MEDIUM

        return Severity.LOW

    # =========================================================
    # DAMAGED ROAD
    # =========================================================

    if issue_type == "damaged_road":

        if (
            facts.extent == "widespread"
            and facts.immediate_hazard
        ):
            return Severity.HIGH

        if facts.extent == "widespread":
            return Severity.HIGH

        if facts.size == "moderate":
            return Severity.MEDIUM

        return Severity.LOW

    # =========================================================
    # BLOCKED DRAIN
    # =========================================================

    if issue_type == "blocked_drain":

        if (
            facts.water_flow in {
                "forceful",
                "flowing",
            }
            and facts.immediate_hazard
        ):
            return Severity.HIGH

        if facts.obstruction and facts.water_present:
            return Severity.MEDIUM

        if facts.obstruction:
            return Severity.MEDIUM

        return Severity.LOW

    # =========================================================
    # OPEN DRAIN
    # =========================================================

    if issue_type == "open_drain":

        # Critical:
        # Deep exposed drain + pedestrian/traffic exposure
        if (
            facts.uncovered
            and facts.depth == "deep"
            and (
                facts.pedestrian_exposure
                or facts.traffic_exposure
            )
        ):
            return Severity.CRITICAL

        # High:
        # Clearly exposed drain with significant hazard
        if (
            facts.uncovered
            and (
                facts.depth == "deep"
                or facts.immediate_hazard
            )
        ):
            return Severity.HIGH

        if facts.uncovered:
            return Severity.MEDIUM

        return Severity.LOW

    # =========================================================
    # GARBAGE OVERFLOW
    # =========================================================

    if issue_type == "garbage_overflow":

        # HIGH requires an actual significant hazard,
        # not merely a large quantity of garbage.
        if (
         facts.immediate_hazard
            and (
                facts.traffic_exposure
                or facts.pedestrian_exposure
            )
        ):
            return Severity.HIGH

        # MEDIUM requires noticeable accumulation with
        # some functional impact.
        if (
            facts.garbage_amount in {"moderate", "large"}
            and (
                facts.obstruction
            )
        ):
            return Severity.MEDIUM

        # Large garbage quantity without a demonstrated
        # hazard or functional obstruction remains LOW.
        return Severity.LOW

    # =========================================================
    # ILLEGAL DUMPING
    # =========================================================

    if issue_type == "illegal_dumping":

        if (
            facts.garbage_amount == "large"
            and facts.extent == "widespread"
            and facts.immediate_hazard
        ):
            return Severity.HIGH

        if (
            facts.garbage_amount == "large"
            or facts.extent == "widespread"
        ):
            return Severity.MEDIUM

        return Severity.LOW

    # =========================================================
    # BROKEN STREETLIGHT
    # =========================================================

    if issue_type == "broken_streetlight":

        if (
            facts.fallen
            or facts.structural_failure
        ):
            return Severity.HIGH

        if facts.immediate_hazard:
            return Severity.HIGH

        if facts.size == "moderate":
            return Severity.MEDIUM

        return Severity.LOW

    # =========================================================
    # WATER LEAKAGE
    # =========================================================

    if issue_type == "water_leakage":

        if (
            facts.water_flow == "forceful"
            and facts.road_affected
            and facts.immediate_hazard
        ):
            return Severity.CRITICAL

        if (
            facts.water_flow == "forceful"
            or facts.water_flow == "flowing"
        ):
            return Severity.HIGH

        if facts.water_flow == "pooling":
            return Severity.LOW

        return Severity.LOW

    # =========================================================
    # FALLBACK
    # =========================================================

    return Severity.MEDIUM