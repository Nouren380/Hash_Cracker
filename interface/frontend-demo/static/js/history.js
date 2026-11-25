(function () {
  const container = document.getElementById("history-container");
  const emptyTemplate = document.getElementById("history-empty-template");
  const errorBanner = document.getElementById("history-error-banner");
  const backendBanner = document.getElementById("history-backend-banner");

  function renderTable(records) {
    const table = document.createElement("table");
    table.className = "data-table";

    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>Hash</th><th>Algorithm</th><th>Status</th><th>Password</th><th>Submitted</th></tr>";
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    records.forEach(function (record) {
      const row = document.createElement("tr");
      const algorithm = AlgorithmConfig.byId(record.algorithm);
      const values = [record.hash, algorithm ? algorithm.label : record.algorithm,
        record.status === "found" ? "Found" : record.status === "not_found" ? "Not found" : record.status,
        record.password == null ? "-" : record.password, record.submittedAt || "-"];
      values.forEach((value, index) => {
        const cell = document.createElement("td");
        cell.textContent = value == null ? "-" : String(value);
        if (index === 0 || index === 3) cell.className = "mono";
        row.appendChild(cell);
      });
      tbody.appendChild(row);
    });
    table.appendChild(tbody);

    container.innerHTML = "";
    container.appendChild(table);
  }

  async function load() {
    try {
      const response = await HashCrackerApi.fetchHistory();
      backendBanner.classList.toggle("is-visible", response.backendConnected === false);

      if (!response.records || response.records.length === 0) {
        container.innerHTML = "";
        container.appendChild(emptyTemplate.content.cloneNode(true));
        return;
      }

      renderTable(response.records);
    } catch (err) {
      container.innerHTML = "";
      errorBanner.textContent = err && err.message ? err.message : "Could not load history from the Backend.";
      errorBanner.classList.add("is-visible");
    }
  }

  load();
})();
