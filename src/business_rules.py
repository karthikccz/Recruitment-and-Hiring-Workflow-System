
import numpy as np
import pandas as pd
import json
from src.config import SEED


def generate_interview_panels(requisitions, managers):
    """Generate one interview panel per requisition."""

    rng = np.random.default_rng(SEED + 2)

    manager_ids = managers[
        "hiring_manager_id"
    ].tolist()

    records = []
    members = []

    for i, (_, req) in enumerate(requisitions.iterrows(), start=1):

        panel_id = f"PANEL-{i:06d}"

        assigned_manager = req["hiring_manager_id"]

        # Select a second, distinct panel member.
        other_managers = [
            manager_id
            for manager_id in manager_ids
            if manager_id != assigned_manager
        ]

        second_manager = rng.choice(other_managers)

        records.append({
            "panel_id": panel_id,
            "requisition_id": req["requisition_id"],
            "panel_name": f"Panel {i:03d}",
            "created_at": "2026-01-03T09:00:00"
        })

        members.append({
            "panel_id": panel_id,
            "interviewer_id": assigned_manager
        })

        members.append({
            "panel_id": panel_id,
            "interviewer_id": second_manager
        })

    return (
        pd.DataFrame(records),
        pd.DataFrame(members)
    )


def generate_availability(managers):
    """
    Generate interviewer calendars.

    Each calendar has four one-hour slots per weekday.
    These are synthetic available windows.
    """

    manager_ids = managers[
        "hiring_manager_id"
    ].tolist()

    dates = pd.bdate_range(
        start="2026-02-02",
        end="2026-12-31"
    )

    time_slots = [
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("14:00", "15:00"),
        ("15:00", "16:00")
    ]

    records = []
    counter = 1

    for manager_id in manager_ids:

        for date in dates:

            for start, end in time_slots:

                start_dt = pd.Timestamp(
                    f"{date.date()} {start}"
                )

                end_dt = pd.Timestamp(
                    f"{date.date()} {end}"
                )

                records.append({
                    "availability_id": f"AVAIL-{counter:06d}",
                    "interviewer_id": manager_id,
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "availability_status": "Available"
                })

                counter += 1

    return pd.DataFrame(records)



def schedule_interviews(
    applications,
    requisitions,
    panels,
    panel_members,
    availability,
    target_count
):
    """
    Schedule interviews using available panel slots.

    Active interviews cannot overlap for any interviewer.
    """

    # Only active applications can be scheduled.
    eligible_apps = applications[
        applications["status"] == "Active"
    ].copy()

    if target_count <= 0:
        raise ValueError("target_count must be positive")

    if target_count > len(eligible_apps):
        raise ValueError(
            "Not enough active applications for requested interviews"
        )

    # Application -> requisition -> panel mapping.
    # Application -> requisition -> panel mapping.
    requisition_panel = dict(
    zip(
        panels["requisition_id"],
        panels["panel_id"]
    )
)

    # Panel -> interviewer list.
    member_lookup = (
        panel_members.groupby("panel_id")["interviewer_id"]
        .apply(list)
        .to_dict()
    )

    # Availability indexed by interviewer and slot.
    availability_lookup = {}

    for _, row in availability.iterrows():

        start = pd.Timestamp(row["start_time"])
        end = pd.Timestamp(row["end_time"])

        key = (
            row["interviewer_id"],
            start.isoformat(),
            end.isoformat()
        )

        availability_lookup[key] = row["availability_status"]

    # Tracks actively booked interviewer slots.
    booked = set()

    records = []

    # Deterministic application ordering.
    eligible_apps = eligible_apps.sort_values(
        ["applied_at", "application_id"]
    ).head(target_count)

    # Slots in chronological order.
    available_slots = (
    availability[
        ["start_time", "end_time"]
    ]
    .drop_duplicates()
    .sort_values("start_time")
)
    
    counter = 1

    for _, app in eligible_apps.iterrows():

        requisition_id = app["requisition_id"]

        panel_id = requisition_panel.get(requisition_id)

        if panel_id is None:
            raise ValueError(
                f"No panel found for {requisition_id}"
            )

        interviewers = member_lookup.get(panel_id, [])

        if not interviewers:
            raise ValueError(
                f"No panel members found for {panel_id}"
            )

        application_date = pd.Timestamp(
            app["applied_at"]
        ).date()

        selected_slot = None

        # Find the first slot available for every panel member.
        for _, slot in available_slots.iterrows():

            start = pd.Timestamp(slot["start_time"])
            end = pd.Timestamp(slot["end_time"])

            if start.date() <= application_date:
                continue

            slot_start = start.isoformat()
            slot_end = end.isoformat()

            all_available = True

            for interviewer in interviewers:

                key = (
                    interviewer,
                    slot_start,
                    slot_end
                )

                if (
                    key in booked
                    or availability_lookup.get(key)
                    != "Available"
                ):
                    all_available = False
                    break

            if all_available:
                selected_slot = (start, end)
                break

        if selected_slot is None:
            raise ValueError(
                f"No conflict-free slot for {app['application_id']}"
            )

        start, end = selected_slot

        # Book every panel member.
        for interviewer in interviewers:
            booked.add((
                interviewer,
                start.isoformat(),
                end.isoformat()
            ))

        interview_id = f"INT-2026-{counter:06d}"

        records.append({
            "interview_id": interview_id,
            "application_id": app["application_id"],
            "panel_id": panel_id,
            "interview_date": start.date().isoformat(),
            "start_time": start.strftime("%H:%M"),
            "end_time": end.strftime("%H:%M"),
            "interview_status": "Scheduled",
            "rescheduled_from_interview_id": None
        })

        counter += 1

    return pd.DataFrame(records)



