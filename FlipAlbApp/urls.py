from django.urls import path
from FlipAlbApp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),
    path("map/", views.map, name="map"),
    path("landing", views.landing, name="landing")

]