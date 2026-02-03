from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim
import requests
import csv
import io
import time
import re
from decimal import Decimal, InvalidOperation
from tqdm import tqdm

from FlipAlbApp.models import Property

geolocator = Nominatim(user_agent="albany_vacant_hack")


def parse_int(x):
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    s = s.replace(",", "")
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else None


def parse_sqft(x):
    if x is None:
        return None
    s = str(x).strip().lower()
    if not s:
        return None
    s = s.replace(",", "")
    m = re.search(r"(\d+(\.\d+)?)", s)
    if not m:
        return None
    return int(float(m.group(1)))


def parse_money(x):
    """
    Handles values like:
      250, 250.00, $250, "$250.00", "250.00 "
    Returns Decimal or None
    """
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    s = s.replace("$", "").replace(",", "")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        # fallback: find first numeric token
        m = re.search(r"(\d+(\.\d+)?)", s)
        if not m:
            return None
        try:
            return Decimal(m.group(1))
        except (InvalidOperation, ValueError):
            return None


def clean_short(x, max_len):
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    return s[:max_len]


class Command(BaseCommand):
    help = "Imports Albany vacant building inventory properties into the database."

    def handle(self, *args, **options):
        # If you truly want a full reset each run, uncomment:
        # Property.objects.all().delete()

        url = "https://data.ny.gov/api/views/nv2j-hmda/rows.csv?accessType=DOWNLOAD"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        reader = list(csv.DictReader(io.StringIO(resp.text)))

        # keep your cap; set None if you want all rows
        limit = 2000
        rows = reader[:limit]
        print(f"Processing {len(rows)} rows...")

        created = 0
        updated = 0
        skipped = 0
        errors = 0

        # tiny in-memory cache so repeated addresses don’t geocode repeatedly
        geo_cache = {}

        for row in tqdm(rows, desc="Geocoding & saving", unit="row"):
            street_num = (row.get("Street Number") or "").strip()
            street_name = (row.get("Street Name") or "").strip()
            if not street_name:
                skipped += 1
                continue

            address = f"{street_num} {street_name}, Albany, NY".strip()

            try:
                # geocode (cached)
                if address in geo_cache:
                    location = geo_cache[address]
                else:
                    location = geolocator.geocode(address)
                    time.sleep(1)  # respect Nominatim usage
                    geo_cache[address] = location

                if not location:
                    skipped += 1
                    continue

                defaults = dict(
                    address=address,
                    city="Albany",
                    lat=location.latitude,
                    lng=location.longitude,

                    # identifiers
                    sbl_number=clean_short(row.get("SBL Number"), 50),
                    tax_id_number=clean_short(row.get("Tax ID Number"), 50),

                    # status/type
                    condition=clean_short(row.get("Status - secured / abandoned / unsecured / etc") or "Unknown", 50),
                    status=clean_short(
                        row.get(
                            "Current Status - Court ACTV / Registered / Owner MIA / County Owned / ACDA Owned / AHA Owned / Rehab - Permits Issued"
                        ) or "vacant",
                        100
                    ),
                    property_type=clean_short(row.get("Property Description / Tax Code") or "UNK", 100),

                    # owner “contact” fields
                    owner_name=clean_short(row.get("Owner Name"), 200),
                    owner_city=clean_short(row.get("Owner City"), 100),
                    owner_state=clean_short(row.get("Owner State"), 50),
                    owner_zip=clean_short(row.get("Owner Zip"), 20),
                    type_of_owner=clean_short(row.get("Type of Owner"), 100),
                    type_of_ownership=clean_short(row.get("Type of Ownership"), 100),
                    lienholder_1_name=clean_short(row.get("Lienholder (1) Name"), 200),
                    type_of_lien=clean_short(row.get("Type of Lien"), 100),

                    # estimation drivers
                    sqft=parse_sqft(row.get("Sq. Footage")),
                    age_of_building=parse_int(row.get("Age of Building")),
                    stories=clean_short(row.get("No. of Stories Above/Below Ground"), 50),
                    units=parse_int(row.get("No. of Dwelling/Office Units")),

                    historic=clean_short(row.get("Historic Y/N"), 10),
                    elevator=clean_short(row.get("Elevator Y/N"), 10),
                    sprinkler=clean_short(row.get("Sprinkler System Y/N"), 10),
                    standpipe=clean_short(row.get("Standpipe System Y/N"), 10),
                    fire_detection=clean_short(row.get("Fire Detection System Y/N"), 10),

                    electric=clean_short(row.get("Electric ON/OFF"), 10),
                    water=clean_short(row.get("Water ON/OFF"), 10),
                    gas=clean_short(row.get("Gas ON/OFF"), 10),

                    hazardous=(row.get("Hazardous materials, uses, conditions") or "").strip() or None,
                    permits_issued=clean_short(row.get("Permits Issued"), 100),

                    # fees / bond
                    current_registration_fee=parse_money(row.get("Current Registration Fee")),
                    current_year_registration_fee=parse_money(row.get("Current Year Registration Fee")),
                    amount_of_bond=parse_money(row.get("Amount of Bond")),
                    bonding_company=clean_short(row.get("Bonding Company"), 200),

                    # optional vacancy fields
                    date_of_vacancy=clean_short(row.get("Date of Vacancy"), 50),
                    estimated_length_of_vacancy=clean_short(row.get("Estimated Length of Vacancy"), 100),
                )

                # Upsert (simple key). If you prefer, key on sbl_number when present.
                obj, was_created = Property.objects.update_or_create(
                    address=address,
                    defaults=defaults
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                errors += 1
                tqdm.write(f"{address}: {e}")

        print(f"Created: {created} | Updated: {updated} | Skipped: {skipped} | Errors: {errors}")
