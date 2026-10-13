import api from './client';

export const AuthApi = {
  login: (body) => api.post('/auth/login', body).then((r) => r.data),
  register: (body) => api.post('/auth/register', body).then((r) => r.data),
};

export const UserApi = {
  me: () => api.get('/users/me').then((r) => r.data),
  update: (body) => api.patch('/users/me', body).then((r) => r.data),
  remove: () => api.delete('/users/me'),
};

export const DocumentApi = {
  upload: (file, language, onProgress) => {
    const form = new FormData();
    form.append('file', file);
    return api
      .post('/documents', form, {
        params: { language },
        timeout: 5 * 60_000,
        onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
      })
      .then((r) => r.data);
  },
  list: (page = 0, size = 20) => api.get('/documents', { params: { page, size } }).then((r) => r.data),
  get: (id) => api.get(`/documents/${id}`).then((r) => r.data),
  process: (id, language, force = false) => api.post(`/documents/${id}/process`, null, { params: { language, force } }).then((r) => r.data),
  result: (id, language) => api.get(`/documents/${id}/results/${language}`).then((r) => r.data),
  deadlines: (id) => api.get(`/documents/${id}/deadlines`).then((r) => r.data),
  remove: (id) => api.delete(`/documents/${id}`),
  /** Fetch the original with the auth header and open it via a blob URL. */
  fileBlob: (id) => api.get(`/documents/${id}/file`, { responseType: 'blob' }).then((r) => r.data),
};

export const DeadlineApi = {
  list: (status) => api.get('/deadlines', { params: status ? { status } : {} }).then((r) => r.data),
  setStatus: (id, status) => api.patch(`/deadlines/${id}`, { status }).then((r) => r.data),
};

export const ChatApi = {
  history: (docId) => api.get(`/documents/${docId}/chat`).then((r) => r.data),
  ask: (docId, question, language) =>
    api.post(`/documents/${docId}/chat`, { question, language }, { timeout: 3 * 60_000 }).then((r) => r.data),
  clear: (docId) => api.delete(`/documents/${docId}/chat`),
};
