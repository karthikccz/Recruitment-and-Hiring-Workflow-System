
import sqlite3

from src.config import OUTPUT_DIR

DB_PATH = OUTPUT_DIR / "database.sqlite"


SCHEMA = """

PRAGMA foreign_keys = ON;

-- 1. HiringManager
CREATE TABLE IF NOT EXISTS HiringManager (
    hiring_manager_id TEXT PRIMARY KEY,
    manager_name TEXT NOT NULL,
    department TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

-- 2. Requisition
CREATE TABLE IF NOT EXISTS Requisition (
    requisition_id TEXT PRIMARY KEY,
    hiring_manager_id TEXT NOT NULL,
    job_title TEXT NOT NULL,
    department TEXT NOT NULL,
    location TEXT NOT NULL,
    min_salary REAL NOT NULL,
    max_salary REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    approved_at TEXT,
    FOREIGN KEY (hiring_manager_id)
        REFERENCES HiringManager(hiring_manager_id),
    CHECK (min_salary > 0),
    CHECK (max_salary >= min_salary)
);

-- 3. Candidate
CREATE TABLE IF NOT EXISTS Candidate (
    candidate_id TEXT PRIMARY KEY,
    candidate_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    experience_years REAL NOT NULL,
    education TEXT NOT NULL,
    location TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (experience_years >= 0)
);

-- 4. Application
CREATE TABLE IF NOT EXISTS Application (
    application_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    requisition_id TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    status TEXT NOT NULL,
    withdrawn_at TEXT,

    FOREIGN KEY (candidate_id)
        REFERENCES Candidate(candidate_id),

    FOREIGN KEY (requisition_id)
        REFERENCES Requisition(requisition_id),

    UNIQUE(candidate_id, requisition_id)
);

-- 5. SkillRequirement
CREATE TABLE IF NOT EXISTS SkillRequirement (
    skill_requirement_id TEXT PRIMARY KEY,
    requisition_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    is_mandatory INTEGER NOT NULL,

    FOREIGN KEY (requisition_id)
        REFERENCES Requisition(requisition_id),

    CHECK (is_mandatory IN (0, 1)),

    UNIQUE(requisition_id, skill_name)
);

-- 6. InterviewPanel
CREATE TABLE IF NOT EXISTS InterviewPanel (
    panel_id TEXT PRIMARY KEY,
    requisition_id TEXT NOT NULL,
    panel_name TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (requisition_id)
        REFERENCES Requisition(requisition_id)
);

-- Bridge table: InterviewPanel and HiringManager
CREATE TABLE IF NOT EXISTS PanelMember (
    panel_id TEXT NOT NULL,
    interviewer_id TEXT NOT NULL,

    PRIMARY KEY (panel_id, interviewer_id),

    FOREIGN KEY (panel_id)
        REFERENCES InterviewPanel(panel_id),

    FOREIGN KEY (interviewer_id)
        REFERENCES HiringManager(hiring_manager_id)
);

-- 7. Availability
CREATE TABLE IF NOT EXISTS Availability (
    availability_id TEXT PRIMARY KEY,
    interviewer_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    availability_status TEXT NOT NULL,

    FOREIGN KEY (interviewer_id)
        REFERENCES HiringManager(hiring_manager_id),

    CHECK (end_time > start_time)
);

-- 8. Interview
CREATE TABLE IF NOT EXISTS Interview (
    interview_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    panel_id TEXT NOT NULL,
    interview_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    interview_status TEXT NOT NULL,
    rescheduled_from_interview_id TEXT,

    FOREIGN KEY (application_id)
        REFERENCES Application(application_id),

    FOREIGN KEY (panel_id)
        REFERENCES InterviewPanel(panel_id),

    FOREIGN KEY (rescheduled_from_interview_id)
        REFERENCES Interview(interview_id),

    CHECK (end_time > start_time)
);

-- 9. Scorecard
CREATE TABLE IF NOT EXISTS Scorecard (
    scorecard_id TEXT PRIMARY KEY,
    interview_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    criterion_scores_json TEXT NOT NULL,
    comments TEXT,
    submitted_at TEXT,
    status TEXT NOT NULL,

    FOREIGN KEY (interview_id)
        REFERENCES Interview(interview_id),

    FOREIGN KEY (reviewer_id)
        REFERENCES HiringManager(hiring_manager_id),

    UNIQUE(interview_id, reviewer_id)
);

-- 10. Offer
CREATE TABLE IF NOT EXISTS Offer (
    offer_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    offered_salary REAL NOT NULL,
    currency TEXT NOT NULL,
    offer_date TEXT NOT NULL,
    offer_status TEXT NOT NULL,

    FOREIGN KEY (application_id)
        REFERENCES Application(application_id),

    CHECK (offered_salary > 0)
);

-- 11. Approval
CREATE TABLE IF NOT EXISTS Approval (
    approval_id TEXT PRIMARY KEY,
    offer_id TEXT NOT NULL,
    approver_id TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    decision_at TEXT,
    comments TEXT,

    FOREIGN KEY (offer_id)
        REFERENCES Offer(offer_id),

    FOREIGN KEY (approver_id)
        REFERENCES HiringManager(hiring_manager_id)
);

-- State change history
CREATE TABLE IF NOT EXISTS StateHistory (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    previous_state TEXT,
    new_state TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_timestamp TEXT NOT NULL
);

"""


def create_database():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.executescript(SCHEMA)
        connection.commit()
        print(f"Database created: {DB_PATH}")
    finally:
        connection.close()


if __name__ == "__main__":
    create_database()
