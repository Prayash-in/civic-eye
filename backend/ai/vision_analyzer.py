import base64
import json
import re
from enum import Enum
from pathlib import Path

import requests
from pydantic import BaseModel, Field, ValidationError


LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen/qwen3-vl-4b"

REQUEST_TIMEOUT = 180


class IssueType(str, Enum):
    POTHOLE = "pothole"
    DAMAGED_ROAD = "damaged_road"
    GARBAGE_OVERFLOW = "garbage_overflow"
    ILLEGAL_DUMPING = "illegal_dumping"
    BROKEN_STREETLIGHT = "broken_streetlight"
    WATER_LEAKAGE = "water_leakage"
    BLOCKED_DRAIN = "blocked_drain"
    OPEN_DRAIN = "open_drain"


class VisualFacts(BaseModel):
    """
    Structured observations extracted from the image.

    These are observations, NOT severity decisions.
    """

    size: str = "unknown"
    extent: str = "unknown"

    depth: str = "unknown"

    water_present: bool = False
    water_flow: str = "none"

    obstruction: bool = False

    garbage_present: bool = False
    garbage_amount: str = "none"

    uncovered: bool = False

    pedestrian_exposure: bool = False
    traffic_exposure: bool = False

    structural_failure: bool = False
    fallen: bool = False

    road_affected: bool = False

    immediate_hazard: bool = False


class VisionAnalysis(BaseModel):
    issue_type: IssueType
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    visual_facts: VisualFacts
    explanation: str


SYSTEM_PROMPT = """
You are the visual perception component of a civic issue reporting
system.

Your job is NOT to decide the final severity.

Your job is to:

1. Identify the PRIMARY civic issue.
2. Extract objective visual facts from the image.
3. Provide a short explanation.

Allowed issue types:

- pothole
- damaged_road
- garbage_overflow
- illegal_dumping
- broken_streetlight
- water_leakage
- blocked_drain
- open_drain


============================================================
IMPORTANT
============================================================

Do NOT assign severity.

Do NOT output low, medium, high, or critical.

Instead, describe what is actually visible.

Do not invent facts that cannot reasonably be observed.

The image is the primary evidence.
The citizen description is supporting evidence.


============================================================
VISUAL FACTS
============================================================

Return these observations:

size:
- small
- moderate
- large
- unknown

extent:
- localized
- moderate
- widespread
- unknown

depth:
- shallow
- moderate
- deep
- unknown

water_present:
true / false

water_flow:
- none
- pooling
- flowing
- forceful
- unknown

obstruction:
true / false

garbage_present:
true / false

garbage_amount:
- none
- small
- moderate
- large
- unknown

uncovered:
true / false

pedestrian_exposure:
true / false

traffic_exposure:
true / false

structural_failure:
true / false

fallen:
true / false

road_affected:
true / false

immediate_hazard:
true / false


============================================================
ISSUE-SPECIFIC GUIDANCE
============================================================

POTHOLE:
Look for distinct holes or depressions in the roadway.
Record size, depth, number/extent, water presence and traffic
exposure.

DAMAGED_ROAD:
Look for widespread cracking, broken asphalt, uneven pavement,
failed patches and general surface deterioration.

BLOCKED_DRAIN:
Look for a drain, grate, inlet or channel that is obstructed.
Record whether garbage/debris is blocking it and whether water is
backing up.

OPEN_DRAIN:
Look for an uncovered or exposed drainage channel.
Record whether it is deep and whether pedestrians or traffic are
exposed to it.

GARBAGE_OVERFLOW:
Look for waste overflowing from or accumulating around a collection
bin/container.

ILLEGAL_DUMPING:
Look for waste deposited in an open or unauthorized area rather
than primarily around a collection bin.

BROKEN_STREETLIGHT:
Look for broken fixtures, damaged poles, fallen poles, structural
failure or exposed/damaged components.

WATER_LEAKAGE:
Look for water escaping from infrastructure, pipes or the road.
Record whether water is pooling, flowing or spraying forcefully.


============================================================
OUTPUT
============================================================

Return ONLY valid JSON:

{
  "issue_type": "...",
  "confidence": 0.0,
  "visual_facts": {
    "size": "...",
    "extent": "...",
    "depth": "...",
    "water_present": false,
    "water_flow": "...",
    "obstruction": false,
    "garbage_present": false,
    "garbage_amount": "...",
    "uncovered": false,
    "pedestrian_exposure": false,
    "traffic_exposure": false,
    "structural_failure": false,
    "fallen": false,
    "road_affected": false,
    "immediate_hazard": false
  },
  "explanation": "..."
}
"""


def encode_image(image_path: str | Path) -> str:

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(
        image_path.suffix.lower(),
        "application/octet-stream",
    )

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(
            f.read()
        ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def extract_json(text: str) -> dict:

    text = text.strip()

    text = re.sub(
        r"```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace("```", "").strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"No JSON found in model response:\n{text}"
        )

    return json.loads(match.group(0))


def analyze_image(
    image_path: str | Path,
    description: str = "",
) -> VisionAnalysis:

    image_data = encode_image(image_path)

    user_prompt = f"""
Analyze this civic issue image.

Citizen description:

{description}

Extract the visual facts defined by the system instructions.

Remember:

- Do NOT determine severity.
- Do NOT invent facts.
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
        "max_tokens": 600,
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
            "Could not connect to LM Studio at "
            "http://localhost:1234"
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

    try:

        data = extract_json(raw_text)

        return VisionAnalysis(
            **data
        )

    except (ValueError, ValidationError) as error:

        raise RuntimeError(
            "Qwen returned invalid structured output.\n\n"
            f"Raw response:\n{raw_text}"
        ) from error