def reschedule_interviews(
    interviews,
    panel_members,
    availability,
    count=40
):
    """
    Reschedule existing interviews.

    Original interview records are retained.
    Replacement records reference original IDs.
    """

    result = interviews.copy()

    if count < 0 or count > len(result):
        raise ValueError("Invalid rescheduling count")

    # Select interviews to reschedule.
    selected_indices = result.index[:count].tolist()

    selected_original_ids = set(
        result.loc[
            selected_indices,
            "interview_id"
        ]
    )

    # Only non-rescheduled interviews occupy active slots.
    active = result[
        ~result["interview_id"].isin(selected_original_ids)
        & (result["interview_status"] == "Scheduled")
    ]

    # Build the existing bookings.
    member_lookup = (
        panel_members.groupby("panel_id")["interviewer_id"]
        .apply(list)
        .to_dict()
    )

    booked = set()

    for _, row in active.iterrows():

        start = pd.Timestamp(
            f"{row['interview_date']} {row['start_time']}"
        )

        end = pd.Timestamp(
            f"{row['interview_date']} {row['end_time']}"
        )

        for interviewer in member_lookup[row["panel_id"]]:

            booked.add((
                interviewer,
                start.isoformat(),
                end.isoformat()
            ))

    availability_lookup = {}

    for _, row in availability.iterrows():

        availability_lookup[
            (
                row["interviewer_id"],
                pd.Timestamp(row["start_time"]).isoformat(),
                pd.Timestamp(row["end_time"]).isoformat()
            )
        ] = row["availability_status"]

    slots = (
    availability[
        ["start_time", "end_time"]
    ]
    .drop_duplicates()
    .sort_values("start_time")
)
    new_records = []

    next_number = len(result) + 1

    for index in selected_indices:

        original = result.loc[index].copy()

        original_start = pd.Timestamp(
            f"{original['interview_date']} "
            f"{original['start_time']}"
        )

        interviewers = member_lookup[
            original["panel_id"]
        ]

        selected_slot = None

        for _, slot in slots.iterrows():

            start = pd.Timestamp(slot["start_time"])
            end = pd.Timestamp(slot["end_time"])

            # Replacement must occur after original slot.
            if start <= original_start:
                continue

            keys = [
                (person, start.isoformat(), end.isoformat())
                for person in interviewers
            ]

            if any(key in booked for key in keys):
                continue

            if any(
                availability_lookup.get(key) != "Available"
                for key in keys
            ):
                continue

            selected_slot = (start, end, keys)
            break

        if selected_slot is None:
            raise ValueError(
                f"Cannot reschedule {original['interview_id']}"
            )

        start, end, keys = selected_slot

        for key in keys:
            booked.add(key)

        # Preserve original interview history.
        result.loc[index, "interview_status"] = "Rescheduled"

        replacement_id = (
            f"INT-2026-{next_number:06d}"
        )

        new_records.append({
            "interview_id": replacement_id,
            "application_id": original["application_id"],
            "panel_id": original["panel_id"],
            "interview_date": start.date().isoformat(),
            "start_time": start.strftime("%H:%M"),
            "end_time": end.strftime("%H:%M"),
            "interview_status": "Scheduled",
            "rescheduled_from_interview_id": original["interview_id"]
        })

        next_number += 1

    replacements = pd.DataFrame(new_records)

    return pd.concat(
        [result, replacements],
        ignore_index=True
    )




