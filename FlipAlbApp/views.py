from django.shortcuts import render
from django.http import JsonResponse
from .models import Property


# ----------------------------
# Page views
# ----------------------------
def home(request):
    return render(request, "home.html")


def map(request):
    return render(request, "map.html")


def landing(request):
    return render(request, "landing.html")


# ----------------------------
# Helpers for API normalization
# ----------------------------
def normalize_status(raw_status: str) -> str:
    """
    Convert messy external status strings into a small canonical set
    used by the frontend pins + filters.

    Canonical statuses:
      - KNOWN
      - REPORTED
      - IN_PROCESS
      - ACTIVATED

    Notes:
    - Your current dataset fields include strings like:
      "Court ACTV", "Registered", "Owner MIA", "County Owned", "ACDA Owned",
      "AHA Owned", "Rehab - Permits Issued", etc.
    - You were slicing to 10 chars in your loader, which can truncate words.
      This function handles partial matches.
    """
    s = (raw_status or "").strip().upper()

    # If you ever introduce explicit statuses later, pass them through
    if s in {"KNOWN", "REPORTED", "IN_PROCESS", "ACTIVATED"}:
        return s

    # Strong signals that something is actively being processed
    in_process_keywords = [
        "REHAB", "PERMIT", "COURT", "ACTV", "ACTIVE",
        "REGISTER", "REGIST", "COUNTY", "ACDA", "AHA", "OWNED",
        "IN PRO", "PROCESS"
    ]
    if any(k in s for k in in_process_keywords):
        return "IN_PROCESS"

    # If you later add a report pipeline, you can detect those here
    report_keywords = ["REPORT", "COMPLAINT", "311", "NEIGHBOR"]
    if any(k in s for k in report_keywords):
        return "REPORTED"

    # Activated keywords (if you end up seeing these in the wild)
    activated_keywords = ["OCCUP", "SOLD", "RENT", "COMPLETE", "FINISH", "ACTIVE UNIT"]
    if any(k in s for k in activated_keywords):
        return "ACTIVATED"

    return "KNOWN"


def normalize_type(raw_type: str) -> str:
    """
    Convert dataset property description/tax code text into
    a small canonical set the frontend filter understands:
      - SFH
      - 2-4
      - 5+
      - UNK
    """
    t = (raw_type or "").strip().upper()

    if not t:
        return "UNK"

    # Common patterns in property descriptions / tax codes can be messy.
    # Heuristics:
    # - If it explicitly says single family / one family
    if "SINGLE" in t or "ONE FAMILY" in t or "1-FAM" in t or "SFH" in t:
        return "SFH"

    # - If it says 2 family / duplex / 3 family / 4 family
    if "2" in t and "FAM" in t:
        return "2-4"
    if "3" in t and "FAM" in t:
        return "2-4"
    if "4" in t and "FAM" in t:
        return "2-4"
    if "DUPLEX" in t or "TRIPLEX" in t or "FOURPLEX" in t:
        return "2-4"

    # - 5+ units / apartment / mixed / commercial-res
    if "APT" in t or "APART" in t or "MULTI" in t or "5" in t or "6" in t:
        return "5+"
    if "MIXED" in t or "COMM" in t:
        return "5+"

    # If the dataset already provides a clean token like "2-4" or "5+"
    if "2-4" in t:
        return "2-4"
    if "5+" in t:
        return "5+"
    if t in {"SFH", "2-4", "5+", "UNK"}:
        return t

    return "UNK"


