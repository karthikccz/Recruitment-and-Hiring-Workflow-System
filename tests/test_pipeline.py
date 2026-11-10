
import pandas as pd

from src.generator import (
    generate_master_data,
    generate_applications
)
import json
from src.business_rules import (
    generate_interview_panels,
    generate_availability,
    schedule_interviews,
    reschedule_interviews,
    apply_interview_stage_transitions,
    validate_stage_transition,
    generate_scorecards,
    validate_scorecard_completeness,
    validate_application_offer_eligibility,
    derive_application_outcomes
)

from src.config import FULL_CONFIG, STARTER_CONFIG



def test_master_data_counts():

    data = generate_master_data("full")

    assert len(data["HiringManager"]) == 40
    assert len(data["Requisition"]) == 200
    assert len(data["Candidate"]) == 5000
    assert len(data["SkillRequirement"]) == 800


def test_primary_key_uniqueness():

    data = generate_master_data("full")

    primary_keys = {
        "HiringManager": "hiring_manager_id",
        "Requisition": "requisition_id",
        "Candidate": "candidate_id",
        "SkillRequirement": "skill_requirement_id"
    }

    for table, column in primary_keys.items():

        assert data[table][column].is_unique


def test_foreign_key_integrity():

    data = generate_master_data("full")

    manager_ids = set(
        data["HiringManager"]["hiring_manager_id"]
    )

    requisition_ids = set(
        data["Requisition"]["requisition_id"]
    )

    assert set(
        data["Requisition"]["hiring_manager_id"]
    ).issubset(manager_ids)

    assert set(
        data["SkillRequirement"]["requisition_id"]
    ).issubset(requisition_ids)


def test_requisitions_are_approved():

    data = generate_master_data("full")

    assert (
        data["Requisition"]["status"] == "Approved"
    ).all()

    assert (
        data["Requisition"]["approved_at"].notna()
    ).all()


def test_seed_reproducibility():

    first = generate_master_data("full")
    second = generate_master_data("full")

    for table in first:

        assert first[table].equals(second[table])





def get_full_data():
    masters = generate_master_data("full")

    applications = generate_applications(
        masters["Candidate"],
        masters["Requisition"],
        FULL_CONFIG["applications"]
    )

    return masters, applications


def test_application_count():
    masters, applications = get_full_data()

    assert len(applications) == 8000


def test_application_id_format():
    masters, applications = get_full_data()

    for _, row in applications.iterrows():

        expected_id = (
            f"APP-{row['candidate_id']}-"
            f"{row['requisition_id']}"
        )

        assert row["application_id"] == expected_id


def test_application_foreign_keys():
    masters, applications = get_full_data()

    candidate_ids = set(
        masters["Candidate"]["candidate_id"]
    )

    requisition_ids = set(
        masters["Requisition"]["requisition_id"]
    )

    assert set(
        applications["candidate_id"]
    ).issubset(candidate_ids)

    assert set(
        applications["requisition_id"]
    ).issubset(requisition_ids)


def test_no_duplicate_applications():
    masters, applications = get_full_data()

    assert applications["application_id"].is_unique

    assert not applications.duplicated(
        ["candidate_id", "requisition_id"]
    ).any()


def test_withdrawal_consistency():
    masters, applications = get_full_data()

    withdrawn = applications[
        applications["status"] == "Withdrawn"
    ]

    active = applications[
        applications["status"] == "Active"
    ]

    assert len(withdrawn) > 0

    assert withdrawn["withdrawn_at"].notna().all()

    assert active["withdrawn_at"].isna().all()

    applied_dates = pd.to_datetime(
        withdrawn["applied_at"]
    )

    withdrawal_dates = pd.to_datetime(
        withdrawn["withdrawn_at"]
    )

    assert (withdrawal_dates > applied_dates).all()


def test_only_approved_requisitions_receive_applications():
    masters, applications = get_full_data()

    approved_ids = set(
        masters["Requisition"].loc[
            masters["Requisition"]["status"] == "Approved",
            "requisition_id"
        ]
    )

    assert set(
        applications["requisition_id"]
    ).issubset(approved_ids)


