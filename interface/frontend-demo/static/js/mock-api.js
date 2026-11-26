const MockApiData = {
  knownPasswords: {
    "5f4dcc3b5aa765d61d8327deb882cf99": "password",
    "e10adc3949ba59abbe56e057f20f883e": "123456"
  },
  history: [
    { id: "h1", hash: "5f4dcc3b5aa765d61d8327deb882cf99", algorithm: "md5", status: "found", password: "password", submittedAt: "2026-11-10T09:14:00Z" },
    { id: "h2", hash: "d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2", algorithm: "md5", status: "not_found", password: null, submittedAt: "2026-11-11T13:02:00Z" }
  ],
  reports: [
    { id: "r1", title: "Weekly cracking summary", generatedAt: "2026-11-09T00:00:00Z", totalJobs: 2, totalFound: 1 }
  ]
};

function mockDelay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const MockApi = {
  async submitHash(hash) {
    const algorithm = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}[hash.trim().length];
    if (!algorithm || !/^[a-f0-9]+$/i.test(hash.trim())) throw new Error("Unsupported hash format or length.");
    await mockDelay(900);
    const normalized = hash.trim().toLowerCase();
    const password = MockApiData.knownPasswords[normalized];
    return {
      hash: hash.trim(),
      algorithm: algorithm,
      status: password ? "found" : "not_found",
      password: password || null,
      durationMs: 820
    };
  },

  async fetchHistory() {
    await mockDelay(500);
    return { records: MockApiData.history, backendConnected: false };
  },

  async fetchReports() {
    await mockDelay(500);
    return { reports: MockApiData.reports, backendConnected: false };
  }
};
