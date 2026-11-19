const ApiConfig = {
  baseUrl: window.HASH_CRACKER_API_BASE || "/api",
  endpoints: {
    crack: "/crack",
    history: "/history",
    reports: "/reports"
  },
  timeoutMs: 15000
};

const ApiMode = {
  current: window.HASH_CRACKER_API_MODE || "live"
};

class ApiError extends Error {
  constructor(message, kind, status) {
    super(message);
    this.kind = kind;
    this.status = status || null;
  }
}

async function apiRequest(path, options) {
  const url = ApiConfig.baseUrl + path;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ApiConfig.timeoutMs);

  let response;
  try {
    response = await fetch(url, {
      method: options.method || "GET",
      headers: { "Content-Type": "application/json" },
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller.signal
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new ApiError("The request to the server timed out.", "network");
    }
    throw new ApiError("Could not reach the server. Check that the Backend is running.", "network");
  }
  clearTimeout(timeoutId);

  let payload = null;
  try {
    payload = await response.json();
  } catch (err) {
    payload = null;
  }

  if (!response.ok) {
    const message = (payload && payload.error && payload.error.message) || "The server returned an unexpected error.";
    throw new ApiError(message, "server", response.status);
  }

  return payload;
}

const HashCrackerApi = {
  submitHash(hash, algorithm) {
    if (ApiMode.current === "mock") {
      return MockApi.submitHash(hash, algorithm);
    }
    return apiRequest(ApiConfig.endpoints.crack, {
      method: "POST",
      body: { hash: hash, algorithm: algorithm }
    });
  },

  fetchHistory() {
    if (ApiMode.current === "mock") {
      return MockApi.fetchHistory();
    }
    return apiRequest(ApiConfig.endpoints.history, { method: "GET" });
  },

  fetchReports() {
    if (ApiMode.current === "mock") {
      return MockApi.fetchReports();
    }
    return apiRequest(ApiConfig.endpoints.reports, { method: "GET" });
  }
};
