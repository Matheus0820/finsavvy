from django.urls import path
from .views_relatorios import RelatoriosView, ExportarRelatorioCSVView

urlpatterns = [
    path('', RelatoriosView.as_view(), name='relatorios'),
    path('exportar-csv/', ExportarRelatorioCSVView.as_view(), name='exportar_relatorios_csv'),
]
