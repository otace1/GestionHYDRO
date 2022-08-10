from django.urls import path

from .views import *

urlpatterns = [
    path('add/cargo/', AddCargo.as_view(), name='addCargo'),
]
