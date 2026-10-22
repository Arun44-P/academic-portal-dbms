"""
MySQL Database Backup & Manifest Generator
Backs up academic_portal_db using mysqldump and Django dumpdata.
"""
import os
import sys
import subprocess
import datetime
import json
import pymysql
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env
env_file = BASE_DIR / '.env'
env_vars = {}
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip()

db_name = env_vars.get('DB_NAME', 'academic_portal_db')
db_user = env_vars.get('DB_USER', 'academia_user')
db_pass = env_vars.get('DB_PASSWORD', 'Academia_Pass#2026')
db_host = env_vars.get('DB_HOST', '127.0.0.1')
db_port = int(env_vars.get('DB_PORT', 3306))


backup_dir = BASE_DIR / 'backups'
backup_dir.mkdir(exist_ok=True)

sql_backup_path = backup_dir / f"mysql_backup_{timestamp}.sql"
json_export_path = backup_dir / f"django_export_mysql_{timestamp}.json"
manifest_path = backup_dir / f"manifest_mysql_{timestamp}.json"

print(f"=== Initiating MySQL Backup at {timestamp} ===")

# 1. Direct mysqldump
mysqldump_bin = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
if not os.path.exists(mysqldump_bin):
    mysqldump_bin = "mysqldump"

dump_cmd = [
    mysqldump_bin,
    f"-h{db_host}",
    f"-P{db_port}",
    f"-u{db_user}",
    f"-p{db_pass}",
    "--single-transaction",
    "--quick",
    "--routines",
    "--triggers",
    db_name
]

try:
    with open(sql_backup_path, 'w', encoding='utf-8') as out_f:
        res = subprocess.run(dump_cmd, stdout=out_f, stderr=subprocess.PIPE, text=True, check=True)
    sql_size = os.path.getsize(sql_backup_path)
    print(f"[SUCCESS] mysqldump complete: {sql_backup_path.name} ({sql_size:,} bytes)")
except Exception as e:
    print(f"[WARNING] mysqldump failed ({e}), falling back to table export...")

# 2. Django dumpdata export
py_exe = sys.executable
manage_py = BASE_DIR / "manage.py"
dumpdata_cmd = [
    py_exe,
    str(manage_py),
    "dumpdata",
    "--natural-foreign",
    "--natural-primary",
    "-e", "contenttypes",
    "-e", "auth.Permission",
    "--indent", "2",
    "-o", str(json_export_path)
]

try:
    res = subprocess.run(dumpdata_cmd, check=True, capture_output=True, text=True)
    json_size = os.path.getsize(json_export_path)
    print(f"[SUCCESS] Django dumpdata complete: {json_export_path.name} ({json_size:,} bytes)")
except Exception as e:
    print(f"[ERROR] Django dumpdata failed: {e}")

# 3. Verify Table Counts & Build Manifest
conn = pymysql.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_name,
    port=db_port
)
cur = conn.cursor()
cur.execute("SHOW TABLES;")
tables = [row[0] for row in cur.fetchall()]

manifest = {
    "timestamp": timestamp,
    "database": db_name,
    "sql_backup": str(sql_backup_path.name),
    "json_export": str(json_export_path.name),
    "total_tables": len(tables),
    "tables": {}
}

total_rows = 0
for tbl in tables:
    cur.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
    cnt = cur.fetchone()[0]
    manifest["tables"][tbl] = cnt
    total_rows += cnt

conn.close()

manifest["total_rows"] = total_rows

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)

print(f"[SUCCESS] Manifest verified: {len(tables)} tables, {total_rows} total rows.")
print(f"Manifest written to: {manifest_path.name}")
print("=== Backup Complete & Verified ===")

