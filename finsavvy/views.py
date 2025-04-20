from django.shortcuts import render

from datetime import datetime

from django.http import HttpResponse

def dashboard(request):
    # now = datetime.now()
    return render(request, "pages/aviso_em_desenvolvimento.html")