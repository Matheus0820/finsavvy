# This file defines URL patterns for Veiculo CRUD operations.
# It is included in finsavvy/urls.py on line 11.
# No other file defines these routes.
# Follows user instruction to implement.

from django.urls import path
from .views_veiculo import (
    VeiculoListView,
    VeiculoCreateView,
    VeiculoUpdateView,
    VeiculoDeleteView,
)

urlpatterns = [
    path('', VeiculoListView.as_view(), name='list_veiculo'),
    path('add/', VeiculoCreateView.as_view(), name='add_veiculo'),
    path('edit/<int:pk>/', VeiculoUpdateView.as_view(), name='edit_veiculo'),
    path('delete/<int:pk>/', VeiculoDeleteView.as_view(), name='remove_veiculo'),
]
