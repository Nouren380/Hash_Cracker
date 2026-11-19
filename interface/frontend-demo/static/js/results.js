(function () {
  const container = document.getElementById("results-container");
  const resultTemplate = document.getElementById("result-template");
  const emptyTemplate = document.getElementById("results-empty-template");

  const stateLabels = {
    found: "Password found",
    not_found: "Not found",
    processing: "Processing",
    error: "Error"
  };

  function render() {
    const raw = sessionStorage.getItem("hashCrackerLastResult");

    if (!raw) {
      container.appendChild(emptyTemplate.content.cloneNode(true));
      return;
    }

    let result;
    try {
      result = JSON.parse(raw);
    } catch (err) {
      container.appendChild(emptyTemplate.content.cloneNode(true));
      return;
    }

    const node = resultTemplate.content.cloneNode(true);
    const stateEl = node.querySelector('[data-field="state"]');
    const stateKey = result.status === "found" ? "found" : result.status === "processing" ? "processing" : result.status === "error" ? "error" : "not-found";
    stateEl.textContent = stateLabels[result.status] || "Unknown status";
    stateEl.classList.add(stateKey);

    node.querySelector('[data-field="hash"]').textContent = result.hash || "";
    const algorithm = AlgorithmConfig.byId(result.algorithm);
    node.querySelector('[data-field="algorithm"]').textContent = algorithm ? algorithm.label : (result.algorithm || "Unknown");
    node.querySelector('[data-field="password"]').textContent = result.password || "Not recovered";
    node.querySelector('[data-field="duration"]').textContent = result.durationMs ? `${result.durationMs} ms` : "Not reported by Backend";

    container.appendChild(node);
  }

  render();
})();
