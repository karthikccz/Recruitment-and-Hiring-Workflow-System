
import numpy as np
import pandas as pd

from src.config import (
    SEED,
    DATA_DIR,
    FULL_CONFIG,
    STARTER_CONFIG
)


def generate_ids(prefix, count, width=6):
    """Generate deterministic zero-padded IDs."""
    return [
        f"{prefix}{i:0{width}d}"
        for i in range(1, count + 1)
    ]


def generate_hiring_managers(rng, count):
    """Generate synthetic hiring manager master records."""

    first_names = [
        "Arun", "Kiran", "Rahul", "Priya", "Sneha",
        "Ravi", "Ananya", "Vikram", "Neha", "Sanjay"
    ]

    last_names = [
        "Kumar", "Sharma", "Reddy", "Rao", "Patel",
        "Verma", "Singh", "Gupta", "Das", "Mehta"
    ]

    departments = [
        "Engineering",
        "Data Science",
        "Artificial Intelligence",
        "Human Resources",
        "Operations"
    ]

    records = []

    ids = generate_ids("MGR-", count)

    for i, manager_id in enumerate(ids):
        first = rng.choice(first_names)
        last = rng.choice(last_names)

        records.append({
            "hiring_manager_id": manager_id,
            "manager_name": f"{first} {last}",
            "department": rng.choice(departments),
            "email": f"{manager_id.lower()}@example.com"
        })

    return pd.DataFrame(records)


def generate_requisitions(rng, managers, count):
    """Generate approved requisitions."""

    job_roles = {
        "Data Science": [
            "Junior Data Scientist",
            "Data Analyst",
            "Machine Learning Engineer"
        ],
        "Engineering": [
            "Software Engineer",
            "Python Developer",
            "Backend Developer"
        ],
        "Artificial Intelligence": [
            "AI Engineer",
            "NLP Engineer",
            "Computer Vision Engineer"
        ],
        "Operations": [
            "Operations Analyst",
            "Business Analyst"
        ],
        "Human Resources": [
            "HR Analyst",
            "Talent Acquisition Specialist"
        ]
    }

    locations = [
        "Hyderabad",
        "Bengaluru",
        "Chennai",
        "Pune",
        "Mumbai",
        "Delhi"
    ]

    records = []

    manager_ids = managers["hiring_manager_id"].tolist()

    requisition_ids = generate_ids(
        "REQ-2026-", count
    )

    for requisition_id in requisition_ids:

        manager_id = rng.choice(manager_ids)

        manager = managers[
            managers["hiring_manager_id"] == manager_id
        ].iloc[0]

        department = manager["department"]

        title = rng.choice(job_roles[department])

        min_salary = int(
            rng.integers(300000, 800000) // 10000 * 10000
        )

        max_salary = min_salary + int(
            rng.integers(200000, 600000) // 10000 * 10000
        )

        records.append({
            "requisition_id": requisition_id,
            "hiring_manager_id": manager_id,
            "job_title": title,
            "department": department,
            "location": rng.choice(locations),
            "min_salary": min_salary,
            "max_salary": max_salary,
            "status": "Approved",
            "created_at": "2026-01-01T09:00:00",
            "approved_at": "2026-01-02T09:00:00"
        })

    return pd.DataFrame(records)


def generate_candidates(rng, count):
    """Generate synthetic candidate profiles."""

    first_names = [
        "Aarav", "Aditya", "Akash", "Ananya", "Arjun",
        "Deepak", "Divya", "Harsha", "Karthik", "Kavya",
        "Manoj", "Meera", "Nikhil", "Pooja", "Pranav",
        "Rahul", "Rohan", "Sakshi", "Sanjana", "Varun"
    ]

    last_names = [
        "Kumar", "Reddy", "Sharma", "Rao", "Patel",
        "Gupta", "Singh", "Verma", "Das", "Naidu"
    ]

    education_options = [
        "B.Tech",
        "B.E",
        "B.Sc",
        "M.Tech",
        "M.Sc",
        "MCA"
    ]

    locations = [
        "Hyderabad",
        "Bengaluru",
        "Chennai",
        "Pune",
        "Mumbai",
        "Delhi",
        "Visakhapatnam",
        "Vijayawada"
    ]

    records = []

    candidate_ids = generate_ids("CAND-", count)

    for i, candidate_id in enumerate(candidate_ids):

        first = rng.choice(first_names)
        last = rng.choice(last_names)

        records.append({
            "candidate_id": candidate_id,
            "candidate_name": f"{first} {last}",
            "email": f"{candidate_id.lower()}@example.com",
            "experience_years": round(
                float(rng.uniform(0, 8)), 1
            ),
            "education": rng.choice(education_options),
            "location": rng.choice(locations),
            "created_at": "2026-01-01T09:00:00"
        })

    return pd.DataFrame(records)


