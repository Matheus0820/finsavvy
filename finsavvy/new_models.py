from django.db import models
from django.contrib.auth.models import User

# Categoria para custos variáveis
class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome

# Custos Variáveis (apenas preço, nome, data e categoria)
class CustoVariavel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_variaveis')
    nome = models.CharField(max_length=255)
    valor = models.FloatField()
    data = models.DateField(auto_now_add=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='custos', null=True, blank=True)

    def __str__(self):
        return f"{self.nome} ({self.valor})"

# Custos de compras via QR / código‑barra
class CustoCompra(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_compras')
    nome = models.CharField(max_length=255)
    valor = models.FloatField()
    data = models.DateField(auto_now_add=True)
    qr_data = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Compra: {self.nome} ({self.valor})"

# Veículos
class Veiculo(models.Model):
    CARRO = 'CAR'
    MOTO = 'MOT'
    TIPO_CHOICES = [
        (CARRO, 'Carro'),
        (MOTO, 'Moto'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='veiculos')
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    placa = models.CharField(max_length=10, unique=True)
    tipo_veiculo = models.CharField(max_length=3, choices=TIPO_CHOICES)
    km_atual = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placa})"

# Custos de combustível
class CustoCombustivel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_combustivel')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='combustiveis')
    data = models.DateField(auto_now_add=True)
    litros = models.FloatField()
    valor = models.FloatField(help_text='Valor pago pela quantidade de litros')

    def __str__(self):
        return f"{self.tempo_vinculacao(self.veiculo)} - {self.litros}L"

# Manutenções (com ou sem troca de óleo)
class Manutencao(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manutencoes')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='manutenções')
    data = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=255)  # ex.: "Troca de óleo"
    descricao = models.TextField(blank=True, null=True)
    valor = models.FloatField()
    km_atual = models.PositiveIntegerField()
    km_proximo_oleo = models.PositiveIntegerField(blank=True, null=True)
    km_troca_oleo = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.veiculo} – {self.tipo} ({self.data})"
