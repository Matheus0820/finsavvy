from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoCompra
from .new_forms import FormCustoCompra

class CustoCompraListView(LoginRequiredMixin, ListView):
    model = CustoCompra
    template_name = 'pages/list_custo_compra.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return CustoCompra.objects.filter(user=self.request.user)

class CustoCompraCreateView(LoginRequiredMixin, CreateView):
    model = CustoCompra
    form_class = FormCustoCompra
    template_name = 'pages/add_custoCompra.html'
    success_url = reverse_lazy('list_custoCompra')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class CustoCompraUpdateView(LoginRequiredMixin, UpdateView):
    model = CustoCompra
    form_class = FormCustoCompra
    template_name = 'pages/add_custoCompra.html'
    success_url = reverse_lazy('list_custoCompra')

    def get_queryset(self):
        return CustoCompra.objects.filter(user=self.request.user)

class CustoCompraDeleteView(LoginRequiredMixin, DeleteView):
    model = CustoCompra
    template_name = 'pages/confirm_delete_custoCompra.html'
    success_url = reverse_lazy('list_custoCompra')

    def get_queryset(self):
        return CustoCompra.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('list_custoCompra')

