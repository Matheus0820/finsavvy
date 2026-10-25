from django import forms
from .models import (
    Categoria,
    CustoVariavel,
    CustoCompra,
    Veiculo,
    CustoCombustivel,
    Manutencao,
)

class FormCategoria(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nome', 'cor')
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control text-bg-dark border-secondary',
                'placeholder': 'Ex: Alimentação, Transporte, Lazer...',
                'autofocus': True,
            }),
            'cor': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'id': 'exampleColorInput',
                'title': 'Choose your color',
            }),
        }

class FormCustoVariavel(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all().order_by('nome'),
        required=False,
        empty_label='Selecione uma categoria (opcional)',
        widget=forms.Select(attrs={'class': 'form-select text-bg-dark border-secondary'})
    )

    class Meta:
        model = CustoVariavel
        fields = ('nome', 'valor', 'categoria')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'placeholder': 'Ex: Almoço, Supermercado...'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'step': '0.01', 'placeholder': '0.00'}),
        }

class FormCustoCompra(forms.ModelForm):
    class Meta:
        model = CustoCompra
        fields = ('nome', 'valor', 'qr_data')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control text-bg-dark border-secondary'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'step': '0.01'}),
            'qr_data': forms.Textarea(attrs={'class': 'form-control text-bg-dark border-secondary', 'rows': 3, 'placeholder': 'QR/Data de leitura'}),
        }

class FormVeiculo(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = ('marca', 'modelo', 'placa', 'tipo_veiculo', 'km_atual')
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control text-bg-dark border-secondary'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control text-bg-dark border-secondary'}),
            'placa': forms.TextInput(attrs={'class': 'form-control text-bg-dark border-secondary'}),
            'tipo_veiculo': forms.Select(attrs={'class': 'form-select text-bg-dark border-secondary'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'min': '0'}),
        }

class FormCustoCombustivel(forms.ModelForm):
    class Meta:
        model = CustoCombustivel
        fields = ('veiculo', 'litros', 'valor')
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select text-bg-dark border-secondary'}),
            'litros': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'step': '0.01'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'step': '0.01'}),
        }

class FormManutencao(forms.ModelForm):
    class Meta:
        model = Manutencao
        fields = ('veiculo', 'tipo', 'descricao', 'valor', 'km_atual', 'km_proximo_oleo', 'km_troca_oleo')
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select text-bg-dark border-secondary'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control text-bg-dark border-secondary'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control text-bg-dark border-secondary', 'rows': 3}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'step': '0.01'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'min': '0'}),
            'km_proximo_oleo': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'min': '0'}),
            'km_troca_oleo': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'min': '0'}),
        }
