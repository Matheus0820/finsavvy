/**
 * mascara_moeda.js - Máscara universal de moeda R$ (Right-to-Left)
 * FinSavvy - Suporte robusto para valores >= 1.000,00 e formatação BRL
 */
(function () {
    'use strict';

    function formatarValorMoeda(valorStr) {
        if (!valorStr) return '0,00';
        let str = String(valorStr).trim();

        // Se contiver ponto ou vírgula decimal direta do banco (ex: "1050.75" ou "12.03" ou "1000.00")
        if (/^\d+(\.\d{1,2})?$/.test(str) && !str.includes(',')) {
            const numero = parseFloat(str);
            if (!isNaN(numero)) {
                return new Intl.NumberFormat('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(numero);
            }
        }

        // Se for string com pontos de milhar e vírgula de centavos (ex: "1.000,00") ou ponto decimal ("1000.00")
        // Remove 'R$', espaços e trata corretamente
        str = str.replace(/R\$/g, '').trim();

        // Regra Right-to-Left: extrair todos os dígitos
        const apenasDigitos = str.replace(/\D/g, '');
        if (!apenasDigitos) return '0,00';

        const centavos = parseInt(apenasDigitos, 10) / 100;
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(centavos);
    }

    function aplicarMascara(input) {
        if (!input) return;
        const valorAntigo = input.value;
        const formatado = formatarValorMoeda(valorAntigo);
        input.value = formatado;

        if (input === document.activeElement) {
            try {
                const pos = input.value.length;
                input.setSelectionRange(pos, pos);
            } catch (e) {}
        }
    }

    function inicializarMascarasMoeda() {
        const inputs = document.querySelectorAll('.mascara-dinheiro');
        if (!inputs || inputs.length === 0) return;

        inputs.forEach(function (input) {
            if (input.dataset.mascaraIniciada === 'true') return;
            input.dataset.mascaraIniciada = 'true';

            aplicarMascara(input);

            input.addEventListener('input', function () {
                aplicarMascara(this);
            });

            input.addEventListener('focus', function () {
                if (this.value === '0,00') {
                    try {
                        this.setSelectionRange(0, this.value.length);
                    } catch (e) {}
                }
            });
        });

        // Garantir limpeza no submit de qualquer formulário contendo .mascara-dinheiro
        document.querySelectorAll('form').forEach(form => {
            if (form.dataset.submitMaskClean === 'true') return;
            form.dataset.submitMaskClean = 'true';

            form.addEventListener('submit', function () {
                form.querySelectorAll('.mascara-dinheiro').forEach(input => {
                    let val = input.value;
                    if (val) {
                        // Remove pontos de milhar e substitui vírgula decimal por ponto para o Django/backend
                        val = val.replace(/\./g, '').replace(',', '.');
                        input.value = val;
                    }
                });
            });
        });
    }

    if (typeof window !== 'undefined') {
        window.formatarValorMoeda = formatarValorMoeda;
        window.inicializarMascarasMoeda = inicializarMascarasMoeda;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializarMascarasMoeda);
    } else {
        inicializarMascarasMoeda();
    }
})();
