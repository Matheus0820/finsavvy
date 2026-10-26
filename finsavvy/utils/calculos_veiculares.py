"""
Módulo utilitário para cálculo de métricas e indicadores de eficiência veicular.
Responsável por consumo médio (km/L), custo por quilômetro (R$/km), agregações
e preparação de séries temporais para visualização gráfica.
"""
from typing import Dict, List, Optional, Any
from django.db.models import Sum


def calcular_consumo_medio(km_total: float, litros_total: float) -> float:
    """
    Calcula o consumo médio em km/L.
    Retorna 0.0 caso litros_total <= 0 ou km_total <= 0 (tratando divisão por zero).
    """
    try:
        km = float(km_total)
        litros = float(litros_total)
    except (TypeError, ValueError):
        return 0.0

    if litros <= 0 or km <= 0:
        return 0.0
    return round(km / litros, 2)


def calcular_custo_por_km(custo_total: float, km_total: float) -> float:
    """
    Calcula o custo por quilômetro rodado em R$/km.
    Retorna 0.0 caso km_total <= 0 ou custo_total <= 0 (tratando divisão por zero).
    """
    try:
        custo = float(custo_total)
        km = float(km_total)
    except (TypeError, ValueError):
        return 0.0

    if km <= 0 or custo <= 0:
        return 0.0
    return round(custo / km, 2)


def calcular_preco_medio_litro(total_valor: float, total_litros: float) -> float:
    """
    Calcula o preço médio pago por litro de combustível (R$/L).
    Retorna 0.0 caso total_litros <= 0 ou total_valor <= 0.
    """
    try:
        valor = float(total_valor)
        litros = float(total_litros)
    except (TypeError, ValueError):
        return 0.0

    if litros <= 0 or valor <= 0:
        return 0.0
    return round(valor / litros, 2)


def calcular_estatisticas_por_veiculo(veiculo, combustiveis_qs=None, manutencoes_qs=None) -> Dict[str, Any]:
    """
    Calcula métricas detalhadas para um veículo específico com base nos querysets fornecidos.
    """
    if combustiveis_qs is None:
        combustiveis = veiculo.combustiveis.all()
    else:
        combustiveis = combustiveis_qs.filter(veiculo=veiculo)

    if manutencoes_qs is None:
        manutencoes = veiculo.manutenções.all()
    else:
        manutencoes = manutencoes_qs.filter(veiculo=veiculo)

    total_litros = sum(c.litros for c in combustiveis)
    total_gasto_combustivel = combustiveis.aggregate(total=Sum('valor_abastecido'))['total'] or 0.0
    total_gasto_manutencao = manutencoes.aggregate(total=Sum('valor'))['total'] or 0.0
    total_gasto = total_gasto_combustivel + total_gasto_manutencao
    total_abastecimentos = combustiveis.count()

    km_rodados = float(veiculo.km_atual) if veiculo.km_atual else 0.0

    consumo_medio = calcular_consumo_medio(km_rodados, total_litros)
    custo_por_km = calcular_custo_por_km(total_gasto, km_rodados)
    custo_combustivel_por_km = calcular_custo_por_km(total_gasto_combustivel, km_rodados)
    preco_medio_litro = calcular_preco_medio_litro(total_gasto_combustivel, total_litros)
    autonomia = calcular_autonomia(veiculo)

    return {
        'veiculo_id': veiculo.id,
        'veiculo_nome': f"{veiculo.marca} {veiculo.modelo} ({veiculo.placa})",
        'placa': veiculo.placa,
        'tipo': veiculo.get_tipo_veiculo_display() if hasattr(veiculo, 'get_tipo_veiculo_display') else veiculo.tipo_veiculo,
        'km_atual': veiculo.km_atual,
        'capacidade_tanque': veiculo.capacidade_tanque,
        'total_abastecimentos': total_abastecimentos,
        'total_litros': round(total_litros, 2),
        'total_gasto_combustivel': round(total_gasto_combustivel, 2),
        'total_gasto_manutencao': round(total_gasto_manutencao, 2),
        'total_gasto': round(total_gasto, 2),
        'consumo_medio': consumo_medio,
        'custo_por_km': custo_por_km,
        'custo_combustivel_por_km': custo_combustivel_por_km,
        'preco_medio_litro': preco_medio_litro,
        'autonomia_ultimo_trecho': autonomia['autonomia_ultimo_trecho'],
        'autonomia_media_global': autonomia['autonomia_media_global'],
        'autonomia_maxima_estimada': autonomia['autonomia_maxima_estimada'],
        'custo_estimado_tanque_cheio': autonomia['custo_estimado_tanque_cheio'],
    }


