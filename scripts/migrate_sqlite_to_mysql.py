"""
Safe SQLite to MySQL Data Migration Script
Migrates authentic data rows from SQLite to MySQL in strict topological order.
"""
import os
import sqlite3
import pymysql
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sqlite_path = BASE_DIR / "db.sqlite3"

# 1. Connect to Source SQLite
sqlite_conn = sqlite3.connect(sqlite_path)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cur = sqlite_conn.cursor()
print(f"Connected to Source SQLite: {sqlite_path}")

# 2. Connect to Target MySQL
db_user = os.environ.get("DB_USER", "root")
db_password = os.environ.get("DB_PASSWORD", "")
db_name = os.environ.get("DB_NAME", "academic_portal_db")
db_host = os.environ.get("DB_HOST", "127.0.0.1")
db_port = int(os.environ.get("DB_PORT", 3306))

mysql_conn = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name,
    port=db_port,
    autocommit=False
)
mysql_cur = mysql_conn.cursor()
print(f"Connected to Target MySQL: {db_name}\n")

tables_to_migrate = [
    # Tier 0: Root independent tables
    "academics_department",
    "academics_academicsemester",
    "accounts_useraccount",

    # Tier 1: Profiles depending on UserAccount & Department
    "accounts_adminprofile",
    "accounts_officestaffprofile",
    "accounts_instructorprofile",
    "academics_program",
    "academics_course",

    # Tier 2: Faculty Subtypes, Students, Course Offerings
    "accounts_permanentfaculty",
    "accounts_assistantprofessor",
    "accounts_visitingprofessor",
    "accounts_studentprofile",
    "academics_courseoffering",

    # Tier 3: Enrollments & Fee Accounts
    "academics_enrollment",
    "academics_studentfeeaccount",

    # Tier 4: Payments & Logs
    "academics_feepayment",
    "core_admin_adminauditlog",

    # Legacy research tables
    "research_researchproject",
    "research_projectcoinvestigator",
    "research_researchjunior",
    "research_stipenddisbursement",
    "research_researchpublication",
]

try:
    mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")

    for table in tables_to_migrate:
        # Check SQLite count
        sqlite_cur.execute(f"SELECT COUNT(*) FROM `{table}`;")
        src_count = sqlite_cur.fetchone()[0]

        if src_count == 0:
            print(f"[{table}]: 0 rows (skipped)")
            continue

        # Fetch SQLite columns & data
        sqlite_cur.execute(f"SELECT * FROM `{table}`;")
        rows = sqlite_cur.fetchall()
        cols = [description[0] for description in sqlite_cur.description]

        # Prepare MySQL INSERT
        col_list = ", ".join([f"`{c}`" for c in cols])
        placeholders = ", ".join(["%s"] * len(cols))
        insert_sql = f"INSERT IGNORE INTO `{table}` ({col_list}) VALUES ({placeholders});"

        row_tuples = [tuple(r) for r in rows]
        mysql_cur.executemany(insert_sql, row_tuples)
        print(f"[{table}]: {len(row_tuples)} rows migrated successfully.")

    mysql_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    mysql_conn.commit()
    print("\n[SUCCESS] All data successfully transferred from SQLite to MySQL!")

except Exception as e:
    mysql_conn.rollback()
    print(f"\n[ERROR] Migration failed: {e}")
    raise

finally:
    sqlite_conn.close()
    mysql_conn.close()
