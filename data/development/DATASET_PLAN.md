# Civic Issue AI — Dataset Plan


## 1. Purpose


This document defines the composition, distribution, and expansion strategy for the Civic Issue Intelligence Engine dataset.


The goal is to create a small but diverse and reliable dataset suitable for:


- Issue classification
- Severity estimation
- Semantic similarity
- Duplicate detection
- End-to-end AI evaluation


The dataset is designed for a 10-day MVP and prioritizes **data quality and diversity over dataset size**.


---


# 2. Dataset Structure


The project will maintain two primary datasets:


```text
data/
├── development/
│   ├── images/
│   └── reports.csv
│
└── evaluation/
    ├── images/
    └── reports.csv
Development Dataset

Used during:

experimentation
model development
prompt/model selection
embedding selection
threshold tuning
Evaluation Dataset

Used only for final evaluation.

The evaluation dataset must not be used to tune the system.

3. Current Dataset

The current development dataset contains:

Total reports: 16
Total images: 16

Distribution by category:

Category	Current Count
Road	4
Waste Management	4
Electricity	2
Water	2
Drainage	4
Total	16
4. Civic Issue Taxonomy

The MVP supports five categories and eight issue types.

Categories
road
waste_management
electricity
water
drainage
Issue Types
pothole
damaged_road
garbage_overflow
illegal_dumping
broken_streetlight
water_leakage
blocked_drain
open_drain
5. Target Dataset Size

For the 10-day MVP, the target development dataset is approximately:

50–60 reports

The dataset does not need to reach an exact number.

A smaller high-quality dataset is preferable to a larger dataset containing:

duplicate images
incorrect labels
unrealistic descriptions
poor-quality photographs
inconsistent severity annotations
6. Target Distribution by Issue Type

The target distribution is approximately:

Issue Type	Target Examples
Pothole	7–8
Damaged Road	7–8
Garbage Overflow	7–8
Illegal Dumping	7–8
Broken Streetlight	6–7
Water Leakage	6–7
Blocked Drain	7–8
Open Drain	7–8
Total	~55–60

The distribution does not need to be perfectly equal.

7. Severity Distribution

The dataset should contain examples across all four severity levels.

Target distribution:

Severity	Approximate Target
Low	10–15
Medium	15
High	20
Critical	5
Total	~50–55

These are targets rather than strict quotas.

Severity must always follow the rules in:

data/annotation_guidelines.md

An issue must never be labelled critical merely to balance the dataset.

8. Issue Type × Severity Coverage

We should avoid having an issue type represented by only one severity level.

The target is to provide multiple severity levels for each issue type.

Example:

Issue Type	Low	Medium	High	Critical
Pothole	✓	✓	✓	Optional
Damaged Road	✓	✓	✓	✓
Garbage Overflow	✓	✓	✓	Optional
Illegal Dumping	✓	✓	✓	Optional
Broken Streetlight	✓	✓	✓	Optional
Water Leakage	✓	✓	✓	Optional
Blocked Drain	✓	✓	✓	Optional
Open Drain	✓	✓	✓	✓

Not every issue type must contain every severity level.

The important requirement is that the dataset contains enough variation to prevent the AI from associating an issue type with a single severity.

9. Image Diversity

Images should represent different real-world conditions.

The dataset should include variation in:

camera angle
distance from the issue
lighting
weather
road/environment type
background
image quality
issue size
issue visibility

Avoid collecting many nearly identical images.

Example

Avoid:

10 photographs of the same pothole

Prefer:

small pothole
large pothole
pothole photographed from close range
pothole photographed from a vehicle
pothole on a residential road
pothole on a major road
10. Description Diversity

Citizen descriptions should not all use the same vocabulary.

Descriptions should include:

Direct descriptions

"There is a large pothole on the road."

Informal descriptions

"Huge hole in the road near the market."

Short descriptions

"Road badly damaged."

Detailed descriptions

"A deep pothole near the intersection is making it difficult for vehicles to pass."

Contextual descriptions

"The road outside the school has a large hole that could be dangerous for vehicles."

The goal is to represent realistic crowdsourced reports.

11. Geographic Diversity

Reports should not all come from exactly the same coordinates.

The dataset should contain:

different locations
different road environments
different neighborhoods
different infrastructure contexts

However, some reports should intentionally be geographically close.

These will later help evaluate duplicate detection.

Example:

Report A
Pothole
26.1442, 91.6586


Report B
Large road hole
26.1444, 91.6588

These may represent the same underlying issue.

12. Duplicate Detection Dataset

Duplicate detection requires a different evaluation structure from ordinary classification.

We will create report pairs.

Example:

Report A	Report B	Expected
Large pothole near school	Deep pothole outside school	Duplicate
Garbage near market	Waste beside market	Duplicate
Pothole on Road A	Broken streetlight on Road A	Not Duplicate
Blocked drain near park	Open drain near park	Not Duplicate

The initial target is:

50–100 report pairs

with approximately:

50% duplicate
50% non-duplicate
13. Duplicate Pair Diversity

Duplicate pairs should include:

High similarity
"Large pothole near the school"
"Deep pothole outside the school"
Moderate similarity
"Road has a dangerous hole"
"Vehicles are struggling because of road damage"
Same location but different issue
Pothole
+
Open drain

These should be labelled:

Not Duplicate
Similar issue but different location
Pothole at Location A
+
Pothole at Location B

These should normally be:

Not Duplicate

This is important for preventing the model from treating all similar civic problems as duplicates.

14. Evaluation Dataset

After development data collection is complete, a separate evaluation dataset will be created.

Target:

10–20% of the total dataset

For example:

Development → 50 reports
Evaluation  → 10 reports

The evaluation data should contain examples from all major issue types where possible.

15. Evaluation Data Isolation

Evaluation data must not be used for:

model training
prompt tuning
threshold tuning
selecting embedding models
adjusting severity rules

It should only be used for final evaluation.

The purpose is to measure performance on previously unseen reports.

16. Data Quality Requirements

Every report must satisfy:

Unique report ID
Valid image filename
Existing image file
Realistic description
Valid category
Valid issue type
Valid severity
Valid latitude
Valid longitude

The validation script:

tests/validate_dataset.py

should be run whenever the dataset is modified.

17. Data Sources

For every externally sourced image, record its source and licensing information.

A future source-tracking file should contain:

image
source
license
url

Personal photographs may be marked as:

source: original

AI-generated images should not be used as the primary source for the real-world image classification dataset.

18. Dataset Expansion Strategy

The dataset will be expanded in stages.

Stage 1 — Initial Dataset
16 reports

Current status:

✓ Complete
Stage 2 — Balanced Development Dataset

Expand to approximately:

35–40 reports

Focus on:

missing severity levels
issue-type diversity
description diversity
image diversity
Stage 3 — Final Development Dataset

Expand to approximately:

50–60 reports

Focus on:

difficult examples
ambiguous cases
realistic citizen language
duplicate scenarios
Stage 4 — Evaluation Dataset

Create:

10–20 previously unseen reports

Keep them isolated from development.

19. Priority of Data Collection

When deciding what example to collect next, use this priority:

1. Missing issue type
        ↓
2. Missing severity level
        ↓
3. Missing image diversity
        ↓
4. Missing language/description diversity
        ↓
5. Duplicate-detection scenarios

Do not simply collect more examples of categories that are already well represented.

20. MVP Dataset Goal

The final MVP dataset should provide enough variation to demonstrate that the system can:

Citizen Report
      ↓
Issue Classification
      ↓
Severity Estimation
      ↓
Semantic Representation
      ↓
Duplicate Detection
      ↓
Priority Calculation
      ↓
Department Routing

The objective is not to create a production-scale dataset within 10 days.

The objective is to create a small, clean, diverse, reproducible dataset capable of demonstrating and evaluating the AI pipeline.



### One important correction to our earlier plan


We're **not going to train a large custom computer-vision model from 50–60 images**. That would be a poor approach for a 10-day MVP.


Instead, once the dataset is ready, we'll likely use **pretrained vision/language models + embeddings + lightweight classification/rules**, and use your dataset primarily for **evaluation and calibration**.


That will give you a much more credible AI system within the deadline.


**Next:** we'll take your current 16 records and build the **exact expansion matrix**—i.e., *which 34–44 additional examples we need and why*.