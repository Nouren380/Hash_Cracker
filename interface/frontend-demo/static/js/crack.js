(function () {
  const form = document.getElementById('crack-form');
  const hashInput = document.getElementById('hash-input');
  const hashField = document.getElementById('hash-field');
  const hashError = document.getElementById('hash-error');
  const suggestion = document.getElementById('hash-suggestion');
  const algorithmSelect = document.getElementById('algorithm-select');
  const submitButton = document.getElementById('submit-button');
  const loadingMessage = document.getElementById('loading-message');
  const errorBanner = document.getElementById('submit-error-banner');
  let isSubmitting = false;

  function updateSuggestion() {
    const hash = hashInput.value.trim();
    if (!hash) { suggestion.textContent = 'Not sure about the algorithm? Paste a hash to see possible matches.'; return; }
    if (!/^[a-f0-9]+$/i.test(hash)) { suggestion.textContent = 'Suggestions are available for hexadecimal hashes only.'; return; }
    const matches = AlgorithmConfig.list.filter(item => item.hexLength === hash.length);
    suggestion.textContent = matches.length
      ? `Possible match in this interface: ${matches.map(item => item.label).join(', ')}. Other algorithms can share this length; choose the algorithm you used.`
      : 'No algorithm in the current list matches this length. Check the hash and algorithm.';
  }

  hashInput.addEventListener('input', () => { hashField.classList.remove('has-error'); hashInput.removeAttribute('aria-invalid'); hashError.textContent = ''; updateSuggestion(); });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (isSubmitting) return;
    errorBanner.classList.remove('is-visible'); errorBanner.textContent = '';
    hashField.classList.remove('has-error'); hashInput.removeAttribute('aria-invalid'); hashError.textContent = '';
    const outcome = HashValidation.validate(hashInput.value, algorithmSelect.value);
    if (!outcome.valid) { hashField.classList.add('has-error'); hashInput.setAttribute('aria-invalid', 'true'); hashError.textContent = outcome.message; hashInput.focus(); return; }
    isSubmitting = true; submitButton.disabled = true; submitButton.classList.add('is-loading'); loadingMessage.hidden = false;
    try {
      const result = await HashCrackerApi.submitHash(outcome.normalized, algorithmSelect.value);
      sessionStorage.setItem('hashCrackerLastResult', JSON.stringify(result));
      const target = new URL('/results', window.location.origin);
      if (ApiMode.current === 'mock') target.searchParams.set('mode', 'mock');
      window.location.href = target.href;
    } catch (error) {
      errorBanner.textContent = error && error.message ? error.message : 'Something went wrong while submitting the hash.';
      errorBanner.classList.add('is-visible');
    } finally { isSubmitting = false; submitButton.disabled = false; submitButton.classList.remove('is-loading'); loadingMessage.hidden = true; }
  });
})();
