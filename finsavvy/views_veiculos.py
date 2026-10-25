# views_veiculos.py

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .new_models import Veiculo

class VeiculoListView(ListView):
    model = Veiculo
    template_name = 'pages/list_veiculo.html'
    context_object_name = 'veiculos'

class VeiculoCreateView(CreateView):
    model = Veiculo
    template_name = 'pages/add_veiculo.html'
    fields = ('marca', 'modelo', 'placa', 'tipo_veiculo', 'km_atual')
    success_url = reverse_lazy('list_veiculo')

class VeiculoUpdateView(UpdateView):
    model = Veiculo
    template_name = 'pages/edit_veiculo.html'
    fields = ('marca', 'modelo', 'placa', 'tipo_veiculo', 'km_atual')
    success_url = reverse_lazy('list_veiculo')

class VeiculoDeleteView(DeleteView):
    model = Veiculo
    template_name = 'pages/confirm_delete_veiculo.html'
    success_url = reverse_lazy('list_veiculo')
