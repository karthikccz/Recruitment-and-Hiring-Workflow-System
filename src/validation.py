
import pandas as pd


def validate_datasets(datasets):
    issues = []

    def add_issue(table, record_id, issue_type, details):
        issues.append({
            "table": table,
            "record_id": record_id,
            "issue_type": issue_type,
            "details": details
        })

    # Primary-key checks
    primary_keys = {
        "HiringManager": "hiring_manager_id",
        "Requisition": "requisition_id",
        "Candidate": "candidate_id",
        "Application": "application_id",
        "SkillRequirement": "skill_requirement_id",
        "InterviewPanel": "panel_id",
        "Availability": "availability_id",
        "Interview": "interview_id",
        "Scorecard": "scorecard_id"
    }

    for table, key in primary_keys.items():
        df = datasets.get(table)

        if df is None or df.empty or key not in df.columns:
            continue

        duplicates = df[df[key].duplicated(keep=False)]

        for value in duplicates[key].dropna().unique():
            add_issue(table, value, "duplicate_primary_key",
                      f"Duplicate value in {key}")

    # Foreign-key checks
    relationships = [
        ("Requisition", "hiring_manager_id",
         "HiringManager", "hiring_manager_id"),
        ("Application", "candidate_id",
         "Candidate", "candidate_id"),
        ("Application", "requisition_id",
         "Requisition", "requisition_id"),
        ("SkillRequirement", "requisition_id",
         "Requisition", "requisition_id"),
        ("InterviewPanel", "requisition_id",
         "Requisition", "requisition_id"),
        ("PanelMember", "panel_id",
         "InterviewPanel", "panel_id"),
        ("PanelMember", "interviewer_id",
         "HiringManager", "hiring_manager_id"),
        ("Availability", "interviewer_id",
         "HiringManager", "hiring_manager_id"),
        ("Interview", "application_id",
         "Application", "application_id"),
        ("Interview", "panel_id",
         "InterviewPanel", "panel_id"),
        ("Scorecard", "interview_id",
         "Interview", "interview_id"),
        ("Scorecard", "reviewer_id",
         "HiringManager", "hiring_manager_id")
    ]

    for child, child_key, parent, parent_key in relationships:
        child_df = datasets.get(child)
        parent_df = datasets.get(parent)

        if child_df is None or parent_df is None:
            continue

        if child_key not in child_df.columns or parent_key not in parent_df.columns:
            continue

        valid_ids = set(parent_df[parent_key].dropna())

        for _, row in child_df.iterrows():
            value = row[child_key]

            if pd.notna(value) and value not in valid_ids:
                add_issue(
                    child,
                    value,
                    "foreign_key_violation",
                    f"{child_key} does not exist in {parent}"
                )

    # Application date checks
    applications = datasets.get("Application")

    if applications is not None:
        for _, row in applications.iterrows():
            if (
                pd.notna(row.get("withdrawn_at"))
                and pd.to_datetime(row["withdrawn_at"])
                < pd.to_datetime(row["applied_at"])
            ):
                add_issue(
                    "Application",
                    row["application_id"],
                    "invalid_date",
                    "Withdrawal is before application date"
                )

    # Interview time checks
    interviews = datasets.get("Interview")

    if interviews is not None:
        for _, row in interviews.iterrows():
            start = pd.to_datetime(
                f"{row['interview_date']} {row['start_time']}"
            )
            end = pd.to_datetime(
                f"{row['interview_date']} {row['end_time']}"
            )

            if end <= start:
                add_issue(
                    "Interview",
                    row["interview_id"],
                    "invalid_interview_time",
                    "Interview end must be after start"
                )

    # Scorecard score checks
    scorecards = datasets.get("Scorecard")

    if scorecards is not None:
        import json

        for _, row in scorecards.iterrows():
            try:
                details = json.loads(row["criterion_scores_json"])

                for criterion in details.get("criteria", []):
                    score = criterion.get("score")

                    if not isinstance(score, (int, float)) or not 1 <= score <= 10:
                        add_issue(
                            "Scorecard",
                            row["scorecard_id"],
                            "invalid_score",
                            "Criterion score must be between 1 and 10"
                        )
            except (ValueError, TypeError, AttributeError):
                add_issue(
                    "Scorecard",
                    row["scorecard_id"],
                    "invalid_scorecard_json",
                    "Could not read criterion score data"
                )

    return pd.DataFrame(
        issues,
        columns=["table", "record_id", "issue_type", "details"]
    )
