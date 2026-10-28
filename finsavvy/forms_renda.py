from django import forms
from .models import Renda
from .utils.forms import MonetaryMaskMixin

class FormRenda(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor',)

    class Meta:
        model = Renda
        fields = ('descricao', 'valor', 'tipo_renda', 'data_recebimento')
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary',
                'placeholder': 'Ex: Salário, Aluguel, Dividendos...'
            }),
            'valor': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary mascara-dinheiro',
                'placeholder': '0,00',
                'id': 'id_valor'
            }),
            'tipo_renda': forms.Select(attrs={
                'class': 'form-select bg-body text-body border-secondary'
            }),
            'data_recebimento': forms.DateInput(format='%Y-%m-%d', attrs={
                'class': 'form-control bg-body text-body border-secondary',
                'type': 'date'
            }),
        }
