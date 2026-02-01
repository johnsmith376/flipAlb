from django.shortcuts import render
from django.http import JsonResponse
from .models import Property

# home page
def home(request):
    return render(request, "home.html")

# map page
def map(request):
    return render(request, "map.html")

# landing page 
def landing(request):
    return render(request, "landing.html")


# group status to known key
def normalize_status(raw_status: str) -> str:
    s = (raw_status or "").strip().upper()

    if s in {"Status", "REPORTED", "IN_PROCESS", "ACTIVATED"}:
        return s

    in_process_keywords = [
        "REHAB", "PERMIT", "COURT", "ACTV", "ACTIVE",
        "REGISTER", "REGIST", "COUNTY", "ACDA", "AHA", "OWNED",
        "IN PRO", "PROCESS"
    ]
    if any(k in s for k in in_process_keywords):
        return "IN_PROCESS"

    report_keywords = ["REPORT", "COMPLAINT", "311", "NEIGHBOR"]
    if any(k in s for k in report_keywords):
        return "REPORTED"

    activated_keywords = ["OCCUP", "SOLD", "RENT", "COMPLETE", "FINISH"]
    if any(k in s for k in activated_keywords):
        return "ACTIVATED"

    return "Status Unknown"


# group property to known filter
def normalize_type(raw_type: str) -> str:
    t = (raw_type or "").strip().upper()

    if not t:
        return "UNK"

    if t in {"SFH", "2-4", "5+", "UNK"}:
        return t
    if "2-4" in t:
        return "2-4"
    if "5+" in t:
        return "5+"

    if "SINGLE" in t or "ONE FAMILY" in t or "1-FAM" in t:
        return "SFH"

    if ("2" in t and "FAM" in t) or ("3" in t and "FAM" in t) or ("4" in t and "FAM" in t):
        return "2-4"
    if any(x in t for x in ["DUPLEX", "TRIPLEX", "FOURPLEX"]):
        return "2-4"

    if any(x in t for x in ["APT", "APART", "MULTI", "MIXED", "COMM"]):
        return "5+"
    if any(x in t for x in ["5", "6", "7", "8"]):
        return "5+"

    return "UNK"

# map key to display value
def type_display_name(canonical_type: str) -> str:
    return {
        "SFH": "Single Family",
        "2-4": "2–4 Units",
        "5+": "5+ Units",
        "UNK": "Unknown",
    }.get(canonical_type, "Unknown")


# condition weight for pricing
def condition_multiplier(condition: str) -> float:
    c = (condition or "").upper()
    if "SECUR" in c:
        return 0.90
    if "UNSECUR" in c:
        return 1.15
    if "ABANDON" in c:
        return 1.30
    return 1.00

# estimate financials based on condition, size, and status
def estimate_financials(canonical_type: str, condition: str) -> dict:
    base = {
        "SFH": {"purchase": (60_000, 120_000), "rehab": (80_000, 170_000)},
        "2-4": {"purchase": (80_000, 160_000), "rehab": (120_000, 260_000)},
        "5+":  {"purchase": (120_000, 260_000), "rehab": (200_000, 450_000)},
        "UNK": {"purchase": (70_000, 140_000), "rehab": (120_000, 250_000)},
    }.get(canonical_type, {"purchase": (70_000, 140_000), "rehab": (120_000, 250_000)})

    mult = condition_multiplier(condition)

    p_low, p_high = base["purchase"]
    r_low, r_high = base["rehab"]

    r_low = int(r_low * mult)
    r_high = int(r_high * mult)

    arv_low = int((p_low + r_low) * 1.25)
    arv_high = int((p_high + r_high) * 1.35)

    return {
        "purchase_low": p_low,
        "purchase_high": p_high,
        "rehab_low": r_low,
        "rehab_high": r_high,
        "arv_low": arv_low,
        "arv_high": arv_high,
    }

# money formatting
def fmt_money(n: int) -> str:
    return f"${n:,.0f}"

