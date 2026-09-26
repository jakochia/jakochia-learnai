const API_BASE = localStorage.getItem('jakochia-api') || 'http://localhost:8000';

const Auth = {
  get token() { return localStorage.getItem('jakochia-token'); },
  set token(v) { v ? localStorage.setItem('jakochia-token', v) : localStorage.removeItem('jakochia-token'); },
  get user() { try { return JSON.parse(localStorage.getItem('jakochia-user') || 'null'); } catch { return null; } },
  set user(u) { u ? localStorage.setItem('jakochia-user', JSON.stringify(u)) : localStorage.removeItem('jakochia-user'); },
  logout() { this.token = null; this.user = null; location.href = 'login.html'; },
  requireAuth() { if (!this.token) { location.href = 'login.html'; return false; } return true; }
};

async function api(path, { method = 'GET', body, headers = {} } = {}) {
  const opts = { method, headers: { ...headers } };
  if (Auth.token) opts.headers['Authorization'] = 'Bearer ' + Auth.token;
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body) opts.body = body;
  const res = await fetch(API_BASE + path, opts);
  if (res.status === 401 && !path.includes('/auth/')) { Auth.logout(); return; }
  if (!res.ok) {
    let detail = res.statusText;
    try { const j = await res.json(); detail = j.detail || JSON.stringify(j); } catch {}
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

function toast(msg, type = '') {
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function fmtMinutes(m) {
  const h = Math.floor(m / 60), mm = m % 60;
  return h ? h + 'h ' + mm + 'm' : mm + 'm';
}
