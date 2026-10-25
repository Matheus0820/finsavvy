# views_custo_compra.py

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoCompra

class CustoCompraListView(ListView):
    model = CustoCompra
    template_name = 'pages/list_custo_compra.html'
    context_object_name = 'custosCompra'

class CustoCompraCreateView(CreateView):
    model = CustoCompra
    template_name = 'pages/add_custo_compra.html'
    fields = ('nome', 'valor', 'data', 'qr_data')
    success_url = reverse_lazy('list_custoCompra')

class CustoCompraUpdateView(UpdateView):
    model = CustoCompra
    template_name = 'pages/edit_custo_compra.html'
    fields = ('nome', 'valor', 'data', 'qr_data')
    success_url = reverse_lazy('list_custoCompra')

class CustoCompraDeleteView(DeleteView):
    model = CustoCompra
    template_name = 'pages/confirm_delete_custo_compra.html'
    success_url = reverse_lazy('list_custoCompra')
