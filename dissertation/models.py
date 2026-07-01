from django.db import models
from django.contrib.auth.models import User


class ClinicianProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clinician_profile')
    medical_id = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.medical_id}"

    class Meta:
        db_table = 'clinician_profiles'
        verbose_name = 'Clinician Profile'
        verbose_name_plural = 'Clinician Profiles'


class Patient(models.Model):
    clinician = models.ForeignKey(ClinicianProfile, on_delete=models.CASCADE, related_name='patients')
    patient_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, blank=True, null=True)
    stage_of_condition = models.CharField(max_length=100, blank=True, null=True)
    examination_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.patient_id}"


class RetinalScan(models.Model):
    DR_GRADES = [
        (0, 'No DR'),
        (1, 'Mild'),
        (2, 'Moderate'),
        (3, 'Severe'),
        (4, 'Proliferative DR'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='scans')
    image = models.ImageField(upload_to='scans/')
    grade = models.IntegerField(choices=DR_GRADES, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    gradcam_image = models.ImageField(upload_to='gradcam/', null=True, blank=True)
    image_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.get_grade_display()}"