def test_application_reproducibility():
    masters = generate_master_data("full")

    first = generate_applications(
        masters["Candidate"],
        masters["Requisition"],
        8000
    )

    second = generate_applications(
        masters["Candidate"],
        masters["Requisition"],
        8000
    )

    assert first.equals(second)





def generate_phase4_data(mode="full"):

    from src.generator import (
        generate_master_data,
        generate_applications
    )

    from src.config import FULL_CONFIG, STARTER_CONFIG

    config = (
        FULL_CONFIG if mode == "full"
        else STARTER_CONFIG
    )

    masters = generate_master_data(mode)

    applications = generate_applications(
        masters["Candidate"],
        masters["Requisition"],
        config["applications"]
    )

    panels, members = generate_interview_panels(
        masters["Requisition"],
        masters["HiringManager"]
    )

    availability = generate_availability(
        masters["HiringManager"]
    )

    return masters, applications, panels, members, availability


def test_panel_relationships():

    masters, apps, panels, members, availability = (
        generate_phase4_data()
    )

    assert len(panels) == 200

    assert members["panel_id"].isin(
        panels["panel_id"]
    ).all()

    assert members["interviewer_id"].isin(
        masters["HiringManager"]["hiring_manager_id"]
    ).all()


def test_interview_count_and_rescheduling():

    masters, apps, panels, members, availability = (
        generate_phase4_data()
    )

    initial = schedule_interviews(
        apps,
        masters["Requisition"],
        panels,
        members,
        availability,
        1960
    )

    result = reschedule_interviews(
        initial,
        members,
        availability,
        40
    )

    assert len(result) == 2000

    assert (
        result["interview_status"] == "Rescheduled"
    ).sum() == 40

    assert (
        result["interview_status"] == "Scheduled"
    ).sum() == 1960

    assert result["interview_id"].is_unique


def test_rescheduling_history():

    masters, apps, panels, members, availability = (
        generate_phase4_data()
    )

    initial = schedule_interviews(
        apps,
        masters["Requisition"],
        panels,
        members,
        availability,
        1960
    )

    result = reschedule_interviews(
        initial,
        members,
        availability,
        40
    )

    originals = result[
        result["interview_status"] == "Rescheduled"
    ]

    replacements = result[
        result["rescheduled_from_interview_id"].notna()
    ]

    assert len(originals) == 40
    assert len(replacements) == 40

    assert set(
        replacements["rescheduled_from_interview_id"]
    ) == set(originals["interview_id"])


def test_no_active_interviewer_conflicts():

    masters, apps, panels, members, availability = (
        generate_phase4_data()
    )

    initial = schedule_interviews(
        apps,
        masters["Requisition"],
        panels,
        members,
        availability,
        1960
    )

    interviews = reschedule_interviews(
        initial,
        members,
        availability,
        40
    )

    active = interviews[
        interviews["interview_status"] == "Scheduled"
    ]

    merged = active.merge(
        members,
        on="panel_id"
    )

    merged["start"] = pd.to_datetime(
        merged["interview_date"] + " " + merged["start_time"]
    )

    merged["end"] = pd.to_datetime(
        merged["interview_date"] + " " + merged["end_time"]
    )

    for interviewer, group in merged.groupby("interviewer_id"):

        group = group.sort_values("start")

        starts = group["start"].tolist()
        ends = group["end"].tolist()

        for i in range(1, len(group)):
            assert starts[i] >= ends[i - 1]


def test_stage_transition_gate():

    valid, message = validate_stage_transition(
        "Interview",
        "Offer",
        submitted_scorecard_count=2,
        required_scorecard_count=2
    )

    assert valid

    valid, message = validate_stage_transition(
        "Interview",
        "Offer",
        submitted_scorecard_count=1,
        required_scorecard_count=2
    )

    assert not valid
    assert message == "Required review is incomplete"


