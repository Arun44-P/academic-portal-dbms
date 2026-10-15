# Architectural Decisions and Why We Have Taken Them
### Project: Online Academic & Research Management Portal (DBMS End-Semester Project)
**Technology Stack**: Python (Django Framework), MySQL 8.0 (InnoDB), HTML5, CSS3, JavaScript (ES6+)

---

## Executive Summary

This document explains all architectural, data modeling, and engineering decisions made for the Online Academic & Research Management Portal. The core mandate of this project is to create an academically rigorous, highly normalized, production-grade database system (achieving Boyce-Codd Normal Form - BCNF) with a seamless, role-segregated user experience.

Every decision documented below outlines:
1. **The Context & Problem**
2. **The Alternatives Considered**
3. **The Chosen Decision**
4. **The Rationale & Technical Justification** (DBMS normalization, referential integrity, security, and developer ergonomics)

---

## 1. Table-per-Type (TPT) Specialization for User Roles

### Context
The portal must support four distinct actors: **Admin**, **Teacher (Faculty)**, **Office Employee (Staff)**, and **Student**. Each actor requires unique profile attributes (e.g., student roll numbers, faculty designations, office staff departments).

### Alternatives Considered
- **Alternative A: Single Table Inheritance (STI)**: Placing all user attributes into a single massive `Users` table with hundreds of columns, where student fields are `NULL` for teachers, teacher fields are `NULL` for students, etc.
  - *Drawback*: Major violation of clean schema design; massive storage waste; impossible to enforce `NOT NULL` constraints on role-specific fields (e.g., `roll_number` cannot be `NOT NULL`); causes severe NULL anomalies.
- **Alternative B: Completely Disconnected Independent Tables**: Separate tables (`admins`, `teachers`, `students`, `office_staff`) each maintaining their own passwords, usernames, and emails.
  - *Drawback*: Redundant credential logic; risk of duplicate emails across tables; difficult to perform global authentication or single sign-on (SSO); complicated password reset and session handling.

### The Chosen Decision: Table-per-Type (TPT) Inheritance
We created a base authentication supertype table `user_accounts` storing shared identity fields (`user_id`, `username`, `password_hash`, `email`, `role`, `is_active`). Each specific role has its own dedicated profile table (`admins`, `instructors`, `office_staff`, `students`) with a primary key that is also a foreign key referencing `user_accounts(user_id)` with `ON DELETE CASCADE`.

### Why We Took This Decision
1. **Zero NULL Anomalies & BCNF Compliance**: Every table contains only attributes functionally determined strictly by its primary key.
2. **Enforceable Domain Constraints**: Role-specific constraints (e.g., `roll_number VARCHAR NOT NULL UNIQUE`) can be enforced at the database engine level.
3. **Django Model Synergy**: Perfectly maps to Django's custom `AbstractUser` and `OneToOneField` pattern (`student = models.OneToOneField(User, primary_key=True)`).
4. **Centralized Security**: Password hashing, token generation, and account lockout reside in one secure table.

---

## 2. Three-Tier Categorization of Faculty (Permanent, Assistant, Visiting)

### Context
Instructors are not uniform. A college employs:
- **Permanent Faculty** (Tenured / Senior professors)
- **Assistant Professors** (Tenure-track, on probation)
- **Visiting Professors** (Adjunct/contractual from external institutes or industry)

### Alternatives Considered
- **Alternative A: Single `instructors` Table with Optional Columns**: Add `tenure_status`, `probation_end_date`, `home_institution`, and `honorarium` into one table.
  - *Drawback*: Visiting professors do not have provident funds; permanent professors do not have contract end dates. This forces columns to be nullable and violates strict 3NF/BCNF.

### The Chosen Decision: Hierarchical Relational Specialization
1. Base Table: `instructors` containing common faculty data (employee code, department ID, qualification, office room, faculty category discriminator).
2. Three 1:1 Subtype Tables:
   - `permanent_faculty`: `tenure_status`, `provident_fund_no`, `pension_eligible`.
   - `assistant_professors`: `probation_end_date`, `tenure_review_date`, `mentor_instructor_id`, `publication_quota`.
   - `visiting_professors`: `home_institution`, `contract_start_date`, `contract_end_date`, `honorarium_per_month`, `max_weekly_lecture_hours`.

