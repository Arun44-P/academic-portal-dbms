# Frontend Development Roadmap & Task Specification (task.md)
### Project: Online Academic & Research Management Portal
**DBMS End-Semester Project**  
**Tech Stack**: HTML5, CSS3, JavaScript (ES6+), Django Template Engine, MySQL

---

## 💬 Briefing Prompt for Teammate (Copy & Paste to Your Friend)

> **Copy and send the message below to your teammate to get them up to speed instantly:**
>
> ---
>
> "Hey! Here is the complete context and architectural breakdown for our DBMS End-Semester Project (**Online Academic & Research Management Portal**).
> 
> ### 1. Tech Stack & Collaboration Split
> - **Backend & DB**: Python (Django), MySQL (InnoDB), achieving Boyce-Codd Normal Form (BCNF).
> - **Frontend & UI**: HTML5, CSS3, modern JavaScript, and Django Template Engine (`templates/` and `static/`).
> - You will be driving the UI and frontend templates. All your tasks, phase-by-phase checklists, and component specs are laid out in `task.md`.
>
> ### 2. The 4 User Roles & Views You Will Build
> 1. **Student Portal**: Course registration catalog, semester timetable, attendance tracking with color alerts (<75% warning), grade cards, and research assistantship tracker.
> 2. **Teacher (Faculty) Portal**:
>    - *Academic Wing*: Assigned course sections, lecture attendance logging grid, and assessment marks entry.
>    - *Research Wing*: Active research grants, research juniors roster (JRF/SRF/PhD), a **1-click monthly stipend approval table**, and publication submissions.
>    - *Faculty Specialization*: Teachers are categorized into **Permanent Faculty**, **Assistant Professors**, and **Visiting Professors** with different profile badges.
> 3. **Office Staff Portal**: Admissions, room scheduling, and the **Research Office Stipend Queue** (where office staff clears and logs bank disbursement for stipends approved by professors).
> 4. **Admin Portal**: Institute analytics, user directory, and the **Database Console & Danger Zone** (with a multi-step safeguard requiring typing the exact table name e.g. `DROP TABLE enrollments` + password re-entry + immutable logging before executing).
>
> ### 3. Key Architectural Decisions to Keep in Mind
> - **Table-per-Type (TPT) for Users**: One central login table (`user_accounts`), but distinct profile tables for Students, Teachers, Staff, and Admins to eliminate NULL anomalies.
> - **Separation of Duties in Stipends**: Professors approve research work $\to$ Office staff executes financial disbursement.
> - **Offerings vs Courses**: Courses are abstract; students enroll in semester sections (`course_offerings`).
>
> ### 4. Essential Reference Files in the Repo
> - `task.md`: Your complete step-by-step frontend roadmap, page specs, and Django integration tips.
> - `Architectural_Decisions_and_Why_We_Have_Taken_Them.md`: Explains every single database and architectural decision we made and why.
> - `schema.sql`: The fully normalized, production-grade MySQL schema with all tables, constraints, and views.
>
> Check out `task.md` and let's start with Phase 1 (Base layout, design tokens, and the unified login page)!"
>
> ---

---

## 1. Project Overview & Architecture

This project is a multi-role college academic portal. The backend is powered by **Django** connected to a **MySQL** database. Your goal is to build a responsive, modern, and accessible frontend using HTML, CSS, and vanilla JS (or CSS utilities) that integrates seamlessly with Django templates (`templates/` and `static/`).

### User Roles & Entry Points
1. **Student**: Course registration, attendance monitoring, grade cards, dues, research assistantship status.
2. **Teacher (Faculty)**: Course sections, student rosters, attendance logging, marks entry, and the **Research Wing** (grants, junior fellows, stipend approvals, publications).
3. **Office Staff**: Fee collection, course schedule publishing, and **stipend payment disbursement**.
4. **Administrator**: Institute analytics, user provisioning, and **Database Console with Danger Zone safeguards**.

---

## 2. Directory Structure Conventions

Organize your frontend assets and templates to mirror the Django app structure:

