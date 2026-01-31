from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim
import requests
import csv
import io
import time
from FlipAlbApp.models import Property

geolocator = Nominatim(user_agent="albany_vacant_hack")

class Command(BaseCommand):
    def handle(self, *args, **options):
        Property.objects.all().delete()  # Fresh start
        
        url = "https://data.ny.gov/api/views/nv2j-hmda/rows.csv?accessType=DOWNLOAD&app_token=7gKHCBp0BSATVeyxqCNQLtzYT"
        resp = requests.get(url)
        reader = list(csv.DictReader(io.StringIO(resp.text)))
        
        print(f"Processing {len(reader)} rows...")
        created = 0
        for row in reader[:200]:  # Rate limit
            street_num = row.get('Street Number', '')
            street_name = row.get('Street Name', '')
            address = f"{street_num} {street_name}, Albany, NY"
            
            if street_name:
                try:
                    location = geolocator.geocode(address)
                    if location:
                        Property.objects.create(
                            address=address,
                            lat=location.latitude,
                            lng=location.longitude,
                            condition=row.get('Status - secured / abandoned / unsecured / etc', 'Unknown')[:30],
                            status=row.get('Current Status - Court ACTV / Registered / Owner MIA / County Owned / ACDA Owned / AHA Owned / Rehab - Permits Issued', 'KNOWN')[:10],
                            property_type=row.get('Property Description / Tax Code', 'UNK'),
                            city='Albany'
                        )
                        created += 1
                        print(f"✅ {created}: {address}")
                    time.sleep(1)  # Rate limit
                except:
                    pass
        
        print(f"✅ {created} geocoded properties!")
