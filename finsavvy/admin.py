# This file registers all custom models in the Django admin. No other file does this.
from django.contrib import admin
from .new_models import (
    Categoria,
    CustoVariavel,
    CustoCompra,
    Veiculo,
    CustoCombustivel,
    Manutencao,
)

admin.site.register(Categoria)
admin.site.register(CustoVariavel)
admin.site.register(CustoCompra)
admin.site.register(Veiculo)
admin.site.register(CustoCombustivel)
admin.site.register(Manutencao)
