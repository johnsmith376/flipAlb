from django.shortcuts import render
from django.http import JsonResponse
from .models import Property

def home(request):
    return render(request, "home.html")


def map(request):
    return render(request, "map.html")

def landing(request):
    return render(request, "landing.html")

def properties(request):
    role = request.GET.get('role')
    type_filter = request.GET.get('type')
    status = request.GET.get('status')
    
    qs = Property.objects.all()
    if role == 'INVESTOR':
        qs = qs.filter(property_type__in=['2-4', '5+'])
    if type_filter:
        qs = qs.filter(property_type=type_filter)
    if status:
        qs = qs.filter(status=status)
    
    data = []
    for p in qs:
        data.append({
            'id': p.id,
            'address': p.address,
            'lat': p.lat,
            'lng': p.lng,
            'condition': getattr(p, 'condition', 'Unknown'),
            'status': p.status,
            'property_type': getattr(p, 'property_type', 'UNK')
        })
    
    return JsonResponse({
        'properties': data,
        'count': len(data)
    })
