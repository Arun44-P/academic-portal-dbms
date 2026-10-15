import re

# ============================================================================
# 1. Patch database_console.html
# ============================================================================
with open('templates/admin/database_console.html', 'r', encoding='utf-8') as f:
    db_html = f.read()

db_html = db_html.replace(
    "action=\"{% url 'admin:database_console' %}\"",
    "action=\"{% url 'core_admin:execute_radical_action' %}\""
)
db_html = db_html.replace(
    'id="challengePhraseInput" class="form-control text-mono"',
    'name="confirmation_text" id="challengePhraseInput" class="form-control text-mono"'
)
db_html = db_html.replace(
    'name="justification" id="actionReasonInput"',
    'name="justification_reason" id="actionReasonInput"'
)

dynamic_tables = """        <tbody>
          {% for tbl in tables %}
          <tr>
            <td><strong class="table-code font-bold">{{ tbl.name }}</strong></td>
            <td><span class="badge badge-info">Relational Table</span></td>
            <td><strong>{{ tbl.count }}</strong> records</td>
            <td>Auto</td>
            <td>Indexed</td>
            <td>utf8mb4</td>
            <td>
              <button type="button" class="btn btn-outline btn-sm text-danger" data-danger-trigger data-action-type="DROP TABLE" data-target-entity="{{ tbl.name }}" data-challenge-phrase="DROP TABLE {{ tbl.name }}">
                Drop Table
              </button>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="7" class="text-center p-4 text-muted">No database tables found.</td>
          </tr>
          {% endfor %}
        </tbody>"""

db_html = re.sub(r'<tbody>\s*<tr>\s*<td><strong class="table-code font-bold">user_accounts</strong>.*?</tbody>', dynamic_tables.strip(), db_html, flags=re.DOTALL)

with open('templates/admin/database_console.html', 'w', encoding='utf-8') as f:
    f.write(db_html)
print("Patched database_console.html")

# ============================================================================
# 2. Patch stipend_queue.html
# ============================================================================
with open('templates/office/stipend_queue.html', 'r', encoding='utf-8') as f:
    sq_html = f.read()

queue_tbody = """        <tbody>
          {% for stp in stipend_queue %}
          <tr>
            <td>
              <div class="font-bold text-main">{{ stp.junior.full_name }}</div>
              <div class="text-xs text-muted">{{ stp.junior.get_cadre_display }}</div>
            </td>
            <td>
              <div class="font-bold">Prof. {{ stp.junior.project.pi.user.last_name }}</div>
              <div class="text-xs text-muted">Approved {{ stp.pi_approval_date|date:"d M Y" }}</div>
            </td>
            <td>
              <span class="table-code font-bold">{{ stp.junior.project.project_code }}</span>
              <div class="text-xs text-muted">{{ stp.junior.project.title|truncatechars:35 }}</div>
            </td>
            <td><strong>Cycle {{ stp.disbursement_month }}/{{ stp.disbursement_year }}</strong></td>
            <td><strong class="text-success" style="font-size: 1.05rem;">₹{{ stp.amount }}</strong></td>
            <td>
              <div class="text-mono text-sm">Direct Bank Credit</div>
              <div class="text-xs text-muted">{{ stp.junior.email }}</div>
            </td>
            <td>
              <button type="button" class="btn btn-primary btn-sm" data-modal-target="#disburseModal" 
                      onclick="openDisburseModal('{{ stp.id }}', '{{ stp.junior.full_name|escapejs }}', 'Prof. {{ stp.junior.project.pi.user.last_name|escapejs }}', '{{ stp.junior.project.project_code|escapejs }}', '₹{{ stp.amount }}', 'Registered Account')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                Process Disbursement
              </button>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="7" class="text-center p-4 text-muted">🎉 All PI-approved stipends have been disbursed! No pending claims in queue.</td>
          </tr>
          {% endfor %}
        </tbody>"""

processed_tbody = """        <tbody>
          {% for stp in processed_stipends %}
          <tr>
            <td><strong>{{ stp.junior.full_name }}</strong></td>
            <td><span class="table-code">{{ stp.junior.project.project_code }}</span></td>
            <td><strong class="text-success">₹{{ stp.amount }}</strong></td>
            <td>Direct Bank Transfer</td>
            <td><span class="table-code font-bold">{{ stp.transaction_reference|default:"PENDING" }}</span></td>
            <td>{{ stp.disbursed_at|date:"d M Y H:i"|default:"Recent" }}</td>
            <td><span class="badge badge-success">Processed / Disbursed</span></td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="7" class="text-center p-4 text-muted">No disbursed transactions recorded yet.</td>
          </tr>
          {% endfor %}
        </tbody>"""

# Replace first tbody
sq_html = re.sub(r'<tbody>\s*<!-- Queue Item 1 -->.*?</tbody>', queue_tbody.strip(), sq_html, flags=re.DOTALL)
# Replace second tbody
sq_html = re.sub(r'<tbody>\s*<tr>\s*<td>Aarav Sharma</td>.*?</tbody>', processed_tbody.strip(), sq_html, flags=re.DOTALL)

