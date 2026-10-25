# views_manutencao.py

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .new_models import Manutencao

class ManutencaoListView(ListView):
    model = Manutencao
    template_name = 'pages/list_manutencao.html'
    context_object_name = 'manutencoes'

class ManutencaoCreateView(CreateView):
    model = Manutencao
    template_name = 'pages/add_manutencao.html'
    fields = ('veiculo', 'data', 'tipo', 'descricao', 'valor', 'km_atual', 'km_proximo_oleo', 'km_troca_oleo')
    success_url = reverse_lazy('list_manutencao')

class ManutencaoUpdateView(UpdateView):
    model = Manutencao
    template_name = 'pages/edit_manutencao.html'
    fields = ('veiculo', 'data', 'tipo', 'descricao', 'valor', 'km_atual', 'km_proximo_oleo', 'km_troca_oleo')
    success_url = reverse_lazy('list_manutencao')

class ManutencaoDeleteView(DeleteView):
    model = Manutencao
    template_name = 'pages/confirm_delete_manutencao.html'
    success_url = reverse_lazy('list_manutencao')
