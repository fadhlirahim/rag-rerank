/**
 * API client for the RAG API
 */

// Base API request with error handling
const apiRequest = async (endpoint, method, body = null) => {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`/api${endpoint}`, options);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API request failed: ${response.status}`);
  }

  return response.json();
};

// Ingest a document
export const ingestDocument = async (document) => {
  return apiRequest('/ingest', 'POST', document);
};

// Query the knowledge base
export const queryKnowledge = async (query) => {
  return apiRequest('/ask', 'POST', query);
};

// Health check
export const healthCheck = async () => {
  return apiRequest('/health', 'GET');
};

// Reset all vectors in the database
export const resetVectors = async () => {
  return apiRequest('/reset', 'POST');
};