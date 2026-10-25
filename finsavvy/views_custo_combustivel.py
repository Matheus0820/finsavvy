# views_custo_combustivel.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoCombustivel, Veiculo
from .new_forms import FormCustoCombustivel

class CustoCombustivelListView(LoginRequiredMixin, ListView):
    model = CustoCombustivel
    template_name = 'pages/list_custo_combustivel.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return CustoCombustivel.objects.filter(user=self.request.user)

class CustoCombustivelCreateView(LoginRequiredMixin, CreateView):
    model = CustoCombustivel
    form_class = FormCustoCombustivel
    template_name = 'pages/add_custoCombustivel.html'
    success_url = reverse_lazy('list_custoCombustivel')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['veiculo'].queryset = Veiculo.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class CustoCombustivelUpdateView(LoginRequiredMixin, UpdateView):
    model = CustoCombustivel
    form_class = FormCustoCombustivel
    template_name = 'pages/add_custoCombustivel.html'
    success_url = reverse_lazy('list_custoCombustivel')

    def get_queryset(self):
        return CustoCombustivel.objects.filter(user=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['veiculo'].queryset = Veiculo.objects.filter(user=self.request.user)
        return form

class CustoCombustivelDeleteView(LoginRequiredMixin, DeleteView):
    model = CustoCombustivel
    template_name = 'pages/confirm_delete_custoCombustivel.html'
    success_url = reverse_lazy('list_custoCombustivel')

    def get_queryset(self):
        return CustoCombustivel.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('list_custoCombustivel')

