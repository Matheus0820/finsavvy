"""
Módulo para análise preventiva e geração de alertas veiculares inteligentes.
Analisa quilometragem, histórico de manutenções e limites de troca de óleo,
armazenando avisos pendentes de forma idempotente no modelo Aviso.
"""
from typing import List
from finsavvy.models import Aviso, Manutencao, TrocaOleo, Veiculo


def gerar_alertas_veiculo(veiculo: Veiculo) -> List[Aviso]:
    """
    Analisa um veículo e gera os alertas preventivos cabíveis caso ainda não existam avisos não lidos.
    Retorna a lista de avisos criados ou atualizados.
    """
    alertas_gerados = []
    user = veiculo.user

    # Busca a última troca de óleo realizada para o veículo
    ultima_troca_oleo = (
        TrocaOleo.objects.filter(veiculo=veiculo)
        .order_by('-data', '-km_atual', '-id')
        .first()
    )

    # 1. Regra para Troca de Óleo
    km_alvo = None
    if ultima_troca_oleo and ultima_troca_oleo.km_proxima_troca:
        km_alvo = ultima_troca_oleo.km_proxima_troca
    else:
        # Fallback para última manutenção caso exista campo legado
        ultima_manutencao = (
            Manutencao.objects.filter(veiculo=veiculo)
            .order_by('-data', '-km_atual', '-id')
            .first()
        )
        if ultima_manutencao:
            if getattr(ultima_manutencao, 'km_proximo_oleo', None):
                km_alvo = ultima_manutencao.km_proximo_oleo
            elif getattr(ultima_manutencao, 'km_troca_oleo', None):
                km_alvo = ultima_manutencao.km_troca_oleo + 10000

    if km_alvo is not None:
        km_atual = veiculo.km_atual or 0
        if km_atual >= km_alvo:
            # Troca de óleo vencida
            titulo = f"Troca de óleo vencida ({veiculo.placa})"
            mensagem = (
                f"O veículo {veiculo.marca} {veiculo.modelo} ({veiculo.placa}) está com {km_atual} km "
                f"e ultrapassou a quilometragem prevista para troca de óleo ({km_alvo} km)."
            )
            aviso = _salvar_ou_atualizar_alerta(
                user=user,
                veiculo=veiculo,
                tipo='OLEO',
                nivel='URGENTE',
                titulo=titulo,
                mensagem=mensagem,
            )
            if aviso:
                alertas_gerados.append(aviso)
        elif km_atual >= (km_alvo - 1000):
            # Troca de óleo próxima (a 1.000 km ou menos)
            faltam = km_alvo - km_atual
            titulo = f"Troca de óleo próxima ({veiculo.placa})"
            mensagem = (
                f"O veículo {veiculo.marca} {veiculo.modelo} ({veiculo.placa}) está com {km_atual} km "
                f"e faltam apenas {faltam} km para a próxima troca de óleo ({km_alvo} km)."
            )
            aviso = _salvar_ou_atualizar_alerta(
                user=user,
                veiculo=veiculo,
                tipo='OLEO',
                nivel='ALERTA',
                titulo=titulo,
                mensagem=mensagem,
            )
            if aviso:
                alertas_gerados.append(aviso)
    else:
        # Veículo sem nenhuma troca de óleo e com quilometragem relevante
        if (veiculo.km_atual or 0) >= 10000:
            titulo = f"Revisão preventiva recomendada ({veiculo.placa})"
            mensagem = (
                f"O veículo {veiculo.marca} {veiculo.modelo} ({veiculo.placa}) atingiu {veiculo.km_atual} km "
                f"e ainda não possui trocas de óleo cadastradas no FinSavvy."
            )
            aviso = _salvar_ou_atualizar_alerta(
                user=user,
                veiculo=veiculo,
                tipo='OLEO',
                nivel='ALERTA',
                titulo=titulo,
                mensagem=mensagem,
            )
            if aviso:
                alertas_gerados.append(aviso)

    return alertas_gerados


def _salvar_ou_atualizar_alerta(user, veiculo, tipo: str, nivel: str, titulo: str, mensagem: str):
    """
    Salva um alerta evitando duplicações desnecessárias caso já exista um aviso não lido
    do mesmo tipo para o veículo. Se houver escalação (ex: de ALERTA para URGENTE), atualiza o existente.
    """
    existente = Aviso.objects.filter(
        user=user,
        veiculo=veiculo,
        tipo=tipo,
        lido=False,
    ).first()

    if existente:
        # Se escalou de ALERTA para URGENTE ou houve alteração de mensagem/título, atualiza
        if existente.nivel != nivel or existente.titulo != titulo:
            existente.nivel = nivel
            existente.titulo = titulo
            existente.mensagem = mensagem
            existente.save(update_fields=['nivel', 'titulo', 'mensagem'])
            return existente
        return None

    # Cria novo aviso
    return Aviso.objects.create(
        user=user,
        veiculo=veiculo,
        tipo=tipo,
        nivel=nivel,
        titulo=titulo,
        mensagem=mensagem,
        lido=False,
    )


def gerar_alertas_usuario(user) -> List[Aviso]:
    """
    Varre todos os veículos do usuário e processa a geração de alertas preventivos.
    """
    novos_ou_atualizados = []
    for veiculo in Veiculo.objects.filter(user=user):
        novos = gerar_alertas_veiculo(veiculo)
        novos_ou_atualizados.extend(novos)
    return novos_ou_atualizados
