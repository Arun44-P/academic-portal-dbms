/**
 * Academic Portal - Core UI JavaScript (main.js)
 * Handles: Alerts dismiss, Sidebar toggling, Accessible Modals, Tabs, User Dropdown
 */

document.addEventListener('DOMContentLoaded', () => {
  initAlerts();
  initSidebar();
  initModals();
  initTabs();
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
   2. Responsive Sidebar & Mobile Drawer
   -------------------------------------------------------------------------- */
function initSidebar() {
  const sidebar = document.querySelector('.app-sidebar');
  const toggleBtn = document.getElementById('sidebarToggle');
  const overlay = document.getElementById('sidebarOverlay');

  if (!sidebar || !toggleBtn) return;

  function openSidebar() {
    sidebar.classList.add('sidebar-open');
    if (overlay) overlay.classList.add('active');
    toggleBtn.setAttribute('aria-expanded', 'true');
  }

  function closeSidebar() {
    sidebar.classList.remove('sidebar-open');
    if (overlay) overlay.classList.remove('active');
    toggleBtn.setAttribute('aria-expanded', 'false');
  }

  toggleBtn.addEventListener('click', () => {
    const isOpen = sidebar.classList.contains('sidebar-open');
    if (isOpen) {
      closeSidebar();
    } else {
      openSidebar();
    }
  });

  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  // Close sidebar on escape if open on mobile
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('sidebar-open')) {
      closeSidebar();
    }
  });
}

/* --------------------------------------------------------------------------
   3. Accessible Modals
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

export function openModal(modal, triggerElement = null) {
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

export function closeModal(modal) {
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
   4. Navigation Tabs
   -------------------------------------------------------------------------- */
function initTabs() {
  const tabContainers = document.querySelectorAll('[data-tabs]');
  tabContainers.forEach((container) => {
    const tabs = container.querySelectorAll('[data-tab-target]');
    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const targetSelector = tab.getAttribute('data-tab-target');
        const targetPane = document.querySelector(targetSelector);

        // Deactivate siblings
        tabs.forEach((t) => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        const parentSection = tab.closest('.tabs-wrapper') || document;
        const allPanes = parentSection.querySelectorAll('.tab-pane');
        allPanes.forEach((pane) => pane.classList.remove('active'));

        // Activate selected
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        if (targetPane) {
          targetPane.classList.add('active');
        }
      });
    });
  });
}

/* --------------------------------------------------------------------------
   5. User Dropdown in Topbar
   -------------------------------------------------------------------------- */
function initUserDropdown() {
  const profileBtn = document.getElementById('userMenuBtn');
  const dropdown = document.getElementById('userMenuDropdown');

  if (!profileBtn || !dropdown) return;

  profileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('is-active');
  });

  document.addEventListener('click', (e) => {
    if (!profileBtn.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('is-active');
    }
  });
}

/* --------------------------------------------------------------------------
   6. Simple Table Search / Filter Helper
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

// Attach globally for inline handlers if needed
window.AcademicPortal = {
  openModal,
  closeModal
};

