from django.urls import path

from app_settings import views

urlpatterns = [

    path('', views.app_settings, name='app_settings'),

]
