"""
Patch templates to support both FACULTY and TEACHER
"""
from pathlib import Path

# 1. Base.html
with open('templates/base.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("{% elif user.role == 'TEACHER' %}", "{% elif user.role == 'TEACHER' or user.role == 'FACULTY' or user.is_faculty %}")
c = c.replace("elif user.role == 'TEACHER' %}{% url 'teacher:dashboard'", "elif user.role == 'TEACHER' or user.role == 'FACULTY' or user.is_faculty %}{% url 'teacher:dashboard'")
c = c.replace("user.role == 'TEACHER' and 'Dr.' not in", "(user.role == 'TEACHER' or user.role == 'FACULTY' or user.is_faculty) and 'Dr.' not in")

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("base.html patched successfully!")

# 2. Dashboard.html
with open('templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("?role=TEACHER", "?role=FACULTY")
c = c.replace("<code>TEACHER</code>", "<code>FACULTY</code>")
c = c.replace("{{ metrics.role_counts.TEACHER }} ({{ metrics.role_pct.TEACHER }}%)", "{{ metrics.role_counts.FACULTY|default:metrics.role_counts.TEACHER }} ({{ metrics.role_pct.FACULTY|default:metrics.role_pct.TEACHER }}%)")
c = c.replace("style=\"width: {{ metrics.role_pct.TEACHER }}%;\"", "style=\"width: {{ metrics.role_pct.FACULTY|default:metrics.role_pct.TEACHER }}%;\"")

with open('templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("dashboard.html patched successfully!")

# 3. Users.html
with open('templates/admin/users.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("<option value=\"TEACHER\">Faculty &amp; Instructors</option>", "<option value=\"FACULTY\">Faculty &amp; Instructors</option>\n      <option value=\"TEACHER\" style=\"display:none;\">Teacher (Legacy)</option>")
c = c.replace("elif u.role == 'TEACHER' %}", "elif u.role == 'TEACHER' or u.role == 'FACULTY' %}")
c = c.replace("elif u.role == 'TEACHER' and u.instructor_profile %}", "elif (u.role == 'TEACHER' or u.role == 'FACULTY') and u.instructor_profile %}")
c = c.replace("u.office_profile", "u.staff_profile")

with open('templates/admin/users.html', 'w', encoding='utf-8') as f:
    f.write(c)
print("users.html patched successfully!")
