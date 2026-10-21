# ACADEMIA Portal — Production Deployment Guide

This guide provides end-to-end instructions for deploying the **Academic & Research Portal (ACADEMIA)** to the internet with an online SQL database, automatic continuous deployment via GitHub, and free SSL (HTTPS).

---

## 1. Architecture Overview

```
                      [ Incoming Web Traffic (HTTPS) ]
                                     │
                                     ▼
                      [ Render Edge Network / SSL ]
                     https://<your-app>.onrender.com
                                     │
                                     ▼
                    [ Gunicorn WSGI Web Process ]
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
  [ WhiteNoise Static Cache ]                     [ Django 5 Application ]
 (CSS, JS, Fonts, SVG Assets)                    (Auth, Academics, Research, Admin)
                                                             │
                                                             ▼
                                                [ Hosted Cloud SQL Database ]
                                                (TiDB Cloud / Aiven / Supabase)
```

- **Frontend**: Server-rendered HTML5, CSS3, Vanilla ES6+ JavaScript, served with WhiteNoise compression.
- **Backend**: Python 3.11 + Django 5 + Gunicorn WSGI.
- **Database**: Cloud-hosted MySQL 8.0 (or PostgreSQL) connected via encrypted `DATABASE_URL`.
- **Hosting**: Render Web Service connected directly to your GitHub repository.
- **CI/CD**: Automatic build, migration, seed, and deployment on every `git push origin main`.

---

## 2. Step 1: Create a Free Hosted SQL Database

For your DBMS college project, you need a true cloud-hosted SQL database. We recommend **TiDB Cloud Serverless** because it is **100% MySQL 8.0 wire-compatible, free forever (5 GB storage), requires zero credit card, and provides persistent storage**.

### Setting up TiDB Cloud (MySQL 8.0):
1. Go to [https://tidbcloud.com/](https://tidbcloud.com/) and click **Sign Up** (you can sign in with your GitHub account).
2. Click **Create Cluster** and choose **Serverless** (Free forever, $0/month).
3. Name your cluster (e.g., `academic-portal-db`) and select a region (e.g., `AWS / us-east-1` or `ap-southeast-1`).
4. Click **Create**.
5. Once created, click the **Connect** button on the cluster dashboard.
6. Under **Connect with**, choose **General** or **Django / Python**.
7. Note down your connection string:
   ```
   mysql://<username>:<password>@<host>:4000/<database_name>?ssl_mode=REQUIRED
   ```
   *(Ensure you save your database password in a safe place!)*

> **Alternative (PostgreSQL)**: If you prefer PostgreSQL, you can create a free database at [Supabase](https://supabase.com) or [Neon](https://neon.tech) and copy your `postgres://...` connection URL. The ACADEMIA backend automatically detects and supports both MySQL and PostgreSQL!

---

## 3. Step 2: Deploy to Render with Automatic GitHub Sync

1. Go to [https://render.com/](https://render.com/) and sign up or log in using your **GitHub account**.
2. From the Render Dashboard, click **New +** in the top navigation bar and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and click **Next**.
4. Select your ACADEMIA repository:
   - `https://github.com/Arun44-P/academic-portal-dbms.git`
5. Configure the web service with the following settings:
   - **Name**: `academic-portal-iiitbhopal` (or your preferred name)
   - **Region**: Choose the closest region (e.g., Singapore or Frankfurt or Oregon)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (root of repository)
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py migrate && python manage.py seed_db && python manage.py collectstatic --no-input
     ```
   - **Start Command**:
     ```bash
     gunicorn academic_portal.wsgi:application
     ```
   - **Plan**: Select **Free** ($0 / month).

---

## 4. Step 3: Configure Environment Variables in Render

Scroll down to the **Environment Variables** section on Render (or go to **Environment** in the service settings) and add the following keys:

| Key | Recommended Value | Purpose |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Pins Python version |
| `DEBUG` | `False` | Disables debug mode for security |
| `SECRET_KEY` | *(Click "Generate" or enter a 50+ character random string)* | Cryptographic security key |
| `DATABASE_URL` | `mysql://<user>:<password>@<host>:4000/<dbname>?ssl_mode=REQUIRED` | Your online SQL database URL |
| `DB_SSL` | `true` | Enforces encrypted SSL database connection |
| `ALLOWED_HOSTS` | `*` | Allows traffic to your Render URL |

Click **Create Web Service**.

---

## 5. Step 4: Verification and Live Deployment

Render will now:
1. Clone your GitHub repository.
2. Install Python packages from `requirements.txt` (Django, Gunicorn, WhiteNoise, PyMySQL, psycopg2).
3. Execute `python manage.py migrate` against your online SQL database (creating all BCNF normalized tables, foreign keys, and indexes).
4. Run `python manage.py seed_db` to load all IIIT Bhopal courses, professors, students, and demo accounts.
5. Collect and compress all static assets with WhiteNoise.
6. Launch Gunicorn.

When the deploy logs display:
```
==> Your service is live 🎉 at https://<your-service-name>.onrender.com
```

### Pre-Configured Test Credentials:

| Role | Username | Password | Full Name / Description |
|---|---|---|---|
| **Student** | `atharv_pathak` | `pass123` | Atharv Pathak (Roll: 2024BCS001) |
| **Student** | `arun_patidar` | `pass123` | Arun Patidar (Roll: 2024BCS002) |
| **Student** | `prashast_mathur`| `pass123` | Prashast Mathur (Roll: 2024BCS003) |
| **Faculty** | `dr_sahu` | `pass123` | Dr. Yatendra Sahu (HOD & Tenured PI) |
| **Faculty** | `dr_chaurasia` | `pass123` | Dr. Rahul Chaurasia (Professor) |
| **Faculty** | `prof_neha` | `pass123` | Dr. Neha Kakkar (Assistant Professor) |
| **Staff** | `staff_sunita` | `pass123` | Staff Sunita (Research Office Accounts) |
| **Admin** | `admin` | `pass123` | System Administrator (Full Access) |

---

## 6. How Automatic Deployment Works

Once connected:
1. You make code edits locally in VS Code or Antigravity.
2. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: your new feature"
   ```
3. Push to GitHub:
   ```bash
   git push origin main
   ```
4. Render receives the GitHub webhook and automatically starts a new build.
5. In ~2 minutes, your updated code is live on the internet at your public URL without any manual file uploads!

---

## 7. Troubleshooting & FAQ

### Q: Why does the first page load take ~30–50 seconds after inactivity?
**A**: Render's free tier spins down web services after 15 minutes of inactivity to save compute resources. As soon as a request arrives, Render automatically spins the container back up. Subsequent pages respond within milliseconds.

### Q: How do I view live application logs?
**A**: Go to your Render Dashboard -> select your Web Service -> click **Logs** in the left menu. You will see live Gunicorn request logs and any Python tracebacks.

### Q: How do I roll back a deployment?
**A**: In your Render Dashboard, click **Events** or **Deploys**. Find a previous successful deployment and click **Rollback to this deploy**.

### Q: Can I run raw SQL queries in production?
**A**: Yes! Log in as `admin`, navigate to **System Governance -> Database & Danger Zone**, and review table counts, schema structure, or execute radical actions protected by the three-tier challenge verification.

