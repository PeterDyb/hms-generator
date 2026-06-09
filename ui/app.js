/* HMS-generator frontend.
   Sikkerhet: ingen inline-script (CSP), all markdown saneres med DOMPurify,
   tilgangsnøkkel oppgis av brukeren og valideres mot /api/auth/check —
   den er aldri innbakt i HTML-en. */

"use strict";

marked.setOptions({ breaks: true, gfm: true });

let currentSessionId = null;
let currentCompany   = null;
let _pollTimer       = null;
const _knownHandbooks = new Set();
const handbookData    = {};

const AGENTS = ["harvey", "donna", "mike", "louis", "jessica"];

// ─── Tilgangsnøkkel ──────────────────────────────────────────────────────────

function getKey()      { return sessionStorage.getItem("hms_api_key") || ""; }
function setKey(k)     { sessionStorage.setItem("hms_api_key", k); }
function clearKey()    { sessionStorage.removeItem("hms_api_key"); }

function showGate(showError = false) {
  document.getElementById("auth-gate").classList.remove("hidden");
  document.getElementById("auth-error").classList.toggle("hidden", !showError);
}

function hideGate() {
  document.getElementById("auth-gate").classList.add("hidden");
}

async function ensureAuth() {
  if (!getKey()) { showGate(); return false; }
  return true;
}

function apiFetch(path, options = {}) {
  return fetch(path, {
    ...options,
    headers: { "X-API-Key": getKey(), ...(options.headers || {}) },
  }).then(resp => {
    if (resp.status === 401) { clearKey(); showGate(true); }
    return resp;
  });
}

// ─── Trygg rendering ─────────────────────────────────────────────────────────

function renderMarkdown(el, markdownText) {
  el.innerHTML = DOMPurify.sanitize(marked.parse(markdownText || ""));
}

// ─── NACE-koder ──────────────────────────────────────────────────────────────

async function loadNaceOptions() {
  const select = document.getElementById("nace_kode");
  select.replaceChildren(new Option("Velg bransje …", "", true, true));
  select.options[0].disabled = true;
  try {
    const resp = await fetch("/api/nace");
    if (!resp.ok) throw new Error("Feil ved lasting");
    const data = await resp.json();
    if (!data?.length) throw new Error("Tom liste");

    const groups = {};
    data.forEach(row => {
      (groups[row.nace_hovedgruppe] ||= []).push(row);
    });

    const risikoEmoji = { "lavt": "🟢", "middels": "🟡", "høyt": "🟠", "svært høyt": "🔴" };
    Object.entries(groups).forEach(([gruppe, rader]) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = gruppe;
      rader.forEach(rad => {
        const opt = document.createElement("option");
        opt.value = rad.nace_kode;
        opt.dataset.navn = rad.nace_navn;
        opt.textContent = `${rad.nace_kode} — ${rad.nace_navn} ${risikoEmoji[rad.risikonivaa] || "⚪"}`;
        optgroup.appendChild(opt);
      });
      select.appendChild(optgroup);
    });
  } catch {
    select.replaceChildren(new Option("Kunne ikke laste bransjer", "", true, true));
    select.options[0].disabled = true;
  }
}

// ─── Skjema ──────────────────────────────────────────────────────────────────

async function onFormSubmit(e) {
  e.preventDefault();
  if (!(await ensureAuth())) return;
  const fd = new FormData(e.target);

  const naceSelect = document.getElementById("nace_kode");
  const naceNavn   = naceSelect.options[naceSelect.selectedIndex]?.dataset.navn || "";

  const payload = {
    bedriftsnavn:             fd.get("bedriftsnavn"),
    organisasjonsnummer:      fd.get("organisasjonsnummer"),
    nace_kode:                fd.get("nace_kode"),
    bransje:                  naceNavn,
    antall_ansatte:           parseInt(fd.get("antall_ansatte"), 10),
    kontaktperson:            fd.get("kontaktperson"),
    har_skiftarbeid:          fd.get("har_skiftarbeid") === "on",
    har_farlige_stoffer:      fd.get("har_farlige_stoffer") === "on",
    har_tungt_arbeid:         fd.get("har_tungt_arbeid") === "on",
    har_utvidet_egenmelding:  fd.get("har_utvidet_egenmelding") === "on",
    spesielle_risikoer:       fd.get("spesielle_risikoer"),
    oensker_personalhaandbok: fd.get("oensker_personalhaandbok") === "on",
  };

  currentCompany = payload.bedriftsnavn;

  const btn = e.target.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Starter …";

  const resp = await apiFetch("/api/sessions", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    alert(typeof err.detail === "string" ? err.detail : "Kunne ikke starte generering. Sjekk at serveren kjører.");
    btn.disabled = false;
    btn.textContent = "Start generering";
    return;
  }

  const { session_id } = await resp.json();
  currentSessionId = session_id;
  _knownHandbooks.clear();

  document.getElementById("form-section").classList.add("hidden");
  document.getElementById("progress-section").classList.remove("hidden");
  document.getElementById("progress-title").textContent =
    `Genererer håndbøker for ${payload.bedriftsnavn}`;

  startPolling(session_id);
}

