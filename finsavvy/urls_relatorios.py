from django.urls import path
from .views_relatorios import RelatoriosView

urlpatterns = [
    path('', RelatoriosView.as_view(), name='relatorios'),
]
