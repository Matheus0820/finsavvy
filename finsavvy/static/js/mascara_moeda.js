/**
 * mascara_moeda.js - Máscara universal de moeda R$ (Right-to-Left)
 * FinSavvy
 */
(function () {
    'use strict';

    function formatarValorMoeda(valorStr) {
        if (!valorStr) return '0,00';
        let str = String(valorStr).trim();

        // Se contiver ponto ou vírgula decimal direta do banco (ex: "1050.75" ou "12.03")
        // e vier sem formatação de milhares/vírgula de digitação:
        if (/^\d+\.\d{1,2}$/.test(str)) {
            const numero = parseFloat(str);
            if (!isNaN(numero)) {
                return new Intl.NumberFormat('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(numero);
            }
        }

        // Regra Right-to-Left: remover tudo que não for dígito
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
        const cursorPos = input.selectionStart;
        const valorAntigo = input.value;
        const formatado = formatarValorMoeda(valorAntigo);
        input.value = formatado;

        // Ajustar cursor para o final para digitação natural Right-to-Left
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
            // Formatar no carregamento inicial (inclusive para valores vindos do banco)
            aplicarMascara(input);

            // Ouvir evento input
            input.addEventListener('input', function () {
                aplicarMascara(this);
            });

            // Garantir seleção no foco se estiver em '0,00'
            input.addEventListener('focus', function () {
                if (this.value === '0,00') {
                    try {
                        this.setSelectionRange(0, this.value.length);
                    } catch (e) {}
                }
            });
        });
    }

    // Exportar para uso externo ou testes caso ambiente module/window
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
