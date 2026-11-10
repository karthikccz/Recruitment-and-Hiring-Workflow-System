# Recruitment and Hiring Workflow System

## Project Overview

This project simulates an end-to-end recruitment workflow using synthetic data. It covers requisitions, candidates, applications, interviewer availability, interview scheduling, scorecards, application outcomes, and data validation.

The objective is to generate realistic, traceable recruitment data while enforcing business rules and identifying data-quality issues.

## Technology Stack

- Python
- Pandas
- NumPy
- SQLite schema definition
- CSV and JSON
- Pytest

## Project Structure

```text
recruitment-hiring-system/
├── data/                 # Generated CSV and JSON files
├── src/
│   ├── config.py
│   ├── generator.py
│   ├── business_rules.py
│   ├── validation.py
│   ├── manifest.py
│   ├── pipeline.py
│   └── schema.py
├── tests/
├── docs/
│   └── data_dictionary.md
├── output/
└── requirements.txt
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Pipeline

Run the smaller starter dataset:

```bash
python -m src.pipeline --mode starter
```

Run the full dataset:

```bash
python -m src.pipeline --mode full
```

## Run Tests

```bash
python -m pytest -v 
```

## Workflow

1. Generate master data such as hiring managers, requisitions, candidates, and skill requirements.
2. Generate candidate applications.
3. Create interview panels and interviewer availability.
4. Schedule and reschedule interviews.
5. Record application stage transitions.
6. Generate rubric-based scorecards.
7. Validate scorecard completeness.
8. Derive application workflow outcomes from generated records.
9. Validate data and create final exports and a source manifest.

## Key Business Rules

- Applications reference existing candidates and requisitions.
- Interviews are scheduled using interviewer availability.
- Interviewers should not have overlapping scheduled interviews.
- Scorecards evaluate requisition-specific skills.
- Incomplete scorecards remain in Draft status.
- Application outcomes are derived from workflow records.
- Data validation reports detected issues rather than silently deleting records.

## Generated Outputs

The `data/` directory contains generated datasets, including:

- HiringManager.csv
- Requisition.csv
- Candidate.csv
- SkillRequirement.csv
- Application.csv
- InterviewPanel.csv
- PanelMember.csv
- Availability.csv
- Interview.csv
- Scorecard.csv
- ApplicationOutcome.csv
- StateHistory.csv
- scorecard_completeness.csv
- validation_issues.csv
- validation_summary.json
- SourceManifest.json

The exact output files depend on the workflow steps implemented and executed.

## Source Manifest

`SourceManifest.json` records the SHA-256 hash, file size, and row count for each exported CSV file. It helps verify the integrity of generated data files.

## Reproducibility

The project uses a fixed random seed configured in `src/config.py`. Running the same pipeline configuration with the same seed should generate reproducible data.

## Important Note

This is a synthetic recruitment workflow simulation. Generated candidates, interviews, scores, and outcomes are test data and do not represent real hiring decisions.
