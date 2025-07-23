from django.shortcuts import render

from datetime import datetime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def aviso(request):
    return render(request, "pages/aviso_em_desenvolvimento.html")

@login_required
def dashboard(request):
    # now = datetime.now()
    return render(request, "pages/dashboard.html")