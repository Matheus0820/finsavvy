from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum

from datetime import datetime

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import *
from .forms import *
from .utils.alertas_veiculares import gerar_alertas_usuario

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
    total_custos_fixos = CustoFixo.objects.filter(user=user).aggregate(total=Sum('valor'))['total'] or 0
    total_custos_variaveis = CustoVariavel.objects.filter(user=user).aggregate(total=Sum('valor'))['total'] or 0
    total_compras = CustoCompra.objects.filter(user=user).aggregate(total=Sum('valor'))['total'] or 0
    total_combustivel = CustoCombustivel.objects.filter(user=user).aggregate(total=Sum('valor'))['total'] or 0
    total_manutencao = Manutencao.objects.filter(user=user).aggregate(total=Sum('valor'))['total'] or 0

    total_geral = total_custos_fixos + total_custos_variaveis + total_compras + total_combustivel + total_manutencao
    total_veiculos = Veiculo.objects.filter(user=user).count()

    recent_variaveis = CustoVariavel.objects.filter(user=user).order_by('-id')[:5]
    recent_compras = CustoCompra.objects.filter(user=user).order_by('-id')[:5]
    recent_manutencoes = Manutencao.objects.filter(user=user).order_by('-id')[:5]

    context = {
        'total_custos_fixos': total_custos_fixos,
        'total_custos_variaveis': total_custos_variaveis,
        'total_compras': total_compras,
        'total_combustivel': total_combustivel,
        'total_manutencao': total_manutencao,
        'total_geral': total_geral,
        'total_veiculos': total_veiculos,
        'recent_variaveis': recent_variaveis,
        'recent_compras': recent_compras,
        'recent_manutencoes': recent_manutencoes,
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