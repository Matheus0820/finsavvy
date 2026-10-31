from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import (
    Categoria,
    CustoVariavel,
    CustoCompra,
    ItemCompra,
    Veiculo,
    CustoCombustivel,
    Manutencao,
    TrocaOleo,
)
from .utils.leitor_qrcode import decodificar_imagem_qrcode, extrair_dados_nfce
from .utils.forms import MonetaryMaskMixin

class FormCategoria(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nome', 'cor')
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary',
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

class FormCustoVariavel(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor',)

    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all().order_by('nome'),
        required=False,
        empty_label='Selecione uma categoria (opcional)',
        widget=forms.Select(attrs={'class': 'form-select bg-body text-body border-secondary'})
    )

    class Meta:
        model = CustoVariavel
        fields = ('nome', 'valor', 'categoria')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary', 'placeholder': 'Ex: Almoço, Supermercado...'}),
            'valor': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
        }

class FormCustoCompra(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor_total',)

    imagem_qr = forms.FileField(
        required=False,
        label="Foto / Imagem do QR-Code (opcional)",
        widget=forms.FileInput(attrs={'class': 'form-control bg-body text-body border-secondary', 'accept': 'image/*'})
    )

    class Meta:
        model = CustoCompra
        fields = ('estabelecimento', 'data', 'valor_total', 'qr_code_url')
        widgets = {
            'estabelecimento': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary',
                'placeholder': 'Ex: Supermercado Araújo, Posto Central...'
            }),
            'data': forms.DateInput(attrs={
                'class': 'form-control bg-body text-body border-secondary',
                'type': 'date'
            }),
            'valor_total': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary mascara-dinheiro',
                'placeholder': '0,00'
            }),
            'qr_code_url': forms.URLInput(attrs={
                'class': 'form-control bg-body text-body border-secondary',
                'placeholder': 'URL da NFC-e consultada (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Suporte a dados passados com nomes legados ('nome', 'qr_data', 'valor')
        if args and args[0] is not None:
            data = args[0]
            if hasattr(data, 'copy'):
                data = data.copy()
            else:
                data = dict(data)
            if 'nome' in data and not data.get('estabelecimento'):
                data['estabelecimento'] = data['nome']
            if 'qr_data' in data and not data.get('qr_code_url'):
                data['qr_code_url'] = data['qr_data']
            if 'valor' in data and not data.get('valor_total'):
                data['valor_total'] = data['valor']
            args = (data,) + args[1:]
        elif 'data' in kwargs and kwargs['data'] is not None:
            data = kwargs['data']
            if hasattr(data, 'copy'):
                data = data.copy()
            else:
                data = dict(data)
            if 'nome' in data and not data.get('estabelecimento'):
                data['estabelecimento'] = data['nome']
            if 'qr_data' in data and not data.get('qr_code_url'):
                data['qr_code_url'] = data['qr_data']
            if 'valor' in data and not data.get('valor_total'):
                data['valor_total'] = data['valor']
            kwargs['data'] = data

        super().__init__(*args, **kwargs)
        self.fields['estabelecimento'].required = False
        self.fields['valor_total'].required = False
        self.fields['qr_code_url'].required = False
        if 'data' in self.fields:
            self.fields['data'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('data'):
            cleaned_data['data'] = timezone.now().date()
        estabelecimento = cleaned_data.get('estabelecimento')
        valor_total = cleaned_data.get('valor_total')
        qr_code_url = cleaned_data.get('qr_code_url')
        imagem_qr = cleaned_data.get('imagem_qr')

        if not estabelecimento or not valor_total:
            texto_qr = None
            if imagem_qr:
                texto_qr = decodificar_imagem_qrcode(imagem_qr)
                if texto_qr:
                    cleaned_data['qr_code_url'] = texto_qr
            elif qr_code_url:
                texto_qr = qr_code_url

            if texto_qr:
                dados = extrair_dados_nfce(texto_qr)
                if not valor_total and dados.get('valor'):
                    cleaned_data['valor_total'] = dados['valor']
                    valor_total = dados['valor']
                if not estabelecimento and dados.get('nome'):
                    cleaned_data['estabelecimento'] = dados['nome']
                    estabelecimento = dados['nome']

        if not estabelecimento:
            self.add_error('estabelecimento', 'Informe o nome do estabelecimento ou produto.')

        return cleaned_data


class FormItemCompra(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor_unitario', 'valor_total_item')

    class Meta:
        model = ItemCompra
        fields = ('descricao', 'quantidade', 'valor_unitario', 'valor_total_item')
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary item-descricao',
                'placeholder': 'Ex: Arroz 5kg, Detergente...'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control bg-body text-body border-secondary item-qtd',
                'step': '0.001',
                'min': '0',
                'placeholder': '1'
            }),
            'valor_unitario': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary item-unitario mascara-dinheiro',
                'placeholder': '0,00'
            }),
            'valor_total_item': forms.TextInput(attrs={
                'class': 'form-control bg-body text-body border-secondary item-total mascara-dinheiro',
                'readonly': 'readonly',
                'placeholder': '0,00'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'descricao' in self.fields:
            self.fields['descricao'].required = False
        if 'valor_total_item' in self.fields:
            self.fields['valor_total_item'].required = False
        if 'quantidade' in self.fields:
            self.fields['quantidade'].required = False
        if 'valor_unitario' in self.fields:
            self.fields['valor_unitario'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('descricao') and not cleaned_data.get('quantidade') and not cleaned_data.get('valor_unitario'):
            return cleaned_data
        qtd = cleaned_data.get('quantidade')
        if qtd is None:
            qtd = 1.0
            cleaned_data['quantidade'] = qtd
        unit = cleaned_data.get('valor_unitario')
        if unit is None:
            unit = 0.0
            cleaned_data['valor_unitario'] = unit
        tot = cleaned_data.get('valor_total_item')
        if not tot:
            cleaned_data['valor_total_item'] = round(float(qtd) * float(unit), 2)
        return cleaned_data


ItemCompraFormSet = inlineformset_factory(
    CustoCompra,
    ItemCompra,
    form=FormItemCompra,
    fields=('descricao', 'quantidade', 'valor_unitario', 'valor_total_item'),
    extra=1,
    can_delete=True
)

class FormVeiculo(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('km_atual', 'capacidade_tanque')

    class Meta:
        model = Veiculo
        fields = ('marca', 'modelo', 'placa', 'tipo_veiculo', 'km_atual', 'capacidade_tanque')
        widgets = {
            'marca': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary'}),
            'placa': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary'}),
            'tipo_veiculo': forms.Select(attrs={'class': 'form-select bg-body text-body border-secondary'}),
            'km_atual': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
            'capacidade_tanque': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
        }

class FormCustoCombustivel(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor_abastecido', 'valor_por_litro')

    class Meta:
        model = CustoCombustivel
        fields = ('veiculo', 'data', 'valor_abastecido', 'valor_por_litro', 'km_atual', 'tanque_cheio')
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select bg-body text-body border-secondary'}),
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control bg-body text-body border-secondary', 'type': 'date'}),
            'valor_abastecido': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
            'valor_por_litro': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
            'km_atual': forms.NumberInput(attrs={'class': 'form-control bg-body text-body border-secondary', 'min': '0'}),
            'tanque_cheio': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        veiculo = cleaned_data.get('veiculo')
        km_atual = cleaned_data.get('km_atual')
        valor_abastecido = cleaned_data.get('valor_abastecido')
        valor_por_litro = cleaned_data.get('valor_por_litro')

        if veiculo is not None:
            # Trava de KM: km_atual deve ser estritamente maior que a do último abastecimento registrado
            ultimo_abastecimento = CustoCombustivel.objects.filter(veiculo=veiculo)
            if self.instance and self.instance.pk:
                ultimo_abastecimento = ultimo_abastecimento.exclude(pk=self.instance.pk)
            ultimo_abastecimento = ultimo_abastecimento.order_by('-km_atual', '-data', '-id').first()

            if km_atual is not None:
                if ultimo_abastecimento and ultimo_abastecimento.km_atual:
                    if km_atual <= ultimo_abastecimento.km_atual:
                        raise forms.ValidationError(
                            f"A KM atual ({km_atual}) deve ser maior que a KM do último abastecimento registrado ({ultimo_abastecimento.km_atual})."
                        )
                elif km_atual < veiculo.km_atual:
                    raise forms.ValidationError(
                        f"A KM atual ({km_atual}) não pode ser menor que a KM cadastrada do veículo ({veiculo.km_atual})."
                    )

            # Trava de Litros: litros calculados não podem ser maiores que a capacidade_tanque do veículo
            if valor_abastecido and valor_por_litro and valor_por_litro > 0:
                litros_calculados = valor_abastecido / valor_por_litro
                if veiculo.capacidade_tanque and litros_calculados > veiculo.capacidade_tanque:
                    raise forms.ValidationError(
                        f"A quantidade calculada ({litros_calculados:.2f} L) excede a capacidade do tanque do veículo ({veiculo.capacidade_tanque} L)."
                    )

        return cleaned_data

class FormManutencao(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor', 'km_atual')

    class Meta:
        model = Manutencao
        fields = ('veiculo', 'tipo', 'descricao', 'valor', 'km_atual')
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select bg-body text-body border-secondary'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control bg-body text-body border-secondary', 'rows': 3}),
            'valor': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
            'km_atual': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
        }


class FormTrocaOleo(MonetaryMaskMixin, forms.ModelForm):
    monetary_fields = ('valor', 'km_atual', 'intervalo_troca')

    class Meta:
        model = TrocaOleo
        fields = ('veiculo', 'data', 'km_atual', 'valor', 'tipo_oleo', 'intervalo_troca', 'observacao')
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select bg-body text-body border-secondary'}),
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control bg-body text-body border-secondary', 'type': 'date'}),
            'km_atual': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
            'valor': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': '0,00'}),
            'tipo_oleo': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary', 'placeholder': 'Ex: 5W30 Sintético'}),
            'intervalo_troca': forms.TextInput(attrs={'class': 'form-control bg-body text-body border-secondary mascara-dinheiro', 'placeholder': 'Ex: 10000'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control bg-body text-body border-secondary', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        veiculo = cleaned_data.get('veiculo')
        km_atual = cleaned_data.get('km_atual')

        if veiculo is not None and km_atual is not None:
            ultimo = TrocaOleo.objects.filter(veiculo=veiculo)
            if self.instance and self.instance.pk:
                ultimo = ultimo.exclude(pk=self.instance.pk)
            ultimo = ultimo.order_by('-km_atual', '-data', '-id').first()

            if ultimo and ultimo.km_atual and km_atual <= ultimo.km_atual:
                raise forms.ValidationError(
                    f"A KM atual da troca ({km_atual}) deve ser maior que a KM da última troca registrada ({ultimo.km_atual})."
                )
            elif km_atual < veiculo.km_atual:
                # Opcional, mas garante consistência com o veículo
                pass

        return cleaned_data

