/**
 * BuildCost AI API Client
 * Configurable base URL via environment variable VITE_API_BASE_URL (defaults to http://localhost:8000)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 10000; // 10 seconds

/**
 * Fetch wrapper with timeout and structured error handling.
 */
async function fetchWithTimeout(resource, options = {}) {
  const { timeout = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(resource, {
      ...fetchOptions,
      signal: controller.signal,
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeout / 1000} seconds. Please check if backend API is responding.`);
    }
    // Network / connection refused errors
    throw new Error('Unable to connect to BuildCost AI backend API. Please ensure the server is running at ' + API_BASE_URL);
  }
}

/**
 * GET /health
 * Returns API and Database status.
 */
export async function getHealth() {
  const url = `${API_BASE_URL}/health`;
  try {
    const response = await fetchWithTimeout(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      timeout: 5000,
    });

    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data.detail || `Health check failed with status code ${response.status}`;
      return { status: 'error', database_connected: false, message: errorMsg };
    }
    return data;
  } catch (err) {
    return {
      status: 'error',
      database_connected: false,
      message: err.message || 'Backend API unreachable'
    };
  }
}

/**
 * POST /predict-optimal-build-window
 * @param {Object} payload - { sqft: number, target_materials: string[] }
 */
export async function predictOptimalBuildWindow(payload) {
  const url = `${API_BASE_URL}/predict-optimal-build-window`;

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();

  if (!response.ok) {
    // Extract FastAPI detail string or object
    let detailMsg = 'API request failed with status ' + response.status;
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        detailMsg = data.detail;
      } else if (Array.isArray(data.detail)) {
        // Pydantic validation errors list
        detailMsg = data.detail.map(d => `${d.loc ? d.loc.join('.') : ''}: ${d.msg}`).join('; ');
      } else {
        detailMsg = JSON.stringify(data.detail);
      }
    }
    const error = new Error(detailMsg);
    error.status = response.status;
    error.detail = data.detail;
    throw error;
  }

  return data;
}
