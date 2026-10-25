import pytest
from django.test import TestCase
from finsavvy.models import Veiculo, Manutencao

class VeiculoModelTest(TestCase):
    def setUp(self):
        self.veiculo = Veiculo.objects.create(marca='Fiat', modelo='Uno', ano=2010, placa='ABC1234')

    def test_veiculo_creation(self):
        assert self.veiculo.pk is not None
        assert str(self.veiculo) == self.veiculo.placa

class ManutencaoModelTest(TestCase):
    def setUp(self):
        veiculo = Veiculo.objects.create(marca='Ford', modelo='Ka', ano=2015, placa='XYZ9876')
        self.manutencao = Manutencao.objects.create(veiculo=veiculo, data='2023-01-01', tipo='Troca de óleo', valor=150.0)

    def test_manutencao_creation(self):
        assert self.manutencao.pk is not None
        assert self.manutencao.veiculo.pk == self.manutencao.veiculo.pk
