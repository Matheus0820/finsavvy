from decimal import Decimal
from django import forms

def sanitizar_valor_monetario(valor):
    """
    Converte uma representação monetária brasileira (ex: '1.050,75', 'R$ 1.050,75', '80,00', '1050.75')
    em float/decimal compatível com os models do Django.
    """
    if valor is None or valor == '':
        return None
    if isinstance(valor, (int, float, Decimal)):
        return float(valor)

    valor_str = str(valor).strip()
    valor_str = valor_str.replace('R$', '').replace('r$', '').strip()

    if not valor_str:
        return None

    # Se contiver milhar com ponto e decimais com vírgula (ex: 1.050,75)
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
        raise forms.ValidationError("Informe um valor monetário válido.")


class MonetaryMaskMixin:
    """
    Mixin para forms do Django que processa campos monetários pré-formatados em BRL (Right-to-Left).
    Sobrescreve a limpeza dos campos listados em monetary_fields antes da validação padrão de Float/NumberInput,
    evitando que strings com formatação '1.050,75' falhem na conversão padrão do Django.
    """
    monetary_fields = ('valor',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Substitui os campos monetários para CharField nos forms para aceitar formatação BRL
        # preservando widgets e attributes originais caso já definidos
        for field_name in getattr(self, 'monetary_fields', ()):
            if field_name in self.fields:
                field = self.fields[field_name]
                widget = field.widget
                required = field.required
                help_text = field.help_text
                label = field.label
                # Adiciona a classe mascara-dinheiro no widget
                existing_class = widget.attrs.get('class', '')
                if 'mascara-dinheiro' not in existing_class:
                    widget.attrs['class'] = f"{existing_class} mascara-dinheiro".strip()
                # Garante que seja CharField para não falhar com formatação pt-BR antes do clean
                self.fields[field_name] = forms.CharField(
                    required=required,
                    widget=widget,
                    label=label,
                    help_text=help_text
                )

    def clean(self):
        cleaned_data = super().clean()
        campos = getattr(self, 'monetary_fields', ())

        for campo in campos:
            val = cleaned_data.get(campo)
            if val is not None and val != '':
                try:
                    cleaned_data[campo] = sanitizar_valor_monetario(val)
                except forms.ValidationError as e:
                    self.add_error(campo, e)
            else:
                # Checa se veio na data bruta (por exemplo se campo estava desabilitado ou omitido)
                raw_val = self.data.get(campo) if hasattr(self, 'data') else None
                if raw_val is not None and raw_val != '':
                    try:
                        cleaned_data[campo] = sanitizar_valor_monetario(raw_val)
                    except forms.ValidationError as e:
                        self.add_error(campo, e)

        return cleaned_data
