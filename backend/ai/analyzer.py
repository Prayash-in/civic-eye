import base64
import json
import re
from pathlib import Path
from enum import Enum

import requests
from pydantic import BaseModel, Field, ValidationError


# ============================================================
# Configuration
# ============================================================

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen/qwen3-vl-4b"

REQUEST_TIMEOUT = 180


# ============================================================
# Civic Issue Schema
# ============================================================
class IssueType(str, Enum):
    POTHOLE = "pothole"
    DAMAGED_ROAD = "damaged_road"
    GARBAGE_OVERFLOW = "garbage_overflow"
    ILLEGAL_DUMPING = "illegal_dumping"
    BROKEN_STREETLIGHT = "broken_streetlight"
    WATER_LEAKAGE = "water_leakage"
    BLOCKED_DRAIN = "blocked_drain"
    OPEN_DRAIN = "open_drain"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CivicIssueAnalysis(BaseModel):
    issue_type: IssueType = Field(
        description="The primary civic issue identified in the image."
    )

    severity: Severity = Field(
        description="Severity level: low, medium, high, or critical."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence between 0 and 1."
    )

    explanation: str = Field(
        description="Brief explanation of the classification."
    )


# ============================================================
# Allowed Values
# ============================================================

VALID_ISSUE_TYPES = {
    "pothole",
    "damaged_road",
    "garbage_overflow",
    "illegal_dumping",
    "broken_streetlight",
    "water_leakage",
    "blocked_drain",
    "open_drain",
}

