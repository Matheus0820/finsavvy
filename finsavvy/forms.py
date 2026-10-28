from datetime import datetime
from django import forms
from .models import (CustoFixo)
from .utils.forms import MonetaryMaskMixin

class FormCustoFixo(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor',)

    class Meta:
        model = CustoFixo
        fields = ('nome', 'valor', 'dia_vencimento', 'data_vigencia')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control bg-body text-body', 'placeholder': 'Internet'}),
            'valor': forms.TextInput(attrs={'class': 'form-control bg-body text-body mascara-dinheiro', 'placeholder': '0,00', 'id': 'id_valor'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'form-control bg-body text-body', 'min': '1', 'max': '31', 'placeholder': '5'}),
            'data_vigencia': forms.DateInput(attrs={'class': 'form-control bg-body text-body', 'type': 'text', 'id': 'datepicker_vigencia', 'placeholder': 'dd/mm/aaaa', 'autocomplete': 'off'})
        }

    def clean_data_vigencia(self):
        data = self.cleaned_data.get('data_vigencia')
        if not data:
            return None
        if isinstance(data, datetime):
            return data.date() if hasattr(data, 'date') else data
        if isinstance(data, str):
            data_str = data.strip()
            if not data_str:
                return None
            try:
                # Formato MM/YYYY ou M/YYYY
                dt = datetime.strptime(data_str, '%m/%Y')
                # Retorna o último dia do mês ou o dia 1 do mês para vigência (usualmente dia 1 ou último dia)
                return dt.date()
            except ValueError:
                try:
                    return datetime.strptime(data_str, '%d/%m/%Y').date()
                except ValueError:
                    try:
                        return datetime.strptime(data_str, '%Y-%m-%d').date()
                    except ValueError:
                        raise forms.ValidationError("Informe um mês e ano válidos no formato mm/aaaa.")
        return data

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