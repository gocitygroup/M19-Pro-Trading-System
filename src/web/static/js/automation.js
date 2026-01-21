function $(id) {
  return document.getElementById(id);
}

function showAlert(message, type = "info") {
  const el = $("autoAlert");
  if (!el) return;
  el.className = `alert alert-${type}`;
  el.textContent = message;
  el.classList.remove("d-none");
  setTimeout(() => el.classList.add("d-none"), 3000);
}

function uniqueSorted(arr) {
  return Array.from(new Set(arr)).sort((a, b) => a.localeCompare(b));
}

function getCheckedBiases() {
  const biases = [];
  if ($("biasBullish").checked) biases.push("BULLISH");
  if ($("biasBearish").checked) biases.push("BEARISH");
  return biases;
}

function getCheckedPhases() {
  const phases = [];
  if ($("phaseRange").checked) phases.push("RANGE");
  if ($("phaseExpansion").checked) phases.push("EXPANSION");
  if ($("phaseMixed").checked) phases.push("MIXED");
  return phases;
}

function getCheckedTimeframes() {
  // Canonical order, stored as chain
  const order = ["D1", "H4", "H1", "M30", "M15", "M5"];
  const enabled = new Set(Array.from(document.querySelectorAll(".tfCheck")).filter(x => x.checked).map(x => x.value));
  return order.filter(tf => enabled.has(tf));
}

async function fetchJson(url, opts) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.error || data.message || `Request failed: ${resp.status}`);
  }
  return data;
}

async function loadSymbols() {
  // Pull from existing trading board endpoint (DB-backed pairs)
  try {
    const data = await fetchJson("/api/trading_board");
    const symbols = [];
    for (const s of (data.sessions || [])) {
      for (const p of (s.pairs || [])) {
        if (p.symbol) symbols.push(String(p.symbol).toUpperCase());
      }
    }
    const options = uniqueSorted(symbols);
    const sel = $("ruleSymbols");
    sel.innerHTML = "";
    for (const sym of options) {
      const opt = document.createElement("option");
      opt.value = sym;
      opt.textContent = sym;
      sel.appendChild(opt);
    }
  } catch (e) {
    // If trading board is unavailable, symbols can still be entered later (rule can be "All").
    console.warn("Failed to load symbols:", e);
  }
}

function setEditingMode(rule) {
  $("ruleId").value = rule ? String(rule.id) : "";
  $("editingBadge").style.display = rule ? "block" : "none";
  $("cancelEditBtn").style.display = rule ? "inline-block" : "none";
  $("saveRuleBtn").innerHTML = rule ? '<i class="fas fa-save"></i> Update Rule' : '<i class="fas fa-save"></i> Save Rule';
}

function resetForm() {
  $("ruleName").value = "";
  $("ruleEnabled").checked = true;
  $("allSymbols").checked = true;
  $("ruleSymbols").disabled = true;
  for (const opt of $("ruleSymbols").options) opt.selected = false;

  $("biasBullish").checked = true;
  $("biasBearish").checked = true;
  $("phaseRange").checked = true;
  $("phaseExpansion").checked = true;
  $("phaseMixed").checked = true;

  for (const el of document.querySelectorAll(".tfCheck")) el.checked = false;
  $("tfD1").checked = true;

  setEditingMode(null);
}

function populateForm(rule) {
  setEditingMode(rule);
  $("ruleName").value = rule.name || "";
  $("ruleEnabled").checked = !!rule.enabled;

  const symbols = (rule.symbols || []).map(s => String(s).toUpperCase());
  if (!symbols.length) {
    $("allSymbols").checked = true;
    $("ruleSymbols").disabled = true;
    for (const opt of $("ruleSymbols").options) opt.selected = false;
  } else {
    $("allSymbols").checked = false;
    $("ruleSymbols").disabled = false;
    const wanted = new Set(symbols);
    for (const opt of $("ruleSymbols").options) opt.selected = wanted.has(opt.value);
  }

  const biases = new Set((rule.biases || []).map(b => String(b).toUpperCase()));
  $("biasBullish").checked = biases.has("BULLISH");
  $("biasBearish").checked = biases.has("BEARISH");

  const phases = new Set((rule.market_phases || []).map(p => String(p).toUpperCase()));
  $("phaseRange").checked = phases.has("RANGE");
  $("phaseExpansion").checked = phases.has("EXPANSION");
  $("phaseMixed").checked = phases.has("MIXED");

  const tfs = new Set((rule.timeframes || []).map(t => String(t).toUpperCase()));
  for (const el of document.querySelectorAll(".tfCheck")) {
    el.checked = tfs.has(el.value);
  }
  if (!tfs.size) $("tfD1").checked = true;
}

async function loadStatus() {
  const data = await fetchJson("/api/automation/status");
  $("autoLastFetch").textContent = data.last_fetch_time || "—";
  $("autoLastSuccess").textContent = data.last_successful_cycle || "—";
  $("autoLastError").textContent = data.last_error || (data.status === "not_running" ? "not running" : "—");
  $("autoActiveCount").textContent = String(data.active_pairs_count || 0);

  const meta = data.fetch_meta ? JSON.stringify(data.fetch_meta) : "";
  $("autoFetchMeta").textContent = meta ? meta : "—";
}

