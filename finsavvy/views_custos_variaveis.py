from datetime import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoVariavel, Categoria, FechamentoMes
from .new_forms import FormCustoVariavel, FormCategoria

class CustoVariavelListView(LoginRequiredMixin, ListView):
    model = CustoVariavel
    template_name = 'pages/list_custos_variaveis.html'
    context_object_name = 'custosVariaveis'

    def get_queryset(self):
        user = self.request.user
        hoje = datetime.today()
        try:
            mes = int(self.request.GET.get('mes') or self.request.GET.get('m', hoje.month))
        except (ValueError, TypeError):
            mes = hoje.month
        try:
            ano = int(self.request.GET.get('ano') or self.request.GET.get('y', hoje.year))
        except (ValueError, TypeError):
            ano = hoje.year
        return CustoVariavel.objects.filter(user=user, data__year=ano, data__month=mes)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = datetime.today()
        try:
            mes = int(self.request.GET.get('mes') or self.request.GET.get('m', hoje.month))
        except (ValueError, TypeError):
            mes = hoje.month
        try:
            ano = int(self.request.GET.get('ano') or self.request.GET.get('y', hoje.year))
        except (ValueError, TypeError):
            ano = hoje.year
        context['object_list'] = context['custosVariaveis']
        context['mes_atual'] = mes
        context['ano_atual'] = ano
        context['is_mes_fechado'] = FechamentoMes.objects.filter(user=self.request.user, mes=mes, ano=ano).exists()
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


# ==========================================
# CRUD de Categorias de Custo Variável
# ==========================================

class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'pages/list_categoria.html'
    context_object_name = 'object_list'
    ordering = ['nome']


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = FormCategoria
    template_name = 'pages/add_categoria.html'
    success_url = reverse_lazy('list_categoria')


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = FormCategoria
    template_name = 'pages/edit_categoria.html'
    success_url = reverse_lazy('list_categoria')


class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'pages/confirm_delete_categoria.html'
    success_url = reverse_lazy('list_categoria')

    def get(self, request, *args, **kwargs):
        return redirect('list_categoria')

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Não é possível excluir esta categoria pois ela possui custos variáveis associados.')
            return redirect('list_categoria')


