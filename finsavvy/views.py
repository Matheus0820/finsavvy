from django.shortcuts import render, redirect, get_object_or_404

from datetime import datetime

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import *
from .forms import *

def landing_page(request):
    return render(request, "pages/landing_page.html")

def aviso(request):
    return render(request, "pages/aviso_em_desenvolvimento.html")

@login_required
def dashboard(request):
    # now = datetime.now()
    return render(request, "pages/dashboard.html")

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