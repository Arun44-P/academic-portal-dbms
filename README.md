# ACADEMIA — Online Academic & Research Management Portal
### DBMS End-Semester Capstone Project

A modern, responsive multi-role college academic portal and research management system built with **Python (Django 5)** and **MySQL 8.0/9.0+**, designed in strict compliance with **Boyce-Codd Normal Form (BCNF)**.

---

## 🏛️ System Features & Roles

1. **Student Portal**:
   - Course registration catalog and curriculum requirements (IIIT Bhopal model).
   - Real-time attendance percentage with detention risk indicator.
   - Comprehensive fee status breakdown (₹3.0 Lakh total, ₹2.0 Lakh paid, ₹1.0 Lakh balance).
   - Research fellowship affiliation tracking (JRF/SRF grant status).
2. **Faculty / Teacher Portal**:
   - *Academic Wing*: Assigned course sections, lecture schedules, interactive attendance logging, marks entry.
   - *Research Wing*: Active research grants, research junior fellows, **1-click monthly stipend approval workflow**, publications index.
   - *Faculty Specialization*: **Permanent Faculty** (Tenured, PF), **Assistant Professor** (Tenure-track), **Visiting Professor**.
3. **Office Staff Portal**: Operations dashboard, timetable scheduling, and the **Research Office Stipend Queue** for bank disbursement processing.
4. **Admin Portal**: Institute analytics, user directory, and the **Database Console & Danger Zone** (with multi-tier challenge verification and immutable audit logging).

---

## 🔑 Demo Login Credentials

The portal is pre-seeded with realistic institutional accounts for instant testing:

| Role | Username | Password | Full Name / Description |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `pass123` | Head Systems Administrator |
| **Faculty (HOD)** | `dr_sahu` | `pass123` | Dr. Yatendra Sahu (Permanent Professor, PI) |
| **Faculty** | `dr_chaurasia` | `pass123` | Dr. Rahul Chaurasia (Professor) |
| **Faculty** | `prof_neha` | `pass123` | Dr. Neha Kakkar (Assistant Professor) |
| **Office Staff** | `staff_sunita`| `pass123` | Staff Sunita (Research Office & Accounts) |
| **Student** | `atharv_pathak`| `pass123` | Atharv Pathak (Roll: 2024BCS001) |
| **Student** | `arun_patidar` | `pass123` | Arun Patidar (Roll: 2024BCS002) |
| **Student** | `prashast_mathur`| `pass123` | Prashast Mathur (Roll: 2024BCS003) |

---

## 🌐 Production Cloud Deployment (Render + Hosted SQL)

For complete deployment instructions with a persistent online SQL database (TiDB Cloud MySQL / PostgreSQL) and automatic continuous deployment from GitHub, see:

📖 **[DEPLOYMENT.md](DEPLOYMENT.md)**

### Quick Render Deployment:
1. Connect this GitHub repository to [Render](https://render.com/).
2. Select **Web Service**.
3. Set Build Command:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py seed_db && python manage.py collectstatic --no-input
   ```
4. Set Start Command:
   ```bash
   gunicorn academic_portal.wsgi:application
   ```
5. Add `DATABASE_URL` under Environment Variables pointing to your hosted cloud SQL instance.
6. Render builds and launches your portal with automatic HTTPS!

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.10+
- MySQL Server 8.0+ (Installed and running on port 3306)
- MySQL Workbench 8.0+ (For visual inspection)
- Git

### 2. Database Configuration (`.env`)
The portal connects to MySQL via environment variables configured in `.env` (git-ignored):
```env
DB_ENGINE=mysql
DB_NAME=academic_portal_db
DB_USER=academia_user
DB_PASSWORD=Academia_Pass#2026
DB_HOST=127.0.0.1
DB_PORT=3306
DB_SSL=false
```
*(To switch back to SQLite for offline testing, simply comment out `DB_ENGINE=mysql` in `.env`)*.

### 3. Setup Virtual Environment & Run Migrations
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
```

### 4. Launch the Web Application
```bash
python manage.py runserver 127.0.0.1:8000
```
Visit `http://127.0.0.1:8000/accounts/login/` in your browser.

---

## 🐬 Inspecting Database in MySQL Workbench

1. Launch **MySQL Workbench**.
2. Click your local connection (or connect as `academia_user` with password `Academia_Pass#2026` or `root`).
3. Under the **Schemas** tab in the left sidebar, double-click **`academic_portal_db`**.
4. Expand **Tables** to inspect all 31 tables.
5. Right-click any table (e.g. `academics_studentfeeaccount` or `accounts_studentprofile`) and choose **Select Rows - Limit 1000**.
6. To generate the **EER Diagram**:
   - Menu: **Database** &rarr; **Reverse Engineer...**
   - Select `academic_portal_db` &rarr; Click **Next** &rarr; **Execute**.
   - Workbench will generate the full visual relational diagram with all foreign keys.

---

## 📁 Key Project Files

- `DEPLOYMENT.md` — Complete production deployment and continuous deployment guide.
- `schema.sql` — MySQL 8.0+ DDL script with all tables, constraints, foreign keys, and views.
- `Architectural_Decisions_and_Why_We_Have_Taken_Them.md` — Formal BCNF normalization documentation.
- `Procfile` & `render.yaml` — Production cloud deployment definitions.
- `apps/` — Modular Django apps (`accounts`, `academics`, `research`, `core_admin`).
- `templates/` — Role-based responsive UI templates.
- `static/` — Modular CSS styling, vanilla ES6+ JavaScript, and institutional SVG branding.
