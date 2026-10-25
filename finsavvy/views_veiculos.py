from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Veiculo
from .forms_veiculos import FormVeiculo


class VeiculoListView(LoginRequiredMixin, ListView):
    model = Veiculo
    template_name = 'pages/list_veiculo.html'
    context_object_name = 'veiculos'

    def get_queryset(self):
        return Veiculo.objects.filter(user=self.request.user)


class VeiculoCreateView(LoginRequiredMixin, CreateView):
    model = Veiculo
    template_name = 'pages/add_veiculo.html'
    form_class = FormVeiculo
    success_url = reverse_lazy('list_veiculo')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class VeiculoUpdateView(LoginRequiredMixin, UpdateView):
    model = Veiculo
    template_name = 'pages/add_veiculo.html'
    form_class = FormVeiculo
    success_url = reverse_lazy('list_veiculo')

    def get_queryset(self):
        return Veiculo.objects.filter(user=self.request.user)


class VeiculoDeleteView(LoginRequiredMixin, DeleteView):
    model = Veiculo
    template_name = 'pages/confirm_delete_veiculo.html'
    success_url = reverse_lazy('list_veiculo')

    def get_queryset(self):
        return Veiculo.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('list_veiculo')

    def form_valid(self, form):
        return super().form_valid(form)
