# AI Problem Definition — Crowdsourced Civic Issue Reporting and Resolution

## 1. Problem Definition

Civic authorities receive reports about problems such as potholes, garbage accumulation, broken streetlights, water leakage, and drainage issues. These reports are often unstructured, incomplete, duplicated, and difficult to prioritize.

A citizen may provide only a photograph, a short description, and a location. For authorities to act efficiently, this raw information must be transformed into structured and actionable intelligence.

The AI component of the system addresses this problem by converting **raw citizen reports into structured civic issue intelligence** that can support classification, prioritization, duplicate detection, and departmental routing.

### Core Problem

> **How can raw, crowdsourced citizen reports containing images, descriptions, and geographic information be automatically transformed into structured, prioritized, and actionable civic issue information?**

---

## 2. AI Objective

The objective is to develop a **Civic Issue Intelligence Engine** that analyzes a citizen's report and determines:

1. What type of civic issue has been reported?
2. How severe is the issue?
3. How confident is the system in its prediction?
4. Which department should handle the issue?
5. Is the report potentially a duplicate of an existing issue?
6. How urgently should the issue be prioritized?

### Input

The system receives:

```text
- Image
- Text description
- Geographic coordinates
- Timestamp
```

### Output

The system produces structured information:

```text
- Category
- Issue type
- Severity
- Confidence
- Department
- Duplicate status
- Duplicate issue ID, if applicable
- Priority score
```

---

# 3. Issue Taxonomy

To keep the MVP focused and achievable within the development timeline, the initial system will support five major civic issue categories.

## 3.1 Road

```text
road
├── pothole
└── damaged_road
```

### Examples

* Large pothole
* Cracked/damaged road
* Broken road surface

---

## 3.2 Waste Management

```text
waste_management
├── garbage_overflow
└── illegal_dumping
```

### Examples

* Overflowing public garbage bin
* Garbage accumulated on roadside
* Waste dumped in an unauthorized location

---

## 3.3 Electricity

```text
electricity
└── broken_streetlight
```

### Examples

* Streetlight not functioning
* Damaged streetlight infrastructure

---

## 3.4 Water

```text
water
└── water_leakage
```

### Examples

* Pipeline leakage
* Water flowing from damaged infrastructure
* Persistent water leakage in a public area

---

## 3.5 Drainage

```text
drainage
├── blocked_drain
└── open_drain
```

### Examples

* Blocked drainage
* Open/uncovered drain
* Drainage overflow

---

# 4. Severity Definitions

Severity describes **how serious the civic issue itself is**.

Severity will initially have four levels.

## LOW

A minor issue with limited immediate impact on public safety or infrastructure.

**Example:**

Small garbage accumulation in a low-traffic residential area.

---

## MEDIUM

An issue that noticeably affects public convenience or normal use of infrastructure but does not represent an immediate major danger.

**Example:**

Moderate garbage accumulation near a public area.

---

## HIGH

An issue that presents a significant safety, accessibility, infrastructure, or public-use concern.

**Example:**

A large pothole on a frequently used road.

---

## CRITICAL

An issue that presents an immediate or potentially severe safety risk or affects a highly sensitive public location.

**Example:**

A large open drain directly beside a school entrance.

---

### Important distinction

**Severity ≠ Priority**

Severity describes:

> **How bad is the issue?**

Priority describes:

> **How urgently should authorities act?**

Priority may consider additional factors such as the number of affected citizens, location, and time unresolved.

---

# 5. Duplicate Definition

Crowdsourced systems can receive multiple reports about the same physical civic problem.

For example:

```text
Report A:
"Huge pothole near the university gate."

Report B:
"Large pothole outside the university entrance."

Report C:
"Road damaged near the university gate."
```

These may represent the same underlying issue.

The system therefore needs to identify **potential duplicate reports** rather than treating every submission as a new civic issue.

## Duplicate Criteria

Two reports will be considered potential duplicates when:

1. They belong to the same or closely related issue category.
2. Their geographic locations are sufficiently close.
3. Their textual descriptions are semantically similar.
4. Where available, their images provide similar visual evidence.

Conceptually:

```text
Duplicate Score =
Semantic Similarity
+
Geographical Proximity
+
Category Similarity
+
Visual Similarity
```

The MVP will initially prioritize:

```text
Category
+
Geographical Distance
+
Text Embedding Similarity
```

Visual similarity can be added if time permits.

---

# 6. Priority Definition

Priority represents the **urgency with which an authority should address an issue**.

Unlike severity, priority depends on multiple contextual factors.

The initial priority model will consider:

```text
- Issue severity
- Number of supporting/duplicate reports
- Location importance
- Time unresolved
```

A normalized priority score can be calculated as:

```text
Priority Score =
0.35 × Severity
+ 0.25 × Public Impact
+ 0.20 × Location Risk
+ 0.20 × Time Unresolved
```

All components will be normalized between `0` and `1`.

### Priority levels

