# CIVIC AI — MVP IMPLEMENTATION INSTRUCTIONS

## ROLE

You are the lead full-stack engineer responsible for converting
the existing Civic AI repository into a working hackathon MVP.

The project is a crowdsourced civic issue reporting system.

The goal is NOT to rebuild the AI research pipeline.

The goal is to build a complete, functional MVP around the
already-working local AI analyzer.

---

# 1. IMPORTANT — DO NOT BREAK THE EXISTING AI

The existing AI analyzer is already implemented in:

backend/ai/analyzer.py

It uses:

- Qwen3-VL 4B
- LM Studio
- OpenAI-compatible local API
- http://localhost:1234/v1/chat/completions

The analyzer currently accepts:

image_path
description

and returns:

CivicIssueAnalysis

with:

- issue_type
- severity
- confidence
- explanation

DO NOT replace this implementation.

DO NOT switch it to Gemini.

DO NOT introduce a cloud LLM.

DO NOT rewrite the AI prompt unless explicitly required.

DO NOT remove the existing evaluation/test infrastructure.

The AI is already working and must be treated as an existing
dependency.

---

# 2. AI MODEL

Current model:

qwen/qwen3-vl-4b

Served through:

http://localhost:1234

The application must assume LM Studio is running locally.

Create configuration so that the LM Studio URL and model name
can be configured through environment variables.

Example:

LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
LM_STUDIO_MODEL=qwen/qwen3-vl-4b

However, preserve the current working defaults.

---

# 3. CIVIC ISSUE TYPES

The system supports exactly these issue types:

- pothole
- damaged_road
- garbage_overflow
- illegal_dumping
- broken_streetlight
- water_leakage
- blocked_drain
- open_drain

Do not introduce additional issue categories in the MVP.

---

# 4. MVP OBJECTIVE

Build a complete working civic reporting application.

A citizen should be able to:

1. Open the application.
2. Submit a civic issue.
3. Upload an image.
4. Enter a description.
5. Provide/select location.
6. Submit the report.
7. Have the image analyzed by Civic AI.
8. See the AI result.
9. Have the report stored.
10. See the report on the dashboard/map.

An administrator should be able to:

1. Open the dashboard.
2. View submitted reports.
3. See issue type.
4. See severity.
5. See confidence.
6. See description.
7. See image.
8. See location.
9. Filter reports.
10. View reports on a map.
11. Open an individual report.

---

# 5. PRIORITY

The MVP priority order is:

P0 — MUST WORK

- report submission
- image upload
- description
- location
- AI analysis
- database persistence
- report listing
- report detail
- map
- basic filtering

P1 — SHOULD WORK

- loading states
- error handling
- responsive UI
- image preview
- AI explanation
- report statistics

P2 — OPTIONAL

- duplicate detection
- report status workflow
- authentication
- notifications
- advanced analytics
- advanced severity logic

Do NOT spend significant time on P2 before P0 is complete.

---

# 6. AI INTEGRATION

Create a clean service boundary around:

backend.ai.analyzer.analyze_report

The API layer must not contain AI implementation logic.

Use:

API route
    ↓
AI service
    ↓
analyze_report()
    ↓
CivicIssueAnalysis

The API should return structured data such as:

{
  "issue_type": "pothole",
  "severity": "high",
  "confidence": 0.95,
  "explanation": "..."
}

---

# 7. REPORT DATA MODEL

A report should contain at minimum:

id

image_path

description

category

issue_type

severity

confidence

explanation

latitude

longitude

created_at

status

Use:

status:
- submitted
- reviewed
- resolved

Default:

submitted

Do not over-engineer the database.

---

# 8. IMAGE STORAGE

Uploaded images must NOT be stored inside the source-code directory.

Create a dedicated uploads directory.

Example:

data/uploads/

Use unique filenames.

Do not overwrite existing images.

Validate:

- file type
- file size
- image extension

Allowed:

jpg
jpeg
png
webp

---

# 9. LOCATION

The MVP must support latitude and longitude.

The frontend should allow:

- browser geolocation
OR
- selecting a location on the map
OR
- manually entering coordinates

If browser geolocation is denied, the user must still be able
to submit a report.

Do not make GPS permission mandatory.

---

# 10. MAP

Use a free map solution.

Prefer:

Leaflet + OpenStreetMap

Do NOT introduce paid map APIs.

The map must:

- show report markers
- display issue type
- display severity
- allow clicking a marker
- show basic report information

---

# 11. DASHBOARD

Create a simple administrator dashboard.

Display:

Total Reports

Reports by Issue Type

