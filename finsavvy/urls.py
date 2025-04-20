# example/urls.py
from django.urls import path

from finsavvy.views import dashboard


urlpatterns = [
    path('', dashboard),
]