```text
0.00 – 0.30 → LOW
0.30 – 0.60 → MEDIUM
0.60 – 0.80 → HIGH
0.80 – 1.00 → CRITICAL
```

These weights and thresholds are initial MVP values and should be evaluated and adjusted using test cases.

---

# 7. AI vs Rule-Based Components

Not every part of the system requires AI.

The system will deliberately combine **machine learning/AI with deterministic rules**.

## AI Components

### Issue Classification

Determine:

```text
What civic issue is present?
```

Input:

```text
Image + Description
```

Output:

```text
Category + Issue Type + Confidence
```

---

### Severity Estimation

Estimate:

```text
How serious is the issue?
```

Input:

```text
Image + Description + Context
```

Output:

```text
LOW / MEDIUM / HIGH / CRITICAL
```

---

### Semantic Similarity

Generate embeddings for reports and determine whether two reports describe similar issues.

Input:

```text
Report A
Report B
```

Output:

```text
Similarity Score
```

---

### Duplicate Detection

Combine semantic similarity with geographic and category information to determine whether a new report may correspond to an existing issue.

---

## Rule-Based Components

### Department Routing

Department assignment will initially use deterministic mappings.

```text
pothole
    ↓
Roads & Transport

garbage_overflow
    ↓
Waste Management

broken_streetlight
    ↓
Electricity

water_leakage
    ↓
Water Supply

blocked_drain
    ↓
Drainage
```

This avoids unnecessary AI usage where a deterministic rule is more reliable.

---

### Priority Calculation

The initial priority score will use an explicit weighted formula rather than an opaque ML model.

This makes the system:

* Explainable
* Easy to debug
* Easy to tune
* Easy for authorities to understand

---

# 8. AI Output Schema

The complete AI pipeline should eventually return a structured object similar to:

```json
{
  "category": "road",
  "issue_type": "pothole",
  "severity": "high",
  "confidence": 0.94,
  "department": "roads_transport",
  "is_duplicate": false,
  "duplicate_of": null,
  "duplicate_similarity": 0.21,
  "priority_score": 0.82,
  "priority_level": "critical"
}
```

If a duplicate is detected:

```json
{
  "category": "road",
  "issue_type": "pothole",
  "severity": "high",
  "confidence": 0.93,
  "department": "roads_transport",
  "is_duplicate": true,
  "duplicate_of": "ISSUE-104",
  "duplicate_similarity": 0.91,
  "priority_score": 0.78,
  "priority_level": "high"
}
```

---

# 9. Overall AI Pipeline

The complete intelligence pipeline is:

```text
                  CITIZEN REPORT
                       │
             ┌─────────┼─────────┐
             │         │         │
          Image    Description  Location
             │         │         │
             └─────────┼─────────┘
                       ▼
              ┌─────────────────┐
              │ Issue Analysis  │
              └────────┬────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        Classification      Severity
              │                 │
              └────────┬────────┘
                       ▼
                 Embedding
                       │
                       ▼
              Duplicate Detection
                       │
                       ▼
                Priority Engine
                       │
                       ▼
              Department Routing
                       │
                       ▼
             STRUCTURED ISSUE
                       │
                       ▼
             CIVIC AUTHORITY
```

---

# 10. MVP AI Scope

Given the **10-day development constraint**, the minimum viable AI system will focus on:

### Must Have

* [ ] Issue classification
* [ ] Severity estimation
* [ ] Text embeddings
* [ ] Duplicate detection
* [ ] Department routing
* [ ] Priority scoring
* [ ] Structured AI output

### If Time Permits

* [ ] Visual similarity for duplicate detection
* [ ] Multilingual descriptions
* [ ] OCR from uploaded images
* [ ] Automatic issue summarization
* [ ] Predictive identification of recurring civic problems

---

# 11. Success Criteria

The AI system should not only work in a demo; it should be evaluated quantitatively.

### Classification

Measure:

* Accuracy
* Precision
* Recall
* F1-score

### Severity

Measure:

* Accuracy
* F1-score
* Agreement with manually assigned severity

### Duplicate Detection

Measure:

* Precision
* Recall
* F1-score

Special attention should be given to **false positives**, because incorrectly merging two different civic issues could hide a genuine problem.

### Priority

Evaluate whether the generated priority ordering agrees with manually defined/expert rankings.

### End-to-End

Measure:

> **Percentage of reports correctly transformed into actionable department-ready civic issues.**

---

# 12. Core AI Philosophy

The system follows one central principle:

> **Convert noisy crowdsourced observations into structured, explainable, and actionable civic intelligence.**

The AI should therefore not replace civic authorities.

Instead:

```text
Citizen
   ↓
Observation
   ↓
AI
   ↓
Understanding
   ↓
Prioritization
   ↓
Authority
   ↓
Action
   ↓
Citizen
   ↓
Verification
```

The AI acts as an **intelligence and decision-support layer**, while final civic decisions remain under human/authority control.
