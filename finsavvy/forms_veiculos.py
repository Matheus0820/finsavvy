from django import forms
from .models import Veiculo

class FormVeiculo(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = ('marca', 'modelo', 'placa', 'tipo_veiculo', 'km_atual', 'capacidade_tanque')
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'placa': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'tipo_veiculo': forms.Select(attrs={'class': 'form-select text-bg-dark'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-control text-bg-dark'}),
            'capacidade_tanque': forms.TextInput(attrs={'class': 'form-control text-bg-dark', 'id': 'id_capacidade_tanque', 'autocomplete': 'off'}),
        }

