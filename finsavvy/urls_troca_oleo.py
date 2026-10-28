# urls_troca_oleo.py

from django.urls import path
from .views_troca_oleo import (
    TrocaOleoListView,
    TrocaOleoCreateView,
    TrocaOleoUpdateView,
    TrocaOleoDeleteView,
)

urlpatterns = [
    path('', TrocaOleoListView.as_view(), name='list_troca_oleo'),
    path('add/', TrocaOleoCreateView.as_view(), name='add_troca_oleo'),
    path('edit/<int:pk>/', TrocaOleoUpdateView.as_view(), name='edit_troca_oleo'),
    path('delete/<int:pk>/', TrocaOleoDeleteView.as_view(), name='delete_troca_oleo'),
    path('remove/<int:pk>/', TrocaOleoDeleteView.as_view(), name='remove_troca_oleo'),
]
