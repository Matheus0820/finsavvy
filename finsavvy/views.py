from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, ProtectedError
from django.db import transaction

from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views import View
from django.urls import reverse_lazy

from .models import *
from .forms import *
from .utils.alertas_veiculares import gerar_alertas_usuario

class FecharMesView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        hoje = datetime.today()
        try:
            mes = int(request.POST.get('mes') or request.GET.get('mes') or hoje.month)
        except (ValueError, TypeError):
            mes = hoje.month
        try:
            ano = int(request.POST.get('ano') or request.GET.get('ano') or hoje.year)
        except (ValueError, TypeError):
            ano = hoje.year

        if not (1 <= mes <= 12):
            mes = hoje.month

        with transaction.atomic():
            fechamento, created = FechamentoMes.objects.get_or_create(
                user=request.user,
                mes=mes,
                ano=ano
            )

            total_fixo = CustoFixo.objects.filter(user=request.user).aggregate(total=Sum('valor'))['total'] or 0.0
            total_variavel = CustoVariavel.objects.filter(user=request.user, data__year=ano, data__month=mes).aggregate(total=Sum('valor'))['total'] or 0.0
            total_compras = CustoCompra.objects.filter(user=request.user, data__year=ano, data__month=mes).aggregate(total=Sum('valor_total'))['total'] or 0.0

            comb_total = CustoCombustivel.objects.filter(user=request.user, data__year=ano, data__month=mes).aggregate(total=Sum('valor_abastecido'))['total'] or 0.0
            manut_total = Manutencao.objects.filter(user=request.user, data__year=ano, data__month=mes).aggregate(total=Sum('valor'))['total'] or 0.0
            total_veiculos = comb_total + manut_total

            total_despesas = total_fixo + total_variavel + total_compras + total_veiculos
            sobra_realizada = -total_despesas

            fechamento.total_fixo = total_fixo
            fechamento.total_variavel = total_variavel
            fechamento.total_compras = total_compras
            fechamento.total_veiculos = total_veiculos
            fechamento.sobra_realizada = sobra_realizada
            fechamento.save()

        messages.success(request, f"Mês {mes:02d}/{ano} fechado e consolidado com sucesso!")
        return redirect(f"{reverse_lazy('dashboard')}?mes={mes}&ano={ano}")


class ReabrirMesView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        hoje = datetime.today()
        try:
            mes = int(request.POST.get('mes') or request.GET.get('mes') or hoje.month)
        except (ValueError, TypeError):
            mes = hoje.month
        try:
            ano = int(request.POST.get('ano') or request.GET.get('ano') or hoje.year)
        except (ValueError, TypeError):
            ano = hoje.year

        FechamentoMes.objects.filter(user=request.user, mes=mes, ano=ano).delete()
        messages.success(request, f"Mês {mes:02d}/{ano} reaberto com sucesso!")
        return redirect(f"{reverse_lazy('dashboard')}?mes={mes}&ano={ano}")

def landing_page(request):
    return render(request, "pages/landing_page.html")

