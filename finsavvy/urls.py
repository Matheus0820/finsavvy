# example/urls.py
from django.urls import path

from finsavvy.views import dashboard, aviso


urlpatterns = [
    path('', aviso),
    path('dashboard/', dashboard, name='dashboard'),
]