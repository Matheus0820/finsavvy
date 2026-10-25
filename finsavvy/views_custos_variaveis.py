# views_custos_variaveis.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoVariavel
from .new_forms import FormCustoVariavel

class CustoVariavelListView(LoginRequiredMixin, ListView):
    model = CustoVariavel
    template_name = 'pages/list_custos_variaveis.html'
    context_object_name = 'custosVariaveis'

    def get_queryset(self):
        return CustoVariavel.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = context['custosVariaveis']
        return context

class CustoVariavelCreateView(LoginRequiredMixin, CreateView):
    model = CustoVariavel
    form_class = FormCustoVariavel
    template_name = 'pages/add_custovariavel.html'
    success_url = reverse_lazy('list_custosVariaveis')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class CustoVariavelUpdateView(LoginRequiredMixin, UpdateView):
    model = CustoVariavel
    form_class = FormCustoVariavel
    template_name = 'pages/add_custovariavel.html'
    success_url = reverse_lazy('list_custosVariaveis')

    def get_queryset(self):
        return CustoVariavel.objects.filter(user=self.request.user)

class CustoVariavelDeleteView(LoginRequiredMixin, DeleteView):
    model = CustoVariavel
    template_name = 'pages/confirm_delete_custovariavel.html'
    success_url = reverse_lazy('list_custosVariaveis')

    def get_queryset(self):
        return CustoVariavel.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('list_custosVariaveis')