// ─── Polling ─────────────────────────────────────────────────────────────────

function startPolling(sessionId) {
  stopPolling();
  _pollTimer = setInterval(() => pollSession(sessionId), 2000);
}

function stopPolling() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

async function pollSession(sessionId) {
  try {
    const sessionResp = await apiFetch(`/api/sessions/${sessionId}`);
    if (!sessionResp.ok) return;
    const session = await sessionResp.json();

    const runsResp = await apiFetch(`/api/sessions/${sessionId}/runs`);
    if (runsResp.ok) {
      const runs = await runsResp.json();
      runs.forEach(run => handleAgentUpdate(run));
    }

    const hbResp = await apiFetch(`/api/sessions/${sessionId}/handbooks`);
    if (hbResp.ok) {
      const hbs = await hbResp.json();
      hbs.forEach(hb => {
        if (!_knownHandbooks.has(hb.id)) { _knownHandbooks.add(hb.id); handleHandbookInsert(hb); }
      });
    }

    if (session.status === "completed") { stopPolling(); onCompleted(); }
    if (session.status === "failed")    { stopPolling(); onFailed(); }
  } catch { /* nettverksfeil — prøv igjen neste runde */ }
}

function handleAgentUpdate(run) {
  const card   = document.getElementById(`card-${run.agent}`);
  const output = document.getElementById(`output-${run.agent}`);
  const status = document.getElementById(`status-${run.agent}`);
  if (!card) return;

  if (run.status === "running") {
    card.classList.remove("opacity-40");
    card.classList.add("ring-2", "ring-blue-400");
    status.textContent = "Arbeider …";
    status.className = "text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600";
  } else if (run.status === "completed") {
    card.classList.remove("ring-2", "ring-blue-400");
    card.classList.add("ring-2", "ring-green-300");
    status.textContent = "Ferdig";
    status.className = "text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-600";
  } else if (run.status === "failed") {
    status.textContent = "Feil";
    status.className = "text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-600";
  }

  if (output) {
    output.textContent = run.output;   // textContent = trygt
    output.scrollTop = output.scrollHeight;
  }
}

function handleHandbookInsert(handbook) {
  handbookData[handbook.type] = handbook.content;
  if (handbook.type === "hms") {
    renderMarkdown(document.getElementById("hms-content"), handbook.content);
  } else if (handbook.type === "personal") {
    renderMarkdown(document.getElementById("personal-content"), handbook.content);
    document.getElementById("tab-personal").classList.remove("hidden");
  }
}

async function onCompleted() {
  document.getElementById("progress-title").textContent = "Håndbøkene er klare!";
  document.getElementById("progress-subtitle").textContent =
    "Kvalitetskontrollert av Louis og godkjent av Jessica. Husk: dokumentene er utkast som skal gjennomgås og godkjennes av daglig leder.";
  document.getElementById("handbooks-section").classList.remove("hidden");
  await loadAttachments();
  document.getElementById("attachments-section").scrollIntoView({ behavior: "smooth", block: "start" });
}

function onFailed() {
  document.getElementById("progress-subtitle").textContent =
    "Genereringen stoppet fordi et kvalitetskrav ikke ble oppfylt — se agentkortene for detaljer. Ingen ufullstendige dokumenter leveres.";
}

// ─── Vedlegg ─────────────────────────────────────────────────────────────────

async function loadAttachments() {
  if (!currentSessionId) return;
  try {
    const resp = await apiFetch(`/api/sessions/${currentSessionId}/files`);
    const files = await resp.json();
    if (!files.length) return;

    const grid = document.getElementById("files-grid");
    grid.replaceChildren();

    const meta = {
      excel:    { icon: "📊", color: "bg-emerald-50 border-emerald-200", label: "Excel" },
      word:     { icon: "📄", color: "bg-blue-50 border-blue-200",       label: "Word" },
      markdown: { icon: "📝", color: "bg-gray-50 border-gray-200",       label: "Markdown" },
    };

    files.forEach(file => {
      const m = meta[file.type] || meta.markdown;

      // Bygges med createElement — filnavn settes med textContent (XSS-trygt)
      const card = document.createElement("div");
      card.className = `flex items-center gap-3 p-4 rounded-xl border ${m.color} transition-colors`;

      const icon = document.createElement("span");
      icon.className = "text-2xl flex-shrink-0";
      icon.textContent = m.icon;

      const info = document.createElement("div");
      info.className = "flex-1 min-w-0";
      const nameP = document.createElement("p");
      nameP.className = "text-sm font-medium text-gray-800 truncate";
      nameP.textContent = file.name;
      const typeP = document.createElement("p");
      typeP.className = "text-xs text-gray-500";
      typeP.textContent = m.label;
      info.append(nameP, typeP);

      const btn = document.createElement("button");
      btn.className = "flex-shrink-0 text-xs px-3 py-1.5 rounded-lg bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 font-medium";
      btn.textContent = "Last ned";
      btn.addEventListener("click", () => downloadAuthFile(file.url, file.name));

      card.append(icon, info, btn);
      grid.appendChild(card);
    });

    document.getElementById("attachments-section").classList.remove("hidden");
  } catch { /* fil-listen er valgfri */ }
}

