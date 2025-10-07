from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('patient/form/', views.patient_form_view, name='patient_form'),
    path('patient/submit/', views.patient_submit_view, name='patient_submit'),
    path('patient/status/<str:specialty>/', views.patient_status_view, name='patient_status'),
    path('doctor/select/', views.doctor_specialty_select_view, name='doctor_specialty_select'),
    path('doctor/dashboard/<str:specialty>/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('doctor/accept/<str:specialty>/', views.doctor_accept_patient_view, name='doctor_accept_patient'),
    path('dijkstra-locator/', views.dijkstra_locator_view, name='dijkstra_locator'),
    path('api/find_pharmacies_dijkstra/', views.find_pharmacies_dijkstra_api, name='find_pharmacies_dijkstra_api'),
]
