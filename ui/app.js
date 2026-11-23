const log = document.getElementById("log");
const form = document.getElementById("form");
const q = document.getElementById("q");
const emp = document.getElementById("emp");
const btn = form.querySelector("button");
const btnReset = document.getElementById("btn-reset");

let isSubmitting = false;

// Pixelarticons SVGs (24x24 retro grid)
const ICONS = {
  loader: `<svg class="pixel-icon spin" viewBox="0 0 24 24" fill="currentColor"><path d="M13 22h-2v-6h2v6Zm-6-3H5v-2h2v2Zm12 0h-2v-2h2v2ZM9 17H7v-2h2v2Zm8 0h-2v-2h2v2Zm-9-4H2v-2h6v2Zm14 0h-6v-2h6v2ZM9 9H7V7h2v2Zm8 0h-2V7h2v2Zm-4-1h-2V2h2v6ZM7 7H5V5h2v2Zm12 0h-2V5h2v2Z"/></svg>`,
  zap: `<svg class="pixel-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M4 13h8v6h2v2h-2v2h-2v-8H2v-4h2v2Zm12 6h-2v-2h2v2Zm2-2h-2v-2h2v2Zm2-2h-2v-2h2v2Zm-6-6h8v4h-2v-2h-8V5h-2V3h2V1h2v8Zm-8 2H4V9h2v2Zm2-2H6V7h2v2Zm2-2H8V5h2v2Z"/></svg>`,
  file: `<svg class="pixel-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M18 22H6v-2h12v2ZM6 20H4V4h2v16ZM16 4h-2v4h4V6h2v14h-2V10h-6V4H6V2h10v2Zm2 2h-2V4h2v2Z"/></svg>`,
  calendar: `<svg class="pixel-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M19 22H5v-2h14v2ZM5 8h14V6h2v14h-2V10H5v10H3V6h2v2Zm12-4h2v2H5V4h2V2h2v2h6V2h2v2Z"/></svg>`,
  reload: `<svg class="pixel-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M10 16h10v2H10v4H8v-2H6v-2H4v-2h2v-2h2v-2h2v4Zm12 0h-2v-5h2v5ZM4 13H2V8h2v5Zm12-9h2v2h2v2h-2v2h-2v2h-2V8H4V6h10V2h2v2Z"/></svg>`,
};

function renderEmptyState() {
  log.innerHTML = `
    <div class="empty">
      <p class="empty-title">Ask a policy question or execute a leave request:</p>
      <div class="chips">
        <button type="button" class="chip" data-query="Do I need a doctor's note for 3 days sick leave?">
          <span class="chip-icon">${ICONS.file}</span>
          <span>Do I need a doctor's note for 3 days sick leave?</span>
        </button>
        <button type="button" class="chip" data-query="Deduct 2 casual leave days starting 2026-12-01">
          <span class="chip-icon">${ICONS.calendar}</span>
          <span>Deduct 2 casual leave days starting 2026-12-01</span>
        </button>
      </div>
    </div>
  `;
}

function bubble(role, text, tools) {
  const empty = log.querySelector(".empty");
  if (empty) empty.remove();

  const div = document.createElement("div");
  div.className = "msg " + role;

  let toolsHtml = "";
  if (role === "agent") {
    if (tools && tools.length) {
      const tags = tools.map((t) => `<span class="tool-tag">${ICONS.zap}<span>${t}</span></span>`).join("");
      toolsHtml = `<div class="tools-list">${tags}</div>`;
    } else {
      toolsHtml = `<div class="tools-list"><span class="memory-tag">${ICONS.file}<span>answered from session context</span></span></div>`;
    }
  }

  div.innerHTML = `<div class="role">${role}</div><div class="body">${text}</div>${toolsHtml}`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function loadingBubble() {
  const div = document.createElement("div");
  div.className = "msg agent loading";
  div.innerHTML = `
    <div class="role">agent</div>
    <div class="loader-box">
      <span class="loader-icon">${ICONS.loader}</span>
      <span class="loader-status">Running agent workflow</span>
      <span class="loader-timer">0.0s</span>
    </div>
  `;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;

  const timerEl = div.querySelector(".loader-timer");
  const start = performance.now();
  const interval = setInterval(() => {
    const elapsed = ((performance.now() - start) / 1000).toFixed(1);
    if (timerEl) {
      timerEl.textContent = `${elapsed}s`;
    }
  }, 100);

  return {
    remove: () => {
      clearInterval(interval);
      div.remove();
    },
  };
}

q.addEventListener("input", () => {
  btn.disabled = isSubmitting || q.value.trim() === "";
});

async function submitQuery(text) {
  if (!text || isSubmitting) return;

  bubble("user", text);
  q.value = "";
  isSubmitting = true;
  btn.disabled = true;

  const loader = loadingBubble();
  try {
    const empId = emp.value.trim() || "EMP123";
    const res = await fetch("/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Employee-ID": empId,
      },
      body: JSON.stringify({ query: text, employee_id: empId }),
    });
    const data = await res.json();
    loader.remove();
    bubble("agent", data.answer || "(no answer)", data.tools);
  } catch (err) {
    loader.remove();
    q.value = text;
    bubble("agent", "Network error: " + err.message + " - your text was restored.");
  } finally {
    isSubmitting = false;
    btn.disabled = q.value.trim() === "";
    q.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  submitQuery(q.value.trim());
});

// Clickable suggestion chips
document.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  const query = chip.dataset.query;
  if (query) {
    submitQuery(query);
  }
});

// Reset session button
if (btnReset) {
  btnReset.addEventListener("click", async () => {
    const empId = emp.value.trim() || "EMP123";
    btnReset.disabled = true;
    try {
      await fetch("/reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Employee-ID": empId,
        },
        body: JSON.stringify({ employee_id: empId }),
      });
      renderEmptyState();
      q.value = "";
      q.focus();
    } catch (err) {
      alert("Failed to reset session: " + err.message);
    } finally {
      btnReset.disabled = false;
    }
  });
}

// Initial mount
window.addEventListener("DOMContentLoaded", () => {
  if (!log.children.length) {
    renderEmptyState();
  }
  q.focus();
});
