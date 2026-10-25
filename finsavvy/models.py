from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    cor = models.CharField(max_length=7, default='#631aff')

    def __str__(self):
        return self.nome

class CustoFixo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_fixos')
    nome = models.CharField(max_length=255, default="")
    valor = models.FloatField(blank=False, default="")

    def __str__(self):
        return self.nome

class CustoVariavel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_variaveis')
    nome = models.CharField(max_length=255)
    valor = models.FloatField()
    data = models.DateField(auto_now_add=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='custos', null=True, blank=True)

    def __str__(self):
        return f"{self.nome} ({self.valor})"

class CustoCompra(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_compras')
    nome = models.CharField(max_length=255)
    valor = models.FloatField()
    data = models.DateField(auto_now_add=True)
    qr_data = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Compra: {self.nome} ({self.valor})"

class Veiculo(models.Model):
    TIPO_VEICULO = [
        ('CARRO', 'Carro'),
        ('MOTO', 'Moto'),
        ('CAMINHAO', 'Caminhão'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='veiculos')
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    placa = models.CharField(max_length=20)
    tipo_veiculo = models.CharField(max_length=20, choices=TIPO_VEICULO)
    km_atual = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placa})"

class CustoCombustivel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_combustivel')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='combustiveis')
    data = models.DateField(auto_now_add=True)
    litros = models.FloatField()
    valor = models.FloatField(help_text='Valor pago pela quantidade de litros')

    def __str__(self):
        return f"{self.veiculo} - {self.litros}L"

class Manutencao(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manutencoes')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='manutenções')
    data = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    valor = models.FloatField()
    km_atual = models.PositiveIntegerField()
    km_proximo_oleo = models.PositiveIntegerField(blank=True, null=True)
    km_troca_oleo = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.veiculo} – {self.tipo} ({self.data})"

