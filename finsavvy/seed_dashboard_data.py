import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.contrib.auth.models import User
from finsavvy.models import (
    Categoria, CustoFixo, CustoVariavel, Renda,
    CustoCompra, Veiculo, CustoCombustivel, Manutencao, TrocaOleo
)
def create_test_data():
    # Get users
    user1 = User.objects.get(username='test_trava')
    user2 = User.objects.get(username='test_verifier')

    # Create categories
    categoria_alimentacao, _ = Categoria.objects.get_or_create(
        nome='Alimentação', cor='#ff6b6b'
    )
    categoria_transportes, _ = Categoria.objects.get_or_create(
        nome='Transporte', cor='#4ecdc4'
    )
    categoria_saude, _ = Categoria.objects.get_or_create(
        nome='Saúde', cor='#45b7d1'
    )

    # Renda for user1
    Renda.objects.create(
        user=user1,
        descricao='Salário',
        valor=5000.0,
        tipo_renda='FIXA',
        data_recebimento=datetime(2026, 11, 1).date()
    )
    Renda.objects.create(
        user=user1,
        descricao='Freelance',
        valor=3000.0,
        tipo_renda='FIXA',
        data_recebimento=datetime(2026, 11, 15).date()
    )
    Renda.objects.create(
        user=user1,
        descricao='Bônus',
        valor=2000.0,
        tipo_renda='VARIAVEL',
        data_recebimento=datetime(2026, 11, 20).date()
    )

    # Renda for user2
    Renda.objects.create(
        user=user2,
        descricao='Investimento',
        valor=8000.0,
        tipo_renda='FIXA',
        data_recebimento=datetime(2026, 11, 5).date()
    )
    Renda.objects.create(
        user=user2,
        descricao='Consultoria',
        valor=1500.0,
        tipo_renda='VARIAVEL',
        data_recebimento=datetime(2026, 11, 10).date()
    )

    # CustoFixo for user1
    CustoFixo.objects.create(
        user=user1,
        nome='Aluguel',
        valor=1200.0,
        dia_vencimento=5,
        data_vigencia=datetime(2026, 12, 31).date()
    )

    # CustoVariavel for user1
    CustoVariavel.objects.create(
        user=user1,
        nome='Supermercado',
        valor=600.0,
        data=datetime(2026, 11, 5).date(),
        categoria=categoria_alimentacao
    )
    CustoVariavel.objects.create(
        user=user1,
        nome='Conta de luz',
        valor=200.0,
        data=datetime(2026, 11, 10).date(),
        categoria=categoria_transportes
    )

    # CustoCompra for user1
    CustoCompra.objects.create(
        user=user1,
        estabelecimento='Mercado',
        data=datetime(2026, 11, 5).date(),
        valor_total=600.0
    )

    # Veiculo for user1
    veiculo1 = Veiculo.objects.create(
        user=user1,
        marca='Toyota',
        modelo='Corolla',
        placa='ABC-1234',
        tipo_veiculo='CARRO',
        km_atual=50000
    )
    CustoCombustivel.objects.create(
        user=user1,
        veiculo=veiculo1,
        data=datetime(2026, 11, 6).date(),
        valor_abastecido=300.0,
        valor_por_litro=5.0,
        km_atual=50000
    )

    # Manutencao for user1
    Manutencao.objects.create(
        user=user1,
        veiculo=veiculo1,
        data=datetime(2026, 11, 15).date(),
        tipo='Manutenção',
        descricao='Troca de óleo',
        valor=150.0,
        km_atual=50000
    )

    # TrocaOleo for user1
    TrocaOleo.objects.create(
        user=user1,
        veiculo=veiculo1,
        data=datetime(2026, 11, 15).date(),
        km_atual=50000,
        valor=150.0,
        tipo_oleo='5W30',
        intervalo_troca=5000
    )

    print("Test data created successfully!")
if __name__ == '__main__':
    create_test_data()