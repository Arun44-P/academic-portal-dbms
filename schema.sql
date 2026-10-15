-- ============================================================================
-- DBMS End-Semester Project: Online Academic & Research Portal
-- Target Database: MySQL 8.0+
-- Normalization Level: Boyce-Codd Normal Form (BCNF)
-- ============================================================================

DROP DATABASE IF EXISTS academic_portal_db;
CREATE DATABASE academic_portal_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;
USE academic_portal_db;

-- ============================================================================
-- 1. AUTHENTICATION & MULTI-ROLE SPECIALIZATION
-- ============================================================================

CREATE TABLE user_accounts (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    role ENUM('ADMIN', 'TEACHER', 'OFFICE_STAFF', 'STUDENT') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE admins (
    admin_id INT PRIMARY KEY,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    designation VARCHAR(50) DEFAULT 'System Administrator',
    is_superadmin BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (admin_id) REFERENCES user_accounts(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE office_staff (
    staff_id INT PRIMARY KEY,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    section ENUM('ACCOUNTS', 'ADMISSIONS', 'EXAMINATIONS', 'RESEARCH_OFFICE', 'GENERAL_ADMIN') NOT NULL,
    designation VARCHAR(50) NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES user_accounts(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    established_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================================
-- 2. INSTRUCTORS & THREE-TIER FACULTY SPECIALIZATION
-- ============================================================================

CREATE TABLE instructors (
    instructor_id INT PRIMARY KEY,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    department_id INT NOT NULL,
    faculty_category ENUM('PERMANENT', 'ASSISTANT_PROFESSOR', 'VISITING') NOT NULL,
    designation VARCHAR(60) NOT NULL,
    highest_qualification VARCHAR(100) NOT NULL,
    hire_date DATE NOT NULL,
    office_room VARCHAR(30),
    FOREIGN KEY (instructor_id) REFERENCES user_accounts(user_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Subtype 1: Permanent / Tenured Faculty
CREATE TABLE permanent_faculty (
    instructor_id INT PRIMARY KEY,
    tenure_status ENUM('TENURED', 'EMERITUS') NOT NULL DEFAULT 'TENURED',
    provident_fund_no VARCHAR(50) NOT NULL UNIQUE,
    pension_eligible BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Subtype 2: Assistant Professors (Tenure-Track)
CREATE TABLE assistant_professors (
    instructor_id INT PRIMARY KEY,
    probation_end_date DATE NOT NULL,
    tenure_review_date DATE NOT NULL,
    mentor_instructor_id INT,
    publication_quota INT NOT NULL DEFAULT 3,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE CASCADE,
    FOREIGN KEY (mentor_instructor_id) REFERENCES instructors(instructor_id) ON DELETE SET NULL,
    CHECK (mentor_instructor_id <> instructor_id)
) ENGINE=InnoDB;

-- Subtype 3: Visiting Professors (Contractual)
CREATE TABLE visiting_professors (
    instructor_id INT PRIMARY KEY,
    home_institution VARCHAR(150) NOT NULL,
    contract_start_date DATE NOT NULL,
    contract_end_date DATE NOT NULL,
    honorarium_per_month DECIMAL(10, 2) NOT NULL,
    max_weekly_lecture_hours INT NOT NULL DEFAULT 8,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE CASCADE,
    CHECK (contract_end_date > contract_start_date)
) ENGINE=InnoDB;

-- ============================================================================
-- 3. STUDENTS, COURSES & OFFERINGS
-- ============================================================================

CREATE TABLE programs (
    program_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    degree_level ENUM('UNDERGRADUATE', 'POSTGRADUATE', 'DOCTORAL') NOT NULL,
    duration_years INT NOT NULL,
    total_semesters INT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT,
    UNIQUE KEY uq_dept_program (department_id, name)
) ENGINE=InnoDB;

CREATE TABLE students (
    student_id INT PRIMARY KEY,
    roll_number VARCHAR(30) NOT NULL UNIQUE,
    registration_number VARCHAR(30) NOT NULL UNIQUE,
    program_id INT NOT NULL,
    current_semester INT NOT NULL DEFAULT 1,
    admission_date DATE NOT NULL,
    status ENUM('ACTIVE', 'SUSPENDED', 'ALUMNI', 'WITHDRAWN') DEFAULT 'ACTIVE',
    FOREIGN KEY (student_id) REFERENCES user_accounts(user_id) ON DELETE CASCADE,
    FOREIGN KEY (program_id) REFERENCES programs(program_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(15) NOT NULL UNIQUE,
    title VARCHAR(120) NOT NULL,
    credits INT NOT NULL,
    lecture_hours INT NOT NULL DEFAULT 3,
    lab_hours INT NOT NULL DEFAULT 0,
    department_id INT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE academic_semesters (
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    term ENUM('FALL', 'SPRING', 'SUMMER') NOT NULL,
    academic_year VARCHAR(9) NOT NULL, -- e.g. '2026-2027'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    UNIQUE KEY uq_term_year (term, academic_year)
) ENGINE=InnoDB;

CREATE TABLE course_offerings (
    offering_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester_id INT NOT NULL,
    instructor_id INT NOT NULL,
    section_name VARCHAR(10) NOT NULL,
    max_capacity INT NOT NULL DEFAULT 60,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE RESTRICT,
    FOREIGN KEY (semester_id) REFERENCES academic_semesters(semester_id) ON DELETE RESTRICT,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE RESTRICT,
    UNIQUE KEY uq_course_sem_section (course_id, semester_id, section_name)
) ENGINE=InnoDB;

CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    offering_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('ENROLLED', 'DROPPED', 'COMPLETED') DEFAULT 'ENROLLED',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id) ON DELETE RESTRICT,
    UNIQUE KEY uq_student_offering (student_id, offering_id)
) ENGINE=InnoDB;

-- ============================================================================
-- 4. RESEARCH WING (PROJECTS, JUNIORS, STIPENDS, PUBLICATIONS)
-- ============================================================================

CREATE TABLE research_projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_code VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    pi_instructor_id INT NOT NULL,
    funding_agency VARCHAR(150) NOT NULL,
    total_grant_amount DECIMAL(12, 2) NOT NULL,
    allocated_stipend_budget DECIMAL(12, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('PROPOSED', 'ACTIVE', 'COMPLETED', 'TERMINATED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pi_instructor_id) REFERENCES instructors(instructor_id) ON DELETE RESTRICT,
    CHECK (allocated_stipend_budget <= total_grant_amount),
    CHECK (end_date > start_date)
) ENGINE=InnoDB;

CREATE TABLE project_co_investigators (
    project_id INT NOT NULL,
    instructor_id INT NOT NULL,
    role_description VARCHAR(100) DEFAULT 'Co-Principal Investigator',
    PRIMARY KEY (project_id, instructor_id),
    FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE research_juniors (
    junior_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    student_id INT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    cadre ENUM('JRF', 'SRF', 'PROJECT_ASSOCIATE', 'PHD_FELLOW', 'STUDENT_INTERN') NOT NULL,
    monthly_stipend DECIMAL(10, 2) NOT NULL,
    appointment_start_date DATE NOT NULL,
    appointment_end_date DATE NOT NULL,
    status ENUM('ACTIVE', 'RELIEVED', 'TERMINATED') NOT NULL DEFAULT 'ACTIVE',
    FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON DELETE RESTRICT,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE SET NULL,
    CHECK (appointment_end_date >= appointment_start_date)
) ENGINE=InnoDB;

CREATE TABLE stipend_disbursements (
    disbursement_id INT AUTO_INCREMENT PRIMARY KEY,
    junior_id INT NOT NULL,
    disbursement_month TINYINT NOT NULL,
    disbursement_year SMALLINT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    pi_approved BOOLEAN NOT NULL DEFAULT FALSE,
    pi_approval_date DATE NULL,
    office_processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_by_staff_id INT NULL,
    payment_status ENUM('PENDING_PI_APPROVAL', 'APPROVED_BY_PI', 'PROCESSED', 'REJECTED') NOT NULL DEFAULT 'PENDING_PI_APPROVAL',
    transaction_reference VARCHAR(100) UNIQUE NULL,
    disbursed_at TIMESTAMP NULL,
    FOREIGN KEY (junior_id) REFERENCES research_juniors(junior_id) ON DELETE RESTRICT,
    FOREIGN KEY (processed_by_staff_id) REFERENCES office_staff(staff_id) ON DELETE SET NULL,
    UNIQUE KEY uq_junior_month_year (junior_id, disbursement_month, disbursement_year),
    CHECK (disbursement_month BETWEEN 1 AND 12)
) ENGINE=InnoDB;

CREATE TABLE research_publications (
    publication_id INT AUTO_INCREMENT PRIMARY KEY,
    instructor_id INT NOT NULL,
    project_id INT NULL,
    title VARCHAR(255) NOT NULL,
    venue_name VARCHAR(200) NOT NULL,
    publication_type ENUM('JOURNAL', 'CONFERENCE', 'PATENT', 'BOOK_CHAPTER') NOT NULL,
    publication_date DATE NOT NULL,
    doi_or_url VARCHAR(255),
    impact_factor DECIMAL(5, 2) DEFAULT 0.00,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES research_projects(project_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================================
-- 5. ADMIN AUDIT & RADICAL DECISION LOGGING
-- ============================================================================

CREATE TABLE admin_audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action_type ENUM(
        'DROP_TABLE',
        'TRUNCATE_TABLE',
        'BULK_DELETE',
        'ALTER_SCHEMA',
        'RAW_SQL_EXECUTE',
        'USER_ROLE_OVERRIDE'
    ) NOT NULL,
    target_entity VARCHAR(100) NOT NULL,
    query_or_command TEXT NOT NULL,
    justification_reason VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    status ENUM('ATTEMPTED', 'EXECUTED', 'REJECTED_BAD_CONFIRMATION', 'FAILED') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ============================================================================
-- 6. SPECIALIZED VIEWS FOR THE 4 USER ROLES
-- ============================================================================

-- 1. Admin Analytics View
CREATE OR REPLACE VIEW view_admin_overview AS
SELECT 
    (SELECT COUNT(*) FROM user_accounts WHERE is_active = TRUE) AS total_active_users,
    (SELECT COUNT(*) FROM students WHERE status = 'ACTIVE') AS active_students,
    (SELECT COUNT(*) FROM instructors) AS total_instructors,
    (SELECT COUNT(*) FROM permanent_faculty) AS permanent_faculty_count,
    (SELECT COUNT(*) FROM assistant_professors) AS assistant_professors_count,
    (SELECT COUNT(*) FROM visiting_professors) AS visiting_professors_count,
    (SELECT COUNT(*) FROM research_projects WHERE status = 'ACTIVE') AS active_research_projects,
    (SELECT COALESCE(SUM(total_grant_amount), 0) FROM research_projects) AS total_research_grants;

-- 2. Instructor Academic & Research View
CREATE OR REPLACE VIEW view_instructor_dashboard AS
SELECT 
    i.instructor_id,
    u.first_name,
    u.last_name,
    i.faculty_category,
    co.offering_id,
    c.course_code,
    c.title AS course_title,
    co.section_name,
    COUNT(e.enrollment_id) AS enrolled_students_count,
    (SELECT COUNT(*) FROM research_projects rp WHERE rp.pi_instructor_id = i.instructor_id AND rp.status = 'ACTIVE') AS my_active_projects,
    (SELECT COUNT(*) FROM research_juniors rj JOIN research_projects rp ON rj.project_id = rp.project_id WHERE rp.pi_instructor_id = i.instructor_id AND rj.status = 'ACTIVE') AS my_research_juniors
FROM instructors i
JOIN user_accounts u ON i.instructor_id = u.user_id
LEFT JOIN course_offerings co ON i.instructor_id = co.instructor_id
LEFT JOIN courses c ON co.course_id = c.course_id
LEFT JOIN enrollments e ON co.offering_id = e.offering_id
GROUP BY i.instructor_id, co.offering_id, c.course_code, c.title, co.section_name;

-- 3. Office Employee View: Stipend Processing Queue
CREATE OR REPLACE VIEW view_office_stipend_queue AS
SELECT 
    sd.disbursement_id,
    sd.disbursement_month,
    sd.disbursement_year,
    sd.amount,
    sd.payment_status,
    rj.full_name AS junior_name,
    rj.cadre,
    rp.project_code,
    rp.title AS project_title,
    u_pi.last_name AS pi_professor_name,
    sd.pi_approved,
    sd.pi_approval_date
FROM stipend_disbursements sd
JOIN research_juniors rj ON sd.junior_id = rj.junior_id
JOIN research_projects rp ON rj.project_id = rp.project_id
JOIN instructors pi ON rp.pi_instructor_id = pi.instructor_id
JOIN user_accounts u_pi ON pi.instructor_id = u_pi.user_id
WHERE sd.payment_status = 'APPROVED_BY_PI';

-- 4. Student Academic Portal View
CREATE OR REPLACE VIEW view_student_portal AS
SELECT 
    s.student_id,
    s.roll_number,
    p.name AS program_name,
    s.current_semester,
    c.course_code,
    c.title AS course_title,
    c.credits,
    co.section_name,
    u_prof.last_name AS instructor_name,
    e.status AS enrollment_status
FROM students s
JOIN programs p ON s.program_id = p.program_id
JOIN enrollments e ON s.student_id = e.student_id
JOIN course_offerings co ON e.offering_id = co.offering_id
JOIN courses c ON co.course_id = c.course_id
JOIN instructors i ON co.instructor_id = i.instructor_id
JOIN user_accounts u_prof ON i.instructor_id = u_prof.user_id;