@login_required
def aviso(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'marcar_lido':
            aviso_id = request.POST.get('aviso_id')
            Aviso.objects.filter(id=aviso_id, user=request.user).update(lido=True)
            messages.success(request, "Aviso marcado como lido.")
        elif action == 'marcar_todos_lidos':
            Aviso.objects.filter(user=request.user, lido=False).update(lido=True)
            messages.success(request, "Todos os avisos foram marcados como lidos.")
        elif action == 'excluir':
            aviso_id = request.POST.get('aviso_id')
            Aviso.objects.filter(id=aviso_id, user=request.user).delete()
            messages.success(request, "Aviso removido com sucesso.")
        return redirect('aviso')

    # Processa e sincroniza alertas preventivos do usuário autenticado
    gerar_alertas_usuario(request.user)

    avisos = Aviso.objects.filter(user=request.user).select_related('veiculo').order_by('lido', '-data_criacao')
    total_avisos = avisos.count()
    total_nao_lidos = avisos.filter(lido=False).count()
    total_urgentes = avisos.filter(nivel='URGENTE', lido=False).count()
    total_alertas = avisos.filter(nivel='ALERTA', lido=False).count()

    context = {
        'avisos': avisos,
        'total_avisos': total_avisos,
        'total_nao_lidos': total_nao_lidos,
        'total_urgentes': total_urgentes,
        'total_alertas': total_alertas,
    }
    return render(request, "pages/aviso.html", context)

@login_required
def dashboard(request):
    user = request.user
    hoje = datetime.today()
    try:
        mes = int(request.GET.get('mes') or request.GET.get('m', hoje.month))
    except (ValueError, TypeError):
        mes = hoje.month
    try:
        ano = int(request.GET.get('ano') or request.GET.get('y', hoje.year))
    except (ValueError, TypeError):
        ano = hoje.year

    # Querysets filtrados por competência (mês e ano)
    cv_qs = CustoVariavel.objects.filter(user=user, data__year=ano, data__month=mes)
    cc_qs = CustoCompra.objects.filter(user=user, data__year=ano, data__month=mes)
    comb_qs = CustoCombustivel.objects.filter(user=user, data__year=ano, data__month=mes)
    manut_qs = Manutencao.objects.filter(user=user, data__year=ano, data__month=mes)
    troca_oleo_qs = TrocaOleo.objects.filter(user=user, data__year=ano, data__month=mes)

    cf_qs = CustoFixo.objects.filter(user=user)

    total_custos_fixos = cf_qs.aggregate(total=Sum('valor'))['total'] or 0
    total_custos_variaveis = cv_qs.aggregate(total=Sum('valor'))['total'] or 0
    total_compras = cc_qs.aggregate(total=Sum('valor_total'))['total'] or 0
    total_combustivel = comb_qs.aggregate(total=Sum('valor_abastecido'))['total'] or 0
    total_manutencao = manut_qs.aggregate(total=Sum('valor'))['total'] or 0
    total_troca_oleo = troca_oleo_qs.aggregate(total=Sum('valor'))['total'] or 0

    total_geral = total_custos_fixos + total_custos_variaveis + total_compras + total_combustivel + total_manutencao + total_troca_oleo
    total_veiculos = Veiculo.objects.filter(user=user).count()

    recent_variaveis = cv_qs.order_by('-id')[:5]
    recent_compras = cc_qs.order_by('-id')[:5]
    recent_manutencoes = manut_qs.order_by('-id')[:5]

    is_mes_fechado = FechamentoMes.objects.filter(user=user, mes=mes, ano=ano).exists()

    context = {
        'total_custos_fixos': total_custos_fixos,
        'total_custos_variaveis': total_custos_variaveis,
        'total_compras': total_compras,
        'total_combustivel': total_combustivel,
        'total_manutencao': total_manutencao,
        'total_troca_oleo': total_troca_oleo,
        'total_geral': total_geral,
        'total_veiculos': total_veiculos,
        'recent_variaveis': recent_variaveis,
        'recent_compras': recent_compras,
        'recent_manutencoes': recent_manutencoes,
        'recent_troca_oleo': troca_oleo_qs.order_by('-id')[:5],
        'mes_atual': mes,
        'ano_atual': ano,
        'is_mes_fechado': is_mes_fechado,
    }
    return render(request, "pages/dashboard.html", context)

@login_required
def list_custosFixos(request):
    custosFixos = CustoFixo.objects.filter(user=request.user)
    context = {
        'custosFixos': custosFixos
    }

    return render(request, "pages/list_custosFixos.html", context)

@login_required
def add_custoFixo(request):
    if request.method == "GET":
        formCustoFixo = FormCustoFixo()

        context = {
            'formCustoFixo': formCustoFixo,
        }

        return render(request, 'pages/add_custofixo.html', context)

    elif request.method == "POST":
        formCustoFixo = FormCustoFixo(request.POST)

        if formCustoFixo.is_valid():
            custofixo = formCustoFixo.save(commit=False)
            custofixo.user = request.user
            custofixo.save()

            messages.success(request, "Custo fixo adicionado!")
            return redirect(list_custosFixos)

        context = {
            'formCustoFixo': formCustoFixo,
        }
        return render(request, 'pages/add_custofixo.html', context)


@login_required
def edit_custoFixo(request, id):
    custo = get_object_or_404(CustoFixo, id=id, user=request.user)

    if request.method == "GET":
        formCustoFixo = FormCustoFixo(instance=custo)
        context = {
            'formCustoFixo': formCustoFixo,
            'custo': custo,
        }
        return render(request, 'pages/add_custofixo.html', context)

    elif request.method == "POST":
        formCustoFixo = FormCustoFixo(request.POST, instance=custo)
        if formCustoFixo.is_valid():
            formCustoFixo.save()
            messages.success(request, "Custo fixo atualizado!")
            return redirect(list_custosFixos)

        context = {
            'formCustoFixo': formCustoFixo,
            'custo': custo,
        }
        return render(request, 'pages/add_custofixo.html', context)


@login_required
def remove_custoFixo(request, id):
    custo = get_object_or_404(CustoFixo, id=id, user=request.user)
    if request.method == "POST":
        custo.delete()
        messages.success(request, "Custo fixo removido!")
    return redirect(list_custosFixos)