from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Renda, FechamentoMes
from .forms_renda import FormRenda

class RendaListView(LoginRequiredMixin, ListView):
    model = Renda
    template_name = 'pages/list_renda.html'
    context_object_name = 'object_list'

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
        return Renda.objects.filter(user=user, data_recebimento__year=ano, data_recebimento__month=mes)

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

        qs = self.get_queryset()
        total_rendas = qs.aggregate(total=Sum('valor'))['total'] or 0.0

        context['mes_atual'] = mes
        context['ano_atual'] = ano
        context['total_rendas'] = total_rendas
        context['is_mes_fechado'] = FechamentoMes.objects.filter(user=self.request.user, mes=mes, ano=ano).exists()
        return context


class RendaCreateView(LoginRequiredMixin, CreateView):
    model = Renda
    form_class = FormRenda
    template_name = 'pages/add_renda.html'
    success_url = reverse_lazy('list_renda')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Renda adicionada com sucesso!")
        return super().form_valid(form)


class RendaUpdateView(LoginRequiredMixin, UpdateView):
    model = Renda
    form_class = FormRenda
    template_name = 'pages/add_renda.html'
    success_url = reverse_lazy('list_renda')

    def get_queryset(self):
        return Renda.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Renda atualizada com sucesso!")
        return super().form_valid(form)


class RendaDeleteView(LoginRequiredMixin, DeleteView):
    model = Renda
    template_name = 'pages/confirm_delete_renda.html'
    success_url = reverse_lazy('list_renda')

    def get_queryset(self):
        return Renda.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Renda removida com sucesso!")
        return super().form_valid(form)
