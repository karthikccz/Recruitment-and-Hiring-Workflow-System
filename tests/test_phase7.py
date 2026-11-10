import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.generator import generate_master_data, generate_applications
from src.business_rules import (
    generate_interview_panels, generate_availability, schedule_interviews,
    reschedule_interviews, apply_interview_stage_transitions,
    generate_scorecards, validate_scorecard_completeness,
    generate_offers_and_approvals, generate_phase7_anomalies
)
from src.config import STARTER_CONFIG


def build_data():
    m = generate_master_data("starter")
    a = generate_applications(m["Candidate"], m["Requisition"], STARTER_CONFIG["applications"])
    p, pm = generate_interview_panels(m["Requisition"], m["HiringManager"])
    av = generate_availability(m["HiringManager"])
    i = schedule_interviews(a, m["Requisition"], p, pm, av, 196)
    i = reschedule_interviews(i, pm, av, 4)
    a, hist = apply_interview_stage_transitions(a, i)
    sc = generate_scorecards(i, a, m["Requisition"], p, pm, m["SkillRequirement"])
    comp = validate_scorecard_completeness(i, pm, sc)
    return m, a, p, pm, av, i, sc, comp


def test_phase7_offers_and_approvals_are_valid_and_reproducible():
    m, a, p, pm, av, i, sc, comp = build_data()
    offers, approvals = generate_offers_and_approvals(a, i, m["Requisition"], comp)
    assert len(offers) > 0
    assert len(offers) == len(approvals)
    assert offers["offer_id"].is_unique
    assert approvals["approval_id"].is_unique
    assert set(offers["offer_status"]) == {"Pending Approval"}
    assert set(approvals["approval_status"]) == {"Pending"}
    joined = offers.merge(a[["application_id", "requisition_id", "status"]], on="application_id")
    joined = joined.merge(m["Requisition"][["requisition_id", "min_salary", "max_salary"]], on="requisition_id")
    assert (joined["status"] == "Active").all()
    assert (joined["offered_salary"] >= joined["min_salary"]).all()
    assert (joined["offered_salary"] <= joined["max_salary"]).all()
    again, _ = generate_offers_and_approvals(a, i, m["Requisition"], comp)
    assert offers.equals(again)


def test_phase7_generates_five_separate_labelled_anomalies():
    m, a, p, pm, av, i, sc, comp = build_data()
    offers, approvals = generate_offers_and_approvals(a, i, m["Requisition"], comp)
    anomalies, truth = generate_phase7_anomalies(a, m["Requisition"], i, pm, sc, comp, offers)
    assert len(anomalies) == 5
    assert len(truth) == 5
    assert anomalies["anomaly_id"].is_unique
    assert truth["anomaly_id"].is_unique
    assert set(anomalies["anomaly_id"]) == set(truth["anomaly_id"])
    assert set(anomalies["anomaly_id"]) == {"ANOM-001", "ANOM-002", "ANOM-003", "ANOM-004", "ANOM-005"}
