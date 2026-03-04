from django.urls import path

from . import views

urlpatterns = [
    path('', views.schedule, name='home'),
    path('schedule/', views.schedule, name='schedule'),
]
