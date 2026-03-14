/* Built from frontend/legacy/app.ts - run npm run build:legacy to regenerate */
/* PlanetHack Web UI -- main app logic (legacy Jinja2) */

/* ── Quote rotation ──────────────────────────────────────────── */
(function (){
  const el = document.getElementById("header-quote");
  if (!el) return;

  function fetchQuote(){
    fetch("/api/quote")
      .then((r) => r.json())
      .then((data) => {
        el.textContent = '"' + data.quote + '"  -- ' + data.movie;
      })
      .catch(() => {});
  }

  fetchQuote();
  setInterval(fetchQuote, 8000);
})();

/* ── Header title animation ──────────────────────────────────── */
(function (){
  const el = document.getElementById("header-title");
  if (!el) return;

  const frames = [
    ["[ PLANETHACK ]", "#00ffff"],
    ["[ PLANETHACK ]", "#00ff41"],
    ["// HACK THE PLANET //", "#ff00ff"],
    ["// HACK THE PLANET //", "#00ffff"],
    ["< PLANETHACK MODE >", "#ff8800"],
    ["< PLANETHACK MODE >", "#ffff00"],
    ["// HACK THE PLANET //", "#00ff41"],
    ["// HACK THE PLANET //", "#33ff66"],
    ["[ PLANETHACK ]", "#00ffff"],
    ["[ PLANETHACK ]", "#00ffff"],
  ];
  let idx = 0;

  setInterval(function (){
    const [text, color] = frames[idx % frames.length];
    el.textContent = text;
    el.style.color = color;
    idx++;
  }, 2400);
})();

