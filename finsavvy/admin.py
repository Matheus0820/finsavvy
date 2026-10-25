# This file registers all custom models in the Django admin. No other file does this.
from django.contrib import admin
from .models import (
    CustoFixo,
    Veiculo,
)

admin.site.register(CustoFixo)
admin.site.register(Veiculo)
