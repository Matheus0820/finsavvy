from unittest.mock import patch, MagicMock
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import CustoFixo, Veiculo, Categoria, CustoVariavel, CustoCombustivel, Manutencao, Aviso, CustoCompra, ItemCompra
from .utils.leitor_qrcode import extrair_dados_nfce, decodificar_imagem_qrcode
from .utils.leitor_nfce import parsear_html_nfce, consultar_nfce
from .utils.calculos_veiculares import (
    calcular_consumo_medio,
    calcular_custo_por_km,
    calcular_preco_medio_litro,
    calcular_estatisticas_por_veiculo,
    calcular_metricas_veiculares_gerais,
    preparar_dados_grafico_consumo,
)
from .utils.alertas_veiculares import (
    gerar_alertas_veiculo,
    gerar_alertas_usuario,
)

User = get_user_model()

class CategoriaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='testpass')
        self.client.login(username='alice', password='testpass')

    def test_add_categoria_with_color(self):
        response = self.client.post(reverse('add_categoria'), {
            'nome': 'Alimentação',
            'cor': '#ff5733'
        })
        self.assertRedirects(response, reverse('list_categoria'))
        cat = Categoria.objects.get(nome='Alimentação')
        self.assertEqual(cat.cor, '#ff5733')

    def test_list_categoria_renders_badge_with_color(self):
        cat = Categoria.objects.create(nome='Transporte', cor='#198754')
        response = self.client.get(reverse('list_categoria'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '#198754')
        self.assertContains(response, 'Transporte')

    def test_edit_categoria_color(self):
        cat = Categoria.objects.create(nome='Saúde', cor='#0d6efd')
        response = self.client.post(reverse('edit_categoria', args=[cat.id]), {
            'nome': 'Saúde & Bem-Estar',
            'cor': '#631aff'
        })
        self.assertRedirects(response, reverse('list_categoria'))
        cat.refresh_from_db()
        self.assertEqual(cat.nome, 'Saúde & Bem-Estar')
        self.assertEqual(cat.cor, '#631aff')

    def test_protected_delete_categoria(self):
        cat = Categoria.objects.create(nome='Educação', cor='#ffc107')
        CustoVariavel.objects.create(user=self.user, nome='Curso Python', valor=250.0, categoria=cat)
        response = self.client.post(reverse('remove_categoria', args=[cat.id]))
        self.assertRedirects(response, reverse('list_categoria'))
        self.assertTrue(Categoria.objects.filter(id=cat.id).exists())


class CustoFixoTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='testpass')
        self.user2 = User.objects.create_user(username='bob', password='testpass')
        self.custo1 = CustoFixo.objects.create(user=self.user1, nome='Serviço A', valor=100.0)
        self.custo2 = CustoFixo.objects.create(user=self.user2, nome='Serviço B', valor=200.0)

    def test_add_custo_valid(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.post(reverse('add_custofixo'), {'nome': 'Novo', 'valor': '50.5', 'dia_vencimento': '10'})
        self.assertRedirects(response, reverse('list_custosFixos'))
        self.assertTrue(CustoFixo.objects.filter(user=self.user1, nome='Novo', valor=50.5, dia_vencimento=10).exists())

    def test_add_custo_invalid(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.post(reverse('add_custofixo'), {'valor': '70'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.', html=True)
        self.assertFalse(CustoFixo.objects.filter(user=self.user1, valor=70).exists())

    def test_edit_custo_valid(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.post(
            reverse('edit_custofixo', args=[self.custo1.id]),
            {'nome': 'Serviço A Editado', 'valor': '150.0', 'dia_vencimento': '15'}
        )
        self.assertRedirects(response, reverse('list_custosFixos'))
        self.custo1.refresh_from_db()
        self.assertEqual(self.custo1.nome, 'Serviço A Editado')
        self.assertEqual(float(self.custo1.valor), 150.0)
        self.assertEqual(self.custo1.dia_vencimento, 15)

    def test_edit_custo_invalid(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.post(
            reverse('edit_custofixo', args=[self.custo1.id]),
            {'nome': '', 'valor': 'abc'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.', html=True)


class RelatoriosVeicularesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='driver', password='testpass')
        self.user_outro = User.objects.create_user(username='otherdriver', password='testpass')
        self.client.login(username='driver', password='testpass')

        self.carro = Veiculo.objects.create(
            user=self.user,
            marca='Toyota',
            modelo='Corolla',
            placa='BRA2E19',
            tipo_veiculo='CARRO',
            km_atual=10000
        )
        self.comb = CustoCombustivel.objects.create(
            user=self.user,
            veiculo=self.carro,
            valor_por_litro=5.0,
            valor_abastecido=250.0
        )
        CustoCombustivel.objects.filter(id=self.comb.id).update(data=date(2025, 5, 10))

        self.manut = Manutencao.objects.create(
            user=self.user,
            veiculo=self.carro,
            tipo='Troca de Óleo',
            valor=200.0,
            km_atual=10000
        )
        Manutencao.objects.filter(id=self.manut.id).update(data=date(2025, 5, 12))

        # Veículo de outro usuário (garantia de isolamento)
        self.carro_outro = Veiculo.objects.create(
            user=self.user_outro,
            marca='Honda',
            modelo='Civic',
            placa='XYZ9999',
            tipo_veiculo='CARRO',
            km_atual=50000
        )
        self.comb_outro = CustoCombustivel.objects.create(
            user=self.user_outro,
            veiculo=self.carro_outro,
            valor_por_litro=6.0,
            valor_abastecido=600.0
        )
        CustoCombustivel.objects.filter(id=self.comb_outro.id).update(data=date(2025, 5, 10))

    def test_relatorios_veiculares_context_e_metricas(self):
        response = self.client.get(reverse('relatorios'), {'ano': '2025', 'mes': '5'})
        self.assertEqual(response.status_code, 200)

        metricas = response.context['metricas_veiculares']
        self.assertEqual(metricas['total_veiculos'], 1)
        self.assertEqual(metricas['total_litros'], 50.0)
        self.assertEqual(metricas['total_combustivel'], 250.0)
        self.assertEqual(metricas['total_manutencao'], 200.0)
        self.assertEqual(metricas['total_gasto_frota'], 450.0)

        # Consumo médio: 10000 km / 50 L = 200.0 km/L
        self.assertEqual(metricas['consumo_medio_frota'], 200.0)
        # Custo/km frota: R$ 450 / 10000 km = 0.045 R$/km (arredondado para 2 casas no Python: 0.04)
        self.assertEqual(metricas['custo_km_frota'], 0.04)
        # Preço médio/litro: R$ 250 / 50 L = 5.0 R$/L
        self.assertEqual(metricas['preco_medio_litro'], 5.0)

        # Template contains vehicle info and tab
        self.assertContains(response, 'Corolla')
        self.assertContains(response, 'BRA2E19')
        self.assertContains(response, 'Estatísticas Veiculares & Eficiência')
        self.assertNotContains(response, 'XYZ9999')
        self.assertNotContains(response, 'Civic')


class ThemeSelectorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='themecases', password='testpass')
        self.client.login(username='themecases', password='testpass')

    def test_theme_selector_present_in_dashboard(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bd-theme')
        self.assertContains(response, 'data-bs-theme-value="light"')
        self.assertContains(response, 'data-bs-theme-value="dark"')
        self.assertContains(response, 'data-bs-theme-value="auto"')
