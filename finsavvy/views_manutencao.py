# views_manutencao.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Manutencao, Veiculo
from .new_forms import FormManutencao

class ManutencaoListView(LoginRequiredMixin, ListView):
    model = Manutencao
    template_name = 'pages/list_manutencao.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        return Manutencao.objects.filter(user=self.request.user)

class ManutencaoCreateView(LoginRequiredMixin, CreateView):
    model = Manutencao
    form_class = FormManutencao
    template_name = 'pages/add_manutencao.html'
    success_url = reverse_lazy('list_manutencao')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['veiculo'].queryset = Veiculo.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ManutencaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Manutencao
    form_class = FormManutencao
    template_name = 'pages/add_manutencao.html'
    success_url = reverse_lazy('list_manutencao')

    def get_queryset(self):
        return Manutencao.objects.filter(user=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['veiculo'].queryset = Veiculo.objects.filter(user=self.request.user)
        return form

class ManutencaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Manutencao
    template_name = 'pages/confirm_delete_manutencao.html'
    success_url = reverse_lazy('list_manutencao')

    def get_queryset(self):
        return Manutencao.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('list_manutencao')

