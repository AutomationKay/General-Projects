#tracker/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('test-email/', views.test_email, name='test_email'),
    path('', views.home, name='home'),
    path('log/', views.log_reading, name='log_reading'),
    path('view_averages_and_trends/', views.view_averages_and_trends, name='view_averages_and_trends'),
    path('view_comparisons/', views.view_comparisons, name='view_comparisons'),
    path('log/result/', views.log_reading_result, name='log_reading_result'),
]