def apply_interview_stage_transitions(
    applications,
    interviews
):
    updated = applications.copy()
    history = []

    counter = 1

    scheduled = interviews[
        interviews["interview_status"] == "Scheduled"
    ]

    scheduled_application_ids = set(
        scheduled["application_id"]
    )

    # Record application withdrawals.
    for _, app in updated.iterrows():

        if app["status"] == "Withdrawn":

            history.append({
                "event_id": f"EVENT-{counter:06d}",
                "entity_type": "Application",
                "entity_id": app["application_id"],
                "previous_state": "Active",
                "new_state": "Withdrawn",
                "event_type": "Withdrawal",
                "event_timestamp": app["withdrawn_at"]
            })

            counter += 1

    # Record valid Applied -> Interview transitions.
    for index, app in updated.iterrows():

        application_id = app["application_id"]

        if (
            app["status"] == "Active"
            and app["current_stage"] == "Applied"
            and application_id in scheduled_application_ids
        ):

            interview_record = (
                scheduled[
                    scheduled["application_id"] == application_id
                ]
                .sort_values("interview_date")
                .iloc[0]
            )

            event_timestamp = (
                f"{interview_record['interview_date']}T"
                f"{interview_record['start_time']}:00"
            )

            history.append({
                "event_id": f"EVENT-{counter:06d}",
                "entity_type": "Application",
                "entity_id": application_id,
                "previous_state": "Applied",
                "new_state": "Interview",
                "event_type": "StageTransition",
                "event_timestamp": event_timestamp
            })

            updated.loc[index, "current_stage"] = "Interview"

            counter += 1

    return updated, pd.DataFrame(history)


def generate_interview_history(interviews, existing_history):
    """Record interview rescheduling events."""

    history = existing_history.to_dict("records")

    counter = len(history) + 1

    replacements = interviews[
        interviews["rescheduled_from_interview_id"].notna()
    ]

    for _, replacement in replacements.iterrows():

        history.append({
            "event_id": f"EVENT-{counter:06d}",
            "entity_type": "Interview",
            "entity_id": replacement[
                "rescheduled_from_interview_id"
            ],
            "previous_state": "Scheduled",
            "new_state": "Rescheduled",
            "event_type": "InterviewRescheduled",
            "event_timestamp": (
                f"{replacement['interview_date']}T"
                f"{replacement['start_time']}:00"
            )
        })

        counter += 1

    return pd.DataFrame(history)


def validate_stage_transition(
    current_stage,
    next_stage,
    submitted_scorecard_count,
    required_scorecard_count
):
    """
    Validate the transition before updating an application.
    """

    allowed_transitions = {
        "Applied": ["Interview"],
        "Interview": ["Offer"],
        "Offer": []
    }

    if next_stage not in allowed_transitions.get(
        current_stage, []
    ):
        return False, "Invalid stage transition"

    if next_stage == "Offer":

        if submitted_scorecard_count < required_scorecard_count:
            return False, "Required review is incomplete"

    return True, "Transition permitted"