VALID_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """
You are an AI system for crowdsourced civic issue reporting.

Your task is to analyze a citizen-submitted image and description and
classify the PRIMARY civic issue.

You MUST classify the report into EXACTLY ONE of these issue types:

1. pothole
2. damaged_road
3. garbage_overflow
4. illegal_dumping
5. broken_streetlight
6. water_leakage
7. blocked_drain
8. open_drain


============================================================
ISSUE TYPE DEFINITIONS
============================================================

POTHOLE:
A localized cavity, depression, hole, or broken-out section in the road
surface.

It may contain water, loose asphalt, gravel, or broken road material.

Examples:
- one large pothole
- several distinct potholes
- water-filled potholes
- deep holes in the roadway

If distinct potholes are clearly the dominant problem, choose "pothole".


DAMAGED_ROAD:
General deterioration of the road surface where the main problem is
widespread cracking, uneven pavement, broken asphalt, surface wear,
exposed aggregate, or failed patches WITHOUT potholes being the dominant
identifiable problem.

Examples:
- extensive surface cracking
- widespread broken asphalt
- severely deteriorated pavement
- uneven road surface
- failed road patches

If distinct potholes are clearly the dominant problem, choose "pothole".


GARBAGE_OVERFLOW:
Waste overflowing from or accumulating primarily around a waste
collection container or bin.


ILLEGAL_DUMPING:
Waste visibly deposited in an open, roadside, vacant, or unauthorized
area rather than primarily around a collection bin.


BROKEN_STREETLIGHT:
A streetlight fixture, lamp, pole, housing, or related component is
visibly damaged, broken, fallen, or incomplete.


WATER_LEAKAGE:
Water is visibly escaping from a pipe, water infrastructure, road
surface, or other water supply source.


BLOCKED_DRAIN:
The PRIMARY problem is that an existing drainage opening or drain is
obstructed by garbage, leaves, debris, sediment, or another blockage.

Even if the drain is partially visible or uncovered, choose
"blocked_drain" when obstruction is the primary problem.

OPEN_DRAIN:
The PRIMARY problem is that the drainage channel itself is uncovered,
exposed, or open beside a road or pedestrian area.

If the drain is uncovered but the main visible problem is garbage,
debris, or obstruction restricting drainage, choose "blocked_drain".


============================================================
IMPORTANT BOUNDARIES
============================================================

POTHOLE vs DAMAGED_ROAD:

Distinct holes or depressions are the dominant problem
-> pothole

General cracking, deterioration, unevenness, or surface damage without
dominant potholes
-> damaged_road


============================================================
OPEN DRAIN vs BLOCKED DRAIN — STRICT RULE
============================================================

OPEN_DRAIN:
Choose "open_drain" when the defining civic problem is that the
drainage channel is uncovered, exposed, or open beside a road,
pedestrian path, or property.

The presence of garbage, leaves, water, or minor debris INSIDE an
otherwise clearly open drainage channel does NOT automatically make
it "blocked_drain".

BLOCKED_DRAIN:
Choose "blocked_drain" only when an existing drainage opening,
grate, inlet, or channel is visibly obstructed to the point that
the obstruction is the primary civic problem.

Decision rule:

1. Clearly exposed/uncovered drainage channel
   → open_drain

2. Drain opening/grate/channel primarily obstructed by waste/debris
   → blocked_drain

3. Open drain containing some garbage/debris but still visibly
   functioning as an open channel
   → open_drain

4. If uncertain, determine whether the PRIMARY problem is:
   "the drain is open"
   or
   "the drain is blocked".


GARBAGE_OVERFLOW vs ILLEGAL_DUMPING:

Garbage primarily around a collection bin
-> garbage_overflow

Garbage deposited in an open/unauthorized area
-> illegal_dumping


============================================================
SEVERITY DEFINITIONS
============================================================

LOW:
A minor civic issue with limited immediate impact.

Examples:
- small/localized pothole
- minor garbage accumulation
- small amount of roadside waste
- minor streetlight damage
- minor water seepage or pooling
- small drain obstruction


MEDIUM:
A clearly noticeable civic issue that affects normal use but does not
create an immediate serious safety hazard.

Examples:
- moderate pothole
- moderate garbage accumulation
- moderate illegal dumping
- partially blocked drain
- moderate water leakage
- noticeable but non-dangerous infrastructure damage


HIGH:
A serious civic issue that creates a significant safety, traffic,
environmental, or infrastructure risk.

Examples:
- deep or very large potholes affecting vehicle movement
- major drainage obstruction causing substantial water backup
- large uncontrolled water leakage across a roadway
- severely damaged/fallen infrastructure
- major garbage accumulation creating significant obstruction or hazard


CRITICAL:
An immediate and severe public safety or infrastructure emergency.

Use CRITICAL sparingly.

Examples:
- deep open drain directly beside a pedestrian path with severe fall risk
- major burst water line creating an immediate dangerous roadway condition
- infrastructure collapse presenting an immediate serious threat

============================================================
IMPORTANT SEVERITY CALIBRATION
============================================================

Do NOT determine severity solely from the visual size or quantity
of an object.

For waste-related issues:

GARBAGE_OVERFLOW:
- LOW: small amount of waste around a bin.
- MEDIUM: noticeable accumulation around a bin without major
  obstruction or immediate danger.
- HIGH: substantial overflow causing significant obstruction,
  spreading into traffic/pedestrian areas, or creating a serious
  sanitation/safety hazard.

ILLEGAL_DUMPING:
- LOW: small scattered amount of dumped waste.
- MEDIUM: noticeable or substantial dumping in an unauthorized
  area without an immediate major hazard.
- HIGH: very large-scale dumping creating major obstruction,
  environmental risk, or significant public safety concern.

A large pile does NOT automatically mean HIGH.

For drainage:

BLOCKED_DRAIN:
- MEDIUM: visible obstruction without major flooding or immediate
  danger.
- HIGH: severe obstruction associated with substantial water
  backup, flooding, or significant infrastructure impact.

For all categories:
Use the visual context and actual hazard, not merely the amount
of material visible.

============================================================
SEVERITY RULES
============================================================

1. Do NOT classify an issue as HIGH merely because it is clearly visible.

2. Do NOT classify an issue as CRITICAL merely because it looks serious.

3. Consider actual scale, extent, obstruction, and immediate hazard.

4. A moderate or localized issue should normally remain LOW or MEDIUM.

5. Use HIGH only when there is strong visual evidence of significant impact.

6. Use CRITICAL only when there is strong evidence of immediate severe danger.

7. When uncertain between two severity levels, choose the LOWER level
   unless the image clearly supports the higher level.


============================================================
CLASSIFICATION RULES
============================================================

1. Use the IMAGE as the primary source of evidence.

2. Use the citizen description as supporting information.

3. Do not invent details that are not visible or stated.

4. Select exactly ONE issue type.

5. Select exactly ONE severity.

6. Classify according to the PRIMARY civic issue.

7. Confidence must represent actual confidence.

8. Do not automatically assign high confidence.

9. Return ONLY valid JSON.

The JSON must have exactly these fields:

{
  "issue_type": "...",
  "severity": "...",
  "confidence": 0.0,
  "explanation": "..."
}
"""


# ============================================================
# Image Encoding
# ============================================================

