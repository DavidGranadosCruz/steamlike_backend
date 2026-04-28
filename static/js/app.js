/* ═══════════════════════════════════════════════════════════
   SteamLike — Frontend App Logic
   ═══════════════════════════════════════════════════════════ */

(() => {
  "use strict";

  // ── Config ────────────────────────────────────────────────
  const API = {
    health:   "/api/health/",
    login:    "/api/auth/login/",
    register: "/api/auth/register/",
    me:       "/api/users/me/",
    entries:  "/api/library/entries/",
    entry: id => `/api/library/entries/${id}/`,
  };

  // ── Helpers ───────────────────────────────────────────────
  function $(sel)  { return document.querySelector(sel); }
  function $$(sel) { return document.querySelectorAll(sel); }

  function getCookie(name) {
    const v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return v ? v.pop() : "";
  }

  async function api(url, opts = {}) {
    const defaults = {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
    };
    if (["POST", "PATCH", "PUT", "DELETE"].includes((opts.method || "").toUpperCase())) {
      defaults.headers["X-CSRFToken"] = getCookie("csrftoken");
    }
    const res = await fetch(url, { ...defaults, ...opts, headers: { ...defaults.headers, ...(opts.headers || {}) } });
    const data = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, data };
  }

  // ── Game icon bank (deterministic by game id hash) ────────
  const GAME_ICONS = ["🎮","🕹️","🏆","⚔️","🚀","🏎️","🧙","🐉","🎯","🌍","💎","🔫","🛡️","⚡","🎲","🧩","🏹","🎵","👾","🤖"];
  const BANNER_GRADIENTS = [
    "linear-gradient(135deg,hsl(240,40%,14%),hsl(260,50%,25%))",
    "linear-gradient(135deg,hsl(200,50%,12%),hsl(220,60%,22%))",
    "linear-gradient(135deg,hsl(280,40%,14%),hsl(300,50%,22%))",
    "linear-gradient(135deg,hsl(160,40%,12%),hsl(180,50%,20%))",
    "linear-gradient(135deg,hsl(20,50%,14%),hsl(40,55%,22%))",
    "linear-gradient(135deg,hsl(330,40%,14%),hsl(350,50%,22%))",
  ];

  function hashCode(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) h = ((h << 5) - h + str.charCodeAt(i)) | 0;
    return Math.abs(h);
  }

  function iconForGame(id) { return GAME_ICONS[hashCode(id) % GAME_ICONS.length]; }
  function gradientForGame(id) { return BANNER_GRADIENTS[hashCode(id) % BANNER_GRADIENTS.length]; }

  const STATUS_INFO = {
    wishlist:  { label: "Wishlist",    icon: "🎯" },
    playing:   { label: "Jugando",     icon: "🕹️" },
    completed: { label: "Completado",  icon: "🏆" },
    dropped:   { label: "Abandonado",  icon: "❌" },
  };

  // ── State ─────────────────────────────────────────────────
  let entries = [];
  let currentFilter = "all";
  let editingId = null;

  // ── DOM refs ──────────────────────────────────────────────
  const loadingScreen  = $("#loading-screen");
  const authSection    = $("#auth-section");
  const appSection     = $("#app-section");

  const loginForm      = $("#login-form");
  const registerForm   = $("#register-form");
  const loginError     = $("#login-error");
  const registerError  = $("#register-error");
  const registerSuccess = $("#register-success");

  const userName       = $("#user-name");
  const gameGrid       = $("#game-grid");
  const emptyState     = $("#empty-state");
  const searchInput    = $("#search-input");

  const modalOverlay   = $("#modal-overlay");
  const modalTitle     = $("#modal-title");
  const gameForm       = $("#game-form");
  const gameIdInput    = $("#game-id");
  const gameStatusSel  = $("#game-status");
  const gameHoursInput = $("#game-hours");
  const modalError     = $("#modal-error");
  const modalSubmitText = $("#modal-submit-text");

  // Stats
  const statTotal     = $("#stat-total");
  const statPlaying   = $("#stat-playing");
  const statCompleted = $("#stat-completed");
  const statHours     = $("#stat-hours");

  // ── Init ──────────────────────────────────────────────────
  async function init() {
    createParticles();

    // Check if user is logged in
    const { ok, data } = await api(API.me);
    setTimeout(() => loadingScreen.classList.add("fade-out"), 1200);
    setTimeout(() => {
      loadingScreen.classList.add("hidden");
      if (ok && data) {
        showApp(data);
      } else {
        showAuth();
      }
    }, 1800);
  }

  function createParticles() {
    const container = $("#auth-particles");
    if (!container) return;
    for (let i = 0; i < 8; i++) {
      const p = document.createElement("div");
      p.className = "particle";
      const size = 60 + Math.random() * 160;
      p.style.cssText = `
        width:${size}px;height:${size}px;
        left:${Math.random()*100}%;top:${Math.random()*100}%;
        animation-delay:${Math.random()*-18}s;
        animation-duration:${14+Math.random()*10}s;
      `;
      container.appendChild(p);
    }
  }

  // ── Auth Flow ─────────────────────────────────────────────
  function showAuth() {
    authSection.classList.remove("hidden");
    appSection.classList.add("hidden");
  }

  function showApp(user) {
    authSection.classList.add("hidden");
    appSection.classList.remove("hidden");
    userName.textContent = user.username;
    loadEntries();
  }

  // Toggle forms
  $("#show-register").addEventListener("click", e => {
    e.preventDefault();
    loginForm.classList.add("hidden");
    registerForm.classList.remove("hidden");
    clearErrors();
  });
  $("#show-login").addEventListener("click", e => {
    e.preventDefault();
    registerForm.classList.add("hidden");
    loginForm.classList.remove("hidden");
    clearErrors();
  });

  function clearErrors() {
    loginError.classList.add("hidden");
    registerError.classList.add("hidden");
    registerSuccess.classList.add("hidden");
    modalError.classList.add("hidden");
  }

  // Login
  loginForm.addEventListener("submit", async e => {
    e.preventDefault();
    clearErrors();
    const btn = $("#login-btn");
    setLoading(btn, true);
    const { ok, data } = await api(API.login, {
      method: "POST",
      body: JSON.stringify({
        username: $("#login-username").value.trim(),
        password: $("#login-password").value,
      }),
    });
    setLoading(btn, false);
    if (ok) {
      toast("¡Bienvenido, " + data.username + "!", "success");
      showApp(data);
    } else {
      loginError.textContent = data?.message || "Error al iniciar sesión";
      loginError.classList.remove("hidden");
    }
  });

  // Register
  registerForm.addEventListener("submit", async e => {
    e.preventDefault();
    clearErrors();
    const btn = $("#register-btn");
    setLoading(btn, true);
    const { ok, data } = await api(API.register, {
      method: "POST",
      body: JSON.stringify({
        username: $("#reg-username").value.trim(),
        password: $("#reg-password").value,
      }),
    });
    setLoading(btn, false);
    if (ok) {
      registerSuccess.textContent = "¡Cuenta creada! Ahora inicia sesión.";
      registerSuccess.classList.remove("hidden");
      setTimeout(() => {
        registerForm.classList.add("hidden");
        loginForm.classList.remove("hidden");
        clearErrors();
      }, 1800);
    } else {
      const msg = data?.details ? Object.values(data.details).join(" ") : (data?.message || "Error al registrar");
      registerError.textContent = msg;
      registerError.classList.remove("hidden");
    }
  });

  // Logout
  $("#logout-btn").addEventListener("click", async () => {
    await api("/api/auth/logout/", { method: "POST" });
    toast("Sesión cerrada", "info");
    setTimeout(() => location.reload(), 600);
  });

  function setLoading(btn, loading) {
    const text = btn.querySelector(".btn-text");
    const loader = btn.querySelector(".btn-loader");
    if (loading) {
      btn.disabled = true;
      if (text) text.classList.add("hidden");
      if (loader) loader.classList.remove("hidden");
    } else {
      btn.disabled = false;
      if (text) text.classList.remove("hidden");
      if (loader) loader.classList.add("hidden");
    }
  }

  // ── Entries ───────────────────────────────────────────────
  async function loadEntries() {
    const { ok, data } = await api(API.entries);
    if (ok && Array.isArray(data)) {
      entries = data;
      renderEntries();
      updateStats();
    }
  }

  function filteredEntries() {
    let list = entries;
    if (currentFilter !== "all") {
      list = list.filter(e => e.status === currentFilter);
    }
    const q = searchInput.value.trim().toLowerCase();
    if (q) {
      list = list.filter(e => e.external_game_id.toLowerCase().includes(q));
    }
    return list;
  }

  function renderEntries() {
    const list = filteredEntries();
    if (list.length === 0 && entries.length === 0) {
      gameGrid.innerHTML = "";
      emptyState.classList.remove("hidden");
      return;
    }
    emptyState.classList.add("hidden");

    if (list.length === 0) {
      gameGrid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:60px 20px;color:var(--text-dim)">
          <p style="font-size:1.1rem">Sin resultados para este filtro</p>
        </div>`;
      return;
    }

    gameGrid.innerHTML = list.map((entry, i) => {
      const si = STATUS_INFO[entry.status] || STATUS_INFO.wishlist;
      const icon = iconForGame(entry.external_game_id);
      const gradient = gradientForGame(entry.external_game_id);
      return `
        <div class="game-card" style="animation-delay:${i * .06}s">
          <div class="card-banner" style="background:${gradient}">
            <span class="card-banner-icon">${icon}</span>
          </div>
          <div class="card-body">
            <div class="card-title" title="${entry.external_game_id}">${entry.external_game_id}</div>
            <div class="card-meta">
              <span class="status-badge ${entry.status}">${si.icon} ${si.label}</span>
              <span class="hours-display">⏱️ ${entry.hours_played}h</span>
            </div>
            <div class="card-actions">
              <button class="btn btn-ghost btn-sm" onclick="window.__editEntry(${entry.id})">✏️ Editar</button>
              <button class="btn btn-danger btn-sm" onclick="window.__deleteEntry(${entry.id})">🗑️</button>
            </div>
          </div>
        </div>`;
    }).join("");
  }

  function updateStats() {
    statTotal.textContent = entries.length;
    statPlaying.textContent = entries.filter(e => e.status === "playing").length;
    statCompleted.textContent = entries.filter(e => e.status === "completed").length;
    statHours.textContent = entries.reduce((s, e) => s + e.hours_played, 0);
    // Animate stat values
    $$(".stat-value").forEach(el => {
      el.style.animation = "none";
      el.offsetHeight; // reflow
      el.style.animation = "cardFadeIn .3s ease";
    });
  }

  // ── Filters ───────────────────────────────────────────────
  $("#filter-pills").addEventListener("click", e => {
    const pill = e.target.closest(".pill");
    if (!pill) return;
    $$(".pill").forEach(p => p.classList.remove("active"));
    pill.classList.add("active");
    currentFilter = pill.dataset.filter;
    renderEntries();
  });

  searchInput.addEventListener("input", () => renderEntries());

  // ── Modal ─────────────────────────────────────────────────
  function openModal(mode, entry) {
    editingId = null;
    clearErrors();
    if (mode === "add") {
      modalTitle.textContent = "Añadir Juego";
      modalSubmitText.textContent = "Guardar";
      gameIdInput.value = "";
      gameIdInput.disabled = false;
      gameStatusSel.value = "wishlist";
      gameHoursInput.value = 0;
    } else {
      modalTitle.textContent = "Editar Juego";
      modalSubmitText.textContent = "Actualizar";
      editingId = entry.id;
      gameIdInput.value = entry.external_game_id;
      gameIdInput.disabled = true;
      gameStatusSel.value = entry.status;
      gameHoursInput.value = entry.hours_played;
    }
    modalOverlay.classList.remove("hidden");
  }

  function closeModal() {
    modalOverlay.classList.add("hidden");
  }

  $("#add-game-btn").addEventListener("click", () => openModal("add"));
  $("#empty-add-btn").addEventListener("click", () => openModal("add"));
  $("#modal-close").addEventListener("click", closeModal);
  $("#modal-cancel").addEventListener("click", closeModal);
  modalOverlay.addEventListener("click", e => {
    if (e.target === modalOverlay) closeModal();
  });

  gameForm.addEventListener("submit", async e => {
    e.preventDefault();
    clearErrors();

    const btn = $("#modal-submit");
    setLoading(btn, true);

    if (editingId) {
      // PATCH
      const { ok, data } = await api(API.entry(editingId), {
        method: "PATCH",
        body: JSON.stringify({
          status: gameStatusSel.value,
          hours_played: parseInt(gameHoursInput.value, 10),
        }),
      });
      setLoading(btn, false);
      if (ok) {
        toast("Juego actualizado", "success");
        closeModal();
        loadEntries();
      } else {
        const msg = data?.details ? Object.values(data.details).join(" ") : (data?.message || "Error");
        modalError.textContent = msg;
        modalError.classList.remove("hidden");
      }
    } else {
      // POST
      const { ok, data } = await api(API.entries, {
        method: "POST",
        body: JSON.stringify({
          external_game_id: gameIdInput.value.trim(),
          status: gameStatusSel.value,
          hours_played: parseInt(gameHoursInput.value, 10),
        }),
      });
      setLoading(btn, false);
      if (ok) {
        toast("¡Juego añadido!", "success");
        closeModal();
        loadEntries();
      } else {
        const msg = data?.details ? Object.values(data.details).join(" ") : (data?.message || "Error");
        modalError.textContent = msg;
        modalError.classList.remove("hidden");
      }
    }
  });

  // ── Delete ────────────────────────────────────────────────
  // Note: The backend doesn't have a DELETE endpoint, so we just
  // provide feedback. If needed in the future, add a DELETE view.
  window.__deleteEntry = async function(id) {
    // For now, since there's no DELETE endpoint, we show a message
    toast("Funcionalidad de eliminación no disponible aún en el backend", "info");
  };

  window.__editEntry = function(id) {
    const entry = entries.find(e => e.id === id);
    if (entry) openModal("edit", entry);
  };

  // ── Toast ─────────────────────────────────────────────────
  function toast(msg, type = "info") {
    const container = $("#toast-container");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    const icons = { success: "✅", error: "❌", info: "ℹ️" };
    el.innerHTML = `<span>${icons[type] || ""}</span><span>${msg}</span>`;
    container.appendChild(el);
    setTimeout(() => {
      el.classList.add("fade-out");
      setTimeout(() => el.remove(), 350);
    }, 3500);
  }

  // ── Boot ──────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", init);

})();
