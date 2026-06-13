/**
 * API client for communicating with the FastAPI backend.
 */
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor
api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.message || err.message || 'Network error';
    console.error('[API Error]', msg);
    return Promise.reject(err);
  }
);

// ---- Workflows ----

export async function saveWorkflow(name, description, nodes, edges) {
  const res = await api.post('/workflows', { name, description, nodes, edges });
  return res.data;
}

export async function getWorkflows() {
  const res = await api.get('/workflows');
  return res.data;
}

export async function getWorkflow(id) {
  const res = await api.get(`/workflows/${id}`);
  return res.data;
}

export async function deleteWorkflow(id) {
  const res = await api.delete(`/workflows/${id}`);
  return res.data;
}

export async function executeWorkflow(id) {
  const res = await api.post(`/workflows/${id}/execute`);
  return res.data;
}

export async function getTaskStatus(taskId) {
  const res = await api.get(`/tasks/${taskId}/status`);
  return res.data;
}

export async function getExecutors() {
  const res = await api.get('/executors');
  return res.data;
}

export async function getPresets() {
  const res = await api.get('/presets');
  return res.data;
}

export async function createPreset(data) {
  const res = await api.post('/presets', data);
  return res.data;
}

// ---- AI Config Generation ----

export async function generateAIConfig(requirement, nodeType) {
  const res = await api.post('/ai/generate-config', { requirement, node_type: nodeType });
  return res.data;
}

// ---- WebSocket Logs ----

export function createLogSocket(taskId, onMessage, onClose) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/tasks/${taskId}/logs`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => console.log(`[WS] Connected to logs for task ${taskId}`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.warn('[WS] Non-JSON message:', event.data);
    }
  };

  ws.onerror = (err) => console.error('[WS] Error:', err);

  ws.onclose = () => {
    console.log(`[WS] Disconnected from logs for task ${taskId}`);
    onClose?.();
  };

  return ws;
}
