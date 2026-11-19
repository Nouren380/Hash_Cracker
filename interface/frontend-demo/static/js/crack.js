(function () {
  const form = document.getElementById("crack-form");
  const hashInput = document.getElementById("hash-input");
  const hashField = document.getElementById("hash-field");
  const hashError = document.getElementById("hash-error");
  const algorithmSelect = document.getElementById("algorithm-select");
  const submitButton = document.getElementById("submit-button");
  const errorBanner = document.getElementById("submit-error-banner");

  let isSubmitting = false;

  function showFieldError(message) {
    hashField.classList.add("has-error");
    hashError.textContent = message;
  }

  function clearFieldError() {
    hashField.classList.remove("has-error");
    hashError.textContent = "";
  }

  function showBanner(message) {
    errorBanner.textContent = message;
    errorBanner.classList.add("is-visible");
  }

  function hideBanner() {
    errorBanner.classList.remove("is-visible");
    errorBanner.textContent = "";
  }

  function setLoading(loading) {
    isSubmitting = loading;
    submitButton.disabled = loading;
    submitButton.classList.toggle("is-loading", loading);
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    hideBanner();
    clearFieldError();

    const rawHash = hashInput.value;
    const algorithmId = algorithmSelect.value;
    const outcome = HashValidation.validate(rawHash, algorithmId);

    if (!outcome.valid) {
      showFieldError(outcome.message);
      return;
    }

    setLoading(true);

    try {
      const result = await HashCrackerApi.submitHash(outcome.normalized, algorithmId);
      sessionStorage.setItem("hashCrackerLastResult", JSON.stringify(result));
      window.location.href = "/results";
    } catch (err) {
      const message = err && err.message ? err.message : "Something went wrong while submitting the hash.";
      showBanner(message);
    } finally {
      setLoading(false);
    }
  });

  hashInput.addEventListener("input", clearFieldError);
})();
