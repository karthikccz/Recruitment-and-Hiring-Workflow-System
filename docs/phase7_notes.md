# Phase 7 – Offers, approvals, and exception scenarios

## Normal workflow
- An offer is generated only for an **Active** application for which every scheduled interview has complete submitted scorecards.
- Offer salary is selected in increments of INR 10,000 within the requisition's approved `min_salary` and `max_salary` band.
- The requisition's assigned hiring manager is recorded as approver.
- Offers and approvals are created with `Pending Approval` / `Pending` status. The synthetic dataset does not make a final hiring decision.
- This is a workflow demonstration, not an automated candidate-selection policy.

## Exception data
`anomalies.csv` contains five isolated, hypothetical exception payloads. They do not overwrite or contaminate the valid baseline tables. `ground_truth.csv` records the expected decision and the rule that should detect each exception.

| ID | Scenario | Expected decision |
|---|---|---|
| ANOM-001 | Application advances to Offer without complete reviews | Reject transition |
| ANOM-002 | Interviewer is double-booked | Reject or reschedule conflicting booking |
| ANOM-003 | Offer exceeds approved salary maximum | Reject offer |
| ANOM-004 | Withdrawn candidate still has a scheduled interview | Cancel interview |
| ANOM-005 | Scorecard uses a criterion outside the role rubric | Reject criterion |

## Reproducibility
Offer generation uses the project seed plus a fixed offset. The same input tables produce the same offers. The exception scenarios are deterministic and are generated separately from baseline records.