Reports by Severity

Recent Reports

Map

Report table/list

Filters:

Issue Type

Severity

Status

The dashboard should be functional before being visually
perfect.

---

# 12. REPORT SUBMISSION FLOW

Expected flow:

Citizen opens:

/report

Then:

Upload Image
+
Description
+
Location

↓

Submit

↓

Show:

"Analyzing your report..."

↓

AI analysis

↓

Show:

Issue:
Pothole

Severity:
High

Confidence:
95%

Explanation:
...

↓

Save report

↓

Show confirmation.

---

# 13. ERROR HANDLING

Handle:

- missing image
- invalid image
- oversized image
- missing description
- AI unavailable
- LM Studio not running
- invalid AI response
- database failure
- location unavailable

Never expose Python stack traces to the user.

Return useful error messages.

---

# 14. AI FAILURE

If LM Studio is unavailable:

Do NOT fake an AI result.

Return:

"AI analysis is temporarily unavailable.
Please try again."

The report may optionally be stored with:

analysis_status = failed

but never fabricate issue_type/severity.

---

# 15. FRONTEND

Build a clean modern civic-tech interface.

The UI should communicate:

"Report a civic problem.
Let AI analyze it.
Help improve the city."

Required pages:

/

Landing page

/report

Citizen report submission

/reports

Report list

/reports/[id]

Report details

/dashboard

Admin dashboard

/map

Civic issue map

---

# 16. DESIGN

Use a modern, clean, trustworthy civic-tech design.

Prioritize:

- mobile responsiveness
- accessibility
- readable typography
- clear buttons
- clear issue badges
- clear severity badges
- image previews
- loading indicators

Do not spend excessive time on animations.

Functionality comes first.

---

# 17. BACKEND ARCHITECTURE

Keep clear separation:

backend/
    ai/
    api/
    models/
    services/
    database/

Suggested:

backend/
    ai/
        analyzer.py
        vision_analyzer.py
        severity_engine.py

    api/
        reports.py

    models/
        report.py

    services/
        report_service.py

    database/
        database.py

Do not move the existing AI files unnecessarily.

---

# 18. TESTING

Preserve all existing tests.

Existing important tests include:

tests/test_analyzer.py

tests/run_dev_benchmark.py

tests/run_evaluation_benchmark.py

tests/test_vision_analyzer.py

tests/test_structured_severity.py

Do not delete or rewrite these tests merely to make them pass.

Add API tests for:

POST /reports

GET /reports

GET /reports/{id}

---

# 19. DEVELOPMENT DATA

Existing development/evaluation datasets are for AI evaluation.

DO NOT modify them.

DO NOT use the evaluation dataset as application data.

Keep evaluation images and CSV files separate from user uploads.

---

# 20. SEVERITY

Severity is currently SECONDARY.

Do not spend significant development time trying to improve
severity accuracy.

The existing severity output should be displayed.

The system must not allow severity errors to break:

- issue classification
- report submission
- database storage
- dashboard
- map

Severity can be improved in a future iteration.

---

# 21. SECURITY

At minimum:

- validate uploaded files
- generate unique filenames
- prevent path traversal
- don't expose environment variables
- don't expose API keys
- don't execute uploaded files
- restrict upload size

---

# 22. ENVIRONMENT

Use the existing Python environment and uv setup.

Do not replace uv with pip.

Do not create unnecessary virtual environments.

Use:

uv run ...

for Python execution.

---

# 23. WORKING STYLE

Before changing architecture:

1. Inspect the existing repository.
2. Understand the existing files.
3. Reuse existing code.
4. Avoid unnecessary dependencies.
5. Make small changes.
6. Run tests after each major change.
7. Keep the application runnable.

Do NOT rewrite the project from scratch.

---

# 24. DEFINITION OF DONE

The MVP is considered complete when this works:

1. Start LM Studio.
2. Start backend.
3. Start frontend.
4. Open the report page.
5. Upload a civic issue image.
6. Enter description.
7. Provide location.
8. Submit.
9. Backend calls Qwen3-VL through LM Studio.
10. AI returns issue classification.
11. Report is stored.
12. Dashboard shows report.
13. Map shows report.
14. Clicking the report displays its details.
15. Existing AI tests still work.

The complete flow must work end-to-end.

---

# 25. FINAL RULE

DO NOT optimize prematurely.

DO NOT build unnecessary features.

DO NOT replace working AI code.

DO NOT introduce cloud AI.

DO NOT spend time perfecting severity.

BUILD THE SMALLEST COMPLETE CIVIC AI MVP THAT WORKS END-TO-END.