# URLs for CustoVariavel

from django.urls import path
from .views_custos_variaveis import (
    CustoVariavelListView,
    CustoVariavelCreateView,
    CustoVariavelUpdateView,
    CustoVariavelDeleteView,
)

urlpatterns = [
    path('', CustoVariavelListView.as_view(), name='list_custosVariaveis'),
    path('add/', CustoVariavelCreateView.as_view(), name='add_custoVariavel'),
    path('edit/<int:pk>/', CustoVariavelUpdateView.as_view(), name='edit_custoVariavel'),
    path('delete/<int:pk>/', CustoVariavelDeleteView.as_view(), name='delete_custoVariavel'),
]
