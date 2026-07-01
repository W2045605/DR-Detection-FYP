from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.clinician_login, name='login'),
    path('register/', views.clinician_register, name='register'),
    path('logout/', views.clinician_logout, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/create/', views.create_patient, name='create_patient'),
    path('patients/<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<str:patient_id>/upload/', views.upload_scan, name='upload_scan'),
    path('scan/<int:scan_id>/loading/', views.scan_loading, name='scan_loading'),
    path('scan/<int:scan_id>/process/', views.process_scan, name='process_scan'),
    path('scan/<int:scan_id>/result/', views.scan_result, name='scan_result'),
]