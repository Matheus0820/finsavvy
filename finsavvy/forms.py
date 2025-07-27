from django import forms
from .models import (CustoFixo)

class FormCustoFixo(forms.ModelForm):
    class Meta:
        model = CustoFixo
        fields = ('nome', 'valor',)
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control text-bg-dark', 'placeholder': 'Internet'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark', 'placeholder':'80,00'})
        }