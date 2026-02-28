// js/dashboard.js
const VIEWS = [
  { id:"overview",  label:"Visão geral",  icon:"📊", roles:["owner","admin","mod","player"] },
  /*{ id:"players",   label:"Players",      icon:"👤", roles:["owner","admin","mod"] },
  { id:"moderation",label:"Moderação",    icon:"🛡️", roles:["owner","admin","mod"] },
  { id:"economy",   label:"Economia",     icon:"💰", roles:["owner","admin"] },
  { id:"settings",  label:"Configurações",icon:"⚙️", roles:["owner"] },*/
];

function role() {
  return localStorage.getItem("user_role") || "player";
}

function setHeader(title, desc){
  document.getElementById("viewTitle").textContent = title;
  document.getElementById("viewDesc").textContent = desc;
}

function renderNav() {
  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  const r = role();

  const allowed = VIEWS.filter(v => v.roles.includes(r));
  for (const v of allowed) {
    const a = document.createElement("a");
    a.href = `#${v.id}`;
    a.className = "navItem";
    a.innerHTML = `<span class="navIcon">${v.icon}</span><span>${v.label}</span>`;
    nav.appendChild(a);
  }
}

function setActiveNav(viewId){
  for (const a of document.querySelectorAll(".navItem")) {
    const id = a.getAttribute("href").replace("#","");
    a.classList.toggle("active", id === viewId);
  }
}

function tile(title, value, badgeText=""){
  return `
    <article class="tile">
      <h3>${title}</h3>
      <div class="kpi">${value}</div>
      ${badgeText ? `<div class="badge">${badgeText}</div>` : ""}
    </article>
  `;
}

function table(title, columns, rows){
  const head = columns.map(c=>`<th>${c}</th>`).join("");
  const body = rows.map(r=>`<tr>${r.map(x=>`<td>${x}</td>`).join("")}</tr>`).join("");
  return `
    <section class="tableWrap">
      <table>
        <thead><tr><th colspan="${columns.length}">${title}</th></tr><tr>${head}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </section>
  `;
}

// --------- VIEWS (cada aba) ---------

async function viewOverview(){
  setHeader("Visão geral", "Resumo do servidor e ações rápidas.");

  // endpoints sugeridos:
  // GET /stats/overview -> { online_now, bans_today, sales_today, reports_open }
  let s = { online_now: 12, bans_today: 0, sales_today: 0, reports_open: 0 };
  try { s = await apiFetch("/stats/overview"); } catch {}

  const html = `
    ${tile("Online agora", s.online_now, "Atualizado via API")}
    ${tile("Bans hoje", s.bans_today)}
    ${tile("Vendas hoje", s.sales_today)}
    ${tile("Reports abertos", s.reports_open)}
    ${table("Últimos eventos", ["Quando","Tipo","User","Detalhe", "Antes", "Depois"], [
      ["—","—","—","—","-—","—"],
    ])}
  `;
  document.getElementById("view").innerHTML = html;
}

