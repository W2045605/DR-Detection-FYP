from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from .models import ClinicianProfile, Patient, RetinalScan
import os


def clinician_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    return render(request, 'login.html')


def clinician_register(request):
    if request.method == 'POST':
        medical_id = request.POST.get('medical_id')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html')
        if ClinicianProfile.objects.filter(medical_id=medical_id).exists():
            messages.error(request, 'Medical ID already registered')
            return render(request, 'register.html')
        user = User.objects.create_user(username=email, email=email, password=password)
        ClinicianProfile.objects.create(user=user, medical_id=medical_id)
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    return render(request, 'register.html')


def password_reset_request(request):
    if request.method == 'POST':
        medical_id = request.POST.get('medical_id')
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        try:
            profile = ClinicianProfile.objects.get(medical_id=medical_id, user__email=email)
            user = profile.user
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password reset successfully! Please login.')
            return redirect('login')
        except ClinicianProfile.DoesNotExist:
            messages.error(request, 'Invalid Medical ID or email address')
    return render(request, 'password_reset.html')


def clinician_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


@login_required
def dashboard(request):
    patients = Patient.objects.filter(clinician=request.user.clinician_profile)
    total_scans = RetinalScan.objects.filter(patient__clinician=request.user.clinician_profile).count()
    followup_count = RetinalScan.objects.filter(patient__clinician=request.user.clinician_profile, grade__gte=2).count()
    recent_scans = RetinalScan.objects.filter(patient__clinician=request.user.clinician_profile).order_by('-created_at')[:5]
    return render(request, 'dashboard.html', {
        'patients': patients,
        'total_scans': total_scans,
        'followup_count': followup_count,
        'recent_scans': recent_scans,
    })


@login_required
def patient_list(request):
    patients = Patient.objects.filter(clinician=request.user.clinician_profile)
    for patient in patients:
        patient.latest_scan = patient.scans.order_by('-created_at').first()
    return render(request, 'patient_list.html', {'patients': patients})



@login_required
def create_patient(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        
        
        existing = Patient.objects.filter(patient_id=patient_id).first()
        if existing:
            messages.info(request, f'Patient {existing.name} already exists. Redirecting to their profile.')
            return redirect('patient_detail', patient_id=existing.patient_id)
        
        Patient.objects.create(
            clinician=request.user.clinician_profile,
            patient_id=patient_id,
            name=request.POST.get('name'),
            date_of_birth=request.POST.get('date_of_birth'),
            gender=request.POST.get('gender'),
            stage_of_condition=request.POST.get('stage_of_condition'),
            examination_date=request.POST.get('examination_date') or None,
            notes=request.POST.get('notes'),
        )
        messages.success(request, 'Patient created successfully!')
        return redirect('dashboard')
    return render(request, 'create_patient.html')


@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    patient.latest_scan = patient.scans.order_by('-created_at').first()
    scans = patient.scans.all().order_by('-created_at')
    return render(request, 'patient_detail.html', {'patient': patient, 'scans': scans})


@login_required
def upload_scan(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id, clinician=request.user.clinician_profile)
    if request.method == 'POST':
        image = request.FILES.get('image')
        scan = RetinalScan.objects.create(patient=patient, image=image)
        return redirect('scan_loading', scan_id=scan.id)
    return render(request, 'upload_scan.html', {'patient': patient})


@login_required
def scan_loading(request, scan_id):
    scan = get_object_or_404(RetinalScan, id=scan_id)
    return render(request, 'scan_loading.html', {'scan': scan})


@login_required
def process_scan(request, scan_id):
    scan = get_object_or_404(RetinalScan, id=scan_id)
    try:
        from .ml_model.predictor import predict, generate_gradcam
        grade, confidence, grade_name = predict(scan.image.path)
        scan.grade = grade
        scan.confidence = confidence
        gradcam_filename = f'gradcam_{scan.id}.jpg'
        gradcam_save_path = os.path.join(settings.MEDIA_ROOT, 'gradcam', gradcam_filename)
        os.makedirs(os.path.dirname(gradcam_save_path), exist_ok=True)
        generate_gradcam(scan.image.path, gradcam_save_path)
        scan.gradcam_image = f'gradcam/{gradcam_filename}'
    except Exception as e:
        print(f'SCAN ERROR: {e}')
        import traceback
        traceback.print_exc()
    scan.save()
    return redirect('scan_result', scan_id=scan.id)


@login_required
def scan_result(request, scan_id):
    scan = get_object_or_404(RetinalScan, id=scan_id)
    advice = {
        0: 'No diabetic retinopathy detected. Continue regular annual screenings.',
        1: 'Mild DR detected. Recommend follow-up in 12 months and blood sugar management.',
        2: 'Moderate DR detected. Recommend follow-up in 6 months and referral to ophthalmologist.',
        3: 'Severe DR detected. Urgent referral to ophthalmologist recommended within 1 month.',
        4: 'Proliferative DR detected. Immediate referral to ophthalmologist required.',
    }
    return render(request, 'scan_results.html', {
        'scan': scan,
        'advice': advice.get(scan.grade, 'Please consult a specialist.')
    })