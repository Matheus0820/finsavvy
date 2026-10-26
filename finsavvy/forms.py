from django import forms
from .models import (CustoFixo)

class FormCustoFixo(forms.ModelForm):
    class Meta:
        model = CustoFixo
        fields = ('nome', 'valor',)
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control text-bg-dark', 'placeholder': 'Internet'}),
            'valor': forms.TextInput(attrs={'class': 'form-control text-bg-dark', 'placeholder': '80,00', 'id': 'id_valor'})
        }

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if not valor:
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)

        valor_str = str(valor).strip()
        valor_str = valor_str.replace('R$', '').replace('r$', '').strip()

        if ',' in valor_str and '.' in valor_str:
            if valor_str.rfind(',') > valor_str.rfind('.'):
                valor_str = valor_str.replace('.', '').replace(',', '.')
            else:
                valor_str = valor_str.replace(',', '')
        elif ',' in valor_str:
            valor_str = valor_str.replace(',', '.')

        try:
            return float(valor_str)
        except ValueError:
            raise forms.ValidationError("Informe um valor numérico válido.")