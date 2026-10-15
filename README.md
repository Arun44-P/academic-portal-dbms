# Online Academic & Research Management Portal
### DBMS End-Semester Project

A college academic portal and research management system built with **Python (Django)** and **MySQL 8.0/9.0+**, designed in strict compliance with **Boyce-Codd Normal Form (BCNF)**.

---

## 🏛️ System Features & Roles

1. **Student Portal**: Course registration catalog, enrolled section schedule, attendance tracking, and research fellowship status.
2. **Faculty / Teacher Portal**:
   - *Academic Wing*: Assigned course sections, student rosters, attendance logging.
   - *Research Wing*: Active research grants, research juniors (JRF, SRF, PhD scholars), **1-click monthly stipend approval**, publications portfolio.
   - *Faculty Specialization*: **Permanent Faculty** (Tenured, PF), **Assistant Professor** (Tenure-track, mentored), **Visiting Professor** (Contractual, home institute).
3. **Office Staff Portal**: Admissions, room scheduling, and the **Research Office Stipend Queue** for bank disbursement processing.
4. **Admin Portal**: Institute analytics, user directory, and the **Database Console & Danger Zone** (with multi-step verification safeguards and immutable logging to `admin_audit_logs`).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- MySQL (Homebrew or system MySQL)

### 2. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Or: pip install django pymysql cryptography
```

### 3. Start Local Isolated MySQL Server
This project includes its own local, isolated MySQL server script (no password required, runs on port 3307):
```bash
./scripts/start_db.sh
```
*(To stop the database server later, run `./scripts/stop_db.sh`)*

### 4. Run Migrations & Seed Demo Data
```bash
python manage.py migrate
python manage.py seed_db
```

### 5. Launch the Web Application
```bash
python manage.py runserver 8000
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🔑 Demo Login Credentials

The `seed_db` command creates realistic accounts for testing:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access & Danger Zone Console |
| **Permanent Prof** | `dr_sharma` | `pass123` | Tenured HOD, PI on ₹45 Lakh DST grant |
| **Assistant Prof** | `prof_neha` | `pass123` | Tenure-track, mentored by Dr. Sharma |
| **Visiting Prof** | `prof_alok` | `pass123` | Visiting professor from IIT Delhi |
| **Office Staff** | `staff_sunita`| `pass123` | Research Office & Accounts Superintendent |
| **Student** | `student_arjun`| `pass123` | Enrolled in CS301/CS302 & JRF fellow |

---

## 🌐 Cloud Deployment (Render / Railway)

This repository includes production configs (`Procfile`, `render.yaml`, `runtime.txt`, `whitenoise` static serving):

### 1-Click / Git Deployment on Render:
1. Connect this GitHub repository on [Render](https://render.com/).
2. Select **Web Service** or use the included `render.yaml` Blueprint.
3. Build Command: `pip install -r requirements.txt && python manage.py migrate && python manage.py seed_db && python manage.py collectstatic --no-input`
4. Start Command: `gunicorn academic_portal.wsgi:application`
5. The portal will launch online with seeded accounts and static assets handled via WhiteNoise!

---

## 📁 Key Files & Documentation

- `task.md` — Frontend development roadmap, page specs, and teammate briefing prompt.
- `Architectural_Decisions_and_Why_We_Have_Taken_Them.md` — Detailed documentation of normalization (1NF → BCNF) and architectural decisions.
- `schema.sql` — MySQL DDL script with all table definitions, constraints, foreign keys, and views.
- `scripts/` — Helper scripts to start, stop, seed, and run test verification suites.
- `Procfile` & `render.yaml` — Production cloud deployment definitions.