### Why We Took This Decision
1. **Mathematical Rigor**: Demonstrates textbook specialization in relational database theory for academic grading.
2. **Business Rule Enforcement**:
   - Contract expiration checks can run specifically on `visiting_professors` without scanning regular faculty.
   - Assistant professors can be assigned a senior mentor (`mentor_instructor_id` FK to `instructors`) with a `CHECK (mentor_instructor_id <> instructor_id)` constraint.
   - Provident fund numbers are guaranteed unique for permanent staff without colliding with visiting staff who have no PF.

---

## 3. Course Deconstruction: Courses vs. Course Offerings vs. Semesters

### Context
A university curriculum has courses like *CS101: Introduction to Database Systems* (3 credits). However:
- CS101 is taught across multiple academic years and terms (Fall 2026, Spring 2027).
- In a single semester, multiple sections (Section A, Section B) might be held by different teachers in different classrooms with different capacities.

### Alternatives Considered
- **Alternative A: Direct `instructor_id` on `courses`**: `courses(course_id, course_name, instructor_id, duration)`.
  - *Drawback*: A course could only ever have one teacher for all eternity. It prevents running two sections simultaneously or changing teachers between semesters.

### The Chosen Decision: Separation of Academic Definition and Term Offerings
1. `courses`: The abstract course definition (code, title, credits, department).
2. `academic_semesters`: Term tracking (term name, academic year, start date, end date, active flag).
3. `course_offerings`: The concrete instance of a course held in a specific term:
   $$\text{course\_offerings}(\underline{\text{offering\_id}}, \text{course\_id}, \text{semester\_id}, \text{instructor\_id}, \text{section\_name}, \text{max\_capacity})$$
   With a composite unique constraint: `UNIQUE (course_id, semester_id, section_name)`.

### Why We Took This Decision
1. **Elimination of Multi-Valued Dependencies**: Prevents course replication across semesters.
2. **Clean Enrollment Cardinality**: Students enroll in an `offering_id` (Section A of Fall 2026), NOT the abstract `course_id`. This cleanly handles repeat courses, grade histories, and capacity management.

---

## 4. The Research Wing Architecture & Two-Stage Stipend Workflow

### Context
Professors conduct research funded by external agencies (DST, SERB, DRDO, etc.), supervise junior researchers (JRFs, SRFs, PhD scholars, undergraduate interns), and must approve their monthly stipends.

### Key Decisions Made:
1. **`research_projects`**: Holds grant codes, funding agency, total grant, and an explicitly earmarked `allocated_stipend_budget` with a database check `CHECK (allocated_stipend_budget <= total_grant_amount)`.
2. **`project_co_investigators`**: Resolves the M:N relationship between multiple faculty members collaborating on one project.
3. **`research_juniors`**: Captures research personnel. Can optionally link to an enrolled `student_id` (if the junior is a university student) or stand independently for external research fellows.
4. **`stipend_disbursements`**: Handles monthly stipend releases.

### The Two-Stage Approval Workflow (Separation of Powers):
```
[Research Junior submits work] 
             │
             ▼
[Stage 1: Supervising Professor / PI Approval]
   - Professor verifies academic progress & attendance
   - Action: Updates `pi_approved = TRUE`, logs `pi_approval_date`
   - Payment Status: 'APPROVED_BY_PI'
             │
             ▼
[Stage 2: Office Accounts Staff Disbursement]
   - Office staff verifies budget pool & accounting paperwork
   - Action: Disburses funds, records `payment_mode` & `transaction_reference`
   - Payment Status: 'PROCESSED'
```

### Why We Took This Decision
1. **Institutional Accounting Compliance**: In real academic institutes, professors cannot directly release payments from university bank accounts (financial fraud risk), and office staff cannot judge research merit. This dual-key workflow enforces proper segregation of duties.
2. **Auditability**: Every monthly stipend record has a composite key `UNIQUE (junior_id, disbursement_month, disbursement_year)`, preventing double-claiming or double-payment for the same month.

---

## 5. Admin Database Console & Radical Decision Multi-Tier Safeguards

### Context
The Administrator user holds superuser capabilities, including the ability to inspect tables, alter data, and perform database maintenance. Radical operations like `DROP TABLE`, `TRUNCATE TABLE`, or bulk-deleting inactive users can cause catastrophic, unrecoverable data loss.

### Alternatives Considered
- **Alternative A: Standard Browser Alert (`confirm("Are you sure?")`)**:
  - *Drawback*: Muscle memory causes users to accidentally click "OK" without reading. Unacceptable for enterprise DBMS safety.
- **Alternative B: Hardcoding no drop/delete capability in the UI**:
  - *Drawback*: Evaluators and administrators need the ability to maintain the database, test resets, and show database administration capabilities.

