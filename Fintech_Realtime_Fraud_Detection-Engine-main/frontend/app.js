/* ════════════════════════════════════════
   SentinelStream — Frontend JavaScript
   ════════════════════════════════════════ */

const API = "http://127.0.0.1:8000/api";

// ── Live Clock ────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById("headerTime").textContent =
    now.toLocaleTimeString("en-IN", { hour12: false }) + " IST";
}
setInterval(updateClock, 1000);
updateClock();

// ── Tab Switching ─────────────────────────────────────────
function switchTab(tab, el) {
  document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  document.getElementById("tab-" + tab).classList.add("active");
  el.classList.add("active");

  const titles = {
    dashboard: ["Dashboard Overview",       "Real-time financial monitoring & threat analysis"],
    submit:    ["New Transaction",           "Submit a transaction for fraud analysis"],
    history:   ["Transaction History",       "View all processed transaction records"],
    rules:     ["Detection Rules",           "Active rule-based fraud detection configuration"]
  };

  document.getElementById("page-title").textContent    = titles[tab][0];
  document.getElementById("page-subtitle").textContent = titles[tab][1];

  if (tab === "dashboard") loadDashboard();
  if (tab === "history")   loadHistory();
}

// ── Dashboard Loader ──────────────────────────────────────
async function loadDashboard() {
  try {
    const [stats, txns] = await Promise.all([
      fetch(`${API}/stats`).then(r => r.json()),
      fetch(`${API}/transactions?limit=10`).then(r => r.json())
    ]);
    renderStats(stats);
    renderRiskBar(txns);
    renderRecentTable(txns);
  } catch (e) {
    console.warn("Could not load dashboard data:", e.message);
  }
}

function renderStats(s) {
  animateCount("total-txn",  s.total_transactions);
  animateCount("safe-txn",   s.safe_transactions);
  animateCount("fraud-txn",  s.fraud_transactions);
  document.getElementById("fraud-rate").textContent = s.fraud_rate.toFixed(1) + "%";
  document.getElementById("total-vol").textContent  = "₹" + formatNum(s.total_volume);
  document.getElementById("fraud-vol").textContent  = "₹" + formatNum(s.fraud_volume);
}

