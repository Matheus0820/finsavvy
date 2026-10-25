from django import forms
from .new_models import (
    CustoVariavel,
    CustoCompra,
    Veiculo,
    CustoCombustivel,
    Manutencao,
)

class FormCustoVariavel(forms.ModelForm):
    class Meta:
        model = CustoVariavel
        fields = ('nome', 'valor', 'data', 'categoria')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }

class FormCustoCompra(forms.ModelForm):
    class Meta:
        model = CustoCompra
        fields = ('nome', 'valor', 'data', 'qr_data')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'qr_data': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'QR/Data de leitura'}),
        }

class FormVeiculo(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = ('marca', 'modelo', 'placa', 'tipo_veiculo', 'km_atual')
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'placa': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'tipo_veiculo': forms.Select(attrs={'class': 'form-select'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

class FormCustoCombustivel(forms.ModelForm):
    class Meta:
        model = CustoCombustivel
        fields = ('veiculo', 'data', 'litros', 'valor')
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'litros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class FormManutencao(forms.ModelForm):
    class Meta:
        model = Manutencao
        fields = ('veiculo', 'data', 'tipo', 'descricao', 'valor', 'km_atual', 'km_proximo_oleo', 'km_troca_oleo')
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control text-bg-dark'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'km_proximo_oleo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'km_troca_oleo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