/*async function viewPlayers(){
  setHeader("Players", "Consultar e gerenciar players.");

  // GET /players?search=... -> [{ userId, name, lastSeen, status }]
  let list = [];
  try { list = await apiFetch("/players"); } catch {}

  const rows = (list.length ? list : [
    { userId: 1, name:"Exemplo", lastSeen:"—", status:"—" }
  ]).map(p => [p.userId, p.name, p.lastSeen, p.status]);

  const html = `
    <article class="tile" style="grid-column:span 12;">
      <h3>Busca</h3>
      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <input class="input" id="playerSearch" placeholder="Nome ou UserId" style="max-width:320px;">
        <button class="btn primary" id="searchBtn">Buscar</button>
      </div>
      <p class="muted" style="margin-top:10px;">Dica: implemente filtros no backend.</p>
    </article>
    ${table("Lista de Players", ["UserId","Nome","Última vez","Status"], rows)}
  `;
  document.getElementById("view").innerHTML = html;

  document.getElementById("searchBtn").addEventListener("click", async () => {
    const q = document.getElementById("playerSearch").value.trim();
    const filtered = await apiFetch(`/players?search=${encodeURIComponent(q)}`);
    const rows2 = filtered.map(p => [p.userId, p.name, p.lastSeen, p.status]);
    document.querySelector(".tableWrap tbody").innerHTML =
      rows2.map(r=>`<tr>${r.map(x=>`<td>${x}</td>`).join("")}</tr>`).join("");
  });
}

async function viewEconomy(){
  setHeader("Economia", "Acompanhar transações e ajustar configurações.");

  // GET /economy/summary -> { revenue_7d, top_item, refunds }
  let e = { revenue_7d: 0, top_item: "—", refunds: 0 };
  try { e = await apiFetch("/economy/summary"); } catch {}

  const html = `
    ${tile("Receita (7d)", e.revenue_7d)}
    ${tile("Item mais vendido", e.top_item)}
    ${tile("Reembolsos", e.refunds)}
    ${table("Últimas transações", ["Quando","Player","Ação","Valor"], [
      ["—","—","—","—"]
    ])}
  `;
  document.getElementById("view").innerHTML = html;
}

async function viewModeration(){
  setHeader("Moderação", "Warn, mute e ban (com auditoria).");

  const html = `
    <article class="tile" style="grid-column:span 12;">
      <h3>Ação rápida</h3>
      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <input class="input" id="modUserId" placeholder="UserId" style="max-width:180px;">
        <select class="input" id="modAction" style="max-width:200px;">
          <option value="warn">Warn</option>
          <option value="ban">Ban</option>
        </select>
        <input class="input" id="modReason" placeholder="Motivo" style="max-width:320px;">
        <button class="btn primary" id="modSubmit">Aplicar</button>
      </div>
      <p class="muted" style="margin-top:10px;">O backend deve validar permissão (role) e registrar no audit log.</p>
      <p class="hint" id="modMsg"></p>
    </article>
    ${table("Audit Log", ["Quando","Staff","Ação","Player","Motivo"], [
      ["—","—","—","—","—"],
      ["—","—","—","—","—"]
    ])}
  `;
  document.getElementById("view").innerHTML = html;

  document.getElementById("modSubmit").addEventListener("click", async () => {
    const msg = document.getElementById("modMsg");
    msg.textContent = "";
    try {
      const userId = Number(document.getElementById("modUserId").value);
      const action = document.getElementById("modAction").value;
      const reason = document.getElementById("modReason").value.trim();

      // POST /moderation/action -> { ok: true }
      await apiFetch("/moderation/action", { method:"POST", body:{ userId, action, reason }});
      msg.textContent = "Ação aplicada com sucesso.";
    } catch (err) {
      msg.textContent = err.message;
    }
  });
}

async function viewSettings(){
  setHeader("Configurações", "Ajustes do jogo, permissões e chaves.");

  const html = `
    <article class="tile" style="grid-column:span 12;">
      <h3>Configurações do jogo</h3>
      <p class="muted">Aqui você coloca flags/configs: multiplicador, eventos, limites, etc.</p>
      <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;">
        <input class="input" id="cfgKey" placeholder="Chave (ex: xp_multiplier)" style="max-width:260px;">
        <input class="input" id="cfgValue" placeholder="Valor (ex: 1.5)" style="max-width:260px;">
        <button class="btn primary" id="cfgSave">Salvar</button>
      </div>
      <p class="hint" id="cfgMsg"></p>
    </article>
    ${table("Audit Log (exemplo)", ["Tipo","Valor","User","Data","Motivo"], [
      ["—","—","—","—","—"],
      ["xp",id="cfgValue","—","—","—"]
    ])}
  `;
  document.getElementById("view").innerHTML = html;

  document.getElementById("cfgSave").addEventListener("click", async () => {
    const msg = document.getElementById("cfgMsg");
    msg.textContent = "";
    try {
      const key = document.getElementById("cfgKey").value.trim();
      const value = document.getElementById("cfgValue").value.trim();

      // POST /settings -> { ok:true }
      await apiFetch("/settings", { method:"POST", body:{ key, value }});
      msg.textContent = "Config salva.";
    } catch (err) {
      msg.textContent = err.message;
    }
  });
}*/

// --------- Router ---------
const ROUTES = {
  overview: viewOverview,
  /*players: viewPlayers,
  economy: viewEconomy,
  moderation: viewModeration,
  settings: viewSettings,*/
};

async function renderRoute() {
  let viewId = (location.hash || "#overview").replace("#","");
  const r = role();
  const allowed = VIEWS.filter(v => v.roles.includes(r)).map(v=>v.id);
  if (!allowed.includes(viewId)) viewId = allowed[0] || "overview";

  setActiveNav(viewId);
  const fn = ROUTES[viewId] || viewOverview;
  await fn();
}

document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  /*
  // carrega usuário/role se ainda não tiver salvo
  try {
    const me = await loadMe();
    document.getElementById("whoami").textContent = `${me.email} • ${me.role}`;
  } catch {
    document.getElementById("whoami").textContent = `${localStorage.getItem("user_email") || ""} • ${role()}`;
  }
  */

  // carrega usuário/role se ainda não tiver salvo
  try {
  if (getToken() !== "DEV_TOKEN") {
    const me = await loadMe();
    document.getElementById("whoami").textContent =
      `${me.email} • ${me.role}`;
  } else {
    document.getElementById("whoami").textContent =
      `${localStorage.getItem("user_email")} • ${role()} (DEV)`;
  }
} catch {
  document.getElementById("whoami").textContent =
    `${localStorage.getItem("user_email") || ""} • ${role()}`;
}

  renderNav();
  window.addEventListener("hashchange", renderRoute);

  document.getElementById("refreshBtn").addEventListener("click", renderRoute);
  await renderRoute();

    // Auto refresh: atualiza a Visão geral a cada 5 segundos
  setInterval(() => {
    // se você estiver usando renderRoute/Hash, deixa assim:
    renderRoute();
  }, 3000);
});