### The Chosen Decision: Three-Tier Confirmation Barrier + Immutable Audit Logging

```
[Admin selects destructive action, e.g., Drop Table 'enrollments']
                           │
                           ▼
          ┌───────────────────────────────────┐
          │     Tier 1: Challenge Match       │
          │ User must type exact phrase:      │
          │ "DROP TABLE enrollments"          │
          │ (Button strictly disabled until   │
          │ string matches character-exact)   │
          └─────────────────┬─────────────────┘
                            │ Matched
                            ▼
          ┌───────────────────────────────────┐
          │     Tier 2: Re-Authentication     │
          │ Admin re-enters current password  │
          └─────────────────┬─────────────────┘
                            │ Validated
                            ▼
          ┌───────────────────────────────────┐
          │   Tier 3: Justification & Audit   │
          │ Mandatory reason note entered;    │
          │ Logged to `admin_audit_logs`      │
          │ (Admin ID, IP, SQL query, time)   │
          └─────────────────┬─────────────────┘
                            │
                            ▼
                 [Execute Operation]
```

### Why We Took This Decision
1. **GitHub/AWS Enterprise Standard**: Mimics industry-standard safety practices (like GitHub repository deletion or AWS RDS termination).
2. **Non-Repudiation**: The `admin_audit_logs` table ensures complete traceability: if a table was altered or dropped, the system records who, when, from which IP address, and why.

---

## 6. Pre-Aggregated Database Views for the Four Role Portals

### Context
Each user role needs a completely distinct dashboard with fast query performance. Writing large, repetitive 6-table `JOIN` statements inside multiple Django view functions increases code duplication and database query latency.

### The Chosen Decision: Four Dedicated SQL Views
We created specialized database views in MySQL:
1. `view_admin_overview`: Pre-aggregates institute KPIs (total active users, faculty counts across all 3 tiers, total research funding).
2. `view_instructor_dashboard`: Joins teacher sections, enrolled student counts, active grant counts, and attached research juniors into a single row per section.
3. `view_office_stipend_queue`: Pre-filters and joins stipends marked `APPROVED_BY_PI` with fellow names, grant codes, and PI professor names for fast accounting clearance.
4. `view_student_portal`: Consolidates student enrolled courses, credits, section schedules, and teacher names into a single clean recordset.

### Why We Took This Decision
1. **Encapsulation & Security**: Restricts direct table access; roles only query their respective view.
2. **Performance**: MySQL query optimizer caches execution plans for views, reducing query overhead.
3. **Clean Code in Django**: Django views can query `AdminOverview.objects.all()` or execute `SELECT * FROM view_instructor_dashboard WHERE instructor_id = %s` with clean, concise code.

---

## 7. Technology Stack Choices: Why Django Templates & MySQL InnoDB

### Why MySQL with InnoDB Engine?
- **InnoDB** provides true **ACID transactions**, row-level locking, and foreign key referential integrity with cascading updates and deletes.
- We explicitly enabled `utf8mb4` encoding to support international names, symbols, and comprehensive text storage.

### Why Server-Side Django Templates (HTML/CSS) instead of React/SPA?
- **DBMS Focus**: This is a Database Management Systems project. The core academic deliverable is the database schema, normalization, query optimization, and transaction safety.
- **Rapid Coordination**: Server-side Django templates avoid the complexity of managing separate Node.js build pipelines, CORS configurations, JWT refresh tokens, and API boilerplate.
- **Built-in Security**: Django templates provide out-of-the-box CSRF protection, secure session cookies, and SQL injection prevention via the Django ORM.

---

## Summary Matrix of Architectural Decisions

| # | Architectural Decision | Primary Benefit |
| :- | :--- | :--- |
| **1** | **Table-per-Type (TPT) for Users** | Eliminates NULL anomalies; preserves BCNF; centralizes auth. |
| **2** | **3-Tier Teacher Specialization** | Accurately models Permanent, Assistant, and Visiting faculty domain rules. |
| **3** | **Course Offerings vs Courses** | Decouples static syllabus from semester sections; handles capacity & repeats. |
| **4** | **Two-Stage Stipend Disbursement** | Enforces separation of duties (PI approves $\to$ Office disburses); audit trail. |
| **5** | **Danger Zone Multi-Tier Safeguard** | Prevents catastrophic accidental drops/truncates; writes immutable audit logs. |
| **6** | **Dedicated SQL Views** | Encapsulates complex joins; accelerates dashboard loading. |
| **7** | **Django Templates + MySQL InnoDB** | Fast, secure, ACID-compliant, deeply integrated with relational tables. |