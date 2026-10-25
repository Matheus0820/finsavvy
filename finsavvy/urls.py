# example/urls.py
from django.urls import path, include

from finsavvy.views import landing_page, dashboard, aviso, list_custosFixos, add_custoFixo, edit_custoFixo, remove_custoFixo


urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('aviso/', aviso, name='aviso'),
    path('custosvariaveis/', include('finsavvy.urls_custos_variaveis'), name='custos_variaveis'),
    path('custoscompras/', include('finsavvy.urls_custo_compra'), name='custos_compras'),
    path('veiculos/', include('finsavvy.urls_veiculos'), name='veiculos'),
    path('combustiveis/', include('finsavvy.urls_custo_combustivel'), name='combustiveis'),
    path('manutencoes/', include('finsavvy.urls_manutencao'), name='manutencoes'),
    path('dashboard/', dashboard, name='dashboard'),
    path('custosfixos/', list_custosFixos, name='list_custosFixos'),
    path('add_custofixo/', add_custoFixo, name='add_custofixo'),
    path('edit_custofixo/<int:id>/', edit_custoFixo, name='edit_custofixo'),
    path('remove_custofixo/<int:id>/', remove_custoFixo, name='remove_custofixo'),
]