def generate_scorecards(
    interviews,
    applications,
    requisitions,
    panels,
    panel_members,
    skill_requirements,
    incomplete_rate=0.05
):
    """
    Generate rubric-based scorecards for active applications
    with scheduled interviews.

    Scoring:
        1-5  -> Does Not Meet
        6-10 -> Meets

    Incomplete scorecards are retained as Draft.
    Complete scorecards are marked Submitted.
    """

    rng = np.random.default_rng(SEED + 3)
    scorecards = []

    # Only applications that are still active can be evaluated.
    application_lookup = (
        applications
        .set_index("application_id")
        .to_dict("index")
    )

    # Get the required criteria for each requisition.
    skills_lookup = (
        skill_requirements
        .groupby("requisition_id")["skill_name"]
        .apply(list)
        .to_dict()
    )

    # Get the reviewers assigned to each panel.
    reviewers_lookup = (
        panel_members
        .groupby("panel_id")["interviewer_id"]
        .apply(list)
        .to_dict()
    )

    for _, interview in interviews.iterrows():

        # Do not score rescheduled or cancelled interview records.
        if interview["interview_status"] != "Scheduled":
            continue

        application = application_lookup.get(
            interview["application_id"]
        )

        if application is None or application["status"] != "Active":
            continue

        requisition_id = application["requisition_id"]
        panel_id = interview["panel_id"]

        criteria = skills_lookup.get(requisition_id, [])
        reviewers = reviewers_lookup.get(panel_id, [])

        # A scorecard needs both role criteria and assigned reviewers.
        if not criteria or not reviewers:
            continue

        for reviewer_id in reviewers:

            # Generate one score for every required criterion.
            criterion_records = []

            for criterion in criteria:

                score = int(rng.integers(1, 11))

                evaluation = (
                    "Meets" if score >= 6
                    else "Does Not Meet"
                )

                criterion_records.append({
                    "criterion": criterion,
                    "score": score,
                    "evaluation": evaluation
                })

            # Randomly retain some incomplete scorecards.
            is_incomplete = rng.random() < incomplete_rate

            if is_incomplete and len(criterion_records) > 1:
                criterion_records = criterion_records[:-1]

            total_score = sum(
                item["score"] for item in criterion_records
            )

            maximum_score = len(criteria) * 10

            if is_incomplete:
                status = "Draft"
                average_score = None
                submitted_at = None

            else:
                status = "Submitted"

                average_score = round(
                    total_score / len(criteria), 2
                )

                submitted_at = (
                    f"{interview['interview_date']} "
                    f"{interview['end_time']}"
                )

            scorecard_data = {
                "criteria": criterion_records,
                "total_score": total_score,
                "maximum_score": maximum_score,
                "average_score": average_score
            }

            scorecards.append({
                "scorecard_id": (
                    f"SCORE-{interview['interview_id']}-{reviewer_id}"
                ),
                "interview_id": interview["interview_id"],
                "reviewer_id": reviewer_id,
                "criterion_scores_json": json.dumps(scorecard_data),
                "comments": (
                    "Synthetic evaluation generated for testing."
                ),
                "submitted_at": submitted_at,
                "status": status
            })

    return pd.DataFrame(scorecards)


def validate_scorecard_completeness(
    interviews,
    panel_members,
    scorecards
):
    """
    An interview is review-complete only when every assigned
    panel reviewer has submitted a scorecard.
    """

    reviewers_lookup = (
        panel_members
        .groupby("panel_id")["interviewer_id"]
        .apply(set)
        .to_dict()
    )

    submitted_lookup = {}

    if not scorecards.empty:
        submitted = scorecards[
            scorecards["status"] == "Submitted"
        ]

        for interview_id, group in submitted.groupby("interview_id"):
            submitted_lookup[interview_id] = set(
                group["reviewer_id"]
            )

    results = []

    scheduled_interviews = interviews[
        interviews["interview_status"] == "Scheduled"
    ]

    for _, interview in scheduled_interviews.iterrows():

        required_reviewers = reviewers_lookup.get(
            interview["panel_id"], set()
        )

        submitted_reviewers = submitted_lookup.get(
            interview["interview_id"], set()
        )

        complete = (
            bool(required_reviewers)
            and required_reviewers.issubset(submitted_reviewers)
        )

        results.append({
            "interview_id": interview["interview_id"],
            "required_scorecards": len(required_reviewers),
            "submitted_scorecards": len(
                required_reviewers.intersection(submitted_reviewers)
            ),
            "review_complete": complete
        })

    return pd.DataFrame(results)