async function loadRules() {
  const data = await fetchJson("/api/automation/rules");
  const tbody = $("rulesTableBody");
  tbody.innerHTML = "";

  for (const r of (data.rules || [])) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.id}</td>
      <td>${escapeHtml(r.name || "")}</td>
      <td>${r.enabled ? '<span class="badge bg-success">ON</span>' : '<span class="badge bg-secondary">OFF</span>'}</td>
      <td class="text-muted small">${(r.symbols || []).length ? escapeHtml((r.symbols || []).join(",")) : "<em>ALL</em>"}</td>
      <td class="text-muted small">${escapeHtml((r.biases || []).join(","))}</td>
      <td class="text-muted small">${escapeHtml((r.market_phases || []).join(","))}</td>
      <td class="text-muted small">${escapeHtml((r.timeframes || []).join("+"))}</td>
      <td class="text-end">
        <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${r.id}"><i class="fas fa-pen"></i></button>
        <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${r.id}"><i class="fas fa-trash"></i></button>
      </td>
    `;
    tr.dataset.rule = JSON.stringify(r);
    tbody.appendChild(tr);
  }

  tbody.querySelectorAll("button[data-action='edit']").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const tr = e.currentTarget.closest("tr");
      const rule = JSON.parse(tr.dataset.rule);
      populateForm(rule);
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  tbody.querySelectorAll("button[data-action='delete']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const id = e.currentTarget.getAttribute("data-id");
      if (!confirm(`Delete rule #${id}?`)) return;
      await fetchJson(`/api/automation/rules/${id}`, { method: "DELETE" });
      showAlert("Rule deleted", "success");
      resetForm();
      await refreshAll();
    });
  });
}

async function loadActivePairs() {
  const data = await fetchJson("/api/automation/active_pairs");
  const tbody = $("activePairsBody");
  tbody.innerHTML = "";

  for (const p of (data.active_pairs || [])) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(p.symbol || "")}</td>
      <td>${p.direction === "buy" ? '<span class="badge bg-success">BUY</span>' : '<span class="badge bg-danger">SELL</span>'}</td>
      <td class="text-muted small">${escapeHtml(p.market_phase || "")}</td>
      <td class="text-muted small">${escapeHtml((p.timeframes || []).join("+"))}</td>
      <td class="text-muted small">${p.confidence ?? ""}</td>
      <td class="text-muted small">${escapeHtml(p.expires_at || "")}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadMatches() {
  const data = await fetchJson("/api/automation/matches");
  const tbody = $("matchesBody");
  tbody.innerHTML = "";
  for (const m of (data.matches || [])) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(m.rule_name || String(m.rule_id))}</td>
      <td>${escapeHtml(m.symbol || "")}</td>
      <td>${m.direction === "buy" ? '<span class="badge bg-success">BUY</span>' : '<span class="badge bg-danger">SELL</span>'}</td>
      <td class="text-muted small">${escapeHtml(m.matched_at || "")}</td>
      <td class="text-muted small">${escapeHtml(m.expires_at || "")}</td>
    `;
    tbody.appendChild(tr);
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function refreshAll() {
  await Promise.allSettled([loadStatus(), loadRules(), loadActivePairs(), loadMatches()]);
}

document.addEventListener("DOMContentLoaded", async () => {
  if (window.ThemeManager && typeof window.ThemeManager.init === "function") {
    window.ThemeManager.init("themeToggleAutomation");
  }

  $("allSymbols").addEventListener("change", () => {
    const all = $("allSymbols").checked;
    $("ruleSymbols").disabled = all;
    if (all) {
      for (const opt of $("ruleSymbols").options) opt.selected = false;
    }
  });

  $("cancelEditBtn").addEventListener("click", () => resetForm());

  $("refreshRulesBtn").addEventListener("click", () => loadRules());
  $("refreshActiveBtn").addEventListener("click", () => loadActivePairs());
  $("refreshMatchesBtn").addEventListener("click", () => loadMatches());

  $("ruleForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = $("ruleName").value || "Rule";
    const enabled = $("ruleEnabled").checked;
    const biases = getCheckedBiases();
    const market_phases = getCheckedPhases();
    const timeframes = getCheckedTimeframes();

    if (!biases.length) {
      showAlert("Select at least one bias", "warning");
      return;
    }
    if (!market_phases.length) {
      showAlert("Select at least one market phase", "warning");
      return;
    }
    if (!timeframes.length) {
      showAlert("Select at least one timeframe", "warning");
      return;
    }

    let symbols = [];
    if (!$("allSymbols").checked) {
      symbols = Array.from($("ruleSymbols").selectedOptions).map(o => o.value);
      if (!symbols.length) {
        showAlert("Select at least one symbol (or switch to All)", "warning");
        return;
      }
    }

    const payload = { name, enabled, symbols, biases, market_phases, timeframes };
    const id = $("ruleId").value;

    if (id) {
      await fetchJson(`/api/automation/rules/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      showAlert("Rule updated", "success");
    } else {
      await fetchJson("/api/automation/rules", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showAlert("Rule created", "success");
    }

    resetForm();
    await refreshAll();
  });

  await loadSymbols();
  await refreshAll();

  // Lightweight auto-refresh
  setInterval(() => {
    refreshAll();
  }, 5000);
});