function animateCount(id, target) {
  const el = document.getElementById(id);
  const start = parseInt(el.textContent) || 0;
  const duration = 600;
  const startTime = performance.now();
  function step(now) {
    const p = Math.min((now - startTime) / duration, 1);
    el.textContent = Math.round(start + (target - start) * easeOut(p));
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

function formatNum(n) {
  if (n >= 1e7) return (n / 1e7).toFixed(2) + "Cr";
  if (n >= 1e5) return (n / 1e5).toFixed(2) + "L";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toFixed(0);
}

function renderRiskBar(txns) {
  const counts = { Low: 0, Medium: 0, High: 0, Critical: 0 };
  txns.forEach(t => { if (counts[t.risk_level] !== undefined) counts[t.risk_level]++; });
  const total = txns.length || 1;
  setTimeout(() => {
    document.getElementById("seg-low").style.width      = (counts.Low      / total * 100) + "%";
    document.getElementById("seg-medium").style.width   = (counts.Medium   / total * 100) + "%";
    document.getElementById("seg-high").style.width     = (counts.High     / total * 100) + "%";
    document.getElementById("seg-critical").style.width = (counts.Critical / total * 100) + "%";
  }, 100);
}

function renderRecentTable(txns) {
  const tbody = document.getElementById("recent-tbody");
  if (!txns.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-row">No transactions found. Submit one to get started.</td></tr>`;
    return;
  }
  tbody.innerHTML = txns.map(t => `
    <tr>
      <td class="mono">${t.transaction_id}</td>
      <td>${escHtml(t.user_id)}</td>
      <td class="mono">₹${parseFloat(t.amount).toLocaleString("en-IN", {minimumFractionDigits:2})}</td>
      <td><span class="badge ${t.status.toLowerCase()}">${t.status}</span></td>
      <td><span class="badge ${t.risk_level.toLowerCase()}">${t.risk_level}</span></td>
      <td class="mono">${t.risk_score}</td>
      <td class="small">${formatTs(t.timestamp)}</td>
    </tr>`).join("");
}

// ── Submit Transaction ────────────────────────────────────
async function submitTransaction(e) {
  e.preventDefault();
  const btn = document.getElementById("submitBtn");
  btn.disabled = true;
  btn.innerHTML = `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.22-8.56"/></svg> Analyzing...`;

  const payload = {
    user_id:     document.getElementById("userId").value.trim(),
    amount:      parseFloat(document.getElementById("amount").value),
    description: document.getElementById("description").value.trim() || null,
    ip_address:  document.getElementById("ipAddress").value.trim() || null
  };

  try {
    const res  = await fetch(`${API}/transaction`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!res.ok) {
      const detail = data.detail;
      const msg = Array.isArray(detail)
        ? detail.map(d => d.msg).join(", ")
        : (typeof detail === "string" ? detail : JSON.stringify(detail));
      throw new Error(msg);
    }

    renderResult(data);
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/></svg> Analyze Transaction`;
  }
}

function renderResult(d) {
  const panel    = document.getElementById("resultPanel");
  const header   = document.getElementById("resultHeader");
  const isFraud  = d.status === "Fraud";

  panel.style.display = "block";
  panel.scrollIntoView({ behavior: "smooth", block: "start" });

  header.className = "result-header " + (isFraud ? "fraud-result" : "safe-result");

  document.getElementById("resultIcon").innerHTML  = isFraud
    ? `<div style="width:52px;height:52px;border-radius:50%;background:rgba(239,68,68,0.18);border:2px solid rgba(239,68,68,0.4);display:flex;align-items:center;justify-content:center;font-size:22px;">🚨</div>`
    : `<div style="width:52px;height:52px;border-radius:50%;background:rgba(34,197,94,0.18);border:2px solid rgba(34,197,94,0.4);display:flex;align-items:center;justify-content:center;font-size:22px;">✅</div>`;

  document.getElementById("resultStatus").textContent  = d.status === "Fraud" ? "FRAUD DETECTED" : "TRANSACTION SAFE";
  document.getElementById("resultStatus").style.color  = isFraud ? "#ef4444" : "#22c55e";
  document.getElementById("resultMessage").textContent = d.message;

  document.getElementById("res-txnId").textContent  = d.transaction_id;
  document.getElementById("res-userId").textContent  = d.user_id;
  document.getElementById("res-amount").textContent  = "₹" + parseFloat(d.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 });
  document.getElementById("res-risk").innerHTML      = `<span class="badge ${d.risk_level.toLowerCase()}">${d.risk_level} Risk</span>`;
  document.getElementById("res-ts").textContent      = d.timestamp;

  const score = d.risk_score;
  document.getElementById("res-score").textContent   = score + " / 100";
  setTimeout(() => {
    document.getElementById("scoreBarFill").style.width = score + "%";
  }, 100);

  const reasonWrap = document.getElementById("flaggedWrap");
  if (d.flagged_reason) {
    reasonWrap.style.display = "block";
    document.getElementById("res-reason").textContent = d.flagged_reason;
  } else {
    reasonWrap.style.display = "none";
  }
}

function showError(msg) {
  const panel = document.getElementById("resultPanel");
  panel.style.display = "block";
  panel.innerHTML = `
    <div class="result-header fraud-result">
      <div style="width:52px;height:52px;border-radius:50%;background:rgba(239,68,68,0.18);border:2px solid rgba(239,68,68,0.4);display:flex;align-items:center;justify-content:center;font-size:22px;">❌</div>
      <div>
        <h2 style="color:#ef4444">Request Failed</h2>
        <p>${escHtml(msg)}</p>
      </div>
    </div>`;
}

// ── History Tab ───────────────────────────────────────────
let historyDebounce;
function debounceHistory() {
  clearTimeout(historyDebounce);
  historyDebounce = setTimeout(loadHistory, 400);
}

async function loadHistory() {
  const status = document.getElementById("filterStatus").value;
  const uid    = document.getElementById("filterUser").value.trim();
  let url      = `${API}/transactions?limit=100`;
  if (status) url += `&status=${encodeURIComponent(status)}`;
  if (uid)    url += `&user_id=${encodeURIComponent(uid)}`;

  try {
    const data  = await fetch(url).then(r => r.json());
    const tbody = document.getElementById("history-tbody");
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="empty-row">No records found.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map(t => `
      <tr>
        <td class="mono small">${t.transaction_id}</td>
        <td>${escHtml(t.user_id)}</td>
        <td class="mono">₹${parseFloat(t.amount).toLocaleString("en-IN", {minimumFractionDigits:2})}</td>
        <td class="small">${t.description ? escHtml(t.description) : "<span style='color:var(--text-muted)'>—</span>"}</td>
        <td><span class="badge ${t.status.toLowerCase()}">${t.status}</span></td>
        <td><span class="badge ${t.risk_level.toLowerCase()}">${t.risk_level}</span></td>
        <td class="mono">${t.risk_score}</td>
        <td class="small" style="color:var(--orange)">${t.flagged_reason ? escHtml(t.flagged_reason.substring(0,60)) + (t.flagged_reason.length > 60 ? "…" : "") : "—"}</td>
        <td class="small mono">${formatTs(t.timestamp)}</td>
      </tr>`).join("");
  } catch (e) {
    console.warn("Failed to load history:", e.message);
  }
}

// ── Utilities ─────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatTs(ts) {
  if (!ts) return "—";
  try {
    const d = new Date(ts.replace(" UTC", "Z"));
    return d.toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" });
  } catch { return ts; }
}

// Add spin animation
const style = document.createElement("style");
style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
document.head.appendChild(style);

// ── Init ──────────────────────────────────────────────────
loadDashboard();
// Week 4: UI improvements