def validate_application_offer_eligibility(
    application_id,
    interviews,
    scorecard_completeness
):
    """
    Check whether all scheduled interviews associated
    with an application have complete reviews.
    """

    application_interviews = interviews[
        (interviews["application_id"] == application_id)
        & (interviews["interview_status"] == "Scheduled")
    ]

    if application_interviews.empty:
        return False, "No scheduled interview found"

    interview_ids = set(
        application_interviews["interview_id"]
    )

    reviews = scorecard_completeness[
        scorecard_completeness["interview_id"].isin(
            interview_ids
        )
    ]

    if len(reviews) != len(interview_ids):
        return False, "Missing interview review records"

    if not reviews["review_complete"].all():
        return False, "Required scorecards are incomplete"

    return True, "Required reviews completed"




def generate_scorecard_history(scorecards, existing_history):
    """
    Record submission events without overwriting existing history.
    """

    history_records = []

    if scorecards.empty:
        return existing_history

    submitted_scorecards = scorecards[
        scorecards["status"] == "Submitted"
    ]

    for _, scorecard in submitted_scorecards.iterrows():

        history_records.append({
            "event_id": (
                f"EVT-SCORE-{scorecard['scorecard_id']}"
            ),
            "entity_type": "Scorecard",
            "entity_id": scorecard["scorecard_id"],
            "previous_state": None,
            "new_state": "Submitted",
            "event_type": "ScorecardSubmitted",
            "event_timestamp": scorecard["submitted_at"]
        })

    if history_records:
        history_df = pd.DataFrame(history_records)

        return pd.concat(
            [existing_history, history_df],
            ignore_index=True
        )

    return existing_history



def derive_application_outcomes(
    applications,
    interviews,
    scorecards,
    scorecard_completeness
):
    """
    Derive application-level workflow outcomes from existing records.

    No outcome is assigned randomly.
    No overall candidate selection decision is made.
    """

    import json

    results = []

    # Map each interview to its application.
    interview_lookup = interviews.groupby(
        "application_id"
    )

    # Map each interview's scorecards to its application.
    if not scorecards.empty:
        scorecard_details = scorecards.merge(
            interviews[["interview_id", "application_id"]],
            on="interview_id",
            how="left"
        )
    else:
        scorecard_details = pd.DataFrame(
            columns=[
                "interview_id",
                "application_id",
                "status",
                "criterion_scores_json"
            ]
        )

    # Completeness is calculated per scheduled interview.
    completeness_lookup = {}

    if not scorecard_completeness.empty:
        completeness_lookup = (
            scorecard_completeness
            .set_index("interview_id")["review_complete"]
            .to_dict()
        )

    for _, application in applications.iterrows():

        application_id = application["application_id"]

        # Get interviews belonging to this application.
        if application_id in interview_lookup.groups:
            app_interviews = interview_lookup.get_group(
                application_id
            )
        else:
            app_interviews = interviews.iloc[0:0]

        total_interviews = len(app_interviews)

        scheduled_interviews = app_interviews[
            app_interviews["interview_status"] == "Scheduled"
        ]

        rescheduled_interviews = app_interviews[
            app_interviews["interview_status"] == "Rescheduled"
        ]

        # Get scorecards belonging to this application.
        app_scorecards = scorecard_details[
            scorecard_details["application_id"] == application_id
        ]

        submitted_scorecards = app_scorecards[
            app_scorecards["status"] == "Submitted"
        ]

        draft_scorecards = app_scorecards[
            app_scorecards["status"] == "Draft"
        ]

        meets_count = 0
        does_not_meet_count = 0
        submitted_scores = []

        # Extract criterion-level evaluations from submitted scorecards.
        for _, scorecard in submitted_scorecards.iterrows():

            details = json.loads(
                scorecard["criterion_scores_json"]
            )

            for criterion in details["criteria"]:

                score = criterion["score"]
                evaluation = criterion["evaluation"]

                submitted_scores.append(score)

                if evaluation == "Meets":
                    meets_count += 1

                elif evaluation == "Does Not Meet":
                    does_not_meet_count += 1

        average_score = (
            round(
                sum(submitted_scores) / len(submitted_scores),
                2
            )
            if submitted_scores
            else None
        )

        # Derive the application workflow outcome.
        if application["status"] == "Withdrawn":

            outcome_label = "Withdrawn"

        elif scheduled_interviews.empty:

            outcome_label = "Interview Not Scheduled"

        else:

            all_reviews_complete = all(
                completeness_lookup.get(
                    interview_id,
                    False
                )
                for interview_id in scheduled_interviews[
                    "interview_id"
                ]
            )

            if all_reviews_complete:
                outcome_label = "Review Complete"
            else:
                outcome_label = "Review Pending"

        results.append({
            "application_id": application_id,
            "requisition_id": application["requisition_id"],
            "application_status": application["status"],
            "current_stage": application["current_stage"],
            "total_interviews": total_interviews,
            "scheduled_interviews": len(scheduled_interviews),
            "rescheduled_interviews": len(rescheduled_interviews),
            "submitted_scorecards": len(submitted_scorecards),
            "draft_scorecards": len(draft_scorecards),
            "meets_count": meets_count,
            "does_not_meet_count": does_not_meet_count,
            "average_score": average_score,
            "outcome_label": outcome_label
        })

    return pd.DataFrame(results)


