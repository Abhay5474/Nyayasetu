import axios from 'axios';

export const TOKEN_KEY = 'nyayasetu.session';

export function readSession() {
  try {
    const raw = localStorage.getItem(TOKEN_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (!s?.token || (s.expiresAt && new Date(s.expiresAt) <= new Date())) {
      localStorage.removeItem(TOKEN_KEY);
      return null;
    }
    return s;
  } catch {
    return null;
  }
}

export function writeSession(session) {
  try {
    if (session) localStorage.setItem(TOKEN_KEY, JSON.stringify(session));
    else localStorage.removeItem(TOKEN_KEY);
  } catch { /* storage unavailable: session lasts until reload */ }
}

const api = axios.create({ baseURL: '/api', timeout: 60_000 });

api.interceptors.request.use((config) => {
  const s = readSession();
  if (s?.token) config.headers.Authorization = `Bearer ${s.token}`;
  return config;
});

let onUnauthorized = () => {};
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url = error.config?.url || '';
    if (error.response?.status === 401 && !url.startsWith('/auth/')) onUnauthorized();
    return Promise.reject(error);
  },
);

/** Turn any axios/network error into a short message that is safe to show. */
export function errorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (error?.code === 'ECONNABORTED') return 'The request timed out. Please try again.';
  if (!error?.response) return error?.request ? 'Cannot reach the server. Check your connection.' : fallback;
  const data = error.response.data;
  if (data?.fieldErrors) {
    const first = Object.entries(data.fieldErrors)[0];
    if (first) return `${first[0]}: ${first[1]}`;
  }
  return data?.message || fallback;
}

export default api;
