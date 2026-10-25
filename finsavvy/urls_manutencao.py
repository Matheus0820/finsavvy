# urls_manutencao.py

from django.urls import path
from .views_manutencao import (
    ManutencaoListView,
    ManutencaoCreateView,
    ManutencaoUpdateView,
    ManutencaoDeleteView,
)

urlpatterns = [
    path('', ManutencaoListView.as_view(), name='list_manutencao'),
    path('add/', ManutencaoCreateView.as_view(), name='add_manutencao'),
    path('edit/<int:pk>/', ManutencaoUpdateView.as_view(), name='edit_manutencao'),
    path('delete/<int:pk>/', ManutencaoDeleteView.as_view(), name='delete_manutencao'),
]
