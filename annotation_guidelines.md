# Civic Issue Annotation Guidelines

## 1. Purpose

This document defines the annotation rules for the Civic Issue Intelligence Engine dataset.

The purpose of these guidelines is to ensure that all reports are labelled **consistently and objectively**, allowing the AI system to be trained and evaluated against reliable ground-truth labels.

Each civic report must be assigned:

* `category`
* `issue_type`
* `severity`

---

# 2. General Annotation Principles

### Rule 1 — Label the underlying issue

Annotate what the report is actually describing, not merely the words used by the citizen.

**Example:**

> "There's a huge hole in the road."

```text
category: road
issue_type: pothole
```

---

### Rule 2 — Do not infer unsupported information

Only use information reasonably supported by the image, description, and available context.

Do not assume:

* exact cause of the issue
* number of people affected
* ownership of infrastructure
* duration of the issue

unless the report provides sufficient evidence.

---

### Rule 3 — Use the predefined taxonomy

Only use the categories and issue types defined in this document.

Do not create new labels for individual examples.

---

# 3. Category Taxonomy

## 3.1 Road

Use `road` when the primary problem concerns the physical condition of a road.

### Issue types

```text
pothole
damaged_road
```

### `pothole`

Use when the report describes a localized hole/depression in the road surface.

Examples:

> "Large pothole near the intersection."

> "Deep hole in the road causing vehicles to slow down."

### `damaged_road`

Use when the road is broadly damaged, cracked, broken, uneven, or deteriorated without the problem being primarily a pothole.

Examples:

> "Road surface has multiple cracks."

> "The entire stretch is badly damaged."

---

# 4. Waste Management

Use `waste_management` when the primary problem involves accumulated or improperly disposed waste.

### Issue types

```text
garbage_overflow
illegal_dumping
```

### `garbage_overflow`

Use when waste is overflowing from a designated garbage bin/container or waste collection point.

Examples:

> "The garbage bin is overflowing."

> "Trash is spilling out of the waste container."

### `illegal_dumping`

Use when waste has been intentionally or improperly deposited in an unauthorized location.

Examples:

> "People are dumping garbage beside the road."

> "Large piles of waste have been dumped in an open area."

---

# 5. Electricity

Use `electricity` when the problem concerns public electrical infrastructure supported by the current taxonomy.

### Issue type

```text
broken_streetlight
```

### `broken_streetlight`

Use when a public streetlight is damaged, non-functional, or providing inadequate illumination because of a malfunction.

Examples:

> "Streetlight has not been working."

> "This road is completely dark because the streetlight is broken."

Do not classify general power outages as `broken_streetlight` unless the issue specifically concerns a streetlight.

---

# 6. Water

Use `water` when the primary problem involves public water infrastructure or water leakage.

### Issue type

```text
water_leakage
```

### `water_leakage`

Use when water is escaping from a damaged pipe or other water infrastructure.

Examples:

> "Water is leaking from a roadside pipe."

> "A broken pipeline is causing water to flow onto the road."

Do not use this category for flooding caused exclusively by rain unless the problem clearly involves a water infrastructure failure.

---

# 7. Drainage

Use `drainage` when the problem concerns drains or drainage infrastructure.

### Issue types

```text
blocked_drain
open_drain
```

### `blocked_drain`

Use when a drain is clogged, obstructed, or unable to carry water properly.

Examples:

> "Drain is blocked with garbage."

> "Water is stagnant because the drain is clogged."

### `open_drain`

Use when a drain is uncovered or exposed and the primary problem is the physical absence of a protective covering.

Examples:

> "Open drain beside the road is dangerous for pedestrians."

> "The drain has no cover."

---

# 8. Severity Annotation

Severity represents:

> **How serious is the civic issue itself?**

Severity must be assigned independently from the number of reports or how long the issue has existed.

Use exactly four levels:

```text
low
medium
high
critical
```

---

## 8.1 LOW

Assign `low` when:

* the issue causes minor inconvenience;
* there is limited immediate safety risk;
* public infrastructure remains mostly usable;
* the impact is localized and relatively minor.

### Examples

* Small amount of garbage accumulation
* Minor road surface deterioration
* Streetlight issue on a low-risk location with alternative lighting

