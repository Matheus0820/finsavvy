"""
Motor de Web Scraping e Extração Resiliente de Dados de NFC-e (Nota Fiscal de Consumidor Eletrônica).
Suporta múltiplos layouts de portais SEFAZ estaduais (SP, RS, PR, RJ, MG e padrão nacional SVRS)
e análise heurística genérica de páginas HTML de notas fiscais.
"""
import re
import urllib.parse
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from .leitor_qrcode import extrair_dados_nfce

USER_AGENT_PADRAO = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

HEADERS_PADRAO = {
    "User-Agent": USER_AGENT_PADRAO,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _limpar_valor_monetario(valor_str: Optional[str]) -> Optional[float]:
    """Converte strings com formato '1.234,56' ou '12.34' para float."""
    if not valor_str:
        return None
    texto = valor_str.strip()
    texto = re.sub(r'[^\d,.-]', '', texto)
    if not texto:
        return None
    # Se contiver vírgula e ponto (ex: 1.250,50)
    if ',' in texto and '.' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    elif ',' in texto:
        texto = texto.replace(',', '.')
    try:
        val = float(texto)
        return round(val, 2)
    except ValueError:
        return None


def _limpar_quantidade(qtd_str: Optional[str]) -> float:
    """Converte strings de quantidade para float positivo (default: 1.0)."""
    if not qtd_str:
        return 1.0
    val = _limpar_valor_monetario(qtd_str)
    return float(val) if val is not None and val > 0 else 1.0


def parsear_html_nfce(html_conteudo: str, url_origem: str = "") -> Dict[str, Any]:
    """
    Analisa o conteúdo HTML retornado por uma consulta de NFC-e e extrai:
    - estabelecimento (Razão Social / Nome Fantasia)
    - data_emissao
    - valor_total
    - chave_acesso
    - itens: lista de dicts com {descricao, quantidade, valor_unitario, valor_total}
    """
    resultado: Dict[str, Any] = {
        'sucesso': False,
        'estabelecimento': '',
        'data_emissao': None,
        'valor_total': 0.0,
        'chave_acesso': '',
        'itens': [],
        'url': url_origem,
        'mensagem': '',
    }

    if not html_conteudo or not html_conteudo.strip():
        resultado['mensagem'] = "Conteúdo HTML vazio."
        return resultado

    soup = BeautifulSoup(html_conteudo, 'html.parser')

    # 1. Chave de Acesso (44 dígitos)
    # Tenta seletores comuns: .chave, #lblChave, #chaveAcesso, etc.
    chave_encontrada = ""
    el_chave = soup.select_one('.chave, #lblChave, #chaveAcesso, .chave-acesso, span[id*="chave"]')
    if el_chave:
        chave_encontrada = re.sub(r'\D', '', el_chave.get_text())

    if len(chave_encontrada) != 44:
        # Busca no texto completo da página
        match_chave = re.search(r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b', soup.get_text())
        if match_chave:
            chave_encontrada = re.sub(r'\D', '', match_chave.group(1))

    if len(chave_encontrada) == 44:
        resultado['chave_acesso'] = chave_encontrada

    # 2. Estabelecimento (Razão Social / Nome Fantasia)
    estabelecimento = ""
    # Seletores específicos conhecidos (SP, RS, PR, etc.)
    el_estab = soup.select_one('.txtTopo, .NFRec, #u20, .razao-social, .nome-empresa, #lblRazaoSocial, .empresa-nome')
    if el_estab and el_estab.get_text(strip=True):
        estabelecimento = el_estab.get_text(strip=True)
    else:
        # Busca pelo primeiro título ou cabeçalho relevante
        for tag in ['h1', 'h2', 'h3', 'b', 'strong']:
            candidatos = soup.find_all(tag)
            for c in candidatos:
                txt = c.get_text(strip=True)
                if len(txt) > 3 and not any(ignorar in txt.lower() for ignorar in ['nfc-e', 'danfe', 'nota fiscal', 'sefaz', 'consulta', 'menu', 'governo']):
                    estabelecimento = txt
                    break
            if estabelecimento:
                break

    resultado['estabelecimento'] = estabelecimento or "Estabelecimento Comercial"

    # 3. Data e Hora de Emissão
    # Procura por "Emissão: dd/mm/aaaa hh:mm:ss" ou tags com classe data
    texto_pagina = soup.get_text(" ", strip=True)
    match_data = re.search(r'(?:emiss[aã]o|data)\s*[:=]?\s*(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)', texto_pagina, re.IGNORECASE)
    if match_data:
        resultado['data_emissao'] = match_data.group(1)
    else:
        # Fallback para regex genérica de data brasileira
        match_data_gen = re.search(r'\b(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)\b', texto_pagina)
        if match_data_gen:
            resultado['data_emissao'] = match_data_gen.group(1)

    # 4. Extração de Itens da Compra
    itens: List[Dict[str, Any]] = []

    # Estratégia A: Layout SP / SVRS com tabela #tabResult ou linhas de produtos
    linhas_tabela = soup.select('#tabResult tr, table.table-striped tr, table.tabelaItens tr, #conteudo table tr')
    for linha in linhas_tabela:
        # Verifica se é uma linha de produto (possui descrição ou classe .txtTit / .txtTit2)
        desc_el = linha.select_one('.txtTit, .txtTit2, .desc-produto, .descricao, .nome-produto')
        if desc_el:
            desc = desc_el.get_text(strip=True)
            # Remove código numérico no início se houver (ex: "(Código: 1234) Arroz" ou "123 - Feijão")
            desc = re.sub(r'^\(\s*c[oó]digo[^\)]*\)\s*', '', desc, flags=re.IGNORECASE).strip()

            # Quantidade
            qtd_el = linha.select_one('.Rqtd, .qtd, .quantidade')
            qtd_texto = qtd_el.get_text(strip=True) if qtd_el else ""
            if not qtd_texto:
                match_qtd = re.search(r'qtd\.?[:\s]*([\d,.]+)', linha.get_text(), re.IGNORECASE)
                qtd_texto = match_qtd.group(1) if match_qtd else "1"
            quantidade = _limpar_quantidade(qtd_texto)

            # Valor Unitário
            vl_unit_el = linha.select_one('.RvlUnit, .vlUnit, .valor-unitario')
            vl_unit_texto = vl_unit_el.get_text(strip=True) if vl_unit_el else ""
            if not vl_unit_texto:
                match_vl_unit = re.search(r'unit\.?[:\s]*([\d,.]+)', linha.get_text(), re.IGNORECASE)
                vl_unit_texto = match_vl_unit.group(1) if match_vl_unit else ""
            vl_unitario = _limpar_valor_monetario(vl_unit_texto) or 0.0

            # Valor Total do Item
            vl_total_el = linha.select_one('.valor, .vlTotal, .valor-total')
            vl_total_texto = vl_total_el.get_text(strip=True) if vl_total_el else ""
            vl_total = _limpar_valor_monetario(vl_total_texto)
            if vl_total is None or vl_total == 0.0:
                vl_total = round(quantidade * vl_unitario, 2)
            if vl_unitario == 0.0 and quantidade > 0 and vl_total > 0:
                vl_unitario = round(vl_total / quantidade, 2)

            if desc and (vl_total > 0 or vl_unitario > 0):
                itens.append({
                    'descricao': desc,
                    'quantidade': quantidade,
                    'valor_unitario': vl_unitario,
                    'valor_total': vl_total,
                })

    # Estratégia B: Se a Estratégia A não encontrou itens, varre células <tr>/<td> de tabelas genéricas
    if not itens:
        for tr in soup.find_all('tr'):
            tds = tr.find_all(['td', 'th'])
            if len(tds) >= 3:
                # Procura coluna de texto (descrição) e colunas numéricas
                textos_td = [td.get_text(strip=True) for td in tds]
                # Se for linha de cabeçalho, pula
                if any(h in textos_td[0].lower() for h in ['descri', 'item', 'código', 'produto']):
                    continue

                desc = textos_td[0]
                # Ignora linhas com textos puramente fiscais ou cabeçalhos
                if len(desc) < 2 or any(k in desc.lower() for k in ['total', 'subtotal', 'desconto', 'troco']):
                    continue

                # Tenta parsear colunas subsequentes como qtd, unit e total
                numeros_encontrados = []
                for t in textos_td[1:]:
                    val = _limpar_valor_monetario(t)
                    if val is not None:
                        numeros_encontrados.append(val)

                if len(numeros_encontrados) >= 2:
                    qtd = numeros_encontrados[0]
                    vl_unit = numeros_encontrados[1]
                    vl_tot = numeros_encontrados[2] if len(numeros_encontrados) >= 3 else round(qtd * vl_unit, 2)
                    itens.append({
                        'descricao': desc,
                        'quantidade': float(qtd) if qtd > 0 else 1.0,
                        'valor_unitario': vl_unit,
                        'valor_total': vl_tot,
                    })

    # Estratégia C: Divs com classes específicas de produtos (ex: mobile layouts)
    if not itens:
        produtos_divs = soup.select('.item, .produto, .box-item, div[id*="item"]')
        for pdiv in produtos_divs:
            desc_el = pdiv.select_one('.descricao, .nome, strong, b')
            if not desc_el:
                continue
            desc = desc_el.get_text(strip=True)
            if any(ign in desc.lower() for ignorar, ign in enumerate(['total', 'nfc-e', 'pago'])):
                continue

            txt_pdiv = pdiv.get_text(" ", strip=True)
            valores = re.findall(r'(\d+[.,]\d{2})', txt_pdiv)
            if valores:
                vl_tot = _limpar_valor_monetario(valores[-1]) or 0.0
                vl_unit = _limpar_valor_monetario(valores[0]) if len(valores) > 1 else vl_tot
                itens.append({
                    'descricao': desc,
                    'quantidade': 1.0,
                    'valor_unitario': vl_unit,
                    'valor_total': vl_tot,
                })

    resultado['itens'] = itens

    # 5. Valor Total da Nota Fiscal
    valor_total = 0.0
    el_total = soup.select_one('.totalNFe, .txtMax, #lblValorTotal, .valor-total-nota, .totalNota')
    if el_total:
        valor_total = _limpar_valor_monetario(el_total.get_text(strip=True)) or 0.0

    if valor_total == 0.0:
        # Busca por "Valor a pagar" ou "Total R$" no texto
        match_tot = re.search(r'(?:valor\s*(?:a\s*pagar|total|pago)?|total\s*r\$)\s*[:=]?\s*(?:r\$\s*)?([\d,.]+)', texto_pagina, re.IGNORECASE)
        if match_tot:
            valor_total = _limpar_valor_monetario(match_tot.group(1)) or 0.0

    # Se ainda for 0.0, calcula pela soma dos itens extraídos
    if valor_total == 0.0 and itens:
        valor_total = round(sum(i['valor_total'] for i in itens), 2)

    resultado['valor_total'] = valor_total

    # Se obtivemos itens ou valor total ou estabelecimento, consideramos sucesso
    if valor_total > 0 or itens or len(resultado['chave_acesso']) == 44:
        resultado['sucesso'] = True
        qtd_itens = len(itens)
        resultado['mensagem'] = f"NFC-e processada com sucesso: {qtd_itens} item(ns), Total R$ {valor_total:.2f}"
    else:
        resultado['mensagem'] = "Não foi possível extrair os dados da NFC-e a partir do HTML."

    return resultado


URLS_BASE_SEFAZ_UF: Dict[str, str] = {
    '11': 'https://www.sefin.ro.gov.br/nfce/qrcode?p=',
    '12': 'http://hml.sefaz.ac.gov.br/nfce/qrcode?p=',
    '13': 'http://sistemas.sefaz.am.gov.br/nfceweb/consultarNFCe.aspx?p=',
    '14': 'https://www.sefaz.rr.gov.br/nfce/servlet/qrcode?p=',
    '15': 'https://appnfc.sefa.pa.gov.br/portal/view/consultas/nfce/nfceForm.action?p=',
    '16': 'https://www.sefaz.ap.gov.br/nfce/qrcode?p=',
    '17': 'http://portal.sefaz.to.gov.br/nfce/qrcode?p=',
    '21': 'http://nfce.sefaz.ma.gov.br/portal/consultarNFCe.form?p=',
    '22': 'http://web.sefaz.pi.gov.br/nfce/qrcode?p=',
    '23': 'http://nfce.sefaz.ce.gov.br/pages/ShowNFCe.html?p=',
    '24': 'http://nfce.set.rn.gov.br/consultarNFCe.aspx?p=',
    '25': 'https://www.sefaz.pb.gov.br/nfce/qrcode?p=',
    '26': 'http://nfce.sefaz.pe.gov.br/nfce-web/consultarNFCe?p=',
    '27': 'http://nfce.sefaz.al.gov.br/QRCode/consultarNFCe.aspx?p=',
    '28': 'http://www.nfce.se.gov.br/portal/consultarNFCe.jsp?p=',
    '29': 'http://nfe.sefaz.ba.gov.br/servicos/nfce/qrcode.aspx?p=',
    '31': 'https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?p=',
    '32': 'http://app.sefaz.es.gov.br/ConsultaNFCe/qrcode.aspx?p=',
    '33': 'http://www4.fazenda.rj.gov.br/consultaNFCe/QRCode?p=',
    '35': 'https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=',
    '41': 'http://www.fazenda.pr.gov.br/nfce/qrcode?p=',
    '42': 'https://sat.sef.sc.gov.br/nfce/consulta?p=',
    '43': 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=',
    '50': 'http://www.dfe.ms.gov.br/nfce/qrcode?p=',
    '51': 'http://www.sefaz.mt.gov.br/nfce/consultanfce?p=',
    '52': 'http://nfe.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe?p=',
    '53': 'http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?p=',
}
URL_BASE_PADRAO_SVRS = 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p='


def obter_url_consulta_por_chave(chave: str) -> Optional[str]:
    """
    A partir de uma chave de acesso de 44 dígitos, extrai os 2 primeiros dígitos
    (código IBGE da UF) e constrói a URL oficial de consulta pública da NFC-e.
    """
    digitos = re.sub(r'\D', '', chave or '')
    if len(digitos) != 44:
        return None
    uf_cod = digitos[:2]
    url_base = URLS_BASE_SEFAZ_UF.get(uf_cod, URL_BASE_PADRAO_SVRS)
    return f"{url_base}{digitos}"


def _consultar_via_playwright(url: str, timeout: int = 15) -> Optional[str]:
    """
    Acessa a URL da SEFAZ utilizando navegador headless Playwright com bypass
    de proteções básicas e espera de carregamento dinâmico de tabelas e DOM.
    Retorna o HTML completo renderizado pelo navegador ou None em caso de falha/bloqueio.
    """
    if not PLAYWRIGHT_AVAILABLE:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            context = browser.new_context(
                user_agent=USER_AGENT_PADRAO,
                viewport={'width': 1280, 'height': 800},
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
            )
            page = context.new_page()

            timeout_ms = max(5000, timeout * 1000)
            page.set_default_timeout(timeout_ms)

            try:
                page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
            except Exception:
                pass

            # Aguarda a tabela de itens ou valor total na DOM
            seletores_tabela = [
                '#tabResult tr',
                'table.table-striped tr',
                'table.tabelaItens tr',
                '#conteudo table tr',
                '.item',
                '.totalNFe',
                '.txtMax',
                '#lblValorTotal'
            ]
            seletor_combinado = ', '.join(seletores_tabela)

            try:
                page.wait_for_selector(seletor_combinado, state='visible', timeout=4000)
            except Exception:
                try:
                    page.wait_for_load_state('networkidle', timeout=3000)
                except Exception:
                    pass

            html = page.content()
            browser.close()
            return html
    except Exception:
        return None


def _consultar_via_requests(url: str, timeout: int = 10) -> Optional[str]:
    """Fallback via HTTP clássico (requests) com headers de navegador padrão."""
    try:
        response = requests.get(
            url,
            headers=HEADERS_PADRAO,
            timeout=timeout,
            allow_redirects=True
        )
        response.raise_for_status()
        if response.encoding and response.encoding.lower() in ('iso-8859-1', 'latin-1'):
            return response.content.decode('latin-1', errors='replace')
        return response.text
    except Exception:
        return None


def consultar_nfce(url_ou_chave: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Executa a requisição resiliente para o portal da SEFAZ apontado pela URL
    do QR-Code ou chave da NFC-e e realiza a extração completa dos dados e itens.

    Utiliza Playwright Headless para vencer proteções WAF e renderização via JavaScript,
    com fallback automático para requests e metadados da chave/URL em caso de bloqueio.
    """
    resultado_fallback = extrair_dados_nfce(url_ou_chave)

    resultado_final: Dict[str, Any] = {
        'sucesso': False,
        'estabelecimento': resultado_fallback.get('nome') or 'Compra NFC-e',
        'data_emissao': None,
        'valor_total': resultado_fallback.get('valor') or 0.0,
        'chave_acesso': resultado_fallback.get('chave_acesso') or '',
        'uf': resultado_fallback.get('uf'),
        'itens': [],
        'url': url_ou_chave,
        'mensagem': '',
    }

    url = (url_ou_chave or '').strip()

    # TASK 2: Se não for uma URL direta, mas houver chave de 44 dígitos,
    # constrói a URL de consulta SEFAZ a partir do código IBGE da UF
    if not url.startswith('http://') and not url.startswith('https://'):
        if resultado_final['chave_acesso']:
            url_gerada = obter_url_consulta_por_chave(resultado_final['chave_acesso'])
            if url_gerada:
                url = url_gerada
                resultado_final['url'] = url_gerada
        else:
            resultado_final['mensagem'] = "Identificador fornecido não é uma URL ou chave válida para consulta Web."
            resultado_final['sucesso'] = bool(resultado_final['chave_acesso'] or resultado_final['valor_total'])
            return resultado_final

    # Se ainda não tiver URL válida mesmo após a tentativa de roteamento
    if not url.startswith('http://') and not url.startswith('https://'):
        if resultado_final['chave_acesso']:
            uf_sigla = resultado_fallback.get('uf')
            uf_msg = f" (UF: {uf_sigla})" if uf_sigla else ""
            resultado_final['sucesso'] = True
            resultado_final['mensagem'] = f"Chave de acesso reconhecida com sucesso{uf_msg}."
        return resultado_final

    # 1. Tentativa com Playwright Headless (vence WAF e JS rendering)
    html = _consultar_via_playwright(url, timeout=timeout)

    # 2. Fallback com requests se Playwright não retornar conteúdo
    if not html:
        html = _consultar_via_requests(url, timeout=min(timeout, 8))

    if html:
        dados_html = parsear_html_nfce(html, url_origem=url)

        if dados_html.get('sucesso'):
            if not dados_html.get('chave_acesso') and resultado_final['chave_acesso']:
                dados_html['chave_acesso'] = resultado_final['chave_acesso']
            if not dados_html.get('valor_total') and resultado_final['valor_total']:
                dados_html['valor_total'] = resultado_final['valor_total']
            if not dados_html.get('uf') and resultado_final.get('uf'):
                dados_html['uf'] = resultado_final['uf']
            return dados_html
        else:
            # Layout não reconhecido no HTML: preserva dados do fallback
            uf_sigla = resultado_final.get('uf')
            uf_msg = f" (UF: {uf_sigla})" if uf_sigla else ""
            prefixo = f"Chave de acesso reconhecida{uf_msg}. " if resultado_final.get('chave_acesso') else ""
            resultado_final['mensagem'] = f"{prefixo}Página acessada, mas layout não identificado. {dados_html.get('mensagem', '')}".strip()
            resultado_final['sucesso'] = bool(resultado_final['chave_acesso'] or resultado_final['valor_total'])
            return resultado_final

    # Falha na conexão de ambos os motores: preserva metadados com resiliência total
    uf_sigla = resultado_fallback.get('uf')
    uf_msg = f" (UF: {uf_sigla})" if uf_sigla else ""
    resultado_final['sucesso'] = bool(resultado_final['chave_acesso'] or resultado_final['valor_total'])
    resultado_final['mensagem'] = f"Chave identificada com sucesso{uf_msg}. Portal da SEFAZ indisponível ou protegido por CAPTCHA no momento."
    return resultado_final
