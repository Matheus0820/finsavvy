from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

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
    dia_vencimento = models.PositiveSmallIntegerField(default=1, help_text='Dia do mês em que vence (1-31)')
    data_vigencia = models.DateField(blank=True, null=True, help_text='Data final de vigência opcional')

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

class CustoCompraQuerySet(models.QuerySet):
    def _remap_kwargs(self, kwargs):
        new_kwargs = {}
        for k, v in kwargs.items():
            if k == 'nome' or k.startswith('nome__'):
                new_key = 'estabelecimento' + k[4:]
                new_kwargs[new_key] = v
            elif k == 'valor' or k.startswith('valor__'):
                new_key = 'valor_total' + k[5:]
                new_kwargs[new_key] = v
            elif k == 'qr_data' or k.startswith('qr_data__'):
                new_key = 'qr_code_url' + k[7:]
                new_kwargs[new_key] = v
            elif k == 'usuario' or k.startswith('usuario__'):
                new_key = 'user' + k[7:]
                new_kwargs[new_key] = v
            else:
                new_kwargs[k] = v
        return new_kwargs

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._remap_kwargs(kwargs))

    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **self._remap_kwargs(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._remap_kwargs(kwargs))


class CustoCompraManager(models.Manager.from_queryset(CustoCompraQuerySet)):
    def create(self, **kwargs):
        remapped = self.get_queryset()._remap_kwargs(kwargs)
        return super().create(**remapped)


class CustoCompra(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_compras')
    estabelecimento = models.CharField(max_length=255)
    data = models.DateField(default=timezone.now)
    valor_total = models.FloatField(default=0.0)
    qr_code_url = models.URLField(max_length=500, blank=True, null=True)

    objects = CustoCompraManager()

    class Meta:
        ordering = ['-data', '-id']

    @property
    def usuario(self):
        return self.user

    @usuario.setter
    def usuario(self, val):
        self.user = val

    @property
    def nome(self):
        return self.estabelecimento

    @nome.setter
    def nome(self, val):
        self.estabelecimento = val

    @property
    def valor(self):
        return self.valor_total

    @valor.setter
    def valor(self, val):
        self.valor_total = val

    @property
    def qr_data(self):
        return self.qr_code_url

    @qr_data.setter
    def qr_data(self, val):
        self.qr_code_url = val

    def __str__(self):
        return f"{self.estabelecimento} - R$ {self.valor_total:.2f} ({self.data})"


class ItemCompra(models.Model):
    compra = models.ForeignKey(CustoCompra, on_delete=models.CASCADE, related_name='itens')
    descricao = models.CharField(max_length=255, blank=True, default="")
    quantidade = models.FloatField(default=1.0, blank=True, null=True)
    valor_unitario = models.FloatField(default=0.0, blank=True, null=True)
    valor_total_item = models.FloatField(default=0.0, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.quantidade is None:
            self.quantidade = 1.0
        if self.valor_unitario is None:
            self.valor_unitario = 0.0
        if self.valor_total_item is None or self.valor_total_item == 0.0:
            qtd = float(self.quantidade) if self.quantidade is not None else 1.0
            val = float(self.valor_unitario) if self.valor_unitario is not None else 0.0
            self.valor_total_item = round(qtd * val, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.descricao} ({self.quantidade} x R$ {self.valor_unitario:.2f})"


@receiver(post_save, sender=ItemCompra)
def atualizar_valor_total_compra_save(sender, instance, **kwargs):
    compra = instance.compra
    total = compra.itens.aggregate(total=Sum('valor_total_item'))['total'] or 0.0
    compra.valor_total = round(float(total), 2)
    compra.save(update_fields=['valor_total'])


@receiver(post_delete, sender=ItemCompra)
def atualizar_valor_total_compra_delete(sender, instance, **kwargs):
    compra = instance.compra
    total = compra.itens.aggregate(total=Sum('valor_total_item'))['total'] or 0.0
    compra.valor_total = round(float(total), 2)
    compra.save(update_fields=['valor_total'])

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
    capacidade_tanque = models.FloatField(default=50.0, help_text='Capacidade do tanque em litros')

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.placa})"