def generate_offers_and_approvals(
    applications,
    interviews,
    requisitions,
    scorecard_completeness
):
    """Create synthetic offers for active applications with complete reviews.

    This demonstrates the offer/approval workflow; it is not a candidate
    selection algorithm. Offers are pending approval and use the requisition
    owner's hiring manager as approver.
    """
    rng = np.random.default_rng(SEED + 7)
    req_lookup = requisitions.set_index("requisition_id").to_dict("index")
    offers, approvals = [], []

    for _, app in applications.iterrows():
        if app["status"] != "Active":
            continue
        eligible, _ = validate_application_offer_eligibility(
            app["application_id"], interviews, scorecard_completeness
        )
        if not eligible:
            continue

        req = req_lookup[app["requisition_id"]]
        low, high = int(req["min_salary"]), int(req["max_salary"])
        salary_values = np.arange(low, high + 1, 10000)
        salary = int(rng.choice(salary_values))
        app_interviews = interviews[
            (interviews["application_id"] == app["application_id"])
            & (interviews["interview_status"] == "Scheduled")
        ]
        offer_id = f"OFF-2026-{len(offers) + 1:06d}"
        offers.append({
            "offer_id": offer_id,
            "application_id": app["application_id"],
            "offered_salary": salary,
            "currency": "INR",
            "offer_date": pd.to_datetime(app_interviews["interview_date"]).max().date().isoformat(),
            "offer_status": "Pending Approval"
        })
        approvals.append({
            "approval_id": f"APR-2026-{len(approvals) + 1:06d}",
            "offer_id": offer_id,
            "approver_id": req["hiring_manager_id"],
            "approval_status": "Pending",
            "decision_at": None,
            "comments": "Awaiting hiring manager approval"
        })

    return pd.DataFrame(offers), pd.DataFrame(approvals)


