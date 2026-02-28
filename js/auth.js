// js/auth.js
function requireAuth() {
  const token = getToken();
  if (!token) window.location.href = "index.html";
}

async function loadMe() {
  // endpoint sugerido: GET /me -> { email, role }
  const me = await apiFetch("/me");
  localStorage.setItem("user_role", me.role);
  localStorage.setItem("user_email", me.email);
  return me;
}

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const logoutBtn = document.getElementById("logoutBtn");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = document.getElementById("msg");
      const btn = document.getElementById("loginBtn");
      msg.textContent = "";
      btn.disabled = true;

      try {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        // endpoint sugerido: POST /auth/login -> { access_token }
        const r = await apiFetch("/auth/login", { method:"POST", body:{ email, password }});
        setToken(r.access_token);

        // opcional: carregar /me e guardar role
        await loadMe();

        window.location.href = "dashboard.html";
      } catch (err) {
        msg.textContent = err.message;
      } finally {
        btn.disabled = false;
      }
    });
  }

    const devBtn = document.getElementById("devLoginBtn");
  if (devBtn) {
    devBtn.addEventListener("click", () => {
      // Token fake (apenas para desenvolvimento)
      setToken("DEV_TOKEN");

      // Defina o role que você quer testar:
      localStorage.setItem("user_role", "owner"); // owner/admin/mod/player
      localStorage.setItem("user_email", "dev@local");

      window.location.href = "dashboard.html";
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      clearToken();
      window.location.href = "index.html";
    });
  }
});