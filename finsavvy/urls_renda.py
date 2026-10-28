from django.urls import path
from .views_renda import (
    RendaListView,
    RendaCreateView,
    RendaUpdateView,
    RendaDeleteView,
)

urlpatterns = [
    path('', RendaListView.as_view(), name='list_renda'),
    path('add/', RendaCreateView.as_view(), name='add_renda'),
    path('edit/<int:pk>/', RendaUpdateView.as_view(), name='edit_renda'),
    path('delete/<int:pk>/', RendaDeleteView.as_view(), name='delete_renda'),
]
