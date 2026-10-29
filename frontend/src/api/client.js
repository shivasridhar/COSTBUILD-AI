/**
 * BuildCost AI API Client
 * Configurable base URL via environment variable VITE_API_BASE_URL (defaults to http://localhost:8000)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 10000; // 10 seconds

const TOKEN_KEY = 'buildcost_jwt_token';

/**
 * Fetch wrapper with timeout, automatic Bearer token insertion, and structured error handling.
 */
async function fetchWithTimeout(resource, options = {}) {
  const { timeout = DEFAULT_TIMEOUT_MS, headers = {}, ...fetchOptions } = options;

  const token = localStorage.getItem(TOKEN_KEY);
  const combinedHeaders = {
    ...headers,
  };
  if (token && !combinedHeaders['Authorization']) {
    combinedHeaders['Authorization'] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(resource, {
      ...fetchOptions,
      headers: combinedHeaders,
      signal: controller.signal,
    });
    clearTimeout(id);

    // Handle 401 Unauthorized for expired/invalid tokens
    if (response.status === 401 && token && !resource.includes('/auth/login')) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event('buildcost_auth_unauthorized'));
    }

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

function parseErrorMessage(data, defaultMsg) {
  if (!data) return defaultMsg;
  if (data.detail) {
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map(d => `${d.loc ? d.loc.join('.') : ''}: ${d.msg}`).join('; ');
    }
    return JSON.stringify(data.detail);
  }
  return defaultMsg;
}

/* =====================================================================
 * AUTHENTICATION API ENDPOINTS
 * ===================================================================== */

export async function loginApi(email, password) {
  const url = `${API_BASE_URL}/auth/login`;

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, 'Login failed'));
  }
  return data;
}

export async function registerApi(email, password, name) {
  const url = `${API_BASE_URL}/auth/register`;

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ email, password, name }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, 'Registration failed'));
  }
  return data;
}

export async function getMeApi(tokenOverride) {
  const url = `${API_BASE_URL}/auth/me`;
  const headers = { 'Accept': 'application/json' };
  if (tokenOverride) {
    headers['Authorization'] = `Bearer ${tokenOverride}`;
  }

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, 'Failed to fetch user profile'));
  }
  return data;
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
 * @param {Object} payload - { sqft: number, target_materials: string[], region?: string }
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
    const error = new Error(parseErrorMessage(data, 'API request failed with status ' + response.status));
    error.status = response.status;
    error.detail = data.detail;
    throw error;
  }

  return data;
}

/**
 * POST /check-fair-price
 * @param {Object} payload - { material: string, quoted_rate: number, quoted_unit: string, quoted_date: string, source_note?: string, region?: string, project_id?: number }
 */
export async function checkFairPrice(payload) {
  const url = `${API_BASE_URL}/check-fair-price`;

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
    const error = new Error(parseErrorMessage(data, 'Fair price check failed with status ' + response.status));
    error.status = response.status;
    error.detail = data.detail;
    throw error;
  }

  return data;
}

/**
 * POST /generate-report
 * Fetches PDF blob, triggers browser download, and handles errors.
 * @param {Object} payload - { sqft?: number, target_materials?: string[], region?: string, include_vendor_quotes?: boolean, vendor_quote_ids?: number[], project_id?: number }
 */
export async function downloadReport(payload) {
  const url = `${API_BASE_URL}/generate-report`;

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/pdf',
    },
    body: JSON.stringify(payload),
    timeout: 20000, // 20s timeout for PDF compiling
  });

  if (!response.ok) {
    let detailMsg = 'PDF Report generation failed with status ' + response.status;
    try {
      const errorJson = await response.json();
      detailMsg = parseErrorMessage(errorJson, detailMsg);
    } catch (e) {
      // Ignore JSON parse error if response was non-JSON
    }
    throw new Error(detailMsg);
  }

  const blob = await response.blob();
  
  let filename = 'buildcost-report.pdf';
  const disposition = response.headers.get('Content-Disposition');
  if (disposition && disposition.includes('filename=')) {
    const matches = disposition.match(/filename="?([^"]+)"?/);
    if (matches && matches[1]) {
      filename = matches[1];
    }
  }

  const blobUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(blobUrl);
}

