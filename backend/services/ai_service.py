from pathlib import Path

from backend.ai.analyzer import analyze_report


class AIServiceError(Exception):
    """Application-level error raised when AI analysis cannot be completed."""


def analyze(
    image_path: str | Path,
    description: str = "",
):
    """
    Analyze a civic issue report through the existing analyzer.

    Delegates to backend.ai.analyzer.analyze_report and maps any failure to
    a clean application-level error. Never fabricates an AI result.
    """
    try:
        return analyze_report(
            image_path=image_path,
            description=description,
        )
    except Exception as error:
        raise AIServiceError(
            "AI analysis is temporarily unavailable. Please try again."
        ) from error