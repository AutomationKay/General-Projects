from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Reading
from django.core import mail
from django.conf import settings

class TrackerTests(TestCase):
    def setUp(self):
        """Set up test client and create a test user."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')
        self.client.login(username='testuser', password='testpassword')
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        print(f"EMAIL_BACKEND in setUp: {settings.EMAIL_BACKEND}")

    def test_log_reading(self):
        """
        Test type: Functional Test
        Description: Test the log_reading view to ensure it creates a new reading.
        Preferred Result: A new Reading object is created with systolic 181, diastolic 120, and pulse 75.
        """
        response = self.client.post(reverse('log_reading'), {
            'systolic': 181,
            'diastolic': 120,
            'pulse': 75,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reading.objects.count(), 1)
        reading = Reading.objects.first()
        self.assertEqual(reading.systolic, 181)
        self.assertEqual(reading.diastolic, 120)
        self.assertEqual(reading.pulse, 75)

    def test_view_averages(self):
        """
        Test type: Functional Test
        Description: Test the view_averages view to ensure it calculates and displays averages correctly.
        Preferred Result: The averages displayed should be 125.0 for systolic, 82.5 for diastolic, and 71.0 for pulse.
        """
        Reading.objects.create(user=self.user, systolic=120, diastolic=80, pulse=70)
        Reading.objects.create(user=self.user, systolic=130, diastolic=85, pulse=72)
        response = self.client.get(reverse('view_averages'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Systolic: 125.0')
        self.assertContains(response, 'Diastolic: 82.5')
        self.assertContains(response, 'Pulse: 71.0')

    def test_display_trends(self):
        """
        Test type: Functional Test
        Description: Test the display_trends view to ensure it generates and displays a trends plot.
        Preferred Result: The response should contain an image element representing the trends plot.
        """
        Reading.objects.create(user=self.user, systolic=120, diastolic=80, pulse=70)
        Reading.objects.create(user=self.user, systolic=130, diastolic=85, pulse=72)
        response = self.client.get(reverse('display_trends'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img')

    def test_log_reading_requires_login(self):
        """
        Test type: Security Test
        Description: Test the log_reading view to ensure it requires login.
        Preferred Result: Redirect to login page if user is not authenticated.
        """
        self.client.logout()
        response = self.client.get(reverse('log_reading'))
        self.assertRedirects(response, '/accounts/login/?next=/log/')

    def test_view_averages_requires_login(self):
        """
        Test type: Security Test
        Description: Test the view_averages view to ensure it requires login.
        Preferred Result: Redirect to login page if user is not authenticated.
        """
        self.client.logout()
        response = self.client.get(reverse('view_averages'))
        self.assertRedirects(response, '/accounts/login/?next=/averages/')

    def test_display_trends_requires_login(self):
        """
        Test type: Security Test
        Description: Test the display_trends view to ensure it requires login.
        Preferred Result: Redirect to login page if user is not authenticated.
        """
        self.client.logout()
        response = self.client.get(reverse('display_trends'))
        self.assertRedirects(response, '/accounts/login/?next=/trends/')
        
    def test_send_email_notification(self):
        """
        Test type: Functional Test
        Description: Test the email notification functionality when a high blood pressure reading is logged.
        Preferred Result: An email with the subject 'Blood Pressure Alert' should be sent to the user's email.
        """
        print("Creating high blood pressure reading...")
        Reading.objects.create(user=self.user, systolic=181, diastolic=122, pulse=75)
        print(f'EMAIL_BACKEND in test_send_email_notification: {settings.EMAIL_BACKEND}')
        print(f"Email outbox length: {len(mail.outbox)}")
        if len(mail.outbox) > 0:
            print(f"Email subject: {mail.outboc[0].subject}")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Blood Pressure Alert', mail.outbox[0].subject)
