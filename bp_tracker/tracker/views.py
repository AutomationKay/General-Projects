#tracker/views.py
from django.shortcuts import render, redirect  # For rendering templates and redirecting URLs
from .forms import ReadingForm  # Importing the form class for handling reading inputs
from .models import Reading  # Importing the model class to interact with the Reading database table
from django.contrib.auth.decorators import login_required  # For restricting views to logged-in users
import pandas as pd  # For data manipulation and analysis
import matplotlib.pyplot as plt  # For creating plots and charts
from io import BytesIO  # For handling byte streams, used in image processing
import base64  # For encoding binary data to base64 strings, used in embedding images in HTML
from django.core.mail import send_mail  # For sending emails
from django.conf import settings  # For accessing settings from the Django settings file
from django.db.models import Avg  # For calculating average values in querysets
from django.http import HttpResponse  # For returning HTTP responses
from .blood_pressure_data import get_blood_pressure_range  # For getting blood pressure range based on certain criteria
import logging # For tracking and debugging issues
import joblib # For loading the trained model

# Setting up logging 
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Loading the trained model
model = joblib.load('bp_model.pkl')

def home(request):
    return render(request, 'tracker/home.html')

@login_required
def log_reading(request):
    """
    Handles the form submission for logging a new blood pressure reading.
    If the form is valid, it saves the reading and redirects to the result page.
    """
    
    if request.method == "POST":
        form = ReadingForm(request.POST)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.user = request.user
            reading.save()
            send_notifications_if_needed(reading)
            
            # Predict potential high blood pressure
            user_data = [[reading.systolic, reading.diastolic, reading.pulse, 0 if reading.sex == 'male' else 1]]
            prediction = model.predict(user_data)
            prediction_text = "High blood pressure risk" if prediction[0] else "Normal blood pressure"

            # Fetch blood pressure range based on the input
            bp_range = get_blood_pressure_range(reading.sex, reading.country)
            comparison = {
                'systolic': 'normal' if bp_range['country']['systolic'][0] <= reading.systolic <= bp_range['country']['systolic'][1] else 'abnormal',
                'diastolic': 'normal' if bp_range['country']['diastolic'][0] <= reading.diastolic <= bp_range['country']['diastolic'][1] else 'abnormal'
            }
            
            # Save comparison and prediction to session for access in result view
            request.session['comparison'] = comparison
            request.session['reading'] = {
                'systolic': reading.systolic,
                'diastolic': reading.diastolic,
                'pulse': reading.pulse,
                'prediction': prediction_text
            }
            return redirect('log_reading_result')
    else:
        form = ReadingForm()
    return render(request, 'tracker/log_reading.html', {'form': form})


@login_required
def log_reading_result(request):
    comparison = request.session.get('comparison')
    reading = request.session.get('reading')
    return render(request, 'tracker/log_reading_result.html', {'reading': reading, 'comparison': comparison})

@login_required
def view_averages_and_trends(request):
    """
    
    
    View to display the average blood pressure readings and trends in a single page.
    
    
    """
    # Fetch all readings of the logged-in user
    readings = Reading.objects.filter(user=request.user)
    
    # Calculate averages
    averages = readings.aggregate(
        Avg('systolic'), Avg('diastolic'), Avg('pulse')
    )
    
    # Round averages to whole numbers
    averages = {k: round(v) for k, v in averages.items()}


    # Plot trends
    df = pd.DataFrame(list(readings.values('timestamp', 'systolic', 'diastolic', 'pulse')))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['systolic'], label='Systolic')
    plt.plot(df.index, df['diastolic'], label='Diastolic')
    plt.plot(df.index, df['pulse'], label='Pulse')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title('Blood Pressure Trends')
    plt.ylim(0, 200)
    plt.legend()
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return render(request, 'tracker/view_averages_and_trends.html', {
        'averages': averages,
        'image': image_base64
    })