def calcular_metricas_veiculares_gerais(veiculos_qs, combustiveis_qs, manutencoes_qs) -> Dict[str, Any]:
    """
    Consolida métricas globais de todos os veículos informados e prepara dados para gráficos.
    """
    total_veiculos = veiculos_qs.count()
    total_litros = sum(c.litros for c in combustiveis_qs)
    total_combustivel = combustiveis_qs.aggregate(total=Sum('valor_abastecido'))['total'] or 0.0
    total_manutencao = manutencoes_qs.aggregate(total=Sum('valor'))['total'] or 0.0
    total_gasto_frota = total_combustivel + total_manutencao

    km_total_frota = sum(v.km_atual for v in veiculos_qs) if total_veiculos > 0 else 0.0

    consumo_medio_frota = calcular_consumo_medio(km_total_frota, total_litros)
    custo_km_frota = calcular_custo_por_km(total_gasto_frota, km_total_frota)
    preco_medio_litro = calcular_preco_medio_litro(total_combustivel, total_litros)

    estatisticas_veiculos = [
        calcular_estatisticas_por_veiculo(v, combustiveis_qs, manutencoes_qs)
        for v in veiculos_qs
    ]

    serie_grafico = preparar_dados_grafico_consumo(combustiveis_qs)

    return {
        'total_veiculos': total_veiculos,
        'total_litros': round(total_litros, 2),
        'total_combustivel': round(total_combustivel, 2),
        'total_manutencao': round(total_manutencao, 2),
        'total_gasto_frota': round(total_gasto_frota, 2),
        'consumo_medio_frota': consumo_medio_frota,
        'custo_km_frota': custo_km_frota,
        'preco_medio_litro': preco_medio_litro,
        'estatisticas_veiculos': estatisticas_veiculos,
        'serie_grafico': serie_grafico,
    }


def preparar_dados_grafico_consumo(combustiveis_qs) -> Dict[str, Any]:
    """
    Prepara dados formatados para renderização no Chart.js (evolução temporal de abastecimentos).
    """
    itens = combustiveis_qs.select_related('veiculo').order_by('data', 'id')
    labels: List[str] = []
    dados_litros: List[float] = []
    dados_valores: List[float] = []
    dados_preco_litro: List[float] = []

    for item in itens:
        label = item.data.strftime('%d/%m') if item.data else f"ID {item.id}"
        preco_litro = calcular_preco_medio_litro(item.valor, item.litros)
        labels.append(label)
        dados_litros.append(round(item.litros, 2))
        dados_valores.append(round(item.valor, 2))
        dados_preco_litro.append(preco_litro)

    return {
        'labels': labels,
        'litros': dados_litros,
        'valores': dados_valores,
        'precos_litro': dados_preco_litro,
    }


def calcular_autonomia(veiculo) -> Dict[str, Any]:
    """
    Calcula as métricas preditivas e estatísticas de autonomia de um veículo:
    1. autonomia_ultimo_trecho: (KM atual - KM anterior) / litros atuais.
       Calculado APENAS se os dois últimos abastecimentos possuírem tanque_cheio=True.
    2. autonomia_media_global: (KM mais recente - KM mais antiga) / soma total de litros.
    3. autonomia_maxima_estimada: autonomia_media_global * capacidade_tanque.
    4. custo_estimado_tanque_cheio: capacidade_tanque * último valor_por_litro registrado.
    """
    combustiveis = list(veiculo.combustiveis.all().order_by('km_atual', 'data', 'id'))
    capacidade_tanque = float(veiculo.capacidade_tanque or 0)

    # 1. autonomia_ultimo_trecho
    autonomia_ultimo_trecho = None
    if len(combustiveis) >= 2:
        penultimo = combustiveis[-2]
        ultimo = combustiveis[-1]
        if penultimo.tanque_cheio and ultimo.tanque_cheio:
            delta_km = ultimo.km_atual - penultimo.km_atual
            litros_atuais = ultimo.litros
            if delta_km > 0 and litros_atuais > 0:
                autonomia_ultimo_trecho = round(delta_km / litros_atuais, 2)

    # 2. autonomia_media_global
    autonomia_media_global = 0.0
    if len(combustiveis) >= 2:
        km_mais_antiga = combustiveis[0].km_atual
        km_mais_recente = combustiveis[-1].km_atual
        soma_total_litros = sum(c.litros for c in combustiveis)
        delta_km_total = km_mais_recente - km_mais_antiga
        if delta_km_total > 0 and soma_total_litros > 0:
            autonomia_media_global = round(delta_km_total / soma_total_litros, 2)

    # 3. autonomia_maxima_estimada
    autonomia_maxima_estimada = round(autonomia_media_global * capacidade_tanque, 2)

    # 4. custo_estimado_tanque_cheio
    ultimo_preco_litro = combustiveis[-1].valor_por_litro if combustiveis else 0.0
    custo_estimado_tanque_cheio = round(capacidade_tanque * float(ultimo_preco_litro or 0), 2)

    return {
        'autonomia_ultimo_trecho': autonomia_ultimo_trecho,
        'autonomia_media_global': autonomia_media_global,
        'autonomia_maxima_estimada': autonomia_maxima_estimada,
        'custo_estimado_tanque_cheio': custo_estimado_tanque_cheio,
    }