---

## 8.2 MEDIUM

Assign `medium` when:

* the issue noticeably affects public convenience;
* infrastructure usability is reduced;
* there is some safety or environmental concern;
* immediate severe danger is not evident.

### Examples

* Moderate garbage overflow
* Moderately damaged road surface
* Streetlight not functioning on a normal road
* Moderate water leakage

---

## 8.3 HIGH

Assign `high` when:

* the issue creates a significant safety risk;
* infrastructure is substantially impaired;
* the problem can cause accidents or significant public disruption;
* the issue affects an important public route or facility.

### Examples

* Deep pothole on a frequently used road
* Major road damage affecting traffic
* Significant water leakage creating hazardous road conditions
* Large blocked drain causing substantial stagnant water
* Open drain beside a pedestrian route

---

## 8.4 CRITICAL

Assign `critical` only when there is an **immediate or potentially severe threat** to public safety or major infrastructure.

Examples:

* Large uncovered drain immediately beside a school entrance
* Major road collapse creating an immediate accident risk
* Severe infrastructure failure creating an immediate danger to pedestrians or vehicles

`critical` should be relatively rare.

---

# 9. Severity Decision Hierarchy

When uncertain between two severity levels, evaluate the issue in this order:

```text
1. Immediate safety risk?
       ↓
   CRITICAL / HIGH

2. Significant safety or infrastructure impact?
       ↓
   HIGH

3. Noticeable public inconvenience or moderate impact?
       ↓
   MEDIUM

4. Minor inconvenience with limited impact?
       ↓
   LOW
```

Do not assign `critical` simply because an issue is unpleasant or inconvenient.

---

# 10. Category vs Severity

Category and severity must be annotated independently.

For example:

```text
category   = road
issue_type = pothole
severity   = high
```

The category describes **what the problem is**.

The severity describes **how serious it is**.

---

# 11. Ambiguous Reports

When a report could belong to multiple categories, identify the **primary underlying civic issue**.

### Example

> "Garbage has blocked the drain and water is collecting on the road."

Primary issue:

```text
category: drainage
issue_type: blocked_drain
```

because the described civic problem is a blocked drainage system.

---

# 12. Duplicate Reports

Duplicate status is **not part of the manual category/severity annotation** at this stage.

Duplicate detection will be handled separately using:

```text
semantic similarity
+
geographical proximity
+
category similarity
```

Two reports at the same location are **not automatically duplicates**.

For example:

```text
Report A → pothole
Report B → open drain
```

Even if their coordinates are identical, they represent different civic issues.

---

# 13. Ground-Truth Priority

Priority is calculated separately from the manually assigned severity.

The initial system will consider:

```text
severity
+
public impact
+
location risk
+
time unresolved
```

Therefore, annotators should **not change severity simply to make an issue appear more urgent**.

---

# 14. Data Quality Rules

Before adding a report to the dataset, verify:

* [ ] `id` is unique.
* [ ] Image filename is correct.
* [ ] Description represents realistic citizen language.
* [ ] `category` belongs to the approved taxonomy.
* [ ] `issue_type` belongs to the selected category.
* [ ] `severity` is one of `low`, `medium`, `high`, or `critical`.
* [ ] Latitude is valid.
* [ ] Longitude is valid.
* [ ] Annotation is supported by the available evidence.

---

# 15. Approved Label Set

The complete label vocabulary for the current MVP is:

```text
CATEGORY
────────
road
waste_management
electricity
water
drainage
```

```text
ISSUE TYPE
──────────
pothole
damaged_road

garbage_overflow
illegal_dumping

broken_streetlight

water_leakage

blocked_drain
open_drain
```

```text
SEVERITY
────────
low
medium
high
critical
```

No additional labels should be introduced without updating this document.

---

# 16. Annotation Philosophy

The dataset should represent how **real citizens describe real-world problems**, while the labels should remain structured and consistent.

The goal is:

```text
Noisy Citizen Report
        ↓
Consistent Annotation
        ↓
Reliable Ground Truth
        ↓
AI Prediction
        ↓
Evaluation
```

A high-quality dataset is more valuable than a large dataset with inconsistent labels.
