# views_troca_oleo.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import TrocaOleo, Veiculo
from .new_forms import FormTrocaOleo

class TrocaOleoListView(LoginRequiredMixin, ListView):
    model = TrocaOleo
    template_name = 'pages/list_troca_oleo.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return TrocaOleo.objects.filter(user=self.request.user)

class TrocaOleoCreateView(LoginRequiredMixin, CreateView):
    model = TrocaOleo
    form_class = FormTrocaOleo
    template_name = 'pages/add_troca_oleo.html'
    success_url = reverse_lazy('list_troca_oleo')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['veiculo'].queryset = Veiculo.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class TrocaOleoUpdateView(LoginRequiredMixin, UpdateView):
    model = TrocaOleo
    form_class = FormTrocaOleo
    template_name = 'pages/add_troca_oleo.html'
    success_url = reverse_lazy('list_troca_oleo')

    def get_queryset(self):
        return TrocaOleo.objects.filter(user=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['veiculo'].queryset = Veiculo.objects.filter(user=self.request.user)
        return form

class TrocaOleoDeleteView(LoginRequiredMixin, DeleteView):
    model = TrocaOleo
    template_name = 'pages/confirm_delete_troca_oleo.html'
    success_url = reverse_lazy('list_troca_oleo')

    def get_queryset(self):
        return TrocaOleo.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('list_troca_oleo')
