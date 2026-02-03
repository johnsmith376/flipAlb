let map;
let markersLayer;


// initialize map
function initMap() {
  map = L.map("map", { zoomControl: true }).setView([42.6526, -73.7562], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
  return map;
}

// clear pins
function clearPins() {
  markersLayer.clearLayers();
}

// status color code
function statusColor(status) {
  switch ((status || "").toUpperCase()) {
    case "REPORTED": return "#ff6666ff";   
    case "IN_PROCESS": return "#4cb6f8ff";
    case "ACTIVATED": return "#21ff55ff";  
    case "Status Unknown":
    default: return "#ea87d4ff";          
  }
}

// draw pins
function addPins(properties, onClick) {
  for (const p of properties) {
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

    marker.bindPopup(
      p.popup_html || `<div style="padding:12px"><b>${p.address || "No Address"}</b></div>`
    );

    marker.on("click", () => onClick(p));
    marker.addTo(markersLayer);
  }
}