# additional property information 
def property_to_dict(p: Property) -> dict:
    canonical_status = normalize_status(getattr(p, "status", ""))
    canonical_type = normalize_type(getattr(p, "property_type", ""))

    type_name = type_display_name(canonical_type)
    condition = getattr(p, "condition", "Unknown")

    sqft = getattr(p, "sqft", None)


    def fmt_opt(v, suffix=""):
        if v is None or v == "" or v == 0:
            return "—"
        return f"{v}{suffix}"

    def fmt_sqft(v):
        if v is None or v == "" or v == 0:
            return "—"
        try:
            return f"{int(v):,} sq ft"
        except Exception:
            return f"{v} sq ft"

    est = estimate_financials(canonical_type, condition)
    purchase_range = f"{fmt_money(est['purchase_low'])}–{fmt_money(est['purchase_high'])}"
    rehab_range = f"{fmt_money(est['rehab_low'])}–{fmt_money(est['rehab_high'])}"
    arv_range = f"{fmt_money(est['arv_low'])}–{fmt_money(est['arv_high'])}"

    popup_html = f"""
      <div style='min-width:320px; padding:14px; font-family:-apple-system,BlinkMacSystemFont,sans-serif; background:white; border-radius:12px; box-shadow:0 6px 24px rgba(0,0,0,0.18)'>
        <div style='font-weight:900; font-size:16px; color:#111; margin-bottom:10px;'>
          {getattr(p, "address", "No Address")}
        </div>

        <div style='display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px;'>
          <span style='font-size:12px; padding:5px 10px; border-radius:999px; background:#eef2ff; color:#1e1b4b; font-weight:800;'>
            Status: {canonical_status}
          </span>
          <span style='font-size:12px; padding:5px 10px; border-radius:999px; background:#f1f5f9; color:#0f172a; font-weight:800;'>
            Type: {type_name}
          </span>
        </div>

        <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:12px;'>
          <div style='padding:10px; border:1px solid #e2e8f0; border-radius:10px; background:#fafafa;'>
            <div style='font-size:11px; color:#64748b; font-weight:700;'>Sq Ft</div>
            <div style='font-size:14px; font-weight:900; color:#0f172a;'>{fmt_sqft(sqft)}</div>
          </div>
        </div>

        <table style='width:100%; font-size:13px; line-height:1.45; border-collapse:collapse'>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Condition</td><td style='padding:2px 0;'>{condition}</td></tr>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Est. purchase</td><td style='padding:2px 0; font-weight:900;'>{purchase_range}</td></tr>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Est. rehab</td><td style='padding:2px 0; font-weight:900;'>{rehab_range}</td></tr>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Est. post-rehab value</td><td style='padding:2px 0; font-weight:900;'>{arv_range}</td></tr>
        </table>

        <button
          onclick="alert('Lead capture coming soon for Property #{p.id}!')"
          style="margin-top:12px; width:100%; padding:10px; background:linear-gradient(135deg,#4a90e2,#357abd); color:white; border:none; border-radius:10px; font-weight:900; font-size:14px; cursor:pointer;"
        >
          💼 I’m Interested
        </button>

        <div style="margin-top:8px; font-size:11px; color:#94a3b8;">
          Beds/Baths/SqFt show when available. Estimates are heuristic for demo purposes.
        </div>
      </div>
    """

    return {
        "id": p.id,
        "address": getattr(p, "address", ""),
        "lat": getattr(p, "lat", None),
        "lng": getattr(p, "lng", None),

        "status": canonical_status,
        "type": canonical_type,
        "type_display": type_name,

        "condition": condition,
        "raw_status": getattr(p, "status", ""),
        "city": getattr(p, "city", ""),
        "sqft": sqft,

        "estimates": {
            **est,
            "purchase_range": purchase_range,
            "rehab_range": rehab_range,
            "arv_range": arv_range,
        },

        "popup_html": popup_html,
    }

# pass property pin data
def properties(request):
    role = (request.GET.get("role") or "").strip().upper()
    type_filter = (request.GET.get("type") or "").strip().upper()
    status_filter = (request.GET.get("status") or "").strip().upper()
    
    qs = Property.objects.all()[:5000]  
    props = [property_to_dict(p) for p in qs]

    if role == "INVESTOR":
        props = [x for x in props if x["type"] in {"2-4", "5+"}]
    elif role == "BUYER":
        props = [x for x in props if x["type"] in {"SFH", "2-4"}]
    elif role == "LANDBANK":
        pass
    elif role == "NONPROFIT":
        pass

    if type_filter in {"SFH", "2-4", "5+", "UNK"}:
        props = [x for x in props if x["type"] == type_filter]

    if status_filter in {"Status Unknown", "REPORTED", "IN_PROCESS", "ACTIVATED"}:
        props = [x for x in props if x["status"] == status_filter]


    return JsonResponse({"properties": props, "count": len(props)})
