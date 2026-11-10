
import argparse

from src.generator import (
    generate_master_data,
    generate_applications
)

from src.business_rules import (
    generate_interview_panels,
    generate_availability,
    schedule_interviews,
    reschedule_interviews,
    apply_interview_stage_transitions,
    generate_interview_history,
    generate_scorecards,
    validate_scorecard_completeness,
    generate_scorecard_history,
    derive_application_outcomes,
    generate_offers_and_approvals,
    generate_phase7_anomalies
)

from src.validation import validate_datasets
from src.manifest import generate_source_manifest
import json

from src.config import (
    FULL_CONFIG,
    STARTER_CONFIG,
    DATA_DIR
)


def main():

    parser = argparse.ArgumentParser(
        description="Recruitment Workflow Pipeline"
    )

    parser.add_argument(
        "--mode",
        choices=["starter", "full"],
        default="full"
    )

    args = parser.parse_args()

    config = (
        FULL_CONFIG
        if args.mode == "full"
        else STARTER_CONFIG
    )

    # --------------------------------------------------
    # STEP 1: MASTER DATA GENERATION
    # --------------------------------------------------

    print("\nSTEP 1: MASTER DATA")

    datasets = generate_master_data(args.mode)

    # --------------------------------------------------
    # STEP 2: APPLICATION GENERATION
    # --------------------------------------------------

    print("\nSTEP 2: APPLICATION GENERATION")

    applications = generate_applications(
        datasets["Candidate"],
        datasets["Requisition"],
        config["applications"]
    )

    # --------------------------------------------------
    # STEP 3: INTERVIEW PANELS
    # --------------------------------------------------

    print("\nSTEP 3: INTERVIEW PANELS")

    panels, panel_members = generate_interview_panels(
        datasets["Requisition"],
        datasets["HiringManager"]
    )

    # --------------------------------------------------
    # STEP 4: INTERVIEWER AVAILABILITY
    # --------------------------------------------------

    print("\nSTEP 4: INTERVIEWER AVAILABILITY")

    availability = generate_availability(
        datasets["HiringManager"]
    )

    # --------------------------------------------------
    # STEP 5: INITIAL INTERVIEW SCHEDULING
    # --------------------------------------------------

    print("\nSTEP 5: INITIAL INTERVIEW SCHEDULING")

    reschedule_count = min(
        40,
        max(1, round(config["interviews"] * 0.02))
    )

    initial_count = (
        config["interviews"] - reschedule_count
    )

    interviews = schedule_interviews(
        applications=applications,
        requisitions=datasets["Requisition"],
        panels=panels,
        panel_members=panel_members,
        availability=availability,
        target_count=initial_count
    )

    # --------------------------------------------------
    # STEP 6: RESCHEDULING
    # --------------------------------------------------

    print("\nSTEP 6: RESCHEDULING")

    interviews = reschedule_interviews(
        interviews=interviews,
        panel_members=panel_members,
        availability=availability,
        count=reschedule_count
    )

    # --------------------------------------------------
    # STEP 7: APPLICATION STAGE TRANSITIONS
    # --------------------------------------------------

    print("\nSTEP 7: APPLICATION STAGE TRANSITIONS")

    applications, state_history = (
        apply_interview_stage_transitions(
            applications,
            interviews
        )
    )

    state_history = generate_interview_history(
        interviews,
        state_history
    )

    # --------------------------------------------------
    # STEP 8: STRUCTURED SCORECARD GENERATION
    # --------------------------------------------------

    print("\nSTEP 8: STRUCTURED SCORECARD GENERATION")

    scorecards = generate_scorecards(
        interviews=interviews,
        applications=applications,
        requisitions=datasets["Requisition"],
        panels=panels,
        panel_members=panel_members,
        skill_requirements=datasets["SkillRequirement"]
    )

    # --------------------------------------------------
    # STEP 9: SCORECARD VALIDATION
    # --------------------------------------------------

    print("\nSTEP 9: SCORECARD VALIDATION")

    scorecard_completeness = (
        validate_scorecard_completeness(
            interviews=interviews,
            panel_members=panel_members,
            scorecards=scorecards
        )
    )

    # --------------------------------------------------
    # STEP 10: SCORECARD HISTORY
    # --------------------------------------------------

    print("\nSTEP 10: SCORECARD HISTORY")

    state_history = generate_scorecard_history(
        scorecards,
        state_history
    )

    # --------------------------------------------------
    # STEP 11: OFFERS AND APPROVALS
    # --------------------------------------------------

    print("\nSTEP 11: OFFERS AND APPROVALS")

    offers, approvals = generate_offers_and_approvals(
        applications=applications,
        interviews=interviews,
        requisitions=datasets["Requisition"],
        scorecard_completeness=scorecard_completeness
    )

    datasets["Offer"] = offers
    datasets["Approval"] = approvals

    # --------------------------------------------------
    # STEP 12: LABELLED EXCEPTION SCENARIOS
    # --------------------------------------------------

    print("\nSTEP 12: LABELLED EXCEPTION SCENARIOS")

    anomalies, ground_truth = generate_phase7_anomalies(
        applications=applications,
        requisitions=datasets["Requisition"],
        interviews=interviews,
        panel_members=panel_members,
        scorecards=scorecards,
        scorecard_completeness=scorecard_completeness,
        offers=offers
    )

    datasets["Anomalies"] = anomalies

    anomalies.to_csv(
        DATA_DIR / "anomalies.csv",
        index=False
    )

    ground_truth.to_csv(
        DATA_DIR / "ground_truth.csv",
        index=False
    )

    # --------------------------------------------------
    # STEP 13: DERIVE APPLICATION OUTCOMES
    # --------------------------------------------------

    print("\nSTEP 13: DERIVING APPLICATION OUTCOMES")

    application_outcomes = derive_application_outcomes(
        applications=applications,
        interviews=interviews,
        scorecards=scorecards,
        scorecard_completeness=scorecard_completeness
    )

    datasets["ApplicationOutcome"] = application_outcomes

    print("\nAPPLICATION OUTCOME SUMMARY")

    print(
        application_outcomes["outcome_label"].value_counts()
    )

    # Export derived application outcomes.
    application_outcomes.to_csv(
        DATA_DIR / "ApplicationOutcome.csv",
        index=False
    )

    # --------------------------------------------------
    # ADD GENERATED DATASETS
    # --------------------------------------------------

    datasets["Application"] = applications
    datasets["InterviewPanel"] = panels
    datasets["PanelMember"] = panel_members
    datasets["Availability"] = availability
    datasets["Interview"] = interviews
    datasets["Scorecard"] = scorecards

    # --------------------------------------------------
    # STEP 14: DATA VALIDATION
    # --------------------------------------------------

    print("\nSTEP 14: DATA VALIDATION")

    validation_issues = validate_datasets(datasets)

    validation_issues.to_csv(
        DATA_DIR / "validation_issues.csv",
        index=False
    )

    print(
        "Validation issues:",
        len(validation_issues)
    )

    if validation_issues.empty:
        print("All implemented validation checks passed.")
    else:
        print(
            validation_issues["issue_type"].value_counts()
        )

    # --------------------------------------------------
    # EXPORT ALL DATASETS
    # --------------------------------------------------

    print("\nEXPORTING DATASETS")

    for name, dataframe in datasets.items():

        dataframe.to_csv(
            DATA_DIR / f"{name}.csv",
            index=False
        )

        print(f"{name}: {len(dataframe)} records")

    # Export scorecard completeness separately.
    scorecard_completeness.to_csv(
        DATA_DIR / "scorecard_completeness.csv",
        index=False
    )

    # Export complete state history.
    state_history.to_csv(
        DATA_DIR / "StateHistory.csv",
        index=False
    )

    # --------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------

    print("\nINTERVIEW STATUS")

    print(interviews["interview_status"].value_counts())

    print("\nAPPLICATION STAGES")

    print(applications["current_stage"].value_counts())

    print("\nSCORECARD STATUS")

    if not scorecards.empty:
        print(scorecards["status"].value_counts())
    else:
        print("No scorecards generated.")

    print("\nREVIEW COMPLETENESS")

    if not scorecard_completeness.empty:
        print(
            scorecard_completeness[
                "review_complete"
            ].value_counts()
        )
    else:
        print("No scheduled interviews to validate.")

    print("\nFINAL SUMMARY")

    print("TOTAL INTERVIEWS:", len(interviews))
    print("TOTAL SCORECARDS:", len(scorecards))

    if not scorecards.empty:

        print(
            "SUBMITTED:",
            (scorecards["status"] == "Submitted").sum()
        )

        print(
            "DRAFT:",
            (scorecards["status"] == "Draft").sum()
        )

    print(
        "SCORECARD COMPLETENESS:",
        len(scorecard_completeness)
    )

    print("STATE HISTORY:", len(state_history))

    print("VALIDATION ISSUES:", len(validation_issues))

    print("\nPipeline generation completed.")


    # PHASE 9: FINAL SUMMARY AND SOURCE MANIFEST

    print("\nPHASE 9: FINAL EXPORTS")

# Create a validation summary
    validation_summary = {
    "total_issues": len(validation_issues),
    "status": (
        "PASSED" if validation_issues.empty
        else "ISSUES_FOUND"
    )
}

    with open(
    DATA_DIR / "validation_summary.json",
    "w",
    encoding="utf-8"
    ) as file:
        json.dump(validation_summary, file, indent=4)

# Generate hashes for all exported CSV files
    manifest = generate_source_manifest(DATA_DIR)

    print("CSV files included in manifest:", len(manifest))
    print("Validation summary:", validation_summary)
    print("\nPHASE 9 COMPLETED")

if __name__ == "__main__":
    main()
