# example/urls.py
from django.urls import path

from finsavvy.views import dashboard, aviso, list_custosFixos, add_custoFixo


urlpatterns = [
    path('', aviso),
    path('dashboard/', dashboard, name='dashboard'),
    path('custosfixos/', list_custosFixos, name='list_custosFixos'),
    path('add_custofixo/', add_custoFixo, name='add_custofixo'),
]