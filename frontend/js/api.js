// ===========================================
// API Helper — fetch wrapper + JWT interceptor
// ทุก request จะแนบ Authorization: Bearer token อัตโนมัติ
// ถ้า token หมดอายุ → auto refresh → retry request
// ===========================================

const API_BASE = '/api';

// --- Token Management ---
const TokenStore = {
  getAccess: () => localStorage.getItem('access_token'),
  getRefresh: () => localStorage.getItem('refresh_token'),
  setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  },
  clear() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
};

// --- User Storage ---
const UserStore = {
  get: () => JSON.parse(localStorage.getItem('user') || 'null'),
  set: (user) => localStorage.setItem('user', JSON.stringify(user)),
  clear: () => localStorage.removeItem('user'),
  isLoggedIn: () => !!TokenStore.getAccess(),
};

// --- Core Fetch Wrapper ---
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = options.headers || {};

  // แนบ JWT token (ถ้ามี)
  const token = TokenStore.getAccess();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // ถ้าไม่ใช่ FormData → set JSON content type
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }

  const response = await fetch(url, { ...options, headers });

  // Token expired → try refresh
  if (response.status === 401 && TokenStore.getRefresh()) {
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry original request with new token
      headers['Authorization'] = `Bearer ${TokenStore.getAccess()}`;
      return fetch(url, { ...options, headers });
    } else {
      // Refresh failed → logout
      TokenStore.clear();
      UserStore.clear();
      window.location.href = '/login.html';
      return response;
    }
  }

  return response;
}

// --- Refresh Token ---
async function refreshToken() {
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: TokenStore.getRefresh() }),
    });
    if (res.ok) {
      const data = await res.json();
      TokenStore.setTokens(data.access, TokenStore.getRefresh());
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// --- Convenience Methods ---
const api = {
  async get(endpoint) {
    const res = await apiFetch(endpoint);
    return res.json();
  },

  async post(endpoint, body) {
    const isFormData = body instanceof FormData;
    const res = await apiFetch(endpoint, {
      method: 'POST',
      body: isFormData ? body : JSON.stringify(body),
    });
    return res.json();
  },

  async patch(endpoint, body) {
    const res = await apiFetch(endpoint, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      const errMsg = data.detail || data.username?.[0] || data.address?.[0] || JSON.stringify(data);
      throw new Error(errMsg);
    }
    return data;
  },

  async delete(endpoint) {
    return apiFetch(endpoint, { method: 'DELETE' });
  },
};

// --- Toast Notification ---
function showToast(message, type = 'success') {
  // ลบ toast เก่า
  document.querySelectorAll('.toast').forEach(t => t.remove());

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
