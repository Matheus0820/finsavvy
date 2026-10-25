from django import forms
from .models import (
    Categoria,
    CustoVariavel,
    CustoCompra,
    Veiculo,
    CustoCombustivel,
    Manutencao,
)
from .utils.leitor_qrcode import decodificar_imagem_qrcode, extrair_dados_nfce

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
    imagem_qr = forms.FileField(
        required=False,
        label="Foto / Imagem do QR-Code (opcional)",
        widget=forms.FileInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'accept': 'image/*'})
    )

    class Meta:
        model = CustoCompra
        fields = ('nome', 'valor', 'qr_data')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'placeholder': 'Ex: Supermercado, Loja de Autopeças...'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control text-bg-dark border-secondary', 'step': '0.01', 'placeholder': '0.00'}),
            'qr_data': forms.Textarea(attrs={'class': 'form-control text-bg-dark border-secondary', 'rows': 3, 'placeholder': 'Conteúdo decodificado ou URL do cupom fiscal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor'].required = False
        self.fields['nome'].required = False

    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get('valor')
        nome = cleaned_data.get('nome')
        qr_data = cleaned_data.get('qr_data')
        imagem_qr = cleaned_data.get('imagem_qr')

        if not valor or not nome:
            texto_qr = None
            if imagem_qr:
                texto_qr = decodificar_imagem_qrcode(imagem_qr)
                if texto_qr:
                    cleaned_data['qr_data'] = texto_qr
            elif qr_data:
                texto_qr = qr_data

            if texto_qr:
                dados = extrair_dados_nfce(texto_qr)
                if not valor and dados.get('valor'):
                    cleaned_data['valor'] = dados['valor']
                    valor = dados['valor']
                if not nome and dados.get('nome'):
                    cleaned_data['nome'] = dados['nome']
                    nome = dados['nome']

        if not valor:
            self.add_error('valor', 'Informe o valor da compra ou forneça um cupom fiscal/QR-Code válido.')
        if not nome:
            self.add_error('nome', 'Informe o nome do estabelecimento ou produto.')

        return cleaned_data

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
