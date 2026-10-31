from unittest.mock import patch, MagicMock
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import CustoFixo, Veiculo, Categoria, CustoVariavel, CustoCombustivel, Manutencao, Aviso, CustoCompra, ItemCompra, Renda
from .utils.leitor_qrcode import extrair_dados_nfce, decodificar_imagem_qrcode
from .utils.leitor_nfce import parsear_html_nfce, consultar_nfce
from .utils.calculos_veiculares import (
    calcular_consumo_medio,
    calcular_custo_por_km,
    calcular_preco_medio_litro,
    calcular_estatisticas_por_veiculo,
    calcular_metricas_veiculares_gerais,
    preparar_dados_grafico_consumo,
    calcular_autonomia,
)
from .utils.alertas_veiculares import (
    gerar_alertas_veiculo,
    gerar_alertas_usuario,
)
from .utils.forms import sanitizar_valor_monetario, MonetaryMaskMixin
from .forms import FormCustoFixo
from .new_forms import FormCustoVariavel, FormCustoCombustivel

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


class VeiculoCombustivelBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='motorista_test', password='testpass')

    def test_model_fields_and_property_litros(self):
        veiculo = Veiculo.objects.create(
            user=self.user,
            marca='Volkswagen',
            modelo='Golf',
            placa='ABC1D23',
            tipo_veiculo='CARRO',
            km_atual=10000,
            capacidade_tanque=55
        )
        self.assertEqual(veiculo.capacidade_tanque, 55)

        combustivel = CustoCombustivel.objects.create(
            user=self.user,
            veiculo=veiculo,
            valor_abastecido=300.0,
            valor_por_litro=6.0,
            km_atual=10500,
            tanque_cheio=True
        )
        self.assertEqual(combustivel.km_atual, 10500)
        self.assertTrue(combustivel.tanque_cheio)
        self.assertEqual(combustivel.litros, 50.0)

    def test_signal_atualiza_km_veiculo(self):
        veiculo = Veiculo.objects.create(
            user=self.user,
            marca='Fiat',
            modelo='Pulse',
            placa='PUL1234',
            tipo_veiculo='CARRO',
            km_atual=20000,
            capacidade_tanque=47
        )
        # Abastecimento com KM maior deve atualizar veiculo.km_atual
        CustoCombustivel.objects.create(
            user=self.user,
            veiculo=veiculo,
            valor_abastecido=200.0,
            valor_por_litro=5.0,
            km_atual=20400,
            tanque_cheio=False
        )
        veiculo.refresh_from_db()
        self.assertEqual(veiculo.km_atual, 20400)

        # Abastecimento com KM menor não deve retroceder o hodômetro do veículo
        CustoCombustivel.objects.create(
            user=self.user,
            veiculo=veiculo,
            valor_abastecido=100.0,
            valor_por_litro=5.0,
            km_atual=20100,
            tanque_cheio=False
        )
        veiculo.refresh_from_db()
        self.assertEqual(veiculo.km_atual, 20400)


class FormCustoCombustivelSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='driver_security', password='testpass')
        self.veiculo = Veiculo.objects.create(
            user=self.user,
            marca='Toyota',
            modelo='Corolla',
            placa='SEC1A23',
            tipo_veiculo='CARRO',
            km_atual=30000,
            capacidade_tanque=50
        )

    def test_retroactive_km_initial_vehicle_blocks(self):
        from .new_forms import FormCustoCombustivel
        form = FormCustoCombustivel(data={
            'veiculo': self.veiculo.id,
            'data': '2025-05-10',
            'valor_abastecido': 200.0,
            'valor_por_litro': 5.0,
            'km_atual': 29000,
            'tanque_cheio': True
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(any('não pode ser menor que a KM cadastrada' in str(err) for err in form.non_field_errors()))

    def test_retroactive_km_previous_fuel_blocks(self):
        from .new_forms import FormCustoCombustivel
        CustoCombustivel.objects.create(
            user=self.user,
            veiculo=self.veiculo,
            data=date(2025, 5, 1),
            valor_abastecido=150.0,
            valor_por_litro=5.0,
            km_atual=30500,
            tanque_cheio=True
        )
        form = FormCustoCombustivel(data={
            'veiculo': self.veiculo.id,
            'data': '2025-05-10',
            'valor_abastecido': 150.0,
            'valor_por_litro': 5.0,
            'km_atual': 30400,
            'tanque_cheio': True
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(any('deve ser maior que a KM do último abastecimento' in str(err) for err in form.non_field_errors()))

    def test_liters_exceeding_tank_capacity_blocks(self):
        from .new_forms import FormCustoCombustivel
        form = FormCustoCombustivel(data={
            'veiculo': self.veiculo.id,
            'data': '2025-05-10',
            'valor_abastecido': 300.0,
            'valor_por_litro': 5.0,
            'km_atual': 30100,
            'tanque_cheio': True
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(any('excede a capacidade do tanque' in str(err) for err in form.non_field_errors()))


class RendaModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='renda_user', password='testpass')

    def test_criar_renda_fixa_e_variavel(self):
        renda_fixa = Renda.objects.create(
            user=self.user,
            descricao='Salário Mensal',
            valor=5500.00,
            tipo_renda='FIXA'
        )
        renda_var = Renda.objects.create(
            user=self.user,
            descricao='Freelance Python',
            valor=1200.50,
            tipo_renda='VARIAVEL'
        )
        self.assertEqual(renda_fixa.tipo_renda, 'FIXA')
        self.assertEqual(renda_var.tipo_renda, 'VARIAVEL')
        self.assertEqual(Renda.objects.filter(user=self.user).count(), 2)


class VeiculoUITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ui_user', password='testpass')
        self.client.login(username='ui_user', password='testpass')
        self.carro = Veiculo.objects.create(
            user=self.user,
            marca='Fiat',
            modelo='Cronos',
            placa='CRO1A23',
            tipo_veiculo='CARRO',
            km_atual=15000,
            capacidade_tanque=48
        )
        self.combustivel = CustoCombustivel.objects.create(
            user=self.user,
            veiculo=self.carro,
            data=date(2025, 6, 1),
            valor_abastecido=240.0,
            valor_por_litro=6.0,
            km_atual=15500,
            tanque_cheio=True
        )

    def test_list_veiculo_displays_tanque(self):
        response = self.client.get(reverse('list_veiculo'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '48')
        self.assertContains(response, 'Cronos')

    def test_list_custo_combustivel_displays_km_and_tanque_cheio(self):
        response = self.client.get(reverse('list_custoCombustivel'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '15500 km')
        self.assertContains(response, 'R$ 6.00')
        self.assertContains(response, 'Sim')

    def test_relatorio_displays_autonomia_columns(self):
        response = self.client.get(reverse('relatorios'), {'ano': '2025', 'mes': '6'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Autonomia Estimada')
        self.assertContains(response, 'Custo Tanque Cheio')


class MonetaryMaskAndSanitizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mask_user', password='testpass')

    def test_sanitizar_valor_monetario_formats(self):
        self.assertEqual(sanitizar_valor_monetario('1.250,50'), 1250.50)
        self.assertEqual(sanitizar_valor_monetario('R$ 1.250,50'), 1250.50)
        self.assertEqual(sanitizar_valor_monetario('250,75'), 250.75)
        self.assertEqual(sanitizar_valor_monetario('100.00'), 100.00)
        self.assertEqual(sanitizar_valor_monetario(50.2), 50.2)
        self.assertIsNone(sanitizar_valor_monetario(''))
        self.assertIsNone(sanitizar_valor_monetario(None))

    def test_form_custofixo_with_masked_value(self):
        form = FormCustoFixo(data={'nome': 'Internet Fibra', 'valor': '1.250,50', 'dia_vencimento': 10})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['valor'], 1250.50)

    def test_form_custo_combustivel_with_masked_values(self):
        veiculo = Veiculo.objects.create(
            user=self.user,
            marca='Fiat',
            modelo='Argo',
            placa='ARG1234',
            tipo_veiculo='CARRO',
            km_atual=1000,
            capacidade_tanque=50
        )
        form = FormCustoCombustivel(data={
            'veiculo': veiculo.id,
            'data': '2025-05-10',
            'valor_abastecido': '250,00',
            'valor_por_litro': '5,00',
            'km_atual': 1500,
            'tanque_cheio': True
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['valor_abastecido'], 250.0)
        self.assertEqual(form.cleaned_data['valor_por_litro'], 5.0)


class LandingPageUITests(TestCase):
    def test_landing_page_renders_successfully_with_ctas(self):
        response = self.client.get(reverse('landing_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Começar a Poupar')
        self.assertContains(response, 'Entrar na minha conta')
        self.assertContains(response, 'FinSavvy')


class AuthViewsUITests(TestCase):
    def test_login_view_renders_fluid_card_and_particles(self):
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bem-vindo de volta')
        self.assertContains(response, 'form-floating')
        self.assertContains(response, 'particles-js')

    def test_signup_view_renders_fluid_card_and_particles(self):
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crie sua conta')
        self.assertContains(response, 'form-floating')
        self.assertContains(response, 'particles-js')

    def test_login_submission_error_renders_alerts_and_particles(self):
        response = self.client.post(reverse('account_login'), {
            'login': 'usuario_inexistente@finsavvy.com',
            'password': 'senhaerrada'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'particles-js')
        self.assertContains(response, 'alert-danger')


class NfceScannerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='nfce_tester', password='testpass')
        self.client.login(username='nfce_tester', password='testpass')
        self.chave_sp = '35240512345678000190650010000000011000000010'
        self.chave_rj = '33240512345678000190650010000000011000000015'

    def test_extrair_dados_nfce_chave_44_digitos(self):
        dados_sp = extrair_dados_nfce(self.chave_sp)
        self.assertTrue(dados_sp['sucesso'])
        self.assertEqual(dados_sp['chave_acesso'], self.chave_sp)
        self.assertEqual(dados_sp['uf'], 'SP')
        self.assertIn('SP', dados_sp['nome'])

        dados_rj = extrair_dados_nfce(self.chave_rj)
        self.assertTrue(dados_rj['sucesso'])
        self.assertEqual(dados_rj['chave_acesso'], self.chave_rj)
        self.assertEqual(dados_rj['uf'], 'RJ')

    def test_consultar_nfce_chave_44_digitos_fallback(self):
        res = consultar_nfce(self.chave_sp)
        self.assertTrue(res['sucesso'])
        self.assertEqual(res['chave_acesso'], self.chave_sp)
        self.assertEqual(res['uf'], 'SP')
        self.assertIn('Chave de acesso reconhecida', res['mensagem'])

    def test_ler_nfce_ajax_chave_44_digitos(self):
        response = self.client.post(reverse('api_ler_nfce'), {'qr_text': self.chave_sp})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data.get('sucesso'))
        self.assertEqual(json_data.get('chave_acesso'), self.chave_sp)
        self.assertEqual(json_data.get('uf'), 'SP')

    def test_ler_nfce_ajax_sem_parametros(self):
        response = self.client.post(reverse('api_ler_nfce'), {})
        self.assertEqual(response.status_code, 400)
        json_data = response.json()
        self.assertFalse(json_data.get('sucesso'))

    def test_add_custo_compra_renders_scanner_modal_elements(self):
        response = self.client.get(reverse('add_custoCompra'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="modalCameraScanner"')
        self.assertContains(response, 'id="btn-tirar-foto-nativa"')
        self.assertContains(response, 'id="btn-toggle-camera-live"')
        self.assertContains(response, 'id="qr-input-file"')
        self.assertContains(response, 'capture="environment"')
        self.assertContains(response, 'id="qr-camera-view"')









