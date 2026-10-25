# urls_custo_compra.py

from django.urls import path
from .views_custo_compra import (
    CustoCompraListView,
    CustoCompraCreateView,
    CustoCompraUpdateView,
    CustoCompraDeleteView,
)

urlpatterns = [
    path('', CustoCompraListView.as_view(), name='list_custoCompra'),
    path('add/', CustoCompraCreateView.as_view(), name='add_custoCompra'),
    path('edit/<int:pk>/', CustoCompraUpdateView.as_view(), name='edit_custoCompra'),
    path('delete/<int:pk>/', CustoCompraDeleteView.as_view(), name='delete_custoCompra'),
]
