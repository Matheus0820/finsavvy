from unittest.mock import patch, MagicMock
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
        self.assertContains(response, 'Enter a number.', html=True)
        self.custo1.refresh_from_db()
        self.assertEqual(self.custo1.nome, 'Serviço A')
        self.assertEqual(float(self.custo1.valor), 100.0)

    def test_delete_other_user_custo_404(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.post(reverse('remove_custofixo', args=[self.custo2.id]))
        self.assertEqual(response.status_code, 404)

class VeiculoTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='testpass')
        self.veiculo1 = Veiculo.objects.create(
            user=self.user1, marca='Toyota', modelo='Corolla', placa='ABC-1234', tipo_veiculo='CARRO', km_atual=10000
        )

    def test_list_veiculos(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.get(reverse('list_veiculo'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Corolla')

    def test_add_veiculo(self):
        self.client.login(username='alice', password='testpass')
        response = self.client.post(reverse('add_veiculo'), {
            'marca': 'Honda', 'modelo': 'Civic', 'placa': 'XYZ-5678', 'tipo_veiculo': 'CARRO', 'km_atual': 5000
        })
        self.assertRedirects(response, reverse('list_veiculo'))
        self.assertTrue(Veiculo.objects.filter(placa='XYZ-5678').exists())


class RelatoriosTests(TestCase):
    def setUp(self):
        from datetime import date
        self.user1 = User.objects.create_user(username='alice', password='testpass')
        self.user2 = User.objects.create_user(username='bob', password='testpass')
        self.client.login(username='alice', password='testpass')

        self.cat_alimentacao = Categoria.objects.create(nome='Alimentação', cor='#ff5733')
        self.cat_lazer = Categoria.objects.create(nome='Lazer', cor='#198754')

        # Custos variáveis de Alice
        self.cv1 = CustoVariavel.objects.create(
            user=self.user1, nome='Supermercado', valor=350.0, categoria=self.cat_alimentacao
        )
        self.cv2 = CustoVariavel.objects.create(
            user=self.user1, nome='Cinema', valor=60.0, categoria=self.cat_lazer
        )
        # Ajusta datas via queryset update para contornar auto_now_add
        CustoVariavel.objects.filter(id=self.cv1.id).update(data=date(2025, 3, 10))
        CustoVariavel.objects.filter(id=self.cv2.id).update(data=date(2025, 4, 15))

        # Custo de Bob (isolamento de usuário)
        self.cv_bob = CustoVariavel.objects.create(
            user=self.user2, nome='Gasto Bob', valor=999.0, categoria=self.cat_alimentacao
        )
        CustoVariavel.objects.filter(id=self.cv_bob.id).update(data=date(2025, 3, 10))

        # Custo Fixo de Alice
        self.cf = CustoFixo.objects.create(user=self.user1, nome='Internet', valor=120.0)

    def test_relatorios_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('relatorios'))
        self.assertEqual(response.status_code, 302)

    def test_relatorios_status_200_authenticated(self):
        response = self.client.get(reverse('relatorios'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/relatorios.html')

    def test_relatorios_filtro_mes_ano(self):
        response = self.client.get(reverse('relatorios'), {'ano': '2025', 'mes': '3'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Supermercado')
        self.assertNotContains(response, 'Cinema')
        self.assertNotContains(response, 'Gasto Bob')

    def test_relatorios_filtro_categoria(self):
        response = self.client.get(
            reverse('relatorios'),
            {'ano': '2025', 'mes': 'todos', 'categoria': str(self.cat_lazer.id)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cinema')
        self.assertNotContains(response, 'Supermercado')
        self.assertNotContains(response, 'Gasto Bob')


class CalculosVeicularesUnitTests(TestCase):
    def test_calcular_consumo_medio_normal(self):
        # 500 km rodados com 50 litros = 10 km/L
        consumo = calcular_consumo_medio(500, 50)
        self.assertEqual(consumo, 10.0)

    def test_calcular_consumo_medio_divisao_por_zero(self):
        # Litros zero ou negativo não deve levantar ZeroDivisionError
        self.assertEqual(calcular_consumo_medio(500, 0), 0.0)
        self.assertEqual(calcular_consumo_medio(500, -5), 0.0)
        self.assertEqual(calcular_consumo_medio(0, 50), 0.0)
        self.assertEqual(calcular_consumo_medio(-100, 50), 0.0)

    def test_calcular_consumo_medio_invalid_input(self):
        self.assertEqual(calcular_consumo_medio(None, 50), 0.0)
        self.assertEqual(calcular_consumo_medio('invalido', 50), 0.0)

    def test_calcular_custo_por_km_normal(self):
        # R$ 300 para 600 km = 0.50 R$/km
        custo_km = calcular_custo_por_km(300, 600)
        self.assertEqual(custo_km, 0.5)

    def test_calcular_custo_por_km_divisao_por_zero(self):
        # Km zero ou negativo
        self.assertEqual(calcular_custo_por_km(300, 0), 0.0)
        self.assertEqual(calcular_custo_por_km(300, -10), 0.0)
        self.assertEqual(calcular_custo_por_km(0, 500), 0.0)
        self.assertEqual(calcular_custo_por_km(-50, 500), 0.0)

    def test_calcular_preco_medio_litro_normal(self):
        # R$ 250 para 50 litros = R$ 5.00/L
        preco_l = calcular_preco_medio_litro(250, 50)
        self.assertEqual(preco_l, 5.0)

    def test_calcular_preco_medio_litro_divisao_por_zero(self):
        self.assertEqual(calcular_preco_medio_litro(250, 0), 0.0)
        self.assertEqual(calcular_preco_medio_litro(0, 50), 0.0)
        self.assertEqual(calcular_preco_medio_litro(-10, 50), 0.0)


class RelatoriosVeicularesIntegrationTests(TestCase):
    def setUp(self):
        from datetime import date
        self.user = User.objects.create_user(username='carlos', password='testpass')
        self.user_outro = User.objects.create_user(username='diana', password='testpass')
        self.client.login(username='carlos', password='testpass')

        # Veículo do usuário autenticado
        self.carro = Veiculo.objects.create(
            user=self.user,
            marca='Toyota',
            modelo='Corolla',
            placa='BRA2E19',
            tipo_veiculo='CARRO',
            km_atual=10000
        )

        # Abastecimento
        self.comb = CustoCombustivel.objects.create(
            user=self.user,
            veiculo=self.carro,
            valor_por_litro=5.0,
            valor_abastecido=250.0
        )
        CustoCombustivel.objects.filter(id=self.comb.id).update(data=date(2025, 5, 10))

        # Manutenção
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


class AvisosVeicularesUnitAndIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='elena', password='testpass')
        self.outro_user = User.objects.create_user(username='felipe', password='testpass')
        self.client.login(username='elena', password='testpass')

        self.veiculo = Veiculo.objects.create(
            user=self.user,
            marca='Fiat',
            modelo='Pulse',
            placa='PLS1020',
            tipo_veiculo='CARRO',
            km_atual=10200,
        )

    def test_alerta_troca_oleo_vencida_inserido_no_banco(self):
        # Manutenção anterior previa troca aos 10.000 km, veículo está com 10.200 km
        Manutencao.objects.create(
            user=self.user,
            veiculo=self.veiculo,
            tipo='Troca de Óleo Anterior',
            valor=250.0,
            km_atual=5000,
            km_proximo_oleo=10000,
        )

        alertas = gerar_alertas_veiculo(self.veiculo)
        self.assertEqual(len(alertas), 1)

        # Garante que o registro foi inserido no banco de dados do modelo Aviso
        aviso_bd = Aviso.objects.filter(
            user=self.user,
            veiculo=self.veiculo,
            tipo='OLEO',
            nivel='URGENTE',
        ).first()
        self.assertIsNotNone(aviso_bd)
        self.assertIn('PLS1020', aviso_bd.titulo)
        self.assertIn('vencida', aviso_bd.titulo.lower())
        self.assertFalse(aviso_bd.lido)

    def test_alerta_troca_oleo_proxima_inserido_no_banco(self):
        # Veículo com 9.500 km e troca prevista para 10.000 km (a menos de 1000 km)
        self.veiculo.km_atual = 9500
        self.veiculo.save()

        Manutencao.objects.create(
            user=self.user,
            veiculo=self.veiculo,
            tipo='Troca de Óleo',
            valor=200.0,
            km_atual=5000,
            km_proximo_oleo=10000,
        )

        alertas = gerar_alertas_veiculo(self.veiculo)
        self.assertEqual(len(alertas), 1)

        aviso_bd = Aviso.objects.filter(
            user=self.user,
            veiculo=self.veiculo,
            tipo='OLEO',
            nivel='ALERTA',
        ).first()
        self.assertIsNotNone(aviso_bd)
        self.assertIn('próxima', aviso_bd.titulo.lower())

    def test_alerta_sem_duplicacao_idempotente(self):
        # Gera o alerta uma vez
        Manutencao.objects.create(
            user=self.user,
            veiculo=self.veiculo,
            tipo='Troca de Óleo',
            valor=200.0,
            km_atual=5000,
            km_proximo_oleo=10000,
        )
        gerar_alertas_veiculo(self.veiculo)
        self.assertEqual(Aviso.objects.filter(veiculo=self.veiculo).count(), 1)

        # Chamada repetida não deve duplicar o registro no banco
        gerar_alertas_veiculo(self.veiculo)
        self.assertEqual(Aviso.objects.filter(veiculo=self.veiculo).count(), 1)

    def test_alerta_revisao_preventiva_sem_manutencao(self):
        # Veículo com 15.000 km e nenhuma manutenção cadastrada
        self.veiculo.km_atual = 15000
        self.veiculo.save()

        alertas = gerar_alertas_veiculo(self.veiculo)
        self.assertEqual(len(alertas), 1)

        aviso_bd = Aviso.objects.filter(
            user=self.user,
            veiculo=self.veiculo,
            tipo='MANUTENCAO',
        ).first()
        self.assertIsNotNone(aviso_bd)
        self.assertIn('Revisão preventiva recomendada', aviso_bd.titulo)

    def test_aviso_view_get_e_actions_post(self):
        # Manutenção disparadora de alerta
        Manutencao.objects.create(
            user=self.user,
            veiculo=self.veiculo,
            tipo='Troca de Óleo',
            valor=200.0,
            km_atual=5000,
            km_proximo_oleo=10000,
        )

        # GET na view aviso deve sincronizar e renderizar o alerta
        response = self.client.get(reverse('aviso'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PLS1020')
        self.assertContains(response, 'Central de Avisos e Notificações')

        aviso_criado = Aviso.objects.get(veiculo=self.veiculo)
        self.assertFalse(aviso_criado.lido)

        # POST para marcar como lido
        post_lido = self.client.post(reverse('aviso'), {
            'action': 'marcar_lido',
            'aviso_id': aviso_criado.id,
        })
        self.assertRedirects(post_lido, reverse('aviso'))
        aviso_criado.refresh_from_db()
        self.assertTrue(aviso_criado.lido)

        # POST para excluir o aviso
        post_del = self.client.post(reverse('aviso'), {
            'action': 'excluir',
            'aviso_id': aviso_criado.id,
        })
        self.assertRedirects(post_del, reverse('aviso'))
        self.assertFalse(Aviso.objects.filter(id=aviso_criado.id).exists())


class CustoCompraAndQrCodeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='gabriel', password='testpass')
        self.outro_user = User.objects.create_user(username='helena', password='testpass')
        self.client.login(username='gabriel', password='testpass')

    def test_extrair_dados_nfce_url_com_parametros(self):
        url = "http://dec.fazenda.df.gov.br/NFCE-decodificador.aspx?chNFe=35231012345678901234567890123456789012345678&vNF=149.90&vICMS=0.00"
        dados = extrair_dados_nfce(url)
        self.assertTrue(dados['sucesso'])
        self.assertEqual(dados['valor'], 149.90)
        self.assertEqual(dados['chave_acesso'], '35231012345678901234567890123456789012345678')

    def test_extrair_dados_nfce_formato_pipe(self):
        payload_sefaz = "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=43231012345678901234567890123456789012345678|2|1|1|79.50|3132"
        dados = extrair_dados_nfce(payload_sefaz)
        self.assertTrue(dados['sucesso'])
        self.assertEqual(dados['valor'], 79.50)
        self.assertEqual(dados['chave_acesso'], '43231012345678901234567890123456789012345678')

    def test_extrair_dados_nfce_texto_livre_com_moeda(self):
        texto = "Cupom Fiscal Supermercado Estrela Total R$ 89,45 Obrigado volte sempre!"
        dados = extrair_dados_nfce(texto)
        self.assertTrue(dados['sucesso'])
        self.assertEqual(dados['valor'], 89.45)
        self.assertTrue(dados['nome'])

    def test_processar_qrcode_view_ajax_sucesso(self):
        url_payload = "http://fazenda.sp.gov.br/nfce/qrcode?chNFe=35231099999999999999999999999999999999999999&vNF=210.35"
        response = self.client.post(reverse('processar_qrcode_compra'), {
            'qr_text': url_payload
        })
        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertTrue(dados['sucesso'])
        self.assertEqual(dados['valor'], 210.35)
        self.assertEqual(dados['chave_acesso'], '35231099999999999999999999999999999999999999')

    def test_processar_qrcode_view_sem_dados(self):
        response = self.client.post(reverse('processar_qrcode_compra'), {})
        self.assertEqual(response.status_code, 400)
        dados = response.json()
        self.assertFalse(dados['sucesso'])

    def test_add_custo_compra_com_autofill_qr(self):
        # Envia formulário com qr_data, mas sem preencher 'valor' explicitamente
        url_qr = "http://dec.fazenda.df.gov.br/NFCE?chNFe=35231012345678901234567890123456789012345678&vNF=98.75"
        response = self.client.post(reverse('add_custoCompra'), {
            'nome': 'Auto Peças Modelo',
            'qr_data': url_qr,
        })
        self.assertRedirects(response, reverse('list_custoCompra'))
        compra = CustoCompra.objects.filter(user=self.user, nome='Auto Peças Modelo').first()
        self.assertIsNotNone(compra)
        self.assertEqual(compra.valor, 98.75)
        self.assertEqual(compra.qr_data, url_qr)

    def test_list_custo_compra_exibe_badge_nfce_e_isolamento_usuario(self):
        compra_com_qr = CustoCompra.objects.create(
            user=self.user,
            nome='Farmácia Central',
            valor=45.0,
            qr_data='http://nfce.fazenda.gov.br/qrcode'
        )
        compra_sem_qr = CustoCompra.objects.create(
            user=self.user,
            nome='Padaria Bairro',
            valor=18.50,
            qr_data=''
        )
        compra_outro = CustoCompra.objects.create(
            user=self.outro_user,
            nome='Compra Secreta Outro',
            valor=999.0
        )

        response = self.client.get(reverse('list_custoCompra'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Farmácia Central')
        self.assertContains(response, 'Padaria Bairro')
        self.assertContains(response, 'NFC-e')
        self.assertContains(response, 'bi-qr-code')
        self.assertNotContains(response, 'Compra Secreta Outro')

    def test_exportar_relatorios_csv(self):
        # Cria registros variados para testar exportação CSV
        CustoVariavel.objects.create(
            user=self.user,
            nome='Mercado Mensal',
            valor=350.50,
        )
        CustoCompra.objects.create(
            user=self.user,
            nome='Ferramentas',
            valor=120.00,
        )
        CustoCompra.objects.create(
            user=self.outro_user,
            nome='Item Outro Usuário Não Deve Aparecer',
            valor=888.88,
        )

        response = self.client.get(reverse('exportar_relatorios_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('attachment; filename="relatorio_despesas_', response['Content-Disposition'])

        conteudo = response.content.decode('utf-8')
        # Cabeçalho
        self.assertIn('Data;Tipo;Descrição / Item;Categoria;Valor (R$)', conteudo)
        # Linhas do usuário logado
        self.assertIn('Mercado Mensal', conteudo)
        self.assertIn('350,50', conteudo)
        self.assertIn('Ferramentas', conteudo)
        self.assertIn('120,00', conteudo)
        # Linha do outro usuário isolada
        self.assertNotIn('Item Outro Usuário Não Deve Aparecer', conteudo)


class CustoCompraMestreDetalheSignalsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='carlos', password='testpass')

    def test_criacao_itens_recalcula_valor_total_da_compra_automaticamente(self):
        compra = CustoCompra.objects.create(
            user=self.user,
            estabelecimento='Supermercado Central',
            valor_total=0.0
        )
        self.assertEqual(compra.valor_total, 0.0)

        # Primeiro item: 2 x 15.50 = 31.00
        item1 = ItemCompra.objects.create(
            compra=compra,
            descricao='Arroz 5kg',
            quantidade=2.0,
            valor_unitario=15.50
        )
        self.assertEqual(item1.valor_total_item, 31.00)

        compra.refresh_from_db()
        self.assertEqual(compra.valor_total, 31.00)

        # Segundo item: 3 x 4.25 = 12.75 -> Total deve ir para 43.75
        item2 = ItemCompra.objects.create(
            compra=compra,
            descricao='Feijão Carioca 1kg',
            quantidade=3.0,
            valor_unitario=4.25
        )
        self.assertEqual(item2.valor_total_item, 12.75)

        compra.refresh_from_db()
        self.assertEqual(compra.valor_total, 43.75)

    def test_exclusao_de_item_recalcula_valor_total_via_signal(self):
        compra = CustoCompra.objects.create(
            user=self.user,
            estabelecimento='Açougue Boi Gordo'
        )
        item1 = ItemCompra.objects.create(
            compra=compra,
            descricao='Picanha',
            quantidade=1.5,
            valor_unitario=60.00  # 90.00
        )
        item2 = ItemCompra.objects.create(
            compra=compra,
            descricao='Carvão',
            quantidade=1.0,
            valor_unitario=25.00  # 25.00
        )

        compra.refresh_from_db()
        self.assertEqual(compra.valor_total, 115.00)

        # Deletando item2 via signal post_delete
        item2.delete()
        compra.refresh_from_db()
        self.assertEqual(compra.valor_total, 90.00)

        # Deletando item1
        item1.delete()
        compra.refresh_from_db()
        self.assertEqual(compra.valor_total, 0.0)

    def test_exclusao_em_cascata_da_compra_remove_itens(self):
        compra = CustoCompra.objects.create(
            user=self.user,
            estabelecimento='Farmácia Popular'
        )
        ItemCompra.objects.create(
            compra=compra,
            descricao='Remédio A',
            quantidade=1,
            valor_unitario=35.00
        )
        ItemCompra.objects.create(
            compra=compra,
            descricao='Remédio B',
            quantidade=2,
            valor_unitario=10.00
        )

        self.assertEqual(ItemCompra.objects.filter(compra=compra).count(), 2)

        # Excluir a compra mestre deve apagar os itens associados
        compra.delete()
        self.assertEqual(ItemCompra.objects.filter(compra_id=compra.id).count(), 0)


class LeitorNfceScrapingTests(TestCase):
    """
    Testes unitários para o motor de Web Scraping de NFC-e (finsavvy/utils/leitor_nfce.py),
    validando parsing de múltiplos layouts estaduais (SP, RS, PR) e tolerância a falhas
    com mocks de requisições HTTP (sem conexão real com a internet).
    """

    def setUp(self):
        self.html_layout_sp = """
        <!DOCTYPE html>
        <html>
        <head><title>Consulta Danfe NFC-e</title></head>
        <body>
            <div class="txtTopo">SUPERMERCADOS PAULISTA LTDA</div>
            <div class="linhaTexto">Emissão: 24/10/2026 18:45:00</div>
            <span class="chave">35261012345678000195650010000001231000004567</span>
            <table id="tabResult">
                <tr>
                    <td>
                        <span class="txtTit">ARROZ TIPO 1 5KG</span>
                        <span class="RCurva"><span class="txtR">Qtd.:</span><span class="Rqtd">2.0</span></span>
                        <span class="RCurva"><span class="txtR">Vl. Unit.:</span><span class="RvlUnit">25,50</span></span>
                        <span class="valor">51,00</span>
                    </td>
                </tr>
                <tr>
                    <td>
                        <span class="txtTit">FEIJAO CARIOCA 1KG</span>
                        <span class="RCurva"><span class="txtR">Qtd.:</span><span class="Rqtd">3.0</span></span>
                        <span class="RCurva"><span class="txtR">Vl. Unit.:</span><span class="RvlUnit">8,00</span></span>
                        <span class="valor">24,00</span>
                    </td>
                </tr>
            </table>
            <div id="totalNota" class="totalNFe">
                <span class="txtMax">75,00</span>
            </div>
        </body>
        </html>
        """

        self.html_layout_rs = """
        <html>
        <body>
            <div class="NFRec">HIPERMERCADO GAUCHO S/A</div>
            <div>Data: 20/10/2026 10:15:30</div>
            <div class="chave-acesso">43261099999999000199650010000009991000009999</div>
            <table class="tabelaItens">
                <tr>
                    <td><span class="txtTit2">LEITE INTEGRAL 1L</span></td>
                    <td><span class="Rqtd">4</span></td>
                    <td><span class="RvlUnit">4,50</span></td>
                    <td><span class="valor">18,00</span></td>
                </tr>
            </table>
            <div class="valor-total-nota">18,00</div>
        </body>
        </html>
        """

    def test_parsear_html_layout_sp(self):
        dados = parsear_html_nfce(self.html_layout_sp)
        self.assertTrue(dados['sucesso'])
        self.assertEqual(dados['estabelecimento'], 'SUPERMERCADOS PAULISTA LTDA')
        self.assertEqual(dados['chave_acesso'], '35261012345678000195650010000001231000004567')
        self.assertEqual(dados['valor_total'], 75.00)
        self.assertEqual(len(dados['itens']), 2)

        item1 = dados['itens'][0]
        self.assertEqual(item1['descricao'], 'ARROZ TIPO 1 5KG')
        self.assertEqual(item1['quantidade'], 2.0)
        self.assertEqual(item1['valor_unitario'], 25.50)
        self.assertEqual(item1['valor_total'], 51.00)

        item2 = dados['itens'][1]
        self.assertEqual(item2['descricao'], 'FEIJAO CARIOCA 1KG')
        self.assertEqual(item2['quantidade'], 3.0)
        self.assertEqual(item2['valor_unitario'], 8.00)
        self.assertEqual(item2['valor_total'], 24.00)

    def test_parsear_html_layout_rs(self):
        dados = parsear_html_nfce(self.html_layout_rs)
        self.assertTrue(dados['sucesso'])
        self.assertEqual(dados['estabelecimento'], 'HIPERMERCADO GAUCHO S/A')
        self.assertEqual(dados['chave_acesso'], '43261099999999000199650010000009991000009999')
        self.assertEqual(dados['valor_total'], 18.00)
        self.assertEqual(len(dados['itens']), 1)
        self.assertEqual(dados['itens'][0]['descricao'], 'LEITE INTEGRAL 1L')
        self.assertEqual(dados['itens'][0]['quantidade'], 4.0)
        self.assertEqual(dados['itens'][0]['valor_unitario'], 4.50)
        self.assertEqual(dados['itens'][0]['valor_total'], 18.00)

    @patch('finsavvy.utils.leitor_nfce.requests.get')
    def test_consultar_nfce_com_mock_sucesso(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.html_layout_sp
        mock_response.content = self.html_layout_sp.encode('utf-8')
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response

        url_teste = "https://www.fazenda.sp.gov.br/nfce/qrcode?p=35261012345678000195650010000001231000004567|2|1|1|75.00"
        resultado = consultar_nfce(url_teste)

        self.assertTrue(resultado['sucesso'])
        self.assertEqual(resultado['estabelecimento'], 'SUPERMERCADOS PAULISTA LTDA')
        self.assertEqual(resultado['valor_total'], 75.00)
        self.assertEqual(len(resultado['itens']), 2)
        mock_get.assert_called_once()

    @patch('finsavvy.utils.leitor_nfce.requests.get')
    def test_consultar_nfce_com_mock_timeout_faz_fallback_url(self, mock_get):
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("Conexão expirou")

        url_com_dados = "https://dfe.sefaz.gov.br/nfce?chNFe=35261012345678000195650010000001231000004567&vNF=142.80"
        resultado = consultar_nfce(url_com_dados)

        self.assertTrue(resultado['sucesso'])
        self.assertEqual(resultado['valor_total'], 142.80)
        self.assertEqual(resultado['chave_acesso'], '35261012345678000195650010000001231000004567')
        self.assertIn("Timeout", resultado['mensagem'])
        self.assertEqual(len(resultado['itens']), 0)

    @patch('finsavvy.utils.leitor_nfce.requests.get')
    def test_consultar_nfce_com_mock_erro_conexao(self, mock_get):
        from requests.exceptions import ConnectionError
        mock_get.side_effect = ConnectionError("Servidor indisponível")

        url = "https://sefaz.invalida.gov.br/nfce"
        resultado = consultar_nfce(url)

        self.assertFalse(resultado['sucesso'])
        self.assertIn("Falha na conexão", resultado['mensagem'])

    def test_consultar_nfce_identificador_sem_url(self):
        resultado = consultar_nfce("chave_sem_protocolo_http")
        self.assertFalse(resultado['sucesso'])
        self.assertIn("não é uma URL válida", resultado['mensagem'])







