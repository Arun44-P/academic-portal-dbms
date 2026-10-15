/**
 * Academic Portal - Core UI JavaScript (main.js)
 * Robust, accessible UI helpers: Alerts, Modals, User Dropdown, Table Search
 */

document.addEventListener('DOMContentLoaded', () => {
  initAlerts();
  initModals();
  initUserDropdown();
  initTableSearch();
});

/* --------------------------------------------------------------------------
   1. Flash Alerts & Messages
   -------------------------------------------------------------------------- */
function initAlerts() {
  const alertCloseButtons = document.querySelectorAll('[data-dismiss="alert"], .alert-close');
  alertCloseButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) {
        alert.classList.add('fade-out');
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // Auto dismiss success alerts after 6 seconds
  const autoDismissAlerts = document.querySelectorAll('.alert-success');
  autoDismissAlerts.forEach((alert) => {
    setTimeout(() => {
      if (document.body.contains(alert)) {
        alert.classList.add('fade-out');
        setTimeout(() => alert.remove(), 250);
      }
    }, 6000);
  });
}

/* --------------------------------------------------------------------------
   2. Accessible Modals
   -------------------------------------------------------------------------- */
let activeModal = null;
let lastActiveElement = null;

function initModals() {
  // Modal open triggers
  const openButtons = document.querySelectorAll('[data-modal-target]');
  openButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-modal-target');
      const modal = document.querySelector(targetId);
      if (modal) {
        openModal(modal, btn);
      }
    });
  });

  // Modal close triggers
  const closeButtons = document.querySelectorAll('[data-close-modal], .modal-close');
  closeButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.modal');
      if (modal) {
        closeModal(modal);
      }
    });
  });

  // Close on backdrop click
  const modals = document.querySelectorAll('.modal');
  modals.forEach((modal) => {
    modal.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-backdrop')) {
        closeModal(modal);
      }
    });
  });

  // Close on ESC key & trap focus
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && activeModal) {
      closeModal(activeModal);
    }
    if (e.key === 'Tab' && activeModal) {
      trapFocus(e, activeModal);
    }
  });
}

function openModal(modal, triggerElement = null) {
  if (!modal) return;
  lastActiveElement = triggerElement || document.activeElement;
  modal.classList.add('is-open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  activeModal = modal;

  // Focus first focusable element in modal
  const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (focusable.length > 0) {
    focusable[0].focus();
  }
}

function closeModal(modal) {
  if (!modal) return;
  modal.classList.remove('is-open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  activeModal = null;

  if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
    lastActiveElement.focus();
  }
}

function trapFocus(e, modal) {
  const focusables = Array.from(modal.querySelectorAll('button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'));
  if (focusables.length === 0) return;

  const first = focusables[0];
  const last = focusables[focusables.length - 1];

  if (e.shiftKey) {
    if (document.activeElement === first) {
      last.focus();
      e.preventDefault();
    }
  } else {
    if (document.activeElement === last) {
      first.focus();
      e.preventDefault();
    }
  }
}

/* --------------------------------------------------------------------------
   3. User Profile Dropdown in Topbar
   -------------------------------------------------------------------------- */
function initUserDropdown() {
  const profileBtn = document.getElementById('userMenuBtn');
  const dropdown = document.getElementById('userMenuDropdown');

  if (!profileBtn || !dropdown) return;

  profileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isExpanded = profileBtn.getAttribute('aria-expanded') === 'true';
    profileBtn.setAttribute('aria-expanded', !isExpanded);
    dropdown.classList.toggle('is-active');
  });

  // Close when clicking anywhere outside
  document.addEventListener('click', (e) => {
    if (!profileBtn.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('is-active');
      profileBtn.setAttribute('aria-expanded', 'false');
    }
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && dropdown.classList.contains('is-active')) {
      dropdown.classList.remove('is-active');
      profileBtn.setAttribute('aria-expanded', 'false');
    }
  });
}

/* --------------------------------------------------------------------------
   4. Simple Table Search / Filter Helper
   -------------------------------------------------------------------------- */
function initTableSearch() {
  const searchInputs = document.querySelectorAll('[data-table-filter]');
  searchInputs.forEach((input) => {
    const targetTableId = input.getAttribute('data-table-filter');
    const table = document.getElementById(targetTableId);
    if (!table) return;

    input.addEventListener('input', () => {
      const query = input.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');

      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        if (text.includes(query)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  });
}

// Global portal helpers
window.AcademicPortal = {
  openModal,
  closeModal
};
