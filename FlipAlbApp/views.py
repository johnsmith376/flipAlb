from django.shortcuts import render
from django.http import JsonResponse
from .models import Property
from decimal import Decimal
from typing import Optional
import json

# home page
def home(request):
    return render(request, "home.html")

# map page
def map(request):
    return render(request, "map.html")

# landing page 
def landing(request):
    return render(request, "landing.html")


def yn(val):
    s = (val or "").strip().upper()
    return s in {"Y", "YES", "TRUE", "T", "1"}

def onoff(val):
    s = (val or "").strip().upper()
    if "ON" in s:
        return "ON"
    if "OFF" in s:
        return "OFF"
    return ""

def to_int(val):
    try:
        if val is None or val == "":
            return None
        return int(val)
    except Exception:
        return None

def to_float(val):
    try:
        if val is None or val == "":
            return None
        if isinstance(val, Decimal):
            return float(val)
        return float(val)
    except Exception:
        return None

def fmt_money(n):
    return f"${n:,.0f}"

def fmt_money_opt(n):
    if n is None:
        return "—"
    try:
        return fmt_money(int(round(float(n))))
    except Exception:
        return "—"



def normalize_status(raw_status: str) -> str:
    s = (raw_status or "").strip().upper()

    if s in {"REPORTED", "IN_PROCESS", "ACTIVATED"}:
        return s

    in_process_keywords = ["REHAB","PERMIT","COURT","ACTV","ACTIVE","REGISTER","REGIST","COUNTY","ACDA","AHA","OWNED","IN PRO","PROCESS"]
    if any(k in s for k in in_process_keywords):
        return "IN_PROCESS"

    report_keywords = ["REPORT","COMPLAINT","311","NEIGHBOR"]
    if any(k in s for k in report_keywords):
        return "REPORTED"

    activated_keywords = ["OCCUP","SOLD","RENT","COMPLETE","FINISH"]
    if any(k in s for k in activated_keywords):
        return "ACTIVATED"

    return "Status Unknown"



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

def type_display_name(canonical_type: str) -> str:
    return {
        "SFH": "Single Family",
        "2-4": "2–4 Units",
        "5+": "5+ Units",
        "UNK": "Unknown",
    }.get(canonical_type, "Unknown")

def condition_multiplier(condition: str) -> float:
    c = (condition or "").upper()
    if "UNSECUR" in c:
        return 1.15
    if "ABANDON" in c:
        return 1.30
    if "SECUR" in c:
        return 0.90
    return 1.00


def estimate_financials(
    canonical_type: str,
    condition: str,
    sqft: Optional[int] = None,
    age: Optional[int] = None,
    historic: Optional[str] = None,
    elevator: Optional[str] = None,
    sprinkler: Optional[str] = None,
    standpipe: Optional[str] = None,
    fire_detection: Optional[str] = None,
    electric: Optional[str] = None,
    water: Optional[str] = None,
    gas: Optional[str] = None,
    hazardous_text: Optional[str] = None,
    current_year_registration_fee=None,
    current_registration_fee=None,
    amount_of_bond=None,
) -> dict:
    """
    A simple heuristic:
    - Purchase: still type-based
    - Rehab: per-sqft if sqft exists, else fallback to your old buckets
    - Multipliers: condition + complexity + risk flags
    - Fees/bond: returned separately for UI
    """

    purchase_base = {
        "SFH": (60_000, 120_000),
        "2-4": (80_000, 160_000),
        "5+":  (120_000, 260_000),
        "UNK": (70_000, 140_000),
    }.get(canonical_type, (70_000, 140_000))

    rehab_per_sqft = {
        "SFH": (110, 180),
        "2-4": (120, 210),
        "5+":  (130, 240),
        "UNK": (115, 200),
    }.get(canonical_type, (115, 200))

    if sqft and sqft > 0:
        r_low = int(sqft * rehab_per_sqft[0])
        r_high = int(sqft * rehab_per_sqft[1])
    else:
        fallback = {
            "SFH": (80_000, 170_000),
            "2-4": (120_000, 260_000),
            "5+":  (200_000, 450_000),
            "UNK": (120_000, 250_000),
        }.get(canonical_type, (120_000, 250_000))
        r_low, r_high = fallback

    mult = 1.0

    mult *= condition_multiplier(condition)

    if (hazardous_text or "").strip():
        mult *= 1.25

    if yn(historic):
        mult *= 1.15

    if yn(elevator):
        mult *= 1.10

    systems_yes = sum([
        1 if yn(sprinkler) else 0,
        1 if yn(standpipe) else 0,
        1 if yn(fire_detection) else 0,
    ])
    mult *= (1.0 + 0.03 * systems_yes)

    utilities_off = sum([
        1 if onoff(electric) == "OFF" else 0,
        1 if onoff(water) == "OFF" else 0,
        1 if onoff(gas) == "OFF" else 0,
    ])
    mult *= (1.0 + 0.04 * utilities_off)

    if age and age >= 80:
        mult *= 1.06
    elif age and age >= 120:
        mult *= 1.10

    r_low = int(r_low * mult)
    r_high = int(r_high * mult)

    p_low, p_high = purchase_base

    arv_low = int((p_low + r_low) * 1.25)
    arv_high = int((p_high + r_high) * 1.35)

    cy_fee = to_float(current_year_registration_fee)
    cur_fee = to_float(current_registration_fee)
    bond = to_float(amount_of_bond)

    annual_fee = None
    if cy_fee is not None and cur_fee is not None:
        annual_fee = max(cy_fee, cur_fee)
    else:
        annual_fee = cy_fee if cy_fee is not None else cur_fee

    return {
        "purchase_low": p_low,
        "purchase_high": p_high,
        "rehab_low": r_low,
        "rehab_high": r_high,
        "arv_low": arv_low,
        "arv_high": arv_high,
        "annual_registration_fee": annual_fee,
        "bond_amount": bond,
        "multiplier": round(mult, 3),
    }

