from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import CustoFixo

User = get_user_model()

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
