(function () {
  /* ─── Bars ──────────────────────────────────────────────────── */

  function animatePanelBars(panel) {
    const bars = panel.querySelectorAll("[data-width]");
    bars.forEach((bar) => {
      bar.style.width = "0%";
    });
    requestAnimationFrame(() => {
      bars.forEach((bar) => {
        bar.style.width = bar.dataset.width || "0%";
      });
    });
  }

  /* ─── Tabs ──────────────────────────────────────────────────── */

  function initTabs() {
    const containers = document.querySelectorAll("[data-tabs]");

    containers.forEach((container) => {
      const tabs = Array.from(container.querySelectorAll("[data-tab-target]"));
      const panels = Array.from(document.querySelectorAll("[data-tab-panel]"));
      const activeTabInputs = Array.from(document.querySelectorAll("[data-active-tab-input]"));

      if (!tabs.length || !panels.length) {
        return;
      }

      const activate = (target) => {
        tabs.forEach((tab) => {
          const isActive = tab.dataset.tabTarget === target;
          tab.classList.toggle("is-active", isActive);
          tab.setAttribute("aria-selected", String(isActive));
          tab.tabIndex = isActive ? 0 : -1;
        });

        panels.forEach((panel) => {
          const isActive = panel.dataset.tabPanel === target;
          panel.classList.toggle("is-active", isActive);
          panel.hidden = !isActive;

          if (isActive) {
            animatePanelBars(panel);
          }
        });

        activeTabInputs.forEach((input) => {
          input.value = target;
        });

        container.dataset.activeTab = target;
      };

      const focusTabAtIndex = (index) => {
        const tab = tabs[index];
        if (!(tab instanceof HTMLButtonElement)) {
          return;
        }
        activate(tab.dataset.tabTarget || "semester");
        tab.focus();
      };

      tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          activate(tab.dataset.tabTarget || "semester");
        });

        tab.addEventListener("keydown", (event) => {
          const currentIndex = tabs.indexOf(tab);
          if (currentIndex === -1) return;

          if (event.key === "ArrowRight" || event.key === "ArrowDown") {
            event.preventDefault();
            focusTabAtIndex((currentIndex + 1) % tabs.length);
            return;
          }

          if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
            event.preventDefault();
            focusTabAtIndex((currentIndex - 1 + tabs.length) % tabs.length);
            return;
          }

          if (event.key === "Home") {
            event.preventDefault();
            focusTabAtIndex(0);
            return;
          }

          if (event.key === "End") {
            event.preventDefault();
            focusTabAtIndex(tabs.length - 1);
          }
        });
      });

      activate(container.dataset.activeTab || "semester");
    });
  }

  /* ─── Auto-Submit Selects ───────────────────────────────────── */

  function initAutoSubmit() {
    document.querySelectorAll("select[data-auto-submit]").forEach((select) => {
      select.addEventListener("change", () => {
        const form = select.closest("form");
        if (form) form.submit();
      });
    });
  }

  /* ─── Nav Shadow on Scroll ──────────────────────────────────── */

  function initNavShadow() {
    const nav = document.querySelector(".scoreboard-nav");
    const sentinel = document.getElementById("nav-sentinel");
    if (!nav || !sentinel || typeof IntersectionObserver === "undefined") return;

    const obs = new IntersectionObserver(
      ([entry]) => {
        nav.classList.toggle("is-scrolled", !entry.isIntersecting);
      },
      { rootMargin: "-1px 0px 0px 0px" }
    );
    obs.observe(sentinel);
  }

  /* ─── Avatar Colors ─────────────────────────────────────────── */

  function initAvatarColors() {
    const dataEl = document.getElementById("ranking-data");
    if (!dataEl) return;

    let ranking;
    try {
      ranking = JSON.parse(dataEl.textContent);
    } catch (_) {
      return;
    }

    const colorMap = {};
    ranking.forEach((row, i) => {
      colorMap[row.display_name] = i % 8;
    });

    document.querySelectorAll(".avatar[data-pname]").forEach((el) => {
      const idx = colorMap[el.dataset.pname];
      if (idx !== undefined) {
        el.classList.add("av-" + idx);
      }
    });
  }

  /* ─── Head-to-Head ──────────────────────────────────────────── */

  function initHeadToHead() {
    const dataEl = document.getElementById("ranking-data");
    const selectA = document.getElementById("h2h-select-a");
    const selectB = document.getElementById("h2h-select-b");
    const output = document.getElementById("h2h-output");
    const prompt = document.getElementById("h2h-prompt");
    const statRows = document.getElementById("h2h-stat-rows");
    const playerA = document.getElementById("h2h-player-a");
    const playerB = document.getElementById("h2h-player-b");
    const avatarA = document.getElementById("h2h-avatar-a");
    const avatarB = document.getElementById("h2h-avatar-b");
    const nameA = document.getElementById("h2h-name-a");
    const nameB = document.getElementById("h2h-name-b");

    if (!dataEl || !selectA || !selectB || !output) return;

    let ranking;
    try {
      ranking = JSON.parse(dataEl.textContent);
    } catch (_) {
      return;
    }

    const colorMap = {};
    ranking.forEach((row, i) => {
      colorMap[row.display_name] = i % 8;
    });

    const byName = Object.fromEntries(ranking.map((r) => [r.display_name, r]));

    const stats = [
      { key: "average", label: "Promedio", fmt: (v) => (v !== null && v !== undefined ? Number(v).toFixed(2) : "—") },
      { key: "wins", label: "Victorias", fmt: (v) => String(v ?? 0) },
      { key: "podiums", label: "Podios", fmt: (v) => String(v ?? 0) },
      { key: "points", label: "Puntos", fmt: (v) => String(v ?? 0) },
    ];

    function getInitials(name) {
      const parts = name.trim().split(/\s+/);
      if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }

    function render() {
      const a = byName[selectA.value];
      const b = byName[selectB.value];

      if (!a || !b || a.display_name === b.display_name) {
        output.hidden = true;
        if (prompt) prompt.hidden = false;
        return;
      }

      output.hidden = false;
      if (prompt) prompt.hidden = true;

      // Header
      const idxA = colorMap[a.display_name] ?? 0;
      const idxB = colorMap[b.display_name] ?? 0;

      if (avatarA) {
        avatarA.className = "avatar av-" + idxA;
        avatarA.textContent = getInitials(a.display_name);
      }
      if (avatarB) {
        avatarB.className = "avatar av-" + idxB;
        avatarB.textContent = getInitials(b.display_name);
      }
      if (nameA) nameA.textContent = a.display_name;
      if (nameB) nameB.textContent = b.display_name;

      // Count wins per player for the header highlight
      let winsA = 0;
      let winsB = 0;
      stats.forEach(({ key }) => {
        const va = Number(a[key] ?? 0);
        const vb = Number(b[key] ?? 0);
        if (va > vb) winsA++;
        else if (vb > va) winsB++;
      });

      if (playerA) playerA.classList.toggle("is-winner", winsA > winsB);
      if (playerB) playerB.classList.toggle("is-winner", winsB > winsA);

      // Stat rows
      if (statRows) {
        statRows.innerHTML = stats
          .map(({ key, label, fmt }) => {
            const va = Number(a[key] ?? 0);
            const vb = Number(b[key] ?? 0);
            const aWins = va > vb;
            const bWins = vb > va;

            return `
            <div class="h2h-stat-row">
              <span class="h2h-val-a${aWins ? " is-winner" : ""}">${fmt(a[key])}</span>
              <span class="h2h-stat-label">${label}</span>
              <span class="h2h-val-b${bWins ? " is-winner" : ""}">${fmt(b[key])}</span>
            </div>`;
          })
          .join("");
      }
    }

    selectA.addEventListener("change", render);
    selectB.addEventListener("change", render);
  }

  /* ─── Sync Form (unchanged) ─────────────────────────────────── */

  function setFeedback(node, message, state) {
    if (!node) return;
    node.textContent = message;
    node.classList.remove("is-success", "is-error", "is-pending");
    if (state) node.classList.add(state);
  }

  function initSyncForm() {
    const form = document.querySelector("[data-sync-form]");
    if (!(form instanceof HTMLFormElement) || typeof window.fetch !== "function") return;

    const feedback = form.querySelector("[data-sync-feedback]");
    const submitButton = form.querySelector("[data-sync-submit]");
    const displayNameNode = document.getElementById("sync-display-name");
    const linkStateNode = document.getElementById("sync-link-state");
    const lastSyncedNode = document.getElementById("sync-last-synced");
    const claimCodeInput = form.elements.namedItem("claim_code");
    const participantInput = form.elements.namedItem("participant_name");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const payload = {
        participant_name: participantInput instanceof HTMLInputElement ? participantInput.value.trim() : "",
      };

      if (claimCodeInput instanceof HTMLInputElement && !claimCodeInput.disabled) {
        payload.claim_code = claimCodeInput.value.trim();
      }

      if (!payload.participant_name) {
        setFeedback(feedback, "Debes indicar un nombre visible antes de sincronizar.", "is-error");
        return;
      }

      if (submitButton instanceof HTMLButtonElement) submitButton.disabled = true;
      setFeedback(feedback, "Sincronizando historial local con el servicio remoto...", "is-pending");

      try {
        const response = await window.fetch(form.action, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        let body = {};
        try {
          body = await response.json();
        } catch (_) {}

        if (!response.ok) {
          const detail = typeof body.detail === "string" ? body.detail : "No se pudo completar la sincronizacion.";
          setFeedback(feedback, detail, "is-error");
          return;
        }

        const participantName = typeof body.participant_name === "string" ? body.participant_name : payload.participant_name;
        const syncedAt = typeof body.synced_at === "string" ? body.synced_at : "Sin timestamp disponible";
        const state = body.state === "linked" ? "Vinculado" : "Actualizado";

        setFeedback(feedback, `Sync completo: ${body.synced_courses || 0} ramos y ${body.synced_assessments || 0} evaluaciones procesadas.`, "is-success");

        if (displayNameNode) displayNameNode.textContent = participantName;
        if (linkStateNode) linkStateNode.textContent = state;
        if (lastSyncedNode) lastSyncedNode.textContent = syncedAt;
        if (participantInput instanceof HTMLInputElement) {
          participantInput.value = participantName;
          participantInput.readOnly = true;
        }
        if (claimCodeInput instanceof HTMLInputElement) {
          claimCodeInput.value = "";
          claimCodeInput.disabled = true;
        }
      } catch (_) {
        setFeedback(feedback, "No se pudo conectar con el servicio de comparacion.", "is-error");
      } finally {
        if (submitButton instanceof HTMLButtonElement) submitButton.disabled = false;
      }
    });
  }

  /* ─── Init ──────────────────────────────────────────────────── */

  document.addEventListener("DOMContentLoaded", function () {
    initTabs();
    initAutoSubmit();
    initNavShadow();
    initAvatarColors();
    initHeadToHead();
    initSyncForm();
  });
})();
