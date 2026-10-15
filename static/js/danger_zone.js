/**
 * Academic Portal - Admin Danger Zone Logic (danger_zone.js)
 * Implements a strict 3-tier safeguard challenge-response before enabling destructive actions:
 *  Tier 1: Character-exact phrase matching (e.g., "DROP TABLE enrollments")
 *  Tier 2: Admin Password Confirmation
 *  Tier 3: Mandatory Justification Note for the Immutable Audit Log (min 15 chars)
 */

document.addEventListener('DOMContentLoaded', () => {
  initDangerZone();
});

function initDangerZone() {
  const modal = document.getElementById('dangerZoneModal');
  if (!modal) return;

  const phraseDisplay = document.getElementById('challengePhraseDisplay');
  const phraseInput = document.getElementById('challengePhraseInput');
  const phraseIndicator = document.getElementById('phraseMatchIndicator');
  const step1 = document.getElementById('dangerStep1');

  const passwordInput = document.getElementById('adminPasswordInput');
  const step2 = document.getElementById('dangerStep2');

  const reasonInput = document.getElementById('actionReasonInput');
  const reasonCounter = document.getElementById('reasonCharCounter');
  const step3 = document.getElementById('dangerStep3');

  const executeBtn = document.getElementById('executeRadicalBtn');
  const targetActionInput = document.getElementById('dangerActionType');
  const targetEntityInput = document.getElementById('dangerTargetEntity');
  const modalTitle = document.getElementById('dangerModalActionTitle');

  let requiredPhrase = '';

  // Trigger buttons that launch danger modal
  const dangerButtons = document.querySelectorAll('[data-danger-trigger]');
  dangerButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const actionType = btn.getAttribute('data-action-type') || 'DROP TABLE';
      const entity = btn.getAttribute('data-target-entity') || 'enrollments';
      const phrase = btn.getAttribute('data-challenge-phrase') || `${actionType} ${entity}`;

      setupModal(actionType, entity, phrase);
      if (window.AcademicPortal && window.AcademicPortal.openModal) {
        window.AcademicPortal.openModal(modal, btn);
      } else {
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
      }
    });
  });

  function setupModal(actionType, entity, phrase) {
    requiredPhrase = phrase;
    if (phraseDisplay) phraseDisplay.textContent = phrase;
    if (modalTitle) modalTitle.textContent = `${actionType}: ${entity}`;
    if (targetActionInput) targetActionInput.value = actionType;
    if (targetEntityInput) targetEntityInput.value = entity;

    // Reset form states
    if (phraseInput) {
      phraseInput.value = '';
      phraseInput.classList.remove('input-match-success');
    }
    if (passwordInput) passwordInput.value = '';
    if (reasonInput) reasonInput.value = '';

    updateValidation();
  }

  function updateValidation() {
    let tier1Valid = false;
    let tier2Valid = false;
    let tier3Valid = false;

    // Tier 1: Challenge Phrase Match
    const typedPhrase = phraseInput ? phraseInput.value.trim() : '';
    if (typedPhrase.length === 0) {
      phraseIndicator.innerHTML = '<span class="match-pending">Waiting for exact input...</span>';
      phraseInput.classList.remove('input-match-success');
      step1.classList.remove('step-completed');
    } else if (typedPhrase === requiredPhrase) {
      phraseIndicator.innerHTML = '<span class="match-success"><svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg> Exact match verified</span>';
      phraseInput.classList.add('input-match-success');
      step1.classList.add('step-completed');
      tier1Valid = true;
    } else {
      phraseIndicator.innerHTML = '<span class="match-error">Text does not match required phrase</span>';
      phraseInput.classList.remove('input-match-success');
      step1.classList.remove('step-completed');
    }

    // Tier 2: Password
    const password = passwordInput ? passwordInput.value : '';
    if (password.length >= 4) {
      tier2Valid = true;
      step2.classList.add('step-completed');
    } else {
      step2.classList.remove('step-completed');
    }

    // Tier 3: Reason (minimum 15 characters for strict audit trace)
    const reason = reasonInput ? reasonInput.value.trim() : '';
    const charCount = reason.length;
    if (reasonCounter) {
      reasonCounter.textContent = `${charCount}/15 characters (minimum 15 required)`;
      if (charCount >= 15) {
        reasonCounter.classList.remove('text-danger');
        reasonCounter.classList.add('text-success');
      } else {
        reasonCounter.classList.remove('text-success');
        reasonCounter.classList.add('text-danger');
      }
    }

    if (charCount >= 15) {
      tier3Valid = true;
      step3.classList.add('step-completed');
    } else {
      step3.classList.remove('step-completed');
    }

    // Final Gatekeeper: Enable execute button strictly when ALL 3 pass
    if (tier1Valid && tier2Valid && tier3Valid) {
      executeBtn.removeAttribute('disabled');
      executeBtn.removeAttribute('aria-disabled');
      executeBtn.title = "All safeguards passed. Click to execute.";
    } else {
      executeBtn.setAttribute('disabled', 'true');
      executeBtn.setAttribute('aria-disabled', 'true');
      executeBtn.title = "All 3 verification steps must pass before proceeding.";
    }
  }

  // Bind live event listeners
  if (phraseInput) phraseInput.addEventListener('input', updateValidation);
  if (passwordInput) passwordInput.addEventListener('input', updateValidation);
  if (reasonInput) reasonInput.addEventListener('input', updateValidation);
}