def encode_image(image_path: str | Path) -> str:
    """
    Convert an image into a base64 data URL.
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    suffix = image_path.suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(
        suffix,
        "application/octet-stream"
    )

    with open(image_path, "rb") as file:
        encoded = base64.b64encode(
            file.read()
        ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# JSON Extraction
# ============================================================

def extract_json(text: str) -> dict:
    """
    Extract JSON from the model response.

    Handles:
    - pure JSON
    - JSON inside markdown fences
    - JSON surrounded by explanatory text
    """

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace("```", "").strip()

    # Try direct JSON parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the first JSON object
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"Could not find JSON in model response:\n{text}"
        )

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON returned by model:\n{text}"
        ) from error


# ============================================================
# Normalize Model Output
# ============================================================

def normalize_result(data: dict) -> dict:
    """
    Normalize Qwen's output before Pydantic validation.
    """

    if "issue_type" not in data:
        raise ValueError("Missing issue_type")

    if "severity" not in data:
        raise ValueError("Missing severity")

    if "confidence" not in data:
        raise ValueError("Missing confidence")

    if "explanation" not in data:
        data["explanation"] = ""

    issue_type = str(
        data["issue_type"]
    ).strip().lower()

    severity = str(
        data["severity"]
    ).strip().lower()

    # Normalize common formatting variations
    issue_type = issue_type.replace(" ", "_")
    issue_type = issue_type.replace("-", "_")

    severity = severity.lower()

    if issue_type not in VALID_ISSUE_TYPES:
        raise ValueError(
            f"Invalid issue_type returned by model: "
            f"{issue_type}"
        )

    if severity not in VALID_SEVERITIES:
        raise ValueError(
            f"Invalid severity returned by model: "
            f"{severity}"
        )

    # Convert confidence safely
    try:
        confidence = float(data["confidence"])
    except (TypeError, ValueError):
        confidence = 0.5

    # Clamp confidence
    confidence = max(
        0.0,
        min(1.0, confidence)
    )

    return {
    "issue_type": IssueType(issue_type),
    "severity": Severity(severity),
    "confidence": confidence,
    "explanation": str(
        data.get("explanation", "")
    ).strip(),
}


# ============================================================
# Main Analyzer
# ============================================================

def analyze_report(
    image_path: str | Path,
    description: str = "",
) -> CivicIssueAnalysis:
    """
    Analyze a civic issue report using Qwen3-VL through LM Studio.

    Parameters
    ----------
    image_path:
        Path to the submitted image.

    description:
        Citizen-provided description.

    Returns
    -------
    CivicIssueAnalysis
        Validated structured AI result.
    """

    image_data = encode_image(image_path)

    user_prompt = f"""
Analyze this civic issue report.

Citizen description:
{description}

Remember:

- The image is the primary evidence.
- The description is supporting evidence.
- Choose exactly one issue type.
- Choose exactly one severity.
- Return ONLY valid JSON.
"""

    payload = {
        "model": MODEL,

        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data,
                        },
                    },
                ],
            },
        ],

        "temperature": 0.1,

        "max_tokens": 400,

        "stream": False,
    }

    try:

        response = requests.post(
            LM_STUDIO_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.exceptions.ConnectionError as error:

        raise RuntimeError(
            "Could not connect to LM Studio.\n"
            "Make sure the LM Studio local server is running "
            "at http://localhost:1234"
        ) from error

    except requests.exceptions.Timeout as error:

        raise RuntimeError(
            "LM Studio request timed out."
        ) from error

    except requests.exceptions.HTTPError as error:

        raise RuntimeError(
            f"LM Studio API error: "
            f"{response.status_code}\n"
            f"{response.text}"
        ) from error

    # --------------------------------------------------------
    # Parse response
    # --------------------------------------------------------

    response_data = response.json()

    try:

        raw_text = (
            response_data["choices"][0]
            ["message"]["content"]
        )

    except (KeyError, IndexError) as error:

        raise RuntimeError(
            f"Unexpected LM Studio response:\n"
            f"{response_data}"
        ) from error

    # --------------------------------------------------------
    # Extract JSON
    # --------------------------------------------------------

    try:

        parsed = extract_json(raw_text)

        normalized = normalize_result(
            parsed
        )

    except (ValueError, json.JSONDecodeError) as error:

        raise RuntimeError(
            "Qwen returned an invalid analysis.\n\n"
            f"Raw response:\n{raw_text}"
        ) from error

    # --------------------------------------------------------
    # Validate with Pydantic
    # --------------------------------------------------------

    try:

        result = CivicIssueAnalysis(
            **normalized
        )

    except ValidationError as error:

        raise RuntimeError(
            "AI result failed schema validation.\n\n"
            f"Result:\n{normalized}\n\n"
            f"Validation error:\n{error}"
        ) from error

    return result