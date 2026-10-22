import os
import shutil
import datetime
import sqlite3
import json

os.makedirs('backups', exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f'backups/db_{timestamp}.sqlite3'

# 1. Physical copy of db.sqlite3
shutil.copy2('db.sqlite3', backup_path)
print(f"Preserved original SQLite file copied to: {backup_path}")

# 2. Verify integrity
conn = sqlite3.connect(backup_path)
cursor = conn.cursor()
cursor.execute("PRAGMA integrity_check;")
result = cursor.fetchone()
print(f"SQLite Integrity Check: {result[0]}")
assert result[0] == 'ok', "Integrity check failed!"

# 3. Check table count and size
cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
table_count = cursor.fetchone()[0]
size = os.path.getsize(backup_path)
print(f"Verified tables in backup: {table_count}")
print(f"Backup file size: {size} bytes")

# 4. Check row counts for key tables
key_tables = [
    'accounts_useraccount',
    'accounts_studentprofile',
    'accounts_instructorprofile',
    'academics_studentfeeaccount',
    'academics_feepayment',
    'academics_course',
    'academics_enrollment',
]
manifest = {
    'timestamp': timestamp,
    'backup_file': backup_path,
    'table_count': table_count,
    'file_size_bytes': size,
    'row_counts': {}
}
for t in key_tables:
    cursor.execute(f"SELECT count(*) FROM `{t}`;")
    cnt = cursor.fetchone()[0]
    manifest['row_counts'][t] = cnt
    print(f"  - {t}: {cnt} rows")

conn.close()

manifest_path = f'backups/manifest_{timestamp}.json'
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
print(f"Backup manifest saved to: {manifest_path}")