def generate_skill_requirements(rng, requisitions):
    """Generate role-specific skill requirements."""

    role_skills = {
        "Junior Data Scientist": [
            "Python", "SQL", "Machine Learning",
            "Statistics", "Pandas"
        ],
        "Data Analyst": [
            "SQL", "Excel", "Power BI",
            "Python", "Statistics"
        ],
        "Machine Learning Engineer": [
            "Python", "Machine Learning",
            "TensorFlow", "SQL", "Model Deployment"
        ],
        "Software Engineer": [
            "Python", "Java", "SQL",
            "Data Structures", "Algorithms"
        ],
        "Python Developer": [
            "Python", "SQL", "REST APIs",
            "Git", "Testing"
        ],
        "Backend Developer": [
            "Python", "Java", "SQL",
            "REST APIs", "Database Design"
        ],
        "AI Engineer": [
            "Python", "Deep Learning",
            "TensorFlow", "NLP", "Machine Learning"
        ],
        "NLP Engineer": [
            "Python", "NLP", "Transformers",
            "Deep Learning", "Machine Learning"
        ],
        "Computer Vision Engineer": [
            "Python", "OpenCV", "Deep Learning",
            "Computer Vision", "PyTorch"
        ],
        "Operations Analyst": [
            "Excel", "SQL", "Reporting",
            "Communication", "Problem Solving"
        ],
        "Business Analyst": [
            "SQL", "Excel", "Business Analysis",
            "Communication", "Reporting"
        ],
        "HR Analyst": [
            "Excel", "HR Analytics",
            "Communication", "Reporting", "SQL"
        ],
        "Talent Acquisition Specialist": [
            "Recruitment", "Communication",
            "Interviewing", "Coordination", "Reporting"
        ]
    }

    records = []
    counter = 1

    for _, requisition in requisitions.iterrows():

        skills = role_skills[requisition["job_title"]]

        # Select role-specific requirements.
        selected_skills = rng.choice(
            skills,
            size=4,
            replace=False
        )

        for skill in selected_skills:

            records.append({
                "skill_requirement_id": f"SKILL-{counter:06d}",
                "requisition_id": requisition["requisition_id"],
                "skill_name": skill,
                "is_mandatory": int(rng.choice([0, 1]))
            })

            counter += 1

    return pd.DataFrame(records)


def generate_master_data(mode="full"):
    """Generate all master datasets."""

    if mode == "full":
        config = FULL_CONFIG
    elif mode == "starter":
        config = STARTER_CONFIG
    else:
        raise ValueError(
            "Mode must be 'starter' or 'full'"
        )

    rng = np.random.default_rng(SEED)

    managers = generate_hiring_managers(
        rng, config["hiring_managers"]
    )

    requisitions = generate_requisitions(
        rng, managers, config["requisitions"]
    )

    candidates = generate_candidates(
        rng, config["candidates"]
    )

    skills = generate_skill_requirements(
        rng, requisitions
    )

    datasets = {
        "HiringManager": managers,
        "Requisition": requisitions,
        "Candidate": candidates,
        "SkillRequirement": skills
    }

    for name, dataframe in datasets.items():

        dataframe.to_csv(
            DATA_DIR / f"{name}.csv",
            index=False
        )

        print(
            f"{name}: {len(dataframe)} records generated"
        )

    return datasets


def generate_applications(
    candidates,
    requisitions,
    count,
    withdrawal_rate=0.05
):
    """
    Generate applications using existing candidate
    and approved requisition records.
    """

    rng = np.random.default_rng(SEED + 1)

    candidate_ids = candidates[
        "candidate_id"
    ].to_numpy()

    requisition_ids = requisitions[
        "requisition_id"
    ].to_numpy()

    # Only approved requisitions can receive applications.
    approved_requisitions = requisitions[
        requisitions["status"] == "Approved"
    ]

    requisition_ids = approved_requisitions[
        "requisition_id"
    ].to_numpy()

    # Total possible unique candidate-requisition pairs.
    total_pairs = len(candidate_ids) * len(requisition_ids)

    if count > total_pairs:
        raise ValueError(
            "Requested applications exceed available unique pairs"
        )

    # Select unique pairs without replacement.
    selected_pairs = rng.choice(
        total_pairs,
        size=count,
        replace=False
    )

    candidate_indices = (
        selected_pairs // len(requisition_ids)
    )

    requisition_indices = (
        selected_pairs % len(requisition_ids)
    )

    selected_candidates = candidate_ids[
        candidate_indices
    ]

    selected_requisitions = requisition_ids[
        requisition_indices
    ]

    # Generate application dates.
    # Synthetic date range: January to October 2026.
    start_date = pd.Timestamp("2026-01-01")

    day_offsets = rng.integers(
        0, 288,
        size=count
    )

    applied_dates = (
        start_date
        + pd.to_timedelta(day_offsets, unit="D")
    )

    # Include a documented synthetic withdrawal rate.
    # The problem requires withdrawals but does not
    # prescribe their percentage.
    if not 0 <= withdrawal_rate <= 1:
        raise ValueError(
            "Withdrawal rate must be between 0 and 1"
        )

    withdrawal_count = round(
        count * withdrawal_rate
    )

    withdrawn_indices = rng.choice(
        count,
        size=withdrawal_count,
        replace=False
    )

    withdrawn_mask = np.zeros(
        count,
        dtype=bool
    )

    withdrawn_mask[withdrawn_indices] = True

    # Withdrawal must happen after application.
    withdrawal_offsets = rng.integers(
        1, 15,
        size=count
    )

    withdrawn_dates = (
        applied_dates
        + pd.to_timedelta(
            withdrawal_offsets,
            unit="D"
        )
    )

    records = []

    for i in range(count):

        candidate_id = selected_candidates[i]
        requisition_id = selected_requisitions[i]

        application_id = (
            f"APP-{candidate_id}-{requisition_id}"
        )

        if withdrawn_mask[i]:
            status = "Withdrawn"
            withdrawn_at = withdrawn_dates[i].isoformat()
        else:
            status = "Active"
            withdrawn_at = None

        records.append({
            "application_id": application_id,
            "candidate_id": candidate_id,
            "requisition_id": requisition_id,
            "applied_at": applied_dates[i].isoformat(),
            "current_stage": "Applied",
            "status": status,
            "withdrawn_at": withdrawn_at
        })

    applications = pd.DataFrame(records)

    # Verify that generated applications are unique.
    if not applications["application_id"].is_unique:
        raise ValueError(
            "Duplicate application IDs generated"
        )

    return applications