class CustoCombustivel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_combustivel')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='combustiveis')
    data = models.DateField(default=timezone.now)
    valor_abastecido = models.FloatField(help_text='Valor total pago no posto (R$)', default=0.0)
    valor_por_litro = models.FloatField(help_text='Preço do litro do combustível (R$)', default=0.0)
    km_atual = models.IntegerField(default=0, help_text='KM do veículo no momento do abastecimento')
    tanque_cheio = models.BooleanField(default=False, help_text='Indica se o tanque foi completado')

    @property
    def litros(self):
        if self.valor_por_litro and self.valor_por_litro > 0:
            return round(self.valor_abastecido / self.valor_por_litro, 2)
        return 0.0

    @property
    def valor(self):
        return self.valor_abastecido

    @valor.setter
    def valor(self, val):
        self.valor_abastecido = val

    @property
    def litros_setter_dummy(self):
        return 0.0

    @litros.setter
    def litros(self, val):
        pass

    def __str__(self):
        return f"{self.veiculo} - R$ {self.valor_abastecido:.2f} ({self.data})"


@receiver(post_save, sender=CustoCombustivel)
def atualizar_km_veiculo_abastecimento(sender, instance, **kwargs):
    if instance.veiculo and instance.km_atual:
        if instance.km_atual > instance.veiculo.km_atual:
            instance.veiculo.km_atual = instance.km_atual
            instance.veiculo.save(update_fields=['km_atual'])

class Manutencao(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manutencoes')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='manutenções')
    data = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    valor = models.FloatField()
    km_atual = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.veiculo} – {self.tipo} ({self.data})"


class TrocaOleo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trocas_oleo')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='trocas_oleo')
    data = models.DateField(default=timezone.now)
    km_atual = models.PositiveIntegerField(help_text='KM atual do veículo na troca de óleo')
    valor = models.FloatField(help_text='Valor pago na troca de óleo (R$)')
    tipo_oleo = models.CharField(max_length=255, help_text='Ex: 5W30 Sintético, 10W40...')
    intervalo_troca = models.IntegerField(help_text='Intervalo em KM para a próxima troca (ex: 5000, 10000)')
    km_proxima_troca = models.PositiveIntegerField(editable=False, help_text='KM calculada para a próxima troca')
    observacao = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.km_atual is not None and self.intervalo_troca is not None:
            self.km_proxima_troca = int(self.km_atual) + int(self.intervalo_troca)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.veiculo} - Óleo: {self.tipo_oleo} ({self.data})"


@receiver(post_save, sender=TrocaOleo)
def atualizar_km_veiculo_troca_oleo(sender, instance, **kwargs):
    if instance.veiculo and instance.km_atual:
        if instance.km_atual > instance.veiculo.km_atual:
            instance.veiculo.km_atual = instance.km_atual
            instance.veiculo.save(update_fields=['km_atual'])


class Aviso(models.Model):
    TIPO_CHOICES = [
        ('OLEO', 'Troca de Óleo'),
        ('MANUTENCAO', 'Manutenção Preventiva'),
        ('REVISAO', 'Revisão Periódica'),
        ('GERAL', 'Geral'),
    ]
    NIVEL_CHOICES = [
        ('INFO', 'Informativo'),
        ('ALERTA', 'Atenção'),
        ('URGENTE', 'Urgente'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avisos')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='avisos', null=True, blank=True)
    titulo = models.CharField(max_length=255)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='MANUTENCAO')
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='ALERTA')
    lido = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return f"[{self.get_nivel_display()}] {self.titulo} - {self.user.username}"


class FechamentoMes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fechamentos_mes')
    mes = models.PositiveSmallIntegerField()
    ano = models.PositiveSmallIntegerField()
    total_receitas = models.FloatField(default=0.0)
    total_fixo = models.FloatField(default=0.0)
    total_variavel = models.FloatField(default=0.0)
    total_compras = models.FloatField(default=0.0)
    total_veiculos = models.FloatField(default=0.0)
    sobra_realizada = models.FloatField(default=0.0)
    data_fechamento = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'mes', 'ano')
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f"Fechamento {self.mes:02d}/{self.ano} - {self.user.username} (Sobra: R$ {self.sobra_realizada:.2f})"



