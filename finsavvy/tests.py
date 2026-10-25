from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import CustoFixo, Veiculo, Categoria, CustoVariavel

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
        response = self.client.post(reverse('add_custofixo'), {'nome': 'Novo', 'valor': '50.5'})
        self.assertRedirects(response, reverse('list_custosFixos'))
        self.assertTrue(CustoFixo.objects.filter(user=self.user1, nome='Novo', valor=50.5).exists())

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
            {'nome': 'Serviço A Editado', 'valor': '150.0'}
        )
        self.assertRedirects(response, reverse('list_custosFixos'))
        self.custo1.refresh_from_db()
        self.assertEqual(self.custo1.nome, 'Serviço A Editado')
        self.assertEqual(float(self.custo1.valor), 150.0)

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
