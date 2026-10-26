import csv
import json
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
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


def obter_dados_relatorio(user, ano_param=None, mes_param=None, categoria_param=None):
    hoje = datetime.today()

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
    if categoria_param and str(categoria_param) not in ('', 'todas', 'None'):
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
        cc_qs = cc_qs.none()
        comb_qs = comb_qs.none()
        manut_qs = manut_qs.none()
        cf_qs = cf_qs.none()

    # Agregações de Totais
    total_custos_variaveis = cv_qs.aggregate(total=Sum('valor'))['total'] or 0.0
    total_compras = cc_qs.aggregate(total=Sum('valor_total'))['total'] or 0.0
    total_combustivel = comb_qs.aggregate(total=Sum('valor_abastecido'))['total'] or 0.0
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

    return {
        'ano': ano,
        'mes': mes,
        'mes_nome': next((m[1] for m in MESES_NOMES if m[0] == mes), 'Todos os Meses') if mes else 'Todos os Meses',
        'categoria_id': categoria_id,
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
    }


class RelatoriosView(LoginRequiredMixin, View):
    template_name = 'pages/relatorios.html'

    def get(self, request, *args, **kwargs):
        dados = obter_dados_relatorio(
            request.user,
            request.GET.get('ano'),
            request.GET.get('mes'),
            request.GET.get('categoria'),
        )

        context = {
            'ano_selecionado': dados['ano'],
            'mes_selecionado': 'todos' if dados['mes'] is None else dados['mes'],
            'mes_nome_selecionado': dados['mes_nome'],
            'categoria_selecionada': dados['categoria_id'] or '',
            'anos_disponiveis': dados['anos_disponiveis'],
            'meses_disponiveis': dados['meses_disponiveis'],
            'categorias': dados['categorias'],
            'total_geral': dados['total_geral'],
            'total_custos_fixos': dados['total_custos_fixos'],
            'total_custos_variaveis': dados['total_custos_variaveis'],
            'total_compras': dados['total_compras'],
            'total_combustivel': dados['total_combustivel'],
            'total_manutencao': dados['total_manutencao'],
            'total_veiculos': dados['total_veiculos'],
            'gastos_consolidados': dados['gastos_consolidados'],
            'quantidade_itens': dados['quantidade_itens'],
            'metricas_veiculares': dados['metricas_veiculares'],
            'dados_grafico_veicular_json': json.dumps(dados['metricas_veiculares']['serie_grafico']),
        }

        return render(request, self.template_name, context)


class ExportarRelatorioCSVView(LoginRequiredMixin, View):
    """
    Exporta a consolidação de gastos filtrados pelo usuário em formato CSV (compatível com Excel).
    """
    def get(self, request, *args, **kwargs):
        dados = obter_dados_relatorio(
            request.user,
            request.GET.get('ano'),
            request.GET.get('mes'),
            request.GET.get('categoria'),
        )
        ano = dados['ano']
        mes = dados['mes']
        mes_str = f"{mes:02d}" if mes else "todos"
        filename = f"relatorio_despesas_{ano}_{mes_str}.csv"

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # UTF-8 BOM para garantir correta acentuação no Excel
        response.write('\ufeff')

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Data', 'Tipo', 'Descrição / Item', 'Categoria', 'Valor (R$)'])

        for item in dados['gastos_consolidados']:
            data_str = item['data'].strftime('%d/%m/%Y') if item['data'] else 'Recorrente'
            valor_str = f"{item['valor']:.2f}".replace('.', ',')
            writer.writerow([
                data_str,
                item['tipo'],
                item['nome'],
                item['categoria_nome'],
                valor_str,
            ])

        return response