def test_invalid_stage_transition():

    valid, message = validate_stage_transition(
        "Applied",
        "Offer",
        submitted_scorecard_count=2,
        required_scorecard_count=2
    )

    assert not valid



def get_phase5_data():

    from src.generator import (
        generate_master_data,
        generate_applications
    )

    from src.business_rules import (
        generate_interview_panels,
        generate_availability,
        schedule_interviews,
        reschedule_interviews,
        generate_scorecards,
        validate_scorecard_completeness
    )

    # STEP 1: Generate master data
    masters = generate_master_data("full")

    # STEP 2: Generate applications
    applications = generate_applications(
        masters["Candidate"],
        masters["Requisition"],
        8000
    )

    # STEP 3: Generate interview panels
    panels, members = generate_interview_panels(
        masters["Requisition"],
        masters["HiringManager"]
    )

    # STEP 4: Generate interviewer availability
    availability = generate_availability(
        masters["HiringManager"]
    )

    # STEP 5: Schedule initial interviews
    initial = schedule_interviews(
        applications,
        masters["Requisition"],
        panels,
        members,
        availability,
        1960
    )

    # STEP 6: Reschedule interviews
    interviews = reschedule_interviews(
        initial,
        members,
        availability,
        40
    )

    # STEP 7: Generate scorecards
    scorecards = generate_scorecards(
        interviews,
        applications,
        masters["Requisition"],
        panels,
        members,
        masters["SkillRequirement"]
    )

    # STEP 8: Validate scorecard completeness
    scorecard_completeness = validate_scorecard_completeness(
        interviews=interviews,
        panel_members=members,
        scorecards=scorecards
    )

    # Return named datasets instead of a tuple.
    return {
        "masters": masters,
        "applications": applications,
        "panels": panels,
        "panel_members": members,
        "availability": availability,
        "interviews": interviews,
        "scorecards": scorecards,
        "scorecard_completeness": scorecard_completeness,
        "skill_requirements": masters["SkillRequirement"]
    }



def test_scorecard_generation():

    data = get_phase5_data()

    interviews = data["interviews"]
    scorecards = data["scorecards"]

    scheduled = interviews[
        interviews["interview_status"] == "Scheduled"
    ]

    # Each scheduled interview has two panel reviewers.
    assert len(scorecards) == len(scheduled) * 2

    assert scorecards["scorecard_id"].is_unique


def test_scorecard_id_format():

    data = get_phase5_data()

    scorecards = data["scorecards"]

    for _, row in scorecards.iterrows():

        expected = (
            f"SCORE-{row['interview_id']}-"
            f"{row['reviewer_id']}"
        )

        assert row["scorecard_id"] == expected


def test_scorecard_criteria_are_role_specific():

    data = get_phase5_data()

    masters = data["masters"]
    interviews = data["interviews"]
    scorecards = data["scorecards"]

    interview_details = interviews.merge(
        data["applications"][["application_id", "requisition_id"]],
        on="application_id"
    )

    for _, scorecard in scorecards.iterrows():

        interview = interview_details[
            interview_details["interview_id"]
            == scorecard["interview_id"]
        ].iloc[0]

        required = set(
            masters["SkillRequirement"].loc[
                masters["SkillRequirement"]["requisition_id"]
                == interview["requisition_id"],
                "skill_name"
            ]
        )

        submitted = json.loads(
            scorecard["criterion_scores_json"]
        )

        evaluated = {
            item["criterion"]
            for item in submitted["criteria"]
        }

        assert evaluated.issubset(required)


def test_incomplete_scorecards_are_preserved():

    data = get_phase5_data()

    scorecards = data["scorecards"]

    assert (scorecards["status"] == "Draft").any()

    assert (scorecards["status"] == "Submitted").any()

    drafts = scorecards[
        scorecards["status"] == "Draft"
    ]

    assert drafts["submitted_at"].isna().all()


