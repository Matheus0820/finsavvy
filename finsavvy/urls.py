# example/urls.py
from django.urls import path

from finsavvy.views import index


urlpatterns = [
    path('', index),
]