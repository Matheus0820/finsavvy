from django.shortcuts import render, redirect

from datetime import datetime

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import *
from .forms import *

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

        custofixo = formCustoFixo.save(commit=False)
        custofixo.user = request.user
        custofixo.save()

        messages.success(request, "Custo fixo adicionado!")
        return redirect(list_custosFixos)


@login_required
def edit_custoFixo(request, id):
    if request.method == "GET":
        pass

    elif request.method == "POST":
        pass

@login_required
def remove_custoFixo(request, id):
    pass