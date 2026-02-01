from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim
import requests
import csv
import io
import time
from tqdm import tqdm
import re
from FlipAlbApp.models import Property

geolocator = Nominatim(user_agent="albany_vacant_hack")

def parse_int_sqft(x):
    if x is None:
        return None
    s = str(x).strip().lower()
    if not s:
        return None

    # remove commas (e.g., "1,425 sq ft")
    s = s.replace(",", "")

    # grab the first integer/decimal in the string
    m = re.search(r"(\d+(\.\d+)?)", s)
    if not m:
        return None

    # convert to int (1425.0 -> 1425)
    return int(float(m.group(1)))

class Command(BaseCommand):
    def handle(self, *args, **options):
        Property.objects.all().delete()  # Fresh start

        url = "https://data.ny.gov/api/views/nv2j-hmda/rows.csv?accessType=DOWNLOAD&app_token=7gKHCBp0BSATVeyxqCNQLtzYT"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()

        reader = list(csv.DictReader(io.StringIO(resp.text)))

        limit = 2000
        rows = reader[:limit]
        print(f"Processing {len(rows)} rows...")

        created = 0
        errors = 0

        for row in tqdm(rows, desc="Geocoding & saving", unit="row"):
            street_num = (row.get("Street Number") or "").strip()
            street_name = (row.get("Street Name") or "").strip()
            if not street_name:
                continue

            address = f"{street_num} {street_name}, Albany, NY".strip()

            try:
                location = geolocator.geocode(address)
                time.sleep(1)  # be nice to Nominatim

                if not location:
                    continue
                print(parse_int_sqft(row.get("Sq. Footage")))
                Property.objects.create(
                    address=address,
                    lat=location.latitude,
                    lng=location.longitude,
                    condition=(row.get("Status - secured / abandoned / unsecured / etc") or "Unknown")[:30],
                    status=(row.get("Current Status - Court ACTV / Registered / Owner MIA / County Owned / ACDA Owned / AHA Owned / Rehab - Permits Issued") or "KNOWN")[:10],
                    property_type=(row.get("Property Description / Tax Code") or "UNK"),
                    city="Albany",
                    sqft=parse_int_sqft(row.get("Sq. Footage")),
                    ownerName=row.get("owner_name")
                )

                created += 1
                tqdm.write(f"✅ {created}: {address}")  # prints without breaking the progress bar

            except Exception as e:
                errors += 1
                tqdm.write(f"❌ {address}: {e}")

        print(f"✅ Done. Created {created} properties. Errors: {errors}.")
