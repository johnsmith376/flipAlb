let map;
let markersLayer;

function initMap() {
  // Center roughly on Albany; tweak later.
  map = L.map("map", { zoomControl: true }).setView([42.6526, -73.7562], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
  return map;
}

function clearPins() {
  markersLayer.clearLayers();
}

function addPins(properties, onClick) {
  // properties: [{ id, address, lat, lng, type, status, ... }]
  for (const p of properties) {
    if (typeof p.lat !== "number" || typeof p.lng !== "number") continue;

    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 7,
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.6
    });

    // Color by status (safe defaults)
    const color = statusColor(p.status);
    marker.setStyle({ color, fillColor: color });

    marker.on("click", () => onClick(p));
    marker.addTo(markersLayer);
  }
}

function statusColor(status) {
  switch (status) {
    case "REPORTED": return "#ffd166";
    case "IN_PROCESS": return "#4ea8de";
    case "ACTIVATED": return "#80ed99";
    case "KNOWN":
    default: return "#87fd48ff";
  }
}

function addPins(properties, onClick) {
  // properties: [{ id, address, lat, lng, type, status, popup_html, ... }]
  for (const p of properties) {
    if (typeof p.lat !== "number" || typeof p.lng !== "number") continue;

    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 7,
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.6
    });

    // Color by status (safe defaults)
    const color = statusColor(p.status);
    marker.setStyle({ color, fillColor: color });

    // 🔥 POPUP ON CLICK
    marker.bindPopup(p.popup_html || `<div style='padding:12px'><b>${p.address || 'No Address'}</b></div>`);

    marker.on("click", () => onClick(p));
    marker.addTo(markersLayer);
  }
}