def property_to_dict(p: Property) -> dict:
    canonical_status = normalize_status(getattr(p, "status", ""))
    canonical_type = normalize_type(getattr(p, "property_type", ""))

    return {
        "id": p.id,
        "address": getattr(p, "address", ""),
        "lat": getattr(p, "lat", None),
        "lng": getattr(p, "lng", None),

        # ✅ Canonical fields the frontend expects:
        "status": canonical_status,
        "type": canonical_type,

        # Optional extras for drawer/debug:
        "condition": getattr(p, "condition", "Unknown"),
        "raw_status": getattr(p, "status", ""),
        "raw_type": getattr(p, "property_type", ""),
        "city": getattr(p, "city", ""),
        
        # 🔥 INTERACTIVE POPUP
        "popup_html": f"""
            <div style='min-width:280px; padding:16px; font-family:-apple-system,BlinkMacSystemFont,sans-serif; background:white; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.15)'>
                <h3 style='margin:0 0 12px 0; color:#1a1a1a; font-size:18px'>{getattr(p, "address", "No Address")}</h3>
                <table style='width:100%; font-size:14px; line-height:1.4'>
                    <tr><td style='color:#666; padding-right:12px'><b>Status:</b></td><td>{canonical_status}</td></tr>
                    <tr><td style='color:#666; padding-right:12px'><b>Type:</b></td><td>{canonical_type}</td></tr>
                    <tr><td style='color:#666; padding-right:12px'><b>Condition:</b></td><td>{getattr(p, "condition", "Unknown")}</td></tr>
                    <tr><td style='color:#666; padding-right:12px'><b>Raw:</b></td><td>{str(getattr(p, "status", "")).replace("\\n", " ").replace("\\r", " ")[:60]}...</td></tr>
                </table>
                <button onclick="alert('🚀 flipAlb Albany Property #{p.id}\\n\\n📞 Contact Owner: Coming Soon!')" 
                        style="margin-top:16px; width:100%; padding:12px; background:linear-gradient(135deg,#4a90e2,#357abd); color:white; border:none; border-radius:8px; font-weight:600; font-size:15px; cursor:pointer; box-shadow:0 2px 8px rgba(74,144,226,0.3)">
                    💼 Contact Owner
                </button>
            </div>
        """
    }
    


# ----------------------------
# API endpoint used by frontend
# ----------------------------
def properties(request):
    """
    GET /api/properties?role=INVESTOR&type=2-4&status=IN_PROCESS

    Returns:
      { "properties": [...], "count": N }
    """
    role = request.GET.get("role")            # INVESTOR / LANDBANK / etc (optional)
    type_filter = request.GET.get("type")     # SFH / 2-4 / 5+ / UNK (optional)
    status_filter = request.GET.get("status") # KNOWN / REPORTED / IN_PROCESS / ACTIVATED (optional)

    qs = Property.objects.all()

    # Convert query params to canonical forms
    type_filter = (type_filter or "").strip().upper()
    status_filter = (status_filter or "").strip().upper()
    role = (role or "").strip().upper()

    # NOTE:
    # Because your DB currently stores raw status/type strings from the dataset,
    # it's hard to filter perfectly at the DB level.
    # For hackathon speed, we:
    #   - do light DB filtering where possible
    #   - then do final filtering in Python on normalized values

    # If you have a lot of records, keep a cap for performance in dev
    qs = qs[:5000]

    props = [property_to_dict(p) for p in qs]

    # Role presets (frontend convenience)
    if role == "INVESTOR":
        # Investor: focus on multi-unit + in-process-ish inventory
        props = [x for x in props if x["type"] in {"2-4", "5+"}]
    elif role == "BUYER":
        # Buyer: single-family and maybe 2-4
        props = [x for x in props if x["type"] in {"SFH", "2-4"}]
    elif role == "LANDBANK":
        # Land bank: prioritize things in process or known; keep broad for now
        # You can tighten later (tax delinquent, violations, etc.)
        pass
    elif role == "NONPROFIT":
        # Nonprofit: multi-unit + SFH can both matter; keep broad for now
        pass

    if type_filter in {"SFH", "2-4", "5+", "UNK"}:
        props = [x for x in props if x["type"] == type_filter]

    if status_filter in {"KNOWN", "REPORTED", "IN_PROCESS", "ACTIVATED"}:
        props = [x for x in props if x["status"] == status_filter]

    return JsonResponse({
        "properties": props,
        "count": len(props),
    })