async function downloadAuthFile(url, filename) {
  const resp = await apiFetch(url);
  if (!resp.ok) { alert("Kunne ikke laste ned filen."); return; }
  triggerDownload(await resp.blob(), filename);
}

// ─── Faner ───────────────────────────────────────────────────────────────────

function showTab(type) {
  document.querySelectorAll(".handbook-panel").forEach(el => el.classList.add("hidden"));
  document.getElementById(`handbook-${type}`).classList.remove("hidden");

  document.getElementById("tab-hms").className =
    "tab-btn px-4 py-2 rounded-lg text-sm font-medium " +
    (type === "hms" ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200");
  document.getElementById("tab-personal").className =
    "tab-btn px-4 py-2 rounded-lg text-sm font-medium " +
    (type === "personal" ? "bg-blue-600 text-white" : "bg-white text-gray-600 border border-gray-200") +
    (handbookData.personal ? "" : " hidden");
}

// ─── Nedlasting ──────────────────────────────────────────────────────────────

function slugify(str) {
  return (str || "haandbok").toLowerCase().replace(/[^a-z0-9æøå]+/g, "_").replace(/^_|_$/g, "");
}

function downloadHandbook(type, format) {
  const content = handbookData[type] || "";
  const label   = type === "hms" ? "HMS_haandbok" : "Personal_haandbok";
  const base    = `${label}_${slugify(currentCompany)}_${new Date().toISOString().slice(0, 10)}`;

  if (format === "md") {
    triggerDownload(new Blob([content], { type: "text/markdown" }), `${base}.md`);

  } else if (format === "pdf") {
    // Print via skjult, sanert print-område — ingen window.open/document.write
    const printArea = document.getElementById("print-area");
    renderMarkdown(printArea, content);
    window.print();

  } else if (format === "json") {
    const jsonPayload = {
      type,
      title:        type === "hms" ? "HMS-håndbok" : "Personalhåndbok",
      company:      currentCompany || null,
      session_id:   currentSessionId,
      generated_at: new Date().toISOString(),
      content,
    };
    triggerDownload(
      new Blob([JSON.stringify(jsonPayload, null, 2)], { type: "application/json" }),
      `${base}.json`
    );
  }
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

async function copyHandbook(type, btn) {
  await navigator.clipboard.writeText(handbookData[type] || "");
  const orig = btn.textContent;
  btn.textContent = "Kopiert!";
  btn.classList.add("text-green-600");
  setTimeout(() => { btn.textContent = orig; btn.classList.remove("text-green-600"); }, 1800);
}

// ─── Reset ───────────────────────────────────────────────────────────────────

function resetUI() {
  stopPolling();
  currentSessionId = null;
  currentCompany   = null;
  handbookData.hms = handbookData.personal = undefined;
  _knownHandbooks.clear();

  AGENTS.forEach(a => {
    const card = document.getElementById(`card-${a}`);
    if (!card) return;
    card.classList.remove("ring-2", "ring-blue-400", "ring-green-300");
    card.classList.add("opacity-40");
    document.getElementById(`status-${a}`).textContent = "Venter";
    document.getElementById(`status-${a}`).className =
      "text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500";
    document.getElementById(`output-${a}`).textContent = "";
  });

  document.getElementById("hms-content").replaceChildren();
  document.getElementById("personal-content").replaceChildren();
  document.getElementById("attachments-section").classList.add("hidden");
  document.getElementById("files-grid").replaceChildren();
  document.getElementById("handbooks-section").classList.add("hidden");
  document.getElementById("tab-personal").classList.add("hidden");
  document.getElementById("progress-section").classList.add("hidden");
  document.getElementById("form-section").classList.remove("hidden");
  showTab("hms");

  const btn = document.querySelector("#company-form button[type=submit]");
  btn.disabled = false;
  btn.textContent = "Start generering";
}

// ─── Oppstart og event-lyttere ───────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  loadNaceOptions();

  document.getElementById("company-form").addEventListener("submit", onFormSubmit);
  document.getElementById("btn-reset").addEventListener("click", resetUI);

  document.querySelectorAll(".tab-btn").forEach(btn =>
    btn.addEventListener("click", () => showTab(btn.dataset.tab)));

  document.querySelectorAll(".btn-download").forEach(btn =>
    btn.addEventListener("click", () => downloadHandbook(btn.dataset.type, btn.dataset.format)));

  document.querySelectorAll(".btn-copy").forEach(btn =>
    btn.addEventListener("click", () => copyHandbook(btn.dataset.type, btn)));

  document.getElementById("auth-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const key = document.getElementById("auth-key").value.trim();
    if (!key) return;
    const resp = await fetch("/api/auth/check", { headers: { "X-API-Key": key } });
    if (resp.ok) {
      setKey(key);
      hideGate();
    } else {
      clearKey();
      showGate(true);
    }
  });

  // Vis port med en gang hvis ingen nøkkel er lagret
  if (!getKey()) showGate();
});