/* ── Recon plan builder ──────────────────────────────────────── */
(function (){
  const form = document.getElementById("recon-form");
  if (!form) return;

  const planContainer = document.getElementById("recon-plan");
  const statusVal = document.getElementById("status-value");

  function escapeAttr(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }  form.addEventListener("submit", function (e){
    e.preventDefault();
    const formData = new FormData(form);
    if (planContainer) planContainer.innerHTML = '<span class="spinner"></span> Running pre-flight checks...';
    if (statusVal) statusVal.textContent = "PRE-FLIGHT HOST CHECK...";

    fetch("/recon/preflight", { method: "POST", body: formData })
      .then((r) => r.json())
      .then(function (pf) {
        if (pf.needs_hosts_update && pf.redirect_hostname) {
          return handleHostsWarning(pf, formData);
        }
        if (pf.warnings && pf.warnings.length > 0) {
          showPreflightWarnings(pf.warnings);
        }
        if (pf.redirect_hostname && pf.hosts_ok) {
          showPreflightInfo(
            "Redirect detected: " + pf.target + " -> " + pf.redirect_hostname + " (resolved OK)"
          );
        }
        return buildPlan(formData);
      })
      .catch((err) => {
        if (planContainer) planContainer.innerHTML = '<span class="line-error">[!] ' + err + "</span>";
      });
  });

  function showPreflightInfo(msg){
    if (!planContainer) return;
    const div = document.createElement("div");
    div.className = "preflight-info";
    div.textContent = "[*] " + msg;
    planContainer.prepend(div);
  }

  function showPreflightWarnings(warnings){
    if (!planContainer) return;
    warnings.forEach(function (w) {
      const div = document.createElement("div");
      div.className = "preflight-warning";
      div.textContent = "[!] " + w;
      planContainer.prepend(div);
    });
  }

  function handleHostsWarning(pf, formData: FormData){
    if (!planContainer || !pf.redirect_hostname || !pf.target) return;
    let html = '<div class="panel" style="border-color:var(--red);">';
    html += '<div class="panel-header" style="color:var(--red);">[ /etc/hosts UPDATE REQUIRED ]</div>';
    html +=
      '<p style="font-size:12px;margin:8px 0;color:var(--fg);">' +
      'Target <strong>' +
      escapeAttr(pf.target) +
      "</strong> redirects to <strong>" +
      escapeAttr(pf.redirect_hostname) +
      "</strong> which cannot be resolved.</p>";
    html +=
      '<p style="font-size:11px;color:var(--fg-dim);margin-bottom:10px;">This is common on THM/HTB boxes. ' +
      "The hostname must be added to /etc/hosts for tools to work.</p>";
    html += '<div style="display:flex;gap:8px;">';
    html += '<button class="neon-btn green" id="hosts-add-btn">ADD TO /etc/hosts</button>';
    html += '<button class="neon-btn yellow" id="hosts-skip-btn">SKIP & BUILD ANYWAY</button>';
    html += '<button class="neon-btn red" id="hosts-abort-btn">ABORT</button>';
    html += "</div>";
    html +=
      '<p style="font-size:10px;color:var(--fg-dim);margin-top:8px;">Manual: echo "' +
      escapeAttr(pf.target) +
      "    " +
      escapeAttr(pf.redirect_hostname) +
      '" | sudo tee -a /etc/hosts</p>';
    html += "</div>";

    planContainer.innerHTML = html;

    const addBtn = document.getElementById("hosts-add-btn");
    if (addBtn) {
      addBtn.addEventListener("click", function () {
        this.disabled = true;
        this.textContent = "ADDING...";
        fetch("/recon/add-host", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ip: pf.target, hostnames: [pf.redirect_hostname] }),
        })
          .then((r) => r.json())
          .then(function (result) {
            if (result.success) {
              showPreflightInfo(result.message || "");
              const targetInput = form.querySelector('input[name="target"]');
              if (targetInput) targetInput.value = pf.redirect_hostname || "";
              formData.set("target", pf.redirect_hostname || "");
              buildPlan(formData);
            } else {
              if (planContainer)
                planContainer.innerHTML =
                  '<span class="line-error">[!] ' +
                  (result.message || "") +
                  "</span>" +
                  '<p style="font-size:11px;color:var(--fg-dim);margin-top:8px;">Run manually: echo "' +
                  escapeAttr(pf.target || "") +
                  "    " +
                  escapeAttr(pf.redirect_hostname || "") +
                  '" | sudo tee -a /etc/hosts</p>';
            }
          });
      });
    }

    const skipBtn = document.getElementById("hosts-skip-btn");
    if (skipBtn) skipBtn.addEventListener("click", () => buildPlan(formData));

    const abortBtn = document.getElementById("hosts-abort-btn");
    if (abortBtn) {
      abortBtn.addEventListener("click", function () {
        if (planContainer) planContainer.innerHTML = "";
        if (statusVal) statusVal.textContent = "ABORTED";
      });
    }
  }

  function buildPlan(formData: FormData){
    if (!planContainer) return;
    planContainer.innerHTML = '<span class="spinner"></span> Building plan...';
    if (statusVal) statusVal.textContent = "BUILDING RECON PLAN...";

    fetch("/recon/plan", { method: "POST", body: formData })
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          planContainer.innerHTML = '<span class="line-error">[!] ' + data.error + "</span>";
          if (statusVal) statusVal.textContent = "ERROR";
          return;
        }
        if (data.phases && data.target) {
          renderPlan(data.phases, data.target);
          if (statusVal)
            statusVal.textContent =
              "PLAN BUILT: " + data.phases.length + " phases for " + data.target;
        }
      })
      .catch((err) => {
        planContainer.innerHTML = '<span class="line-error">[!] ' + err + "</span>";
      });
  }

  function renderPlan(phases: Phase[], target){
    if (!planContainer) return;
    let html =
      '<div class="section-title">[ RECON PLAN -- EDIT COMMANDS BEFORE EXECUTION ]</div>';
    html +=
      '<p style="color:var(--fg-dim);font-size:11px;margin-bottom:12px;">Each command is editable. Modify flags, wordlists, ports, or options before running.</p>';

    phases.forEach(function (p, idx) {
      const avail = p.tool_available ? "" : "  [NOT FOUND]";
      html += '<div class="phase-card">';
      html +=
        '<div class="phase-title">PHASE ' +
        p.phase +
        "  |  " +
        (p.purpose || "").toUpperCase() +
        "  |  " +
        (p.tool || "").toUpperCase() +
        avail +
        "</div>";
      html += '<div class="phase-cmd-edit">';
      html += '<span style="color:var(--yellow);margin-right:6px;">$</span>';
      html +=
        '<input type="text" class="cyber-input phase-cmd-input" data-phase-idx="' +
        idx +
        '" value="' +
        escapeAttr(p.resolved_cmd) +
        '"' +
        (p.tool_available ? "" : " disabled") +
        ">";
      html += "</div>";
      html += '<div class="phase-actions">';
      html += '<button class="neon-btn green copy-btn" data-idx="' + idx + '">COPY CMD</button>';
      if (p.tool_available) {
        html +=
          '<button class="neon-btn run-single-btn" data-idx="' +
          idx +
          '" style="margin-left:6px;">RUN THIS</button>';
      }
      html += "</div></div>";
    });

    html +=
      '<button id="run-all-btn" class="neon-btn magenta wide" style="margin-top:16px">' +
      ">>> RUN ALL PHASES (SEQUENTIAL) <<<</button>";

    planContainer.innerHTML = html;

    planContainer.querySelectorAll(".phase-cmd-input").forEach(function (input) {
      const inp = input;
      inp.addEventListener("change", function () {
        const idx = parseInt(inp.dataset.phaseIdx || "0", 10);
        phases[idx].resolved_cmd = inp.value;
      });
    });

    planContainer.querySelectorAll(".copy-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const idx = parseInt((btn).dataset.idx || "0", 10);
        const val = (
          planContainer.querySelector(
            '.phase-cmd-input[data-phase-idx="' + idx + '"]'
          )
        )?.value;
        if (val)
          navigator.clipboard.writeText(val).then(function () {
            if (statusVal) statusVal.textContent = "COPIED TO CLIPBOARD";
          });
      });
    });

    planContainer.querySelectorAll(".run-single-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const idx = parseInt((btn).dataset.idx || "0", 10);
        const cmd = (
          planContainer.querySelector(
            '.phase-cmd-input[data-phase-idx="' + idx + '"]'
          )
        )?.value;
        if (!cmd) return;
        (btn).disabled = true;
        if (statusVal) statusVal.textContent = "LAUNCHING PHASE " + (idx + 1) + "...";
        fetch("/nextsteps/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command: cmd, target: target }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.job_id) {
              window.open("/terminal?job=" + data.job_id, "_blank");
            }
          });
      });
    });

    const runAll = document.getElementById("run-all-btn");
    if (runAll) {
      runAll.addEventListener("click", function () {
        planContainer.querySelectorAll(".phase-cmd-input").forEach(function (input) {
          const inp = input;
          const idx = parseInt(inp.dataset.phaseIdx || "0", 10);
          phases[idx].resolved_cmd = inp.value;
        });
        (runAll).disabled = true;
        runAll.innerHTML = '<span class="spinner"></span> LAUNCHING...';
        if (statusVal) statusVal.textContent = "LAUNCHING ALL PHASES...";

        const presetEl = form.querySelector('input[name="preset"]:checked');
        const preset = presetEl ? presetEl.value : "full";
        fetch("/recon/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phases: phases, target: target, preset: preset }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.job_id) {
              window.open("/terminal?job=" + data.job_id, "_blank");
              (runAll).disabled = false;
              runAll.textContent = ">>> RUN ALL PHASES (SEQUENTIAL) <<<";
            }
          });
      });
    }
  }
})();

