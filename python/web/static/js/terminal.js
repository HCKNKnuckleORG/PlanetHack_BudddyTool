/* Built from frontend/legacy/terminal.ts - run npm run build:legacy to regenerate */
/* Terminal SSE consumer -- streams live tool output, shows findings + next steps (legacy Jinja2) */
(function (){
  const output = document.getElementById("terminal-output");
  if (!output) return;

  const jobId = output.dataset.jobId;
  if (!jobId) {
    output.textContent = "[*] No active job. Execute a phase or module to see output here.\n";
    return;
  }

  output.textContent = "";

  const progressFill = document.getElementById("progress-fill");
  const progressLabel = document.getElementById("progress-label");
  const reportActions = document.getElementById("report-actions");
  const findingsPanel = document.getElementById("findings-panel");
  const nextStepsPanel = document.getElementById("next-steps-panel");

  function classifyLine(text) {
    if (/^\[!\]/.test(text)) return "line-error";
    if (/^\[\+\]/.test(text)) return "line-success";
    if (/^\[\*\] ===/.test(text)) return "line-phase";
    if (/^\[\*\] \$/.test(text)) return "line-cmd";
    return "";
  }

  function appendLine(text){
    const span = document.createElement("span");
    const cls = classifyLine(text);
    if (cls) span.className = cls;
    span.textContent = text;
    output.appendChild(span);
    output.scrollTop = output.scrollHeight;
  }

  function updateProgress(current, total, tool, purpose){
    const pct = total > 0 ? (current / total) * 100 : 0;
    if (progressFill) (progressFill).style.width = pct + "%";
    if (progressLabel) {
      if (tool === "done") {
        progressLabel.textContent = "ALL PHASES COMPLETE";
      } else {
        progressLabel.textContent =
          "PHASE " + current + "/" + total + ": " + tool.toUpperCase() + " -- " + purpose;
      }
    }
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function escapeAttr(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function applyFindings(
    nextSteps,
    summary,
    target,
    history,
    _logFile){
    renderFindings(summary);
    renderNextSteps(nextSteps, target || "");
    renderRunHistory(history);
  }

  function loadFindings(){
    if (jobId) {
      fetch("/findings/" + jobId)
        .then((r) => r.json())
        .then((jdata) => {
          if (jdata.error) return;
          const target = jdata.target || "";
          const nextSteps = jdata.next_steps || [];
          const summary = jdata.summary || {};
          if (jdata.new_hostnames && jdata.new_hostnames.length > 0) {
            renderHostnameWarning(jdata.new_hostnames, target);
          }
          fetch("/session/findings")
            .then((r) => r.json())
            .then((sdata) => {
              if (sdata.error) return;
              const useTarget = target || (sdata.target || "");
              const useSteps =
                nextSteps.length > 0 ? nextSteps : (sdata.next_steps || []);
              const useSummary =
                Object.keys(summary).length > 0 ? summary : (sdata.summary || {});
              applyFindings(
                useSteps,
                useSummary,
                useTarget,
                sdata.history || [],
                sdata.log_file || ""
              );
            })
            .catch(() => {
              applyFindings(nextSteps, summary, target, [], "");
            });
        })
        .catch(() => {
          fetch("/session/findings")
            .then((r) => r.json())
            .then((data) => {
              if (data.error) return;
              applyFindings(
                data.next_steps || [],
                (data.summary || {}),
                data.target || "",
                data.history || [],
                data.log_file || ""
              );
            });
        });
    } else {
      fetch("/session/findings")
        .then((r) => r.json())
        .then((data) => {
          if (data.error) return;
          applyFindings(
            data.next_steps || [],
            (data.summary || {}),
            data.target || "",
            data.history || [],
            data.log_file || ""
          );
        })
        .catch(() => {});
    }
  }

  function renderRunHistory(
    history
  ){
    if (!history || history.length === 0) return;
    let container = document.getElementById("run-history-panel");
    if (!container) {
      container = document.createElement("div");
      container.id = "run-history-panel";
      container.className = "panel";
      (container).style.marginTop = "6px";
      if (findingsPanel && findingsPanel.parentNode) {
        findingsPanel.parentNode.insertBefore(container, findingsPanel);
      }
    }
    let html =
      '<div class="panel-header" style="color:var(--cyan);">[ SESSION RUN HISTORY ]</div>';
    html += '<div style="font-size:11px;color:var(--fg-dim);padding:4px 8px;">';
    html +=
      history.length +
      ' tool(s) run this session | ';
    html +=
      '<a href="/session/report?format=md" target="_blank" style="color:var(--green);text-decoration:underline;">Download Cumulative Report (MD)</a> | ';
    html +=
      '<a href="/session/report?format=html" target="_blank" style="color:var(--cyan);text-decoration:underline;">HTML</a>';
    html += "</div>";
    html +=
      '<table style="width:100%;font-size:11px;color:var(--fg);border-collapse:collapse;">';
    html +=
      '<tr style="color:var(--cyan);border-bottom:1px solid var(--border-dim);">' +
      '<th style="text-align:left;padding:3px 8px;">Tool</th>' +
      '<th style="text-align:left;padding:3px 8px;">Source</th>' +
      '<th style="text-align:left;padding:3px 8px;">Exit</th>' +
      '<th style="text-align:left;padding:3px 8px;">Time</th></tr>';
    history.forEach((h) => {
      const t = h.time ? h.time.split("T")[1].split(".")[0] : "";
      html +=
        '<tr style="border-bottom:1px solid rgba(0,255,65,0.1);">' +
        '<td style="padding:2px 8px;color:var(--green);">' +
        escapeHtml(h.tool) +
        "</td>" +
        '<td style="padding:2px 8px;">' +
        escapeHtml(h.source) +
        "</td>" +
        '<td style="padding:2px 8px;">' +
        h.exit_code +
        "</td>" +
        '<td style="padding:2px 8px;color:var(--fg-dim);">' +
        escapeHtml(t) +
        "</td></tr>";
    });
    html += "</table>";
    container.innerHTML = html;
  }

  function renderHostnameWarning(hostnames, target){
    const container = document.createElement("div");
    container.className = "panel";
    (container).style.borderColor = "var(--yellow)";
    (container).style.marginTop = "6px";
    let html =
      '<div class="panel-header" style="color:var(--yellow);">[ NEW HOSTNAMES DISCOVERED ]</div>';
    html +=
      '<p style="font-size:12px;margin:6px 0;color:var(--fg);">Recon output contains hostnames not in /etc/hosts:</p>';
    html +=
      '<p style="font-size:13px;font-weight:bold;color:var(--cyan);margin:4px 0;">' +
      escapeHtml(hostnames.join(", ")) +
      "</p>";
    html +=
      '<p style="font-size:11px;color:var(--fg-dim);margin-bottom:8px;">Add these to /etc/hosts so enumeration tools can reach them.</p>';
    html += '<div style="display:flex;gap:8px;align-items:center;">';
    html +=
      '<button class="neon-btn green" id="add-hosts-btn" style="padding:6px 14px;font-size:11px;">ADD TO /etc/hosts</button>';
    html +=
      '<span style="font-size:10px;color:var(--fg-dim);">echo "' +
      escapeHtml(target) +
      "    " +
      escapeHtml(hostnames.join(" ")) +
      '" | sudo tee -a /etc/hosts</span>';
    html += "</div>";
    container.innerHTML = html;

    if (findingsPanel && findingsPanel.parentNode) {
      findingsPanel.parentNode.insertBefore(container, findingsPanel);
    }

    const addBtn = document.getElementById("add-hosts-btn");
    if (addBtn) {
      addBtn.addEventListener("click", function () {
        this.disabled = true;
        this.textContent = "ADDING...";
        fetch("/recon/add-host", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ip: target, hostnames: hostnames }),
        })
          .then((r) => r.json())
          .then((result) => {
            if (result.success) {
              container.innerHTML =
                '<div class="preflight-info">[+] ' + escapeHtml(result.message || "") + "</div>";
            } else {
              this.textContent = "FAILED";
              this.style.borderColor = "var(--red)";
              this.style.color = "var(--red)";
            }
          });
      });
    }
  }

  function renderFindings(summary){
    if (!findingsPanel || !summary) return;
    let html = '<div class="panel-header">[ FINDINGS SUMMARY ]</div>';
    const items = [];

    const ports = summary.ports || [];
    if (ports.length > 0) {
      const portList = ports
        .map((p) => p.port + "/" + p.proto + " " + p.service)
        .join(", ");
      items.push('<span class="finding-label">OPEN PORTS:</span> ' + escapeHtml(portList));
    }

    const techs = summary.technologies || [];
    if (techs.length > 0) {
      items.push(
        '<span class="finding-label">TECH STACK:</span> ' +
          escapeHtml(techs.slice(0, 8).join(", "))
      );
    }

    const vulns = summary.vulnerabilities || [];
    if (vulns.length > 0) {
      items.push('<span class="finding-label">VULNS FOUND:</span> ' + vulns.length + " item(s)");
    }

    const dirs = summary.directories || [];
    if (dirs.length > 0) {
      items.push(
        '<span class="finding-label">DIRECTORIES:</span> ' + dirs.length + " path(s) discovered"
      );
    }

    const nuclei = summary.nuclei || [];
    if (nuclei.length > 0) {
      const crits = nuclei.filter((f) => f.severity === "critical" || f.severity === "high");
      items.push(
        '<span class="finding-label">NUCLEI:</span> ' +
          nuclei.length +
          " finding(s), " +
          crits.length +
          " critical/high"
      );
    }

    if (items.length === 0) {
      items.push(
        '<span class="finding-label">No significant findings extracted from output.</span>'
      );
    }

    html +=
      '<div class="findings-list">' +
      items.map((i) => '<div class="finding-item">' + i + "</div>").join("") +
      "</div>";

    findingsPanel.innerHTML = html;
    (findingsPanel).style.display = "block";
  }

  function renderNextSteps(steps, target){
    if (!nextStepsPanel || !steps || steps.length === 0) return;
    let html =
      '<div class="panel-header">[ RECOMMENDED NEXT STEPS -- EDIT AND RUN ]</div>';

    steps.forEach((step, idx) => {
      html += '<div class="next-step-card">';
      html += '<div class="next-step-reason">' + escapeHtml(step.reason) + "</div>";
      html += '<div class="next-step-cmd-row">';
      html += '<span style="color:var(--yellow);margin-right:6px;">$</span>';
      html +=
        '<input type="text" class="cyber-input next-step-input" data-idx="' +
        idx +
        '" value="' +
        escapeAttr(step.command) +
        '">';
      html +=
        '<button class="neon-btn green next-run-btn" data-idx="' +
        idx +
        '" style="padding:4px 12px;font-size:11px;margin-left:6px;">RUN</button>';
      html +=
        '<button class="neon-btn next-copy-btn" data-idx="' +
        idx +
        '" style="padding:4px 12px;font-size:11px;margin-left:4px;">COPY</button>';
      html += "</div></div>";
    });

    nextStepsPanel.innerHTML = html;
    (nextStepsPanel).style.display = "block";

    nextStepsPanel.querySelectorAll(".next-run-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const idx = parseInt((btn).dataset.idx || "0", 10);
        const input = nextStepsPanel.querySelector(
          '.next-step-input[data-idx="' + idx + '"]'
        );
        const cmd = input ? input.value : "";
        if (!cmd) return;
        (btn).disabled = true;
        (btn).textContent = "...";
        fetch("/nextsteps/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command: cmd, target: target || "" }),
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.job_id) {
              window.open("/terminal?job=" + data.job_id, "_blank");
            }
          });
      });
    });

    nextStepsPanel.querySelectorAll(".next-copy-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const idx = parseInt((btn).dataset.idx || "0", 10);
        const input = nextStepsPanel.querySelector(
          '.next-step-input[data-idx="' + idx + '"]'
        );
        if (input) {
          navigator.clipboard.writeText(input.value);
          const sv = document.getElementById("status-value");
          if (sv) sv.textContent = "COPIED TO CLIPBOARD";
        }
      });
    });
  }

  const source = new EventSource("/stream/" + jobId);

  source.onmessage = function (e){
    const text = String(e.data).replace(/\\n/g, "\n");
    appendLine(text);
  };

  source.addEventListener("progress", function (e){
    const ev = e;
    const parts = String(ev.data).split("|");
    if (parts.length >= 4) {
      updateProgress(
        parseInt(parts[0], 10),
        parseInt(parts[1], 10),
        parts[2],
        parts[3]
      );
    }
  });

  source.addEventListener("phase_confirm", function (e){
    try {
      const ev = e;
      const data = JSON.parse(String(ev.data));
      showPhaseConfirm(data);
    } catch (_err) {}
  });

  function showPhaseConfirm(data){
    const existing = document.getElementById("phase-confirm-panel");
    if (existing) existing.remove();

    const panel = document.createElement("div");
    panel.id = "phase-confirm-panel";
    panel.className = "panel";
    (panel).style.borderColor = "var(--yellow)";
    (panel).style.marginTop = "8px";
    (panel).style.padding = "12px";

    let html =
      '<div class="panel-header" style="color:var(--yellow);font-size:14px;">' +
      "[ PHASE " +
      escapeHtml(String(data.phase)) +
      " COMPLETE -- " +
      escapeHtml(data.tool.toUpperCase()) +
      " ]</div>";
    html +=
      "<div style=\"font-size:11px;color:var(--fg-dim);margin:4px 0 8px;\">Phase " +
      data.phase_idx +
      " of " +
      data.total +
      " | " +
      escapeHtml(data.purpose) +
      " | exit " +
      data.exit_code +
      "</div>";

    html +=
      '<div style="border:1px solid var(--border-dim);padding:8px;margin-bottom:10px;background:rgba(0,0,0,0.3);">';
    (data.findings || []).forEach((line) => {
      const lineClass = /^(OPEN PORTS|TECH STACK|FINDINGS|DIRECTORIES|NUCLEI)/i.test(line)
        ? "color:var(--green);font-weight:bold;"
        : "color:var(--fg);";
      html +=
        '<div style="font-size:12px;font-family:Courier New,monospace;' +
        lineClass +
        'padding:1px 0;">' +
        escapeHtml(line) +
        "</div>";
    });
    html += "</div>";

    html += '<div style="display:flex;gap:10px;align-items:center;">';
    html +=
      '<button class="neon-btn green" id="confirm-continue-btn" ' +
      'style="padding:8px 20px;font-size:12px;font-weight:bold;">' +
      "CONTINUE TO NEXT PHASE >>></button>";
    html +=
      '<button class="neon-btn" id="confirm-stop-btn" ' +
      'style="padding:8px 20px;font-size:12px;border-color:var(--red);color:var(--red);">' +
      "STOP HERE</button>";
    html += "</div>";

    panel.innerHTML = html;
    output.parentNode.insertBefore(panel, output.nextSibling);

    const statusVal = document.getElementById("status-value");
    if (statusVal)
      statusVal.textContent = "WAITING -- Review Phase " + data.phase + " findings and confirm";

    const continueBtn = document.getElementById("confirm-continue-btn");
    if (continueBtn) {
      continueBtn.addEventListener("click", function () {
        this.disabled = true;
        this.textContent = "CONTINUING...";
        sendConfirm(true);
        panel.remove();
        if (statusVal) statusVal.textContent = "RUNNING NEXT PHASE...";
      });
    }

    const stopBtn = document.getElementById("confirm-stop-btn");
    if (stopBtn) {
      stopBtn.addEventListener("click", function () {
        this.disabled = true;
        this.textContent = "STOPPING...";
        sendConfirm(false);
        panel.remove();
        if (statusVal) statusVal.textContent = "STOPPED BY USER";
      });
    }
  }

  function sendConfirm(shouldContinue){
    fetch("/recon/confirm/" + jobId, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ continue: shouldContinue }),
    }).catch(() => {});
  }

  source.addEventListener("done", function (){
    const existing = document.getElementById("phase-confirm-panel");
    if (existing) existing.remove();

    appendLine("\n[*] === ALL PHASES COMPLETE ===\n");
    source.close();
    const statusVal = document.getElementById("status-value");
    if (statusVal) statusVal.textContent = "EXECUTION COMPLETE -- Review findings below";
    if (reportActions) (reportActions).style.display = "flex";
    loadFindings();
  });

  source.onerror = function (){
    appendLine("\n[!] Connection to server lost.\n");
    source.close();
  };

  const statusVal = document.getElementById("status-value");
  if (statusVal) statusVal.textContent = "STREAMING LIVE OUTPUT...";

  const mdBtn = document.getElementById("report-md");
  const htmlBtn = document.getElementById("report-html");

  if (mdBtn) {
    mdBtn.addEventListener("click", function () {
      window.open("/report/" + jobId + "?format=md", "_blank");
    });
  }
  if (htmlBtn) {
    htmlBtn.addEventListener("click", function () {
      window.open("/report/" + jobId + "?format=html", "_blank");
    });
  }
})();
