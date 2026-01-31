let map;
let markersLayer;

function initMap() {
  // Center roughly on Albany; tweak later.
  map = L.map("map", { zoomControl: true }).setView([42.6526, -73.7562], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
  return map;
}

function clearPins() {
  markersLayer.clearLayers();
}

function statusColor(status) {
  switch ((status || "").toUpperCase()) {
    case "REPORTED": return "#ffd166";   // orange
    case "IN_PROCESS": return "#4ea8de"; // blue
    case "ACTIVATED": return "#80ed99";  // green
    case "KNOWN":
    default: return "#87fd48";           // bright green (6-digit)
  }
}

function addPins(properties, onClick) {
  // properties: [{ id, address, lat, lng, type, status, popup_html, estimates, ... }]
  for (const p of properties) {
    // Robust: handle numbers or numeric strings
    const lat = Number(p.lat);
    const lng = Number(p.lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;

    const color = statusColor(p.status);

    const marker = L.circleMarker([lat, lng], {
      radius: 7,
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.65,
      color: color,
      fillColor: color
    });

    // Popup HTML from backend (fallback if missing)
    marker.bindPopup(
      p.popup_html || `<div style="padding:12px"><b>${p.address || "No Address"}</b></div>`
    );

    marker.on("click", () => onClick(p));
    marker.addTo(markersLayer);
  }
}
