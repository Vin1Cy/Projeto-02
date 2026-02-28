// js/api.js
const API_BASE = "https://SEU-DOMINIO-DA-API.com"; // <-- troque isso

function getToken() {
  return localStorage.getItem("access_token");
}
function setToken(token) {
  localStorage.setItem("access_token", token);
}
function clearToken() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_role");
  localStorage.removeItem("user_email");
}

async function apiFetch(path, { method="GET", body=null, headers={} } = {}) {
    if (getToken() === "DEV_TOKEN") {
        // Retornos fake por endpoint (mock)
        if (path === "/stats/overview") return { online_now: 12, bans_today: 1, sales_today: 5, reports_open: 2 };
        if (path.startsWith("/players")) return [{ userId: 123, name: "PlayerTeste", lastSeen: "Hoje", status: "OK" }];
        if (path === "/economy/summary") return { revenue_7d: 999, top_item: "VIP", refunds: 0 };
        if (path === "/me") return { email: "dev@local", role: role() };
        return { ok: true };
    }
  const token = getToken();
  const h = { "Content-Type": "application/json", ...headers };
  if (token) h["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: h,
    body: body ? JSON.stringify(body) : null,
  });

  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }

  if (!res.ok) {
    const msg = (data && data.message) ? data.message : `Erro ${res.status}`;
    throw new Error(msg);
  }
  return data;
}