```
academic_portal/
├── static/
│   ├── css/
│   │   ├── main.css              # Global styles, variables, typography, reset
│   │   ├── components.css        # Cards, modals, tables, badges, buttons
│   │   ├── dashboard.css         # Sidebar, topbar, grid layouts
│   │   └── danger_zone.css       # Admin safeguard modal & security styles
│   ├── js/
│   │   ├── main.js               # Common UI logic (alerts, tooltips, sidebar toggle)
│   │   ├── danger_zone.js        # Admin confirmation challenge matching logic
│   │   └── attendance_grid.js    # Bulk attendance checklist helpers
│   └── img/
│       └── logo.svg              # Portal branding
└── templates/
    ├── base.html                 # Master layout (sidebar, topbar, flash messages)
    ├── accounts/
    │   └── login.html            # Unified login page
    ├── student/
    │   ├── dashboard.html        # Academic summary & alerts
    │   ├── courses.html          # Registration catalog & enrolled courses
    │   ├── attendance_grades.html# Attendance percentages & grade breakdown
    │   └── research_role.html    # Research junior status & stipend history
    ├── teacher/
    │   ├── dashboard.html        # Faculty overview
    │   ├── sections.html         # Allocated course sections
    │   ├── attendance_entry.html # Attendance marking grid
    │   ├── marks_entry.html      # Assessment components & student marks
    │   ├── research_projects.html# Grant details, budget, and co-PIs
    │   ├── research_juniors.html # JRF/SRF/PhD scholars & stipend approval
    │   └── publications.html     # Publication submission & portfolio
    ├── office/
    │   ├── dashboard.html        # Operations summary
    │   ├── stipend_queue.html    # PI-approved stipends ready for disbursement
    │   └── schedule.html         # Timetable & room allocations
    └── admin/
        ├── dashboard.html        # Institute KPIs & analytics
        ├── users.html            # User directory & role editor
        ├── database_console.html # Table schema inspector & runner
        └── audit_logs.html       # Immutable administrative activity trail
```

---

## 3. Design System & Style Guidelines

- **Primary Colors**: Deep Navy (`#0f172a`), Slate Blue (`#1e293b`), Primary Blue (`#2563eb`).
- **Accent Colors**: Emerald Green (`#10b981` for active/paid/approved), Amber (`#f59e0b` for pending/warning), Crimson (`#ef4444` for danger/absent/unpaid).
- **Backgrounds**: Light clean background (`#f8fafc`) with pure white card surfaces (`#ffffff`).
- **Typography**: System font stack or Inter (`font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`).
- **Components Needed**:
  - Stat Cards with icons, numeric KPI, and delta badges.
  - Data Tables with responsive scrolling, zebra striping, sticky headers, and action buttons.
  - Status Badges: `.badge-success`, `.badge-warning`, `.badge-danger`, `.badge-info`.
  - Accessible Forms: Floating labels, error messages (`.form-error`), help text.

---

## 4. Phase-by-Phase Task Checklist

### Phase 1: Core Layout, Design System & Authentication

- [ ] **Task 1.1: Design Tokens & CSS Reset (`static/css/main.css`)**
  - Define CSS custom variables: `--primary`, `--text-dark`, `--border-color`, `--shadow-sm`, etc.
  - Base typography, button styles (`.btn`, `.btn-primary`, `.btn-danger`, `.btn-outline`).
- [ ] **Task 1.2: Master Layout Template (`templates/base.html`)**
  - Responsive layout: Collapsible Sidebar (nav links change depending on user role), Topbar (user profile, role badge, logout button), Content Container.
  - Django message banner block (`{% for message in messages %}`).
- [ ] **Task 1.3: Unified Login Page (`templates/accounts/login.html`)**
  - Clean centered card with college branding.
  - Input fields: Username / Roll Number / Employee Code, Password.
  - Role pill indicator or automatic detection message.
  - CSRF protection (`{% csrf_token %}`) and error alert containers.

---

### Phase 2: Student Portal UI

