// collect api data for frontend 
async function apiGetProperties(filters) {
  const params = new URLSearchParams();
  if (filters.role) params.set("role", filters.role);        
  if (filters.type) params.set("type", filters.type);
  if (filters.status) params.set("status", filters.status);

  const url = "/api/properties" + (params.toString() ? `?${params}` : "");

  try {
    const res = await fetch(url, { headers: { "Accept": "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data || !Array.isArray(data.properties)) return [];
    return data.properties;
  } catch (err) {
    console.warn("apiGetProperties failed (expected if backend not ready):", err);
    return [];
  }
}
