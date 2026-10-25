# views_custos_variaveis.py

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoVariavel

class CustoVariavelListView(ListView):
    model = CustoVariavel
    template_name = 'pages/list_custos_variaveis.html'
    context_object_name = 'custosVariaveis'

class CustoVariavelCreateView(CreateView):
    model = CustoVariavel
    template_name = 'pages/add_custo_variavel.html'
    fields = ('nome', 'valor', 'data', 'categoria')
    success_url = reverse_lazy('list_custosVariaveis')

class CustoVariavelUpdateView(UpdateView):
    model = CustoVariavel
    template_name = 'pages/edit_custo_variavel.html'
    fields = ('nome', 'valor', 'data', 'categoria')
    success_url = reverse_lazy('list_custosVariaveis')

class CustoVariavelDeleteView(DeleteView):
    model = CustoVariavel
    template_name = 'pages/confirm_delete_custo_variavel.html'
    success_url = reverse_lazy('list_custosVariaveis')