# money formatting
def fmt_money(n: int) -> str:
    return f"${n:,.0f}"

def property_to_dict(p: Property) -> dict:
    canonical_status = normalize_status(getattr(p, "status", ""))
    canonical_type = normalize_type(getattr(p, "property_type", ""))
    type_name = type_display_name(canonical_type)

    condition = getattr(p, "condition", "Unknown")

    # New fields (safe getattr so it won’t break if DB not fully migrated)
    sqft = to_int(getattr(p, "sqft", None))
    age = to_int(getattr(p, "age_of_building", None))
    units = to_int(getattr(p, "units", None))

    historic = getattr(p, "historic", None)
    elevator = getattr(p, "elevator", None)
    sprinkler = getattr(p, "sprinkler", None)
    standpipe = getattr(p, "standpipe", None)
    fire_detection = getattr(p, "fire_detection", None)

    electric = getattr(p, "electric", None)
    water = getattr(p, "water", None)
    gas = getattr(p, "gas", None)

    hazardous = getattr(p, "hazardous", None)
    permits_issued = getattr(p, "permits_issued", None)

    current_year_fee = getattr(p, "current_year_registration_fee", None)
    current_fee = getattr(p, "current_registration_fee", None)
    bond_amount = getattr(p, "amount_of_bond", None)
    bonding_company = getattr(p, "bonding_company", None)

    owner_name = getattr(p, "owner_name", None) or getattr(p, "ownerName", None)  # supports old model too
    owner_city = getattr(p, "owner_city", None)
    owner_state = getattr(p, "owner_state", None)
    owner_zip = getattr(p, "owner_zip", None)
    lienholder = getattr(p, "lienholder_1_name", None)
    type_of_lien = getattr(p, "type_of_lien", None)

    def fmt_sqft(v):
        if not v:
            return "—"
        return f"{int(v):,} sq ft"

    def fmt_opt(v):
        if v is None or v == "" or v == 0:
            return "—"
        return str(v)

    est = estimate_financials(
        canonical_type=canonical_type,
        condition=condition,
        sqft=sqft,
        age=age,
        historic=historic,
        elevator=elevator,
        sprinkler=sprinkler,
        standpipe=standpipe,
        fire_detection=fire_detection,
        electric=electric,
        water=water,
        gas=gas,
        hazardous_text=hazardous,
        current_year_registration_fee=current_year_fee,
        current_registration_fee=current_fee,
        amount_of_bond=bond_amount,
    )

    purchase_range = f"{fmt_money(est['purchase_low'])}–{fmt_money(est['purchase_high'])}"
    rehab_range = f"{fmt_money(est['rehab_low'])}–{fmt_money(est['rehab_high'])}"
    arv_range = f"{fmt_money(est['arv_low'])}–{fmt_money(est['arv_high'])}"

    annual_fee_display = fmt_money_opt(est.get("annual_registration_fee"))
    bond_display = fmt_money_opt(est.get("bond_amount"))

    # Owner “mailing” line (dataset only gives city/state/zip)
    owner_location = "—"
    if owner_city or owner_state or owner_zip:
        owner_location = " ".join([x for x in [owner_city, owner_state, owner_zip] if x])

    # Button: copy owner contact + parcel info to clipboard
    copy_text = (
        f"Property: {getattr(p,'address','')}\n"
        f"Owner: {owner_name or '—'}\n"
        f"Owner location: {owner_location}\n"
        f"SBL: {getattr(p,'sbl_number', '') or '—'}\n"
        f"Tax ID: {getattr(p,'tax_id_number', '') or '—'}\n"
        f"Lienholder: {lienholder or '—'} ({type_of_lien or '—'})\n"
    )

    copy_text_js = json.dumps(copy_text) 

    popup_html = f"""
    <div style='box-sizing:border-box;width:340px;max-width:calc(100vw - 60px);padding:14px;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:white;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,0.18);overflow:hidden;overflow-wrap:anywhere;'>
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

        <div style='display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:10px;'>
          <div style='padding:10px; border:1px solid #e2e8f0; border-radius:10px; background:#fafafa;'>
            <div style='font-size:11px; color:#64748b; font-weight:700;'>Sq Ft</div>
            <div style='font-size:14px; font-weight:900; color:#0f172a;'>{fmt_sqft(sqft)}</div>
          </div>
          <div style='padding:10px; border:1px solid #e2e8f0; border-radius:10px; background:#fafafa;'>
            <div style='font-size:11px; color:#64748b; font-weight:700;'>Units / Age</div>
            <div style='font-size:14px; font-weight:900; color:#0f172a;'>{fmt_opt(units)} / {fmt_opt(age)}</div>
          </div>
        </div>

        <table style='width:100%; font-size:13px; line-height:1.45; border-collapse:collapse; margin-bottom:10px;'>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Condition</td><td style='padding:2px 0;'>{condition}</td></tr>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Est. purchase</td><td style='padding:2px 0; font-weight:900;'>{purchase_range}</td></tr>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Est. rehab</td><td style='padding:2px 0; font-weight:900;'>{rehab_range}</td></tr>
          <tr><td style='color:#64748b; padding:2px 0; font-weight:700;'>Est. post-rehab value</td><td style='padding:2px 0; font-weight:900;'>{arv_range}</td></tr>
        </table>

        <div style='padding:10px; border:1px solid #e2e8f0; border-radius:10px; background:#ffffff; margin-bottom:10px;'>
          <div style='font-size:12px; font-weight:900; color:#0f172a; margin-bottom:6px;'>Owner / Contact</div>
          <div style='font-size:12px; color:#334155;'><b>{owner_name or "—"}</b></div>
          <div style='font-size:12px; color:#64748b;'>Mailing: {owner_location}</div>
          <div style='font-size:12px; color:#64748b;'>Lienholder: {lienholder or "—"}</div>
        </div>

        <div style='padding:10px; border:1px solid #e2e8f0; border-radius:10px; background:#ffffff; margin-bottom:10px;'>
          <div style='font-size:12px; font-weight:900; color:#0f172a; margin-bottom:6px;'>Fees / Bond</div>
          <div style='font-size:12px; color:#334155;'>Annual reg. fee (est): <b>{annual_fee_display}</b></div>
          <div style='font-size:12px; color:#334155;'>Bond: <b>{bond_display}</b> {f"({bonding_company})" if bonding_company else ""}</div>
        </div>

        <button
          onclick='navigator.clipboard.writeText({copy_text_js}).then(()=>alert("Copied owner + parcel info!")).catch(()=>alert("Copy failed"))'
          style="width:100%; padding:10px; background:#0f172a; color:white; border:none; border-radius:10px; font-weight:900; font-size:14px; cursor:pointer;"
        >
        📋 Copy owner info
        </button>


        <button
          onclick="alert('Lead capture coming soon for Property #{p.id}!')"
          style="margin-top:10px; width:100%; padding:10px; background:linear-gradient(135deg,#4a90e2,#357abd); color:white; border:none; border-radius:10px; font-weight:900; font-size:14px; cursor:pointer;"
        >
          💼 I’m Interested
        </button>

        <div style="margin-top:8px; font-size:11px; color:#94a3b8;">
          Estimates are heuristic for demo purposes (now adjusted for sqft + risk flags).
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

        # NEW: richer property data for frontend
        "sqft": sqft,
        "age_of_building": age,
        "units": units,
        "historic": historic,
        "elevator": elevator,
        "sprinkler": sprinkler,
        "standpipe": standpipe,
        "fire_detection": fire_detection,
        "electric": electric,
        "water": water,
        "gas": gas,
        "hazardous": hazardous,
        "permits_issued": permits_issued,

        # parcel identifiers (helpful for “contact” workflow)
        "sbl_number": getattr(p, "sbl_number", None),
        "tax_id_number": getattr(p, "tax_id_number", None),

        # NEW: owner/contact fields
        "owner": {
            "name": owner_name,
            "city": owner_city,
            "state": owner_state,
            "zip": owner_zip,
            "lienholder_1_name": lienholder,
            "type_of_lien": type_of_lien,
        },

        # NEW: fees/bond surfaced
        "fees": {
            "current_year_registration_fee": to_float(current_year_fee),
            "current_registration_fee": to_float(current_fee),
            "annual_registration_fee_est": est.get("annual_registration_fee"),
            "bond_amount": est.get("bond_amount"),
            "bonding_company": bonding_company,
        },

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
