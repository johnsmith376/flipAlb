// load time 
function nowTimeLabel() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// load status
function setStatusPill(text, kind) {
  const el = document.getElementById("statusPill");
  el.textContent = text;
  el.classList.remove("pill--ok", "pill--warn", "pill--neutral");
  el.classList.add(kind);
}

// format filters
function getFiltersFromUI() {
  return {
    role: document.getElementById("filterRole").value,
    type: document.getElementById("filterType").value,
    status: document.getElementById("filterStatus").value
  };
}

// expand location info
function openDrawer(property) {
  const drawer = document.getElementById("drawer");
  drawer.classList.remove("drawer--hidden");
  

  document.getElementById("drawerTitle").textContent = property.address || "Unknown address";
  document.getElementById("drawerSubtitle").textContent =
    `${property.type || "UNK"} • ${property.status || "Status Unkown"}`;

  const body = drawer.querySelector(".drawer__body");
  body.innerHTML = `
    <div style="display:grid; gap:10px;">
      <div style="color: var(--muted); font-size: 13px; line-height:1.35;">
        <div><strong>ID:</strong> ${property.id ?? "—"}</div>
        <div><strong>Lat/Lng:</strong> ${property.lat?.toFixed?.(5) ?? "—"}, ${property.lng?.toFixed?.(5) ?? "—"}</div>
      </div>

      <div style="padding: 12px; border: 1px solid var(--border); border-radius: 14px; background: rgba(0,0,0,0.12);">
        <div style="font-weight:700; margin-bottom:6px;">Next actions (stub)</div>
        <div style="color: var(--muted); font-size: 13px;">
          When backend endpoints are ready, this drawer can show:
          <ul style="margin: 8px 0 0 18px; padding:0;">
            <li>“I’m interested” lead form</li>
            <li>Report condition change</li>
            <li>Status updates (Land Bank)</li>
          </ul>
        </div>
      </div>
    </div>
  `;
}

// hide location info
function closeDrawer() {
  document.getElementById("drawer").classList.add("drawer--hidden");
}


// refresh pins
async function refresh() {
  setStatusPill("Loading pins…", "pill--neutral");

  const filters = getFiltersFromUI();
  const properties = await apiGetProperties(filters);

  clearPins();
  addPins(properties, openDrawer);

  document.getElementById("pinCount").textContent = String(properties.length);
  document.getElementById("lastLoad").textContent = nowTimeLabel();

  if (properties.length > 0) {
    setStatusPill(`Showing ${properties.length} pins`, "pill--ok");
  } else {
    setStatusPill("No data yet (pins will appear when /api/properties is ready)", "pill--warn");
  }
}


// initialize 
window.addEventListener("DOMContentLoaded", () => {
  initMap();

  document.getElementById("btnRefresh").addEventListener("click", refresh);
  document.getElementById("drawerClose").addEventListener("click", closeDrawer);

  ["filterRole", "filterType", "filterStatus"].forEach((id) => {
    document.getElementById(id).addEventListener("change", refresh);
  });

  refresh();
});