@login_required
def view_comparisons(request):
    """
    View to display comparisons of the user's readings against country and global averages.
    """
    reading = Reading.objects.filter(user=request.user).latest('timestamp')
    user_country = reading.country
    user_sex = reading.sex

    # Get country and global averages
    country_bp_range = get_blood_pressure_range(user_sex, user_country).get('country')
    global_bp_range = get_blood_pressure_range(user_sex, 'global').get('global')

    # Fetch all readings of the logged-in user
    readings = Reading.objects.filter(user=request.user)
    
    # Calculate averages
    averages = readings.aggregate(
        Avg('systolic'), Avg('diastolic'), Avg('pulse')
    )
    
    # Convert numpy float64 to float and format as integers
    if country_bp_range:
        country_avg_systolic = int(float(country_bp_range['systolic'][0]))
        country_avg_diastolic = int(float(country_bp_range['diastolic'][0]))
    else:
        country_avg_systolic = country_avg_diastolic = 0

    if global_bp_range:
        global_avg_systolic = int(float(global_bp_range['systolic'][0]))
        global_avg_diastolic = int(float(global_bp_range['diastolic'][0]))
    else:
        global_avg_systolic = global_avg_diastolic = 0

    # Plot trends
    df = pd.DataFrame(list(readings.values('timestamp', 'systolic', 'diastolic', 'pulse')))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['systolic'], label='Systolic')
    plt.plot(df.index, df['diastolic'], label='Diastolic')
    plt.plot(df.index, df['pulse'], label='Pulse')
    
    fig, axs = plt.subplots(3, 1, figsize=(10, 18))
    
    # Plot user readings
    axs[0].plot(df.index, df['systolic'], label='Systolic')
    axs[0].plot(df.index, df['diastolic'], label='Diastolic')
    axs[0].plot(df.index, df['pulse'], label='Pulse')
    axs[0].set_xlabel('Date')
    axs[0].set_ylabel('Value')
    axs[0].set_title('User Blood Pressure Readings')
    axs[0].legend()
    axs[0].set_ylim(0, 200)

    # Plot country averages
    axs[1].axhline(y=country_avg_systolic, color='r', linestyle='--', label='Country Avg Systolic')
    axs[1].axhline(y=country_avg_diastolic, color='r', linestyle='-', label='Country Avg Diastolic')
    axs[1].set_xlabel('Date')
    axs[1].set_ylabel('Value')
    axs[1].set_title('Country Averages')
    axs[1].legend()
    axs[1].set_ylim(0, 200)

    # Plot global averages
    axs[2].axhline(y=global_avg_systolic, color='g', linestyle='--', label='Global Avg Systolic')
    axs[2].axhline(y=global_avg_diastolic, color='g', linestyle='-', label='Global Avg Diastolic')
    axs[2].set_xlabel('Date')
    axs[2].set_ylabel('Value')
    axs[2].set_title('Global Averages')
    axs[2].legend()
    axs[2].set_ylim(0, 200)
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return render(request, 'tracker/view_comparisons.html', {
        'averages': {k: int(v) if v is not None else '' for k, v in averages.items()},
        'country_avg': {'systolic': country_avg_systolic, 'diastolic': country_avg_diastolic},
        'global_avg': {'systolic': global_avg_systolic, 'diastolic': global_avg_diastolic},
        'image': image_base64
    })




def send_notifications_if_needed(reading):
    """
    
    Check if a blood pressure reading exceeds the threshold and send a notification email if needed.
    
    """
    
    
    
    print("Checking if notification is needed...")
    if reading.systolic >= 180 or reading.diastolic >= 120:
        logger.debug("Blood pressure reading is high. Preparing to send email notification.")
        subject = "Blood Pressure Alert"
        message =  "Your blood pressure reading is dangerously high. Please consult a doctor."
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [reading.user.email]
        try:
            send_mail(subject, message, from_email, recipient_list)
            logger.debug("Email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    else:
        logger.debug("Blood pressure reading is not high enough to send notification.")

def test_email(request):
    send_mail(
        'Test Email',
        'This is a test email.',
        settings.DEFAULT_FROM_EMAIL,
        ['automationkay@gmail.com'],
    )
    return HttpResponse("Email sent!")

def update_dataset_with_new_reading(reading):
    data = pd.read_csv('data/bp_standardised_cleaned.csv')
    new_row = {
        'country': reading.country,
        'sex': 'male' if reading.sex == 0 else 'female',
        'Year': pd.Timestamp.now().year,
        'systolic': reading.systolic,
        'diastolic': reading.diastolic,
        'Prevalence of raised blood pressure': None
    }
    data = data.append(new_row, ignore_index=True)
    data.to_csv('data/bp_standardised_cleaned.csv', index=False)