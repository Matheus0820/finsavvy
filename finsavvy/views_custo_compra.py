from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CustoCompra, FechamentoMes
from .new_forms import FormCustoCompra, ItemCompraFormSet
from .utils.leitor_qrcode import decodificar_imagem_qrcode, extrair_dados_nfce
from .utils.leitor_nfce import consultar_nfce

class CustoCompraListView(LoginRequiredMixin, ListView):
    model = CustoCompra
    template_name = 'pages/list_custo_compra.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        user = self.request.user
        hoje = datetime.today()
        try:
            mes = int(self.request.GET.get('mes') or self.request.GET.get('m', hoje.month))
        except (ValueError, TypeError):
            mes = hoje.month
        try:
            ano = int(self.request.GET.get('ano') or self.request.GET.get('y', hoje.year))
        except (ValueError, TypeError):
            ano = hoje.year
        return CustoCompra.objects.filter(user=user, data__year=ano, data__month=mes)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = datetime.today()
        try:
            mes = int(self.request.GET.get('mes') or self.request.GET.get('m', hoje.month))
        except (ValueError, TypeError):
            mes = hoje.month
        try:
            ano = int(self.request.GET.get('ano') or self.request.GET.get('y', hoje.year))
        except (ValueError, TypeError):
            ano = hoje.year
        context['mes_atual'] = mes
        context['ano_atual'] = ano
        context['is_mes_fechado'] = FechamentoMes.objects.filter(user=self.request.user, mes=mes, ano=ano).exists()
        return context

class CustoCompraCreateView(LoginRequiredMixin, CreateView):
    model = CustoCompra
    form_class = FormCustoCompra
    template_name = 'pages/add_custoCompra.html'
    success_url = reverse_lazy('list_custoCompra')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['itens_formset'] = ItemCompraFormSet(self.request.POST, prefix='itens')
        else:
            context['itens_formset'] = ItemCompraFormSet(prefix='itens')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        itens_formset = context.get('itens_formset')
        has_formset_data = any(k.startswith('itens-') for k in self.request.POST)

        if has_formset_data and itens_formset and not itens_formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            form.instance.user = self.request.user

            # Atribui valores processados no form.clean()
            if form.cleaned_data.get('valor') and not form.instance.valor:
                form.instance.valor = form.cleaned_data.get('valor')
            if form.cleaned_data.get('nome') and not form.instance.nome:
                form.instance.nome = form.cleaned_data.get('nome')
            if form.cleaned_data.get('qr_data') and not form.instance.qr_data:
                form.instance.qr_data = form.cleaned_data.get('qr_data')

            # Processamento adicional de imagem de QR-Code enviada no formulário
            imagem = form.cleaned_data.get('imagem_qr')
            if imagem:
                texto_qr = decodificar_imagem_qrcode(imagem)
                if texto_qr:
                    form.instance.qr_data = texto_qr
                    dados = extrair_dados_nfce(texto_qr)
                    if not form.instance.valor and dados.get('valor'):
                        form.instance.valor = dados['valor']
                    if not form.instance.nome and dados.get('nome'):
                        form.instance.nome = dados['nome']

            # Se houver qr_data preenchido e valor não definido
            if form.instance.qr_data and not form.instance.valor:
                dados = extrair_dados_nfce(form.instance.qr_data)
                if dados.get('valor'):
                    form.instance.valor = dados['valor']

            self.object = form.save()

            if has_formset_data and itens_formset and itens_formset.is_valid():
                itens_formset.instance = self.object
                itens_formset.save()

        messages.success(self.request, "Custo de compra adicionado com sucesso!")
        return redirect(self.get_success_url())

