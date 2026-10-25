# views_custo_combustivel.py

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoCombustivel

class CustoCombustivelListView(ListView):
    model = CustoCombustivel
    template_name = 'pages/list_custo_combustivel.html'
    context_object_name = 'object_list'

class CustoCombustivelCreateView(CreateView):
    model = CustoCombustivel
    template_name = 'pages/add_custo_combustivel.html'
    fields = ('veiculo', 'data', 'litros', 'valor')
    success_url = reverse_lazy('list_custoCombustivel')

class CustoCombustivelUpdateView(UpdateView):
    model = CustoCombustivel
    template_name = 'pages/edit_custo_combustivel.html'
    fields = ('veiculo', 'data', 'litros', 'valor')
    success_url = reverse_lazy('list_custoCombustivel')

class CustoCombustivelDeleteView(DeleteView):
    model = CustoCombustivel
    template_name = 'pages/confirm_delete_custo_combustivel.html'
    success_url = reverse_lazy('list_custoCombustivel')
