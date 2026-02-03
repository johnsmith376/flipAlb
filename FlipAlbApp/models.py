from django.db import models

class Property(models.Model):
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50, default="Albany")
    lat = models.FloatField()
    lng = models.FloatField()

    sbl_number = models.CharField(max_length=50, null=True, blank=True)
    tax_id_number = models.CharField(max_length=50, null=True, blank=True)

    condition = models.CharField(max_length=50, default="Unknown")  
    status = models.CharField(max_length=100, default="vacant")    
    property_type = models.CharField(max_length=100, default="UNK") 
    owner_name = models.CharField(max_length=200, null=True, blank=True)
    owner_city = models.CharField(max_length=100, null=True, blank=True)
    owner_state = models.CharField(max_length=50, null=True, blank=True)
    owner_zip = models.CharField(max_length=20, null=True, blank=True)
    type_of_owner = models.CharField(max_length=100, null=True, blank=True)
    type_of_ownership = models.CharField(max_length=100, null=True, blank=True)

    lienholder_1_name = models.CharField(max_length=200, null=True, blank=True)
    type_of_lien = models.CharField(max_length=100, null=True, blank=True)
    sqft = models.IntegerField(null=True, blank=True)
    age_of_building = models.IntegerField(null=True, blank=True)
    stories = models.CharField(max_length=50, null=True, blank=True)  
    units = models.IntegerField(null=True, blank=True)

    historic = models.CharField(max_length=10, null=True, blank=True)  
    elevator = models.CharField(max_length=10, null=True, blank=True) 
    sprinkler = models.CharField(max_length=10, null=True, blank=True) 
    standpipe = models.CharField(max_length=10, null=True, blank=True) 
    fire_detection = models.CharField(max_length=10, null=True, blank=True)

    electric = models.CharField(max_length=10, null=True, blank=True)  
    water = models.CharField(max_length=10, null=True, blank=True)     
    gas = models.CharField(max_length=10, null=True, blank=True)       

    hazardous = models.TextField(null=True, blank=True)
    permits_issued = models.CharField(max_length=100, null=True, blank=True)

    current_registration_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_year_registration_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount_of_bond = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bonding_company = models.CharField(max_length=200, null=True, blank=True)

    date_of_vacancy = models.CharField(max_length=50, null=True, blank=True)
    estimated_length_of_vacancy = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.address