- [ ] **Task 2.1: Student Dashboard (`templates/student/dashboard.html`)**
  - Top profile banner: Roll No, Program (e.g. B.Tech Computer Science), Semester, Status badge.
  - 4 KPI cards: Enrolled Courses count, Overall Attendance %, Semester Credits, Fee Due status.
  - Quick list of upcoming classes and recent grades.
- [ ] **Task 2.2: Course Catalog & Registration Page (`templates/student/courses.html`)**
  - Table of active semester course offerings (Course Code, Title, Credits, Instructor, Schedule).
  - "Register" button with disabled state if prerequisites are unmet or capacity is full.
  - Enrolled courses tab with "Drop" action modal.
- [ ] **Task 2.3: Attendance & Grade Cards (`templates/student/attendance_grades.html`)**
  - Course-wise attendance progress bars with color thresholds:
    - $\ge 75\%$: Green (`#10b981`)
    - $65\% - 74\%$: Amber (`#f59e0b`)
    - $< 65\%$: Red (`#ef4444`) with "Detention Risk" warning.
  - Component-wise marks breakdown (Midterm, Quizzes, Endterm) and calculated Letter Grade.
- [ ] **Task 2.4: Research Assistantship View (`templates/student/research_role.html`)**
  - Visible only if student is attached as a Research Junior.
  - Displays project title, supervising professor (PI), monthly stipend, and history of stipend payments.

---

### Phase 3: Teacher (Faculty) Portal UI

- [ ] **Task 3.1: Faculty Dashboard (`templates/teacher/dashboard.html`)**
  - Header showing Teacher Designation, Category Badge (`Permanent Faculty`, `Assistant Professor`, or `Visiting Professor`), and Department.
  - Quick metrics: Active Course Sections, Total Students Enrolled, Active Research Grants, Attached Juniors.
- [ ] **Task 3.2: Course Section & Attendance Logging (`templates/teacher/attendance_entry.html`)**
  - Dropdown to select course offering/section.
  - Date selector and "Topic Covered" input.
  - Student roster checklist with "Mark All Present" toggle and quick Absent toggles.
- [ ] **Task 3.3: Assessment & Grade Submission (`templates/teacher/marks_entry.html`)**
  - Matrix table to enter marks for Mid-Term, Quiz, and End-Term.
  - Client-side validation ensuring marks entered do not exceed `max_marks`.
  - "Save Draft" and "Finalize & Submit Grades" buttons.
- [ ] **Task 3.4: Research Wing — Projects Dashboard (`templates/teacher/research_projects.html`)**
  - Visual cards for all research grants: Grant code, funding agency (DST/SERB/DRDO), total grant amount, allocated stipend budget, project timeline.
  - Co-PIs list and project status tags (`ACTIVE`, `COMPLETED`).
- [ ] **Task 3.5: Research Wing — Juniors & Monthly Stipend Approval (`templates/teacher/research_juniors.html`)**
  - Table of junior fellows (JRF, SRF, PhD scholars, Student interns) under this professor's projects.
  - **Monthly Stipend Action Table**:
    - Columns: Fellow Name, Project, Month/Year, Stipend Amount, Status Badge.
    - Action: **"Approve Monthly Stipend"** button triggering confirmation modal.
    - Status changes from `Pending PI Approval` $\to$ `Approved by PI (Sent to Office)`.
- [ ] **Task 3.6: Research Wing — Publications Portfolio (`templates/teacher/publications.html`)**
  - Publication submission modal (Title, Journal/Conference, Date, DOI, Impact factor).
  - Clean filterable bibliographic list with DOI hyperlinks.

---

### Phase 4: Office Staff Portal UI

- [ ] **Task 4.1: Office Overview Dashboard (`templates/office/dashboard.html`)**
  - Metrics: Pending Admissions, Unpaid Student Dues, Pending Stipend Clearances.