/* =====================================================================
 * PROJECT MANAGEMENT API ENDPOINTS
 * ===================================================================== */

/**
 * GET /projects
 * @param {string} [statusFilter] - Optional filter ('planning', 'in_progress', 'completed', 'archived')
 */
export async function getProjects(statusFilter) {
  let url = `${API_BASE_URL}/projects`;
  if (statusFilter) {
    url += `?status_filter=${encodeURIComponent(statusFilter)}`;
  }

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, 'Failed to fetch projects'));
  }
  return data;
}

/**
 * POST /projects
 * @param {Object} projectData - { name: string, sqft: number, target_materials: string[], region?: string, notes?: string }
 */
export async function createProject(projectData) {
  const url = `${API_BASE_URL}/projects`;

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(projectData),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, 'Failed to create project'));
  }
  return data;
}

/**
 * GET /projects/:id
 */
export async function getProject(id) {
  const url = `${API_BASE_URL}/projects/${id}`;

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to fetch project #${id}`));
  }
  return data;
}

/**
 * PATCH /projects/:id
 * @param {number} id
 * @param {Object} patchData - { name?, sqft?, target_materials?, region?, status?, notes? }
 */
export async function updateProject(id, patchData) {
  const url = `${API_BASE_URL}/projects/${id}`;

  const response = await fetchWithTimeout(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(patchData),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to update project #${id}`));
  }
  return data;
}

/**
 * DELETE /projects/:id (Soft Delete - Sets status to 'archived')
 */
export async function archiveProject(id) {
  const url = `${API_BASE_URL}/projects/${id}`;

  const response = await fetchWithTimeout(url, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to archive project #${id}`));
  }
  return data;
}

/**
 * GET /projects/:id/forecast
 */
export async function getProjectForecast(id) {
  const url = `${API_BASE_URL}/projects/${id}/forecast`;

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to fetch forecast for project #${id}`));
  }
  return data;
}

/* =====================================================================
 * PROJECT PHASES API ENDPOINTS (STAGED PROCUREMENT)
 * ===================================================================== */

/**
 * GET /projects/:projectId/phases
 */
export async function getPhases(projectId) {
  const url = `${API_BASE_URL}/projects/${projectId}/phases`;

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to fetch phases for project #${projectId}`));
  }
  return data;
}

/**
 * POST /projects/:projectId/phases
 * @param {number} projectId
 * @param {Object} phaseData - { phase_name, materials, expected_start_month, sequence_order }
 */
export async function createPhase(projectId, phaseData) {
  const url = `${API_BASE_URL}/projects/${projectId}/phases`;

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(phaseData),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, 'Failed to create phase'));
  }
  return data;
}

/**
 * PATCH /projects/:projectId/phases/:phaseId
 */
export async function updatePhase(projectId, phaseId, patchData) {
  const url = `${API_BASE_URL}/projects/${projectId}/phases/${phaseId}`;

  const response = await fetchWithTimeout(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(patchData),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to update phase #${phaseId}`));
  }
  return data;
}

/**
 * DELETE /projects/:projectId/phases/:phaseId
 */
export async function deletePhase(projectId, phaseId) {
  const url = `${API_BASE_URL}/projects/${projectId}/phases/${phaseId}`;

  const response = await fetchWithTimeout(url, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to delete phase #${phaseId}`));
  }
  return data;
}

/**
 * GET /projects/:projectId/phases/:phaseId/forecast
 */
export async function getPhaseForecast(projectId, phaseId) {
  const url = `${API_BASE_URL}/projects/${projectId}/phases/${phaseId}/forecast`;

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to fetch forecast for phase #${phaseId}`));
  }
  return data;
}

/**
 * GET /projects/:projectId/phases/summary
 */
export async function getPhasesSummary(projectId) {
  const url = `${API_BASE_URL}/projects/${projectId}/phases/summary`;

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to fetch phases summary for project #${projectId}`));
  }
  return data;
}

/**
 * GET /projects/:projectId/procurement-strategy
 */
export async function getProjectProcurementStrategy(projectId) {
  const url = `${API_BASE_URL}/projects/${projectId}/procurement-strategy`;

  const response = await fetchWithTimeout(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(parseErrorMessage(data, `Failed to fetch procurement strategy for project #${projectId}`));
  }
  return data;
}
