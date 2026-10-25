from django.urls import path
from .views_veiculos import (
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
    path('remove/<int:pk>/', VeiculoDeleteView.as_view(), name='delete_veiculo'),
]
