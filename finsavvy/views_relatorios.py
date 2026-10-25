import json
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import render
from django.views import View

from .models import (
    Categoria,
    CustoCombustivel,
    CustoCompra,
    CustoFixo,
    CustoVariavel,
    Manutencao,
    Veiculo,
)
from .utils.calculos_veiculares import calcular_metricas_veiculares_gerais

MESES_NOMES = [
    (1, 'Janeiro'),
    (2, 'Fevereiro'),
    (3, 'Março'),
    (4, 'Abril'),
    (5, 'Maio'),
    (6, 'Junho'),
    (7, 'Julho'),
    (8, 'Agosto'),
    (9, 'Setembro'),
    (10, 'Outubro'),
    (11, 'Novembro'),
    (12, 'Dezembro'),
]


class RelatoriosView(LoginRequiredMixin, View):
    template_name = 'pages/relatorios.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        hoje = datetime.today()

        # Leitura e sanitização dos filtros GET
        ano_param = request.GET.get('ano')
        mes_param = request.GET.get('mes')
        categoria_param = request.GET.get('categoria')

        try:
            ano = int(ano_param) if ano_param else hoje.year
        except (ValueError, TypeError):
            ano = hoje.year

        if mes_param == 'todos':
            mes = None
        elif mes_param:
            try:
                mes_int = int(mes_param)
                mes = mes_int if 1 <= mes_int <= 12 else hoje.month
            except (ValueError, TypeError):
                mes = hoje.month
        else:
            mes = hoje.month

        categoria_id = None
        if categoria_param and categoria_param not in ('', 'todas'):
            try:
                categoria_id = int(categoria_param)
            except (ValueError, TypeError):
                categoria_id = None

        # Base de consulta filtrada pelo usuário logado
        cv_qs = CustoVariavel.objects.filter(user=user)
        cc_qs = CustoCompra.objects.filter(user=user)
        comb_qs = CustoCombustivel.objects.filter(user=user)
        manut_qs = Manutencao.objects.filter(user=user)
        cf_qs = CustoFixo.objects.filter(user=user)

        # Filtro por ano
        cv_qs = cv_qs.filter(data__year=ano)
        cc_qs = cc_qs.filter(data__year=ano)
        comb_qs = comb_qs.filter(data__year=ano)
        manut_qs = manut_qs.filter(data__year=ano)

        # Filtro por mês (se não for "todos")
        if mes is not None:
            cv_qs = cv_qs.filter(data__month=mes)
            cc_qs = cc_qs.filter(data__month=mes)
            comb_qs = comb_qs.filter(data__month=mes)
            manut_qs = manut_qs.filter(data__month=mes)

        # Filtro por categoria (aplicável diretamente a Custos Variáveis)
        if categoria_id:
            cv_qs = cv_qs.filter(categoria_id=categoria_id)
            # Demais categorias específicas são zeradas quando uma categoria de custo variável é isolada
            cc_qs = cc_qs.none()
            comb_qs = comb_qs.none()
            manut_qs = manut_qs.none()
            cf_qs = cf_qs.none()

        # Agregações de Totais
        total_custos_variaveis = cv_qs.aggregate(total=Sum('valor'))['total'] or 0.0
        total_compras = cc_qs.aggregate(total=Sum('valor'))['total'] or 0.0
        total_combustivel = comb_qs.aggregate(total=Sum('valor'))['total'] or 0.0
        total_manutencao = manut_qs.aggregate(total=Sum('valor'))['total'] or 0.0
        total_custos_fixos = cf_qs.aggregate(total=Sum('valor'))['total'] or 0.0

        total_veiculos = total_combustivel + total_manutencao
        total_geral = (
            total_custos_variaveis
            + total_compras
            + total_combustivel
            + total_manutencao
            + total_custos_fixos
        )

        # Montagem da lista consolidada de gastos
        gastos_consolidados = []

        for item in cv_qs.select_related('categoria').order_by('-data', '-id'):
            gastos_consolidados.append({
                'id': f"cv-{item.id}",
                'data': item.data,
                'nome': item.nome,
                'tipo': 'Custo Variável',
                'categoria_nome': item.categoria.nome if item.categoria else 'Sem Categoria',
                'categoria_cor': item.categoria.cor if item.categoria else '#6c757d',
                'valor': item.valor,
            })

        for item in cc_qs.order_by('-data', '-id'):
            gastos_consolidados.append({
                'id': f"cc-{item.id}",
                'data': item.data,
                'nome': item.nome,
                'tipo': 'Compra',
                'categoria_nome': 'Compras',
                'categoria_cor': '#0d6efd',
                'valor': item.valor,
            })

        for item in comb_qs.select_related('veiculo').order_by('-data', '-id'):
            gastos_consolidados.append({
                'id': f"comb-{item.id}",
                'data': item.data,
                'nome': f"Abastecimento ({item.veiculo.modelo} - {item.litros}L)",
                'tipo': 'Combustível',
                'categoria_nome': 'Veículos',
                'categoria_cor': '#ffc107',
                'valor': item.valor,
            })

        for item in manut_qs.select_related('veiculo').order_by('-data', '-id'):
            gastos_consolidados.append({
                'id': f"manut-{item.id}",
                'data': item.data,
                'nome': f"{item.tipo} ({item.veiculo.modelo})",
                'tipo': 'Manutenção',
                'categoria_nome': 'Veículos',
                'categoria_cor': '#0dcaf0',
                'valor': item.valor,
            })

        for item in cf_qs.order_by('nome'):
            gastos_consolidados.append({
                'id': f"cf-{item.id}",
                'data': None,
                'nome': item.nome,
                'tipo': 'Custo Fixo',
                'categoria_nome': 'Recorrente',
                'categoria_cor': '#adb5bd',
                'valor': item.valor,
            })

        # Ordenar por data decrescente (custos com data primeiro, fixos recorrentes ao final)
        gastos_consolidados.sort(
            key=lambda x: (x['data'] is not None, x['data']),
            reverse=True,
        )

        # Métricas de Estatísticas Veiculares (km/L, R$/km, etc.)
        veiculos_user = Veiculo.objects.filter(user=user)
        metricas_veiculares = calcular_metricas_veiculares_gerais(veiculos_user, comb_qs, manut_qs)

        # Anos disponíveis para seleção
        anos_disponiveis = [hoje.year - 2, hoje.year - 1, hoje.year, hoje.year + 1]
        categorias = Categoria.objects.all().order_by('nome')

        context = {
            'ano_selecionado': ano,
            'mes_selecionado': 'todos' if mes is None else mes,
            'mes_nome_selecionado': next((m[1] for m in MESES_NOMES if m[0] == mes), 'Todos os Meses') if mes else 'Todos os Meses',
            'categoria_selecionada': categoria_id or '',
            'anos_disponiveis': anos_disponiveis,
            'meses_disponiveis': MESES_NOMES,
            'categorias': categorias,
            'total_geral': total_geral,
            'total_custos_fixos': total_custos_fixos,
            'total_custos_variaveis': total_custos_variaveis,
            'total_compras': total_compras,
            'total_combustivel': total_combustivel,
            'total_manutencao': total_manutencao,
            'total_veiculos': total_veiculos,
            'gastos_consolidados': gastos_consolidados,
            'quantidade_itens': len(gastos_consolidados),
            'metricas_veiculares': metricas_veiculares,
            'dados_grafico_veicular_json': json.dumps(metricas_veiculares['serie_grafico']),
        }

        return render(request, self.template_name, context)
