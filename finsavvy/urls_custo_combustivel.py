# urls_custo_combustivel.py

from django.urls import path
from .views_custo_combustivel import (
    CustoCombustivelListView,
    CustoCombustivelCreateView,
    CustoCombustivelUpdateView,
    CustoCombustivelDeleteView,
)

urlpatterns = [
    path('', CustoCombustivelListView.as_view(), name='list_custoCombustivel'),
    path('add/', CustoCombustivelCreateView.as_view(), name='add_custoCombustivel'),
    path('edit/<int:pk>/', CustoCombustivelUpdateView.as_view(), name='edit_custoCombustivel'),
    path('delete/<int:pk>/', CustoCombustivelDeleteView.as_view(), name='delete_custoCombustivel'),
]
