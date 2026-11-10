
import sqlite3

from src.schema import DB_PATH

connection = sqlite3.connect(DB_PATH)

tables = connection.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("DATABASE TABLES")

for table in tables:
    print("-", table[0])

print("\nFOREIGN KEY CHECK")

for table in [
    "Requisition",
    "Application",
    "SkillRequirement",
    "InterviewPanel",
    "PanelMember",
    "Availability",
    "Interview",
    "Scorecard",
    "Offer",
    "Approval"
]:
    result = connection.execute(
        f"PRAGMA foreign_key_list({table})"
    ).fetchall()

    print(f"{table}: {len(result)} foreign-key relationships")

connection.close()
