#tracker/views.py
from django.shortcuts import render, redirect
from .forms import ReadingForm
from .models import Reading
from django.contrib.auth.decorators import login_required
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from .blood_pressure_data import get_blood_pressure_range


def home(request):
    return render(request, 'tracker/home.html')

@login_required
def log_reading(request):
    if request.method == "POST":
        form = ReadingForm(request.POST)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.user = request.user
            reading.save()
            send_notifications_if_needed(reading)
            
            #Fetch blood pressure range based on the input
            bp_range = get_blood_pressure_range(reading.weight, reading.height, reading.age)
            comparison = {
                'systolic' : 'normal' if bp_range['systolic'][0] <= reading.systolic <= bp_range['systolic'][1] else 'abnormal',
                'diastolic' : 'normal' if bp_range['diastolic'][0] <= reading.diastolic <= bp_range['diastolic'][1] else 'abnormal'
                }
            return redirect('view_averages')
    else:
        form = ReadingForm()
    return render(request, 'tracker/log_reading.html', {'form': form})

@login_required
def view_averages(request):
    readings = Reading.objects.filter(user=request.user).order_by('-timestamp')[:7]
    if readings.exists():
        df = pd.DataFrame(list(readings.values()))
        averages = df[['systolic', 'diastolic', 'pulse']].mean()
    else:
        averages = {'systolic': 'No data', 'diastolic' : 'No data', 'pulse' : 'No data'}
    return render(request, 'tracker/view_averages.html', {'averages': averages})

@login_required
def display_trends(request):
    readings = Reading.objects.filter(user=request.user).order_by('-timestamp')
    if readings.exists():
        df = pd.DataFrame(list(readings.values('timestamp', 'systolic', 'diastolic', 'pulse')))
        plt.figure()
        df.plot(x='timestamp', y=['systolic', 'diastolic', 'pulse'], subplots=True, layout=(3,1), figsize=(10, 8))
        plt.suptitle("Blood Pressure Trends")
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        image_base64 = base64.b64encode(image_png).decode('utf-8')
        return render(request, 'tracker/display_trends.html', {'image': image_base64})
    else:
        return render(request, 'tracker/display_trends.html', {'image': None})


def send_notifications_if_needed(reading):
    print("Checking if notification is needed...")
    if reading.systolic > 180 or reading.diastolic > 120:
        print("sending email notification...")
        send_mail(
            'Blood Pressure Alert',
            "Your blood pressure reading is dangerously high. Please consult a doctor.",
            settings.DEFAULT_FROM_EMAIL,
            [reading.user.email],
        )
        print("Email parameters:", {
            'subject': 'Blood Pressure Alert',
            'message': 'Your blood pressure reading is dangerously high. Please consult a doctor.',
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'recipient_list': [reading.user.email]
        })
        print("Email sent!")

def test_email(request):
    send_mail(
        'Test Email',
        'This is a test email.',
        settings.DEFAULT_FROM_EMAIL,
        ['automationkay@gmail.com'],
    )
    return HttpResponse("Email sent!")