/* ── Module runner ───────────────────────────────────────────── */
(function (){
  const grid = document.getElementById("module-grid");
  if (!grid) return;

  const statusVal = document.getElementById("status-value");

  grid.addEventListener("click", function (e) {
    const btn = (e.target).closest(".module-btn");
    if (!btn) return;

    const moduleId = (btn).dataset.module || "";
    const targetInput = document.getElementById("module-target");
    const target = targetInput ? targetInput.value.trim() : "";

    if (!target) {
      alert("Enter a target URL or IP address");
      return;
    }

    (btn).disabled = true;
    if (statusVal) statusVal.textContent = "RUNNING " + moduleId.toUpperCase() + "...";

    const body = { module_id: moduleId, target: target };
    if (moduleId === "recon") body.preset = "htb";
    fetch("/modules/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then((r) => r.json())
      .then((data) => {
        (btn).disabled = false;
        if (data.redirect) {
          window.location.href = data.redirect;
        } else if (data.job_id) {
          window.location.href = "/terminal?job=" + data.job_id;
        } else if (data.error) {
          alert(data.error);
        }
      })
      .catch(() => {
        (btn).disabled = false;
      });
  });
})();

/* ── Terminal clear button ───────────────────────────────────── */
(function (){
  const btn = document.getElementById("clear-terminal");
  const output = document.getElementById("terminal-output");
  if (!btn || !output) return;

  btn.addEventListener("click", function () {
    output.textContent = "";
  });
})();
