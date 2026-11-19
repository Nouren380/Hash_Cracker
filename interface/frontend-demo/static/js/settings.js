(function () {
  const connectionDot = document.getElementById("connection-dot");
  const connectionLabel = document.getElementById("connection-label");
  const compactToggle = document.getElementById("toggle-compact");
  const hintsToggle = document.getElementById("toggle-hints");

  if (ApiMode.current === "mock") {
    connectionDot.classList.add("unknown");
    connectionLabel.textContent = "Using mock data for Frontend testing (no live Backend).";
  } else {
    connectionDot.classList.add("unknown");
    connectionLabel.textContent = `Pointed at ${ApiConfig.baseUrl} (connection not verified from this page).`;
  }

  function applyToggleState(button, storageKey, defaultOn) {
    const stored = localStorage.getItem(storageKey);
    const isOn = stored === null ? defaultOn : stored === "true";
    button.classList.toggle("on", isOn);
    button.setAttribute("aria-pressed", String(isOn));

    button.addEventListener("click", function () {
      const nowOn = !button.classList.contains("on");
      button.classList.toggle("on", nowOn);
      button.setAttribute("aria-pressed", String(nowOn));
      localStorage.setItem(storageKey, String(nowOn));
    });
  }

  applyToggleState(compactToggle, "hashCrackerCompactTables", false);
  applyToggleState(hintsToggle, "hashCrackerShowHints", true);
})();