- [ ] **Task 4.2: Research Office — Stipend Disbursement Queue (`templates/office/stipend_queue.html`)**
  - Queue displaying all stipends marked as `Approved by PI`.
  - Details: Junior Name, PI Professor Name, Grant Code, Amount.
  - Action button: **"Process Disbursement"**.
  - Modal with inputs: Payment Mode (Bank Transfer, Cheque, Online), Transaction Reference Number.
  - On submit: Status updates to `Processed / Disbursed`.
- [ ] **Task 4.3: Timetable & Room Allocation Screen (`templates/office/schedule.html`)**
  - Interactive grid showing classroom allocations and timetable clashes.

---

### Phase 5: Administrator Portal & Danger Zone Safeguards

- [ ] **Task 5.1: Admin Analytics Dashboard (`templates/admin/dashboard.html`)**
  - Institutional summary charts/cards:
    - Total Users breakdown (Students, Teachers, Staff).
    - Faculty breakdown (Permanent vs Assistant vs Visiting).
    - Total Research Funding Active across the University.
- [ ] **Task 5.2: User & Role Directory (`templates/admin/users.html`)**
  - Filterable user table with role badges and active/inactive status toggles.
  - "Add User" modal with dynamic sub-form depending on selected role (e.g., student requires roll no & program; permanent faculty requires PF number).
- [ ] **Task 5.3: Database Maintenance Console & Danger Zone (`templates/admin/database_console.html`)**
  - Table Browser: Displays all MySQL database tables, row counts, and storage size.
  - **The Danger Zone Component**:
    - Section styled with high-visibility red accent border and caution icons.
    - Buttons for radical operations: `Drop Table`, `Truncate Table`, `Purge Inactive Users`.
    - **Multi-Step Safeguard Modal (`static/js/danger_zone.js`)**:
      1. Explains irreversible data loss impact.
      2. Asks user to type the exact verification phrase (e.g. `DROP TABLE enrollments`).
      3. The "Execute Radical Action" button stays **strictly disabled** until the text matches character-for-character.
      4. Requires entering the Admin's login password.
      5. Mandatory "Reason for Action" textarea (for the audit log).
- [ ] **Task 5.4: Admin Audit Log Viewer (`templates/admin/audit_logs.html`)**
  - Immutable table displaying records from `admin_audit_logs`.
  - Columns: Timestamp, Admin Username, Action Type, Target Entity, Justification Reason, IP Address, Execution Status (`EXECUTED`, `BLOCKED`).

---

## 5. Django Template Integration Checklist for Frontend Dev

When writing the HTML templates, ensure you follow these Django conventions:

1. **CSRF Tokens**: Every `<form method="POST">` **must** include `{% csrf_token %}` immediately after the `<form>` opening tag.
2. **Dynamic URLs**: Use named URL tags instead of hardcoded paths:
   - `<a href="{% url 'accounts:login' %}">`
   - `<a href="{% url 'teacher:approve_stipend' disbursement.id %}">`
3. **Template Inheritance**:
   ```html
   {% extends "base.html" %}
   {% block title %}Course Registration | Academic Portal{% endblock %}
   {% block content %}
     <!-- Page HTML here -->
   {% endblock %}
   ```
4. **Conditional Role Rendering**:
   ```html
   {% if user.role == 'TEACHER' %}
     <!-- Show Research Wing & Sections links -->
   {% elif user.role == 'ADMIN' %}
     <!-- Show Database Console & Danger Zone -->
   {% endif %}
   ```
5. **Static Asset Loading**:
   Always load static files using `{% load static %}`:
   `<link rel="stylesheet" href="{% static 'css/main.css' %}">`

---

## 6. Definition of Done (DoD)

- [ ] All 4 user roles have distinct, styled dashboard views with clear navigation.
- [ ] The Teacher Research Wing displays Projects, Juniors, and the 1-click Stipend Approval workflow.
- [ ] The Office Staff Queue can view approved stipends and trigger disbursement modals.
- [ ] The Admin Danger Zone contains the live JavaScript challenge-response confirmation before any destructive action can be triggered.
- [ ] HTML is valid, responsive, and cleanly broken down into Django partials where appropriate.
