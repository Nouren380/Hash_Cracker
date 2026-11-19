(function () {
  const container = document.getElementById("reports-container");
  const emptyTemplate = document.getElementById("reports-empty-template");
  const rowTemplate = document.getElementById("report-row-template");
  const errorBanner = document.getElementById("reports-error-banner");

  async function load() {
    try {
      const response = await HashCrackerApi.fetchReports();

      if (!response.reports || response.reports.length === 0) {
        container.innerHTML = "";
        container.appendChild(emptyTemplate.content.cloneNode(true));
        return;
      }

      container.innerHTML = "";
      response.reports.forEach(function (report) {
        const node = rowTemplate.content.cloneNode(true);
        node.querySelector('[data-field="total_found"]').textContent = `${report.totalFound} / ${report.totalJobs}`;
        node.querySelector('[data-field="title"]').textContent = `${report.title} · ${new Date(report.generatedAt).toLocaleDateString()}`;
        container.appendChild(node);
      });
    } catch (err) {
      container.innerHTML = "";
      errorBanner.textContent = err && err.message ? err.message : "Could not load reports from the Backend.";
      errorBanner.classList.add("is-visible");
    }
  }

  load();
})();
