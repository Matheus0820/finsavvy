# URLs for CustoVariavel e Categoria

from django.urls import path
from .views_custos_variaveis import (
    CustoVariavelListView,
    CustoVariavelCreateView,
    CustoVariavelUpdateView,
    CustoVariavelDeleteView,
    CategoriaListView,
    CategoriaCreateView,
    CategoriaUpdateView,
    CategoriaDeleteView,
)

urlpatterns = [
    # Custos Variáveis
    path('', CustoVariavelListView.as_view(), name='list_custosVariaveis'),
    path('add/', CustoVariavelCreateView.as_view(), name='add_custoVariavel'),
    path('edit/<int:pk>/', CustoVariavelUpdateView.as_view(), name='edit_custoVariavel'),
    path('delete/<int:pk>/', CustoVariavelDeleteView.as_view(), name='delete_custoVariavel'),

    # Categorias
    path('categorias/', CategoriaListView.as_view(), name='list_categoria'),
    path('categorias/add/', CategoriaCreateView.as_view(), name='add_categoria'),
    path('categorias/edit/<int:pk>/', CategoriaUpdateView.as_view(), name='edit_categoria'),
    path('categorias/delete/<int:pk>/', CategoriaDeleteView.as_view(), name='delete_categoria'),
    path('categorias/remove/<int:pk>/', CategoriaDeleteView.as_view(), name='remove_categoria'),
]

