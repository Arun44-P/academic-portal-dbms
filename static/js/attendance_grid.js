/**
 * Academic Portal - Bulk Attendance Grid Helper (attendance_grid.js)
 * Provides 1-click bulk marking (All Present / All Absent), live stat calculations,
 * and roster filtering for the Faculty Attendance Entry module.
 */

document.addEventListener('DOMContentLoaded', () => {
  initAttendanceGrid();
});

function initAttendanceGrid() {
  const table = document.getElementById('attendanceTable');
  if (!table) return;

  const markAllPresentBtn = document.getElementById('markAllPresentBtn');
  const markAllAbsentBtn = document.getElementById('markAllAbsentBtn');

  const totalCountEl = document.getElementById('totalStudentsCount');
  const presentCountEl = document.getElementById('presentStudentsCount');
  const absentCountEl = document.getElementById('absentStudentsCount');
  const percentageEl = document.getElementById('attendancePercentageVal');

  const searchInput = document.getElementById('rosterSearchInput');

  function calculateStats() {
    const rows = table.querySelectorAll('tbody tr.student-row');
    const total = rows.length;
    let present = 0;
    let absent = 0;

    rows.forEach((row) => {
      const presentRadio = row.querySelector('input[type="radio"][value="PRESENT"]');
      const absentRadio = row.querySelector('input[type="radio"][value="ABSENT"]');

      if (presentRadio && presentRadio.checked) {
        present++;
        row.classList.remove('row-absent');
        row.classList.add('row-present');
      } else if (absentRadio && absentRadio.checked) {
        absent++;
        row.classList.remove('row-present');
        row.classList.add('row-absent');
      }
    });

    if (totalCountEl) totalCountEl.textContent = total;
    if (presentCountEl) presentCountEl.textContent = present;
    if (absentCountEl) absentCountEl.textContent = absent;

    const pct = total > 0 ? Math.round((present / total) * 100) : 0;
    if (percentageEl) percentageEl.textContent = `${pct}%`;
  }

  // Bulk Mark All Present
  if (markAllPresentBtn) {
    markAllPresentBtn.addEventListener('click', () => {
      const presentRadios = table.querySelectorAll('input[type="radio"][value="PRESENT"]');
      presentRadios.forEach((radio) => {
        radio.checked = true;
      });
      calculateStats();
    });
  }

  // Bulk Mark All Absent
  if (markAllAbsentBtn) {
    markAllAbsentBtn.addEventListener('click', () => {
      const absentRadios = table.querySelectorAll('input[type="radio"][value="ABSENT"]');
      absentRadios.forEach((radio) => {
        radio.checked = true;
      });
      calculateStats();
    });
  }

  // Listen to individual radio changes
  const radios = table.querySelectorAll('input[type="radio"]');
  radios.forEach((radio) => {
    radio.addEventListener('change', calculateStats);
  });

  // Roster Filter Search
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const query = searchInput.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr.student-row');

      rows.forEach((row) => {
        const rollNo = row.getAttribute('data-roll-no') || '';
        const name = row.getAttribute('data-student-name') || '';
        const match = rollNo.toLowerCase().includes(query) || name.toLowerCase().includes(query);

        row.style.display = match ? '' : 'none';
      });
    });
  }

  // Initial Calculation
  calculateStats();
}

