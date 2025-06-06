from django.urls import path
from . import views

# Application name space
app_name = 'blog'


urlpatterns = [
    # post views

    # No arguments
    path('', views.post_list, name = 'post_list'),

    # Takes 'id' as an argument
    path('<int:id>/', views.post_detail, name = 'post_detail'),
    ]