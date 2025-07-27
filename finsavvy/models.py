from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class CustoFixo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custos_fixos')
    nome = models.CharField(max_length=255, default="")
    valor = models.FloatField(blank=False, default="")

    def __str__(self):
        return self.nome
    
    def get_custosFixos(cls):
        return [(custoFixo.nome, custoFixo.valor) for custoFixo in cls.objects.all()]

