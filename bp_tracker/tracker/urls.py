#tracker/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('test-email/', views.test_email, name='test_email'),
    path('', views.home, name='home'),
    path('log/', views.log_reading, name='log_reading'),
    path('averages/', views.view_averages, name='view_averages'),
    path('trends/', views.display_trends, name='display_trends'),
]