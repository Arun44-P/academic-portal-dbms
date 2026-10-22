"""
Fix template tags in base.html to use UserAccount helper properties
"""
with open('templates/base.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace line 32
c = c.replace(
    """<a href="{% if user.role == 'STUDENT' %}{% url 'student:dashboard' %}{% elif user.role == 'TEACHER' or user.role == 'FACULTY' or user.is_faculty %}{% url 'teacher:dashboard' %}{% elif user.role == 'OFFICE' or user.role == 'OFFICE_STAFF' %}{% url 'office:dashboard' %}{% elif user.role == 'ADMIN' %}{% url 'core_admin:dashboard' %}{% else %}#{% endif %}" class="sidebar-brand">""",
    """<a href="{% if user.is_student %}{% url 'student:dashboard' %}{% elif user.is_faculty %}{% url 'teacher:dashboard' %}{% elif user.is_office_staff %}{% url 'office:dashboard' %}{% elif user.is_administrator %}{% url 'core_admin:dashboard' %}{% else %}#{% endif %}" class="sidebar-brand">"""
)

# Replace role navigation checks
c = c.replace("{% if user.role == 'STUDENT' %}", "{% if user.is_student %}")
c = c.replace("{% elif user.role == 'TEACHER' or user.role == 'FACULTY' or user.is_faculty %}", "{% elif user.is_faculty %}")
c = c.replace("{% elif user.role == 'OFFICE' or user.role == 'OFFICE_STAFF' %}", "{% elif user.is_office_staff %}")
c = c.replace("{% elif user.role == 'ADMIN' %}", "{% elif user.is_administrator %}")

# Replace Dr. prefix checks
c = c.replace(
    "{% if (user.role == 'TEACHER' or user.role == 'FACULTY' or user.is_faculty) and 'Dr.' not in user.get_full_name and 'Prof.' not in user.get_full_name %}Dr. {% endif %}",
    "{% if user.is_faculty and 'Dr.' not in user.get_full_name and 'Prof.' not in user.get_full_name %}Dr. {% endif %}"
)

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("base.html successfully rewritten with clean model properties!")

