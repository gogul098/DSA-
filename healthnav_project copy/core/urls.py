from django.urls import path
from . import views

urlpatterns = [
    # The main page
    path('', views.index, name='index'),

    # API endpoint for the symptom checker
    path('api/symptom_check/', views.symptom_check_api, name='symptom_check_api'),

    # API endpoint for finding pharmacies
    path('api/find_pharmacies/', views.find_pharmacies_api, name='find_pharmacies_api'),
]