def generate_phase7_anomalies(
    applications, requisitions, interviews, panel_members,
    scorecards, scorecard_completeness, offers
):
    """Create five isolated, labelled exception examples without corrupting baseline tables."""
    import json

    anomalies, truth = [], []

    def add(anomaly_id, issue_type, entity, record_id, payload, expected, rule):
        anomalies.append({
            "anomaly_id": anomaly_id,
            "source_entity": entity,
            "source_record_id": record_id,
            "issue_type": issue_type,
            "anomaly_payload_json": json.dumps(payload, sort_keys=True)
        })
        truth.append({
            "anomaly_id": anomaly_id,
            "expected_decision": expected,
            "detection_rule": rule
        })

    # 1. Attempt to advance an application without all required submitted reviews.
    incomplete = scorecard_completeness[
        ~scorecard_completeness["review_complete"]
    ]
    if not incomplete.empty:
        interview_id = incomplete.iloc[0]["interview_id"]
        app_id = interviews.loc[
            interviews["interview_id"] == interview_id, "application_id"
        ].iloc[0]
    else:
        app_id = applications.loc[applications["status"] == "Active", "application_id"].iloc[0]
        interview_id = None
    add("ANOM-001", "advance_without_required_review", "Application", app_id,
        {"attempted_stage": "Offer", "interview_id": interview_id,
         "submitted_reviews_complete": False},
        "Reject transition", "Offer transition requires all scheduled interview reviews to be complete")

    # 2. Add a hypothetical booking that overlaps an existing panel member's interview.
    scheduled = interviews[interviews["interview_status"] == "Scheduled"]
    base_interview = scheduled.iloc[0]
    panel_people = panel_members[panel_members["panel_id"] == base_interview["panel_id"]]
    interviewer = panel_people.iloc[0]["interviewer_id"]
    add("ANOM-002", "interviewer_double_booked", "Interview", base_interview["interview_id"],
        {"interviewer_id": interviewer, "existing_interview_id": base_interview["interview_id"],
         "conflicting_date": base_interview["interview_date"],
         "conflicting_start_time": base_interview["start_time"],
         "conflicting_end_time": base_interview["end_time"]},
        "Reject or reschedule conflicting booking", "An interviewer cannot attend overlapping interviews")

    # 3. An offer with salary above the requisition's approved maximum.
    if not offers.empty:
        base_offer = offers.iloc[0]
        app_id = base_offer["application_id"]
    else:
        app_id = applications.loc[applications["status"] == "Active", "application_id"].iloc[0]
    app = applications[applications["application_id"] == app_id].iloc[0]
    req = requisitions[requisitions["requisition_id"] == app["requisition_id"]].iloc[0]
    add("ANOM-003", "offer_exceeds_salary_band", "Offer", base_offer["offer_id"] if not offers.empty else "UNGENERATED-OFFER",
        {"application_id": app_id, "offered_salary": int(req["max_salary"]) + 50000,
         "approved_min_salary": int(req["min_salary"]), "approved_max_salary": int(req["max_salary"]), "currency": "INR"},
        "Reject offer", "Offered salary must be between requisition min_salary and max_salary")

    # 4. A withdrawn candidate must not retain an active interview booking.
    withdrawn = applications[applications["status"] == "Withdrawn"]
    withdrawn_app = withdrawn.iloc[0]
    add("ANOM-004", "withdrawn_candidate_still_scheduled", "Application", withdrawn_app["application_id"],
        {"application_status": "Withdrawn", "hypothetical_interview_status": "Scheduled",
         "requisition_id": withdrawn_app["requisition_id"]},
        "Cancel interview", "Withdrawn applications cannot have active scheduled interviews")

    # 5. Scorecard criterion must belong to the requisition's defined skill rubric.
    if not scorecards.empty:
        scorecard = scorecards.iloc[0]
        add("ANOM-005", "irrelevant_evaluation_criterion", "Scorecard", scorecard["scorecard_id"],
            {"interview_id": scorecard["interview_id"], "reviewer_id": scorecard["reviewer_id"],
             "criterion": "Unrelated Personal Preference", "score": 8},
            "Reject scorecard criterion", "Every scorecard criterion must match a SkillRequirement for that requisition")
    else:
        add("ANOM-005", "irrelevant_evaluation_criterion", "Scorecard", "UNGENERATED-SCORECARD",
            {"criterion": "Unrelated Personal Preference", "score": 8},
            "Reject scorecard criterion", "Every scorecard criterion must match a SkillRequirement for that requisition")

    return pd.DataFrame(anomalies), pd.DataFrame(truth)