class CustoCompraUpdateView(LoginRequiredMixin, UpdateView):
    model = CustoCompra
    form_class = FormCustoCompra
    template_name = 'pages/add_custoCompra.html'
    success_url = reverse_lazy('list_custoCompra')

    def get_queryset(self):
        return CustoCompra.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['itens_formset'] = ItemCompraFormSet(self.request.POST, instance=self.object, prefix='itens')
        else:
            context['itens_formset'] = ItemCompraFormSet(instance=self.object, prefix='itens')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        itens_formset = context.get('itens_formset')
        has_formset_data = any(k.startswith('itens-') for k in self.request.POST)

        if has_formset_data and itens_formset and not itens_formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            imagem = form.cleaned_data.get('imagem_qr')
            if imagem:
                texto_qr = decodificar_imagem_qrcode(imagem)
                if texto_qr:
                    form.instance.qr_data = texto_qr
                    dados = extrair_dados_nfce(texto_qr)
                    if not form.instance.valor and dados.get('valor'):
                        form.instance.valor = dados['valor']

            self.object = form.save()

            if has_formset_data and itens_formset and itens_formset.is_valid():
                itens_formset.instance = self.object
                itens_formset.save()

        messages.success(self.request, "Custo de compra atualizado com sucesso!")
        return redirect(self.get_success_url())

class CustoCompraDeleteView(LoginRequiredMixin, DeleteView):
    model = CustoCompra
    template_name = 'pages/confirm_delete_custoCompra.html'
    success_url = reverse_lazy('list_custoCompra')

    def get_queryset(self):
        return CustoCompra.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return redirect('list_custoCompra')

    def post(self, request, *args, **kwargs):
        messages.success(self.request, "Custo de compra removido com sucesso!")
        return super().post(request, *args, **kwargs)

class ProcessarQrCodeView(LoginRequiredMixin, View):
    """
    Endpoint para decodificar imagens ou strings de QR-Code (NFC-e / cupons fiscais)
    via chamada assíncrona ou AJAX, retornando os dados extraídos em formato JSON.
    """
    def post(self, request, *args, **kwargs):
        texto_qr = request.POST.get('qr_text') or request.POST.get('qr_data')
        imagem = request.FILES.get('imagem') or request.FILES.get('imagem_qr')

        if imagem:
            texto_decodificado = decodificar_imagem_qrcode(imagem)
            if not texto_decodificado:
                return JsonResponse({
                    'sucesso': False,
                    'mensagem': 'Nenhum QR-Code foi identificado na imagem enviada. Certifique-se de que a imagem esteja nítida.'
                }, status=400)
            texto_qr = texto_decodificado

        if not texto_qr:
            return JsonResponse({
                'sucesso': False,
                'mensagem': 'Nenhum texto ou arquivo de QR-Code foi fornecido.'
            }, status=400)

        dados = extrair_dados_nfce(texto_qr)
        return JsonResponse(dados)


class LerNfceAjaxView(LoginRequiredMixin, View):
    """
    Endpoint AJAX (/api/ler-nfce/) para processar QR-Code de NFC-e (texto, URL ou upload de imagem).
    Dispara o motor de web scraping de portais SEFAZ estaduais e retorna os dados
    (estabelecimento, valor_total, chave_acesso, data_emissao e lista de itens) em formato JSON.
    """
    def post(self, request, *args, **kwargs):
        texto_qr = request.POST.get('qr_text') or request.POST.get('qr_data') or request.POST.get('url')
        imagem = request.FILES.get('imagem') or request.FILES.get('imagem_qr')

        if imagem:
            texto_decodificado = decodificar_imagem_qrcode(imagem)
            if not texto_decodificado:
                return JsonResponse({
                    'sucesso': False,
                    'mensagem': 'Nenhum QR-Code foi identificado na imagem enviada. Certifique-se de que a imagem esteja nítida.'
                }, status=400)
            texto_qr = texto_decodificado

        if not texto_qr:
            return JsonResponse({
                'sucesso': False,
                'mensagem': 'Nenhum texto, URL ou imagem de QR-Code foi fornecido.'
            }, status=400)

        dados = consultar_nfce(texto_qr)

        # Garante chaves de retrocompatibilidade
        if 'nome' not in dados and 'estabelecimento' in dados:
            dados['nome'] = dados['estabelecimento']
        if 'valor' not in dados and 'valor_total' in dados:
            dados['valor'] = dados['valor_total']

        status_code = 200 if dados.get('sucesso') else 422
        return JsonResponse(dados, status=status_code)


