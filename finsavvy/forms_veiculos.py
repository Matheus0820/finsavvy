from django import forms
from .models import Veiculo

class FormVeiculo(forms.ModelForm):
    capacidade_tanque = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control text-bg-dark', 'id': 'id_capacidade_tanque', 'autocomplete': 'off'})
    )

    class Meta:
        model = Veiculo
        fields = ('marca', 'modelo', 'placa', 'tipo_veiculo', 'km_atual', 'capacidade_tanque')
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'placa': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'tipo_veiculo': forms.Select(attrs={'class': 'form-select text-bg-dark'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-control text-bg-dark'}),
        }

    def clean_capacidade_tanque(self):
        val = self.cleaned_data.get('capacidade_tanque')
        if not val:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace('L', '').strip()
        try:
            if ',' in val_str:
                val_str = val_str.replace('.', '').replace(',', '.')
                return float(val_str)
            elif '.' in val_str:
                return float(val_str)
            else:
                return float(int(val_str) / 10.0)
        except ValueError:
            raise forms.ValidationError("Informe um valor válido.")

