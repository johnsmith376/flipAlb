async function apiGetProperties(filters) {
  // Build query string from filters (all optional)
  const params = new URLSearchParams();
  if (filters.role) params.set("role", filters.role);         // optional, backend can ignore
  if (filters.type) params.set("type", filters.type);
  if (filters.status) params.set("status", filters.status);

  const url = "/api/properties" + (params.toString() ? `?${params}` : "");

  try {
    const res = await fetch(url, { headers: { "Accept": "application/json" } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Expecting: { properties: [...] }
    if (!data || !Array.isArray(data.properties)) return [];
    return data.properties;
  } catch (err) {
    console.warn("apiGetProperties failed (expected if backend not ready):", err);
    return [];
  }
}
