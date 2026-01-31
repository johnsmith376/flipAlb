from django.db import models

# Create your models here.

class Property(models.Model):
    address = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()
    condition = models.CharField(max_length=50, default='Unknown')
    status = models.CharField(max_length=50, default='vacant')  # KNOWN/REPORTED/etc
    property_type = models.CharField(max_length=50, default='UNK')  # SFH/2-4/etc
    city = models.CharField(max_length=50, default='Albany')
