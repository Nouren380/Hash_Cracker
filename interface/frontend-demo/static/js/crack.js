(function () {
  const form = document.getElementById('crack-form');
  const hashInput = document.getElementById('hash-input');
  const hashField = document.getElementById('hash-field');
  const hashError = document.getElementById('hash-error');
  const submitButton = document.getElementById('submit-button');
  const loadingMessage = document.getElementById('loading-message');
  const errorBanner = document.getElementById('submit-error-banner');
  let isSubmitting = false;

  function clearFieldError() {
    hashField.classList.remove('has-error');
    hashInput.removeAttribute('aria-invalid');
    hashError.textContent = '';
  }

  hashInput.addEventListener('input', clearFieldError);

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (isSubmitting) return;

    errorBanner.classList.remove('is-visible');
    errorBanner.textContent = '';
    clearFieldError();

    const outcome = HashValidation.validate(hashInput.value);
    if (!outcome.valid) {
      hashField.classList.add('has-error');
      hashInput.setAttribute('aria-invalid', 'true');
      hashError.textContent = outcome.message;
      hashInput.focus();
      return;
    }

    isSubmitting = true;
    submitButton.disabled = true;
    submitButton.classList.add('is-loading');
    loadingMessage.hidden = false;

    try {
      const result = await HashCrackerApi.submitHash(outcome.normalized);
      sessionStorage.setItem('hashCrackerLastResult', JSON.stringify(result));
      const target = new URL('/results', window.location.origin);
      if (ApiMode.current === 'mock') target.searchParams.set('mode', 'mock');
      window.location.href = target.href;
    } catch (error) {
      errorBanner.textContent = error && error.message ? error.message : 'Something went wrong while submitting the hash.';
      errorBanner.classList.add('is-visible');
    } finally {
      isSubmitting = false;
      submitButton.disabled = false;
      submitButton.classList.remove('is-loading');
      loadingMessage.hidden = true;
    }
  });
})();