# Replace form action and JS in stipend_queue
sq_html = sq_html.replace(
    'action="{% url \'office:stipend_queue\' %}"',
    'id="disburseModalForm" action=""'
)
sq_html = re.sub(
    r'function openDisburseModal\(id, fellow, pi, grant, amount, bank\) \{.*?\}',
    '''function openDisburseModal(id, fellow, pi, grant, amount, bank) {
    document.getElementById('disburseModalId').value = id;
    document.getElementById('disburseFellowName').textContent = fellow;
    document.getElementById('disbursePiName').textContent = pi;
    document.getElementById('disburseGrantCode').textContent = grant;
    document.getElementById('disburseAmount').textContent = amount;
    document.getElementById('disburseBankDetails').textContent = bank;
    document.getElementById('disburseModalForm').action = '/office-portal/stipend/disburse/' + id + '/';
    document.getElementById('txnRef').value = `UTR-${Date.now().toString().slice(-8)}-SBI`;
  }''',
    sq_html,
    flags=re.DOTALL
)

with open('templates/office/stipend_queue.html', 'w', encoding='utf-8') as f:
    f.write(sq_html)
print("Patched stipend_queue.html")

# ============================================================================
# 3. Patch research_juniors.html
# ============================================================================
with open('templates/teacher/research_juniors.html', 'r', encoding='utf-8') as f:
    rj_html = f.read()

pending_rj_tbody = """        <tbody>
          {% for stp in pending_stipends %}
          <tr style="background-color: #fffdf5;">
            <td>
              <div class="font-bold text-main">{{ stp.junior.full_name }}</div>
              <div class="text-xs text-muted">{{ stp.junior.get_cadre_display }} • {{ stp.junior.email }}</div>
            </td>
            <td><span class="table-code font-bold">{{ stp.junior.project.project_code }}</span></td>
            <td><strong>Cycle {{ stp.disbursement_month }}/{{ stp.disbursement_year }}</strong></td>
            <td><strong class="text-success" style="font-size: 1rem;">₹{{ stp.amount }}</strong></td>
            <td>
              <span class="badge badge-success">Milestone Submitted</span>
            </td>
            <td>
              <span class="badge badge-warning">
                <span class="badge-dot"></span>
                Pending PI Approval
              </span>
            </td>
            <td>
              <button type="button" class="btn btn-success btn-sm" data-modal-target="#approveStipendModal" 
                      onclick="openApproveModal('{{ stp.id }}', '{{ stp.junior.full_name|escapejs }}', '{{ stp.junior.project.project_code|escapejs }}', '{{ stp.disbursement_month }}/{{ stp.disbursement_year }}', '₹{{ stp.amount }}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                Approve Stipend
              </button>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="7" class="text-center p-4 text-muted">No monthly stipend claims awaiting your approval.</td>
          </tr>
          {% endfor %}
        </tbody>"""

juniors_roster_tbody = """        <tbody>
          {% for jun in juniors %}
          <tr>
            <td>
              <div class="font-bold text-main">{{ jun.full_name }}</div>
              <div class="text-xs text-muted">{{ jun.email }}</div>
            </td>
            <td><span class="badge badge-info">{{ jun.get_cadre_display }}</span></td>
            <td>
              <span class="table-code font-bold">{{ jun.project.project_code }}</span>
              <div class="text-xs text-muted">{{ jun.project.title|truncatechars:30 }}</div>
            </td>
            <td><strong>₹{{ jun.monthly_stipend }}</strong> / month</td>
            <td>{{ jun.appointment_start_date|date:"d M Y" }} &mdash; {{ jun.appointment_end_date|date:"d M Y" }}</td>
            <td>
              <span class="badge {% if jun.status == 'ACTIVE' %}badge-success{% else %}badge-warning{% endif %}">
                <span class="badge-dot"></span>
                {{ jun.status }}
              </span>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="6" class="text-center p-4 text-muted">No junior fellows currently attached to your projects.</td>
          </tr>
          {% endfor %}
        </tbody>"""

rj_html = re.sub(r'<tbody>\s*<!-- Item 1: Pending PI Approval.*?</tbody>', pending_rj_tbody.strip(), rj_html, flags=re.DOTALL)
rj_html = re.sub(r'<tbody>\s*<!-- Fellow 1 -->.*?</tbody>', juniors_roster_tbody.strip(), rj_html, flags=re.DOTALL)

# Wire modal form in research_juniors.html
rj_html = rj_html.replace(
    'action="{% url \'teacher:research_juniors\' %}"',
    'id="approveStipendForm" action=""'
)
rj_html = re.sub(
    r'function openApproveModal\(id, fellow, project, month, amount\) \{.*?\}',
    '''function openApproveModal(id, fellow, project, month, amount) {
    document.getElementById('approveStipendForm').action = '/faculty-portal/stipend/approve/' + id + '/';
    document.getElementById('modalStipendId').value = id;
    document.getElementById('modalFellowName').textContent = fellow;
    document.getElementById('modalProjectCode').textContent = project;
    document.getElementById('modalMonth').textContent = month;
    document.getElementById('modalAmount').textContent = amount;
  }''',
    rj_html,
    flags=re.DOTALL
)

with open('templates/teacher/research_juniors.html', 'w', encoding='utf-8') as f:
    f.write(rj_html)
print("Patched research_juniors.html")

import glob

for path in glob.glob('templates/**/*.html', recursive=True):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if "{% url 'admin:" in content:
        new_content = content.replace("{% url 'admin:", "{% url 'core_admin:")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Updated admin: to core_admin: in', path)

print("All patches completed successfully!")