def test_scorecard_completeness_validation():

    data = get_phase5_data()

    interviews = data["interviews"]
    members = data["panel_members"]
    scorecards = data["scorecards"]

    result = validate_scorecard_completeness(
        interviews,
        members,
        scorecards
    )

    assert len(result) == 1960

    assert result["review_complete"].dtype == bool


def test_offer_gate_blocks_incomplete_reviews():

    data = get_phase5_data()

    applications = data["applications"]
    interviews = data["interviews"]
    members = data["panel_members"]
    scorecards = data["scorecards"]

    completeness = validate_scorecard_completeness(
        interviews,
        members,
        scorecards
    )

    incomplete_interviews = completeness.loc[
        ~completeness["review_complete"],
        "interview_id"
    ]

    assert len(incomplete_interviews) > 0

    interview_id = incomplete_interviews.iloc[0]

    application_id = interviews.loc[
        interviews["interview_id"] == interview_id,
        "application_id"
    ].iloc[0]

    eligible, reason = validate_application_offer_eligibility(
        application_id,
        interviews,
        completeness
    )

    assert not eligible
    assert reason == "Required scorecards are incomplete"


def test_offer_gate_accepts_complete_reviews():

    data = get_phase5_data()

    applications = data["applications"]
    interviews = data["interviews"]
    members = data["panel_members"]
    scorecards = data["scorecards"]

    completeness = validate_scorecard_completeness(
        interviews,
        members,
        scorecards
    )

    complete_interviews = completeness.loc[
        completeness["review_complete"],
        "interview_id"
    ]

    assert len(complete_interviews) > 0

    interview_id = complete_interviews.iloc[0]

    application_id = interviews.loc[
        interviews["interview_id"] == interview_id,
        "application_id"
    ].iloc[0]

    eligible, reason = validate_application_offer_eligibility(
        application_id,
        interviews,
        completeness
    )

    assert eligible



def test_application_outcomes_cover_all_applications():
    data = get_phase5_data()

    outcomes = derive_application_outcomes(
        applications=data["applications"],
        interviews=data["interviews"],
        scorecards=data["scorecards"],
        scorecard_completeness=data["scorecard_completeness"]
    )

    assert len(outcomes) == len(data["applications"])
    assert outcomes["application_id"].is_unique


def test_withdrawn_applications_are_labelled():
    data = get_phase5_data()

    outcomes = derive_application_outcomes(
        applications=data["applications"],
        interviews=data["interviews"],
        scorecards=data["scorecards"],
        scorecard_completeness=data["scorecard_completeness"]
    )

    withdrawn_ids = set(
        data["applications"].loc[
            data["applications"]["status"] == "Withdrawn",
            "application_id"
        ]
    )

    actual_withdrawn_ids = set(
        outcomes.loc[
            outcomes["outcome_label"] == "Withdrawn",
            "application_id"
        ]
    )

    assert withdrawn_ids.issubset(actual_withdrawn_ids)


def test_application_outcome_labels_are_valid():
    data = get_phase5_data()

    outcomes = derive_application_outcomes(
        applications=data["applications"],
        interviews=data["interviews"],
        scorecards=data["scorecards"],
        scorecard_completeness=data["scorecard_completeness"]
    )

    allowed_labels = {
        "Withdrawn",
        "Interview Not Scheduled",
        "Review Pending",
        "Review Complete"
    }

    assert set(outcomes["outcome_label"]).issubset(
        allowed_labels
    )


def test_outcome_evaluations_are_derived_from_submitted_scorecards():
    data = get_phase5_data()

    outcomes = derive_application_outcomes(
        applications=data["applications"],
        interviews=data["interviews"],
        scorecards=data["scorecards"],
        scorecard_completeness=data["scorecard_completeness"]
    )

    assert (
        outcomes["meets_count"]
        + outcomes["does_not_meet_count"]
    ).ge(0).all()

    assert outcomes["average_score"].dropna().between(
        1, 10
    ).all()



if __name__ == "__main__":
    print("Master data validation completed.")



