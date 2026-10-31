"""
Módulo para leitura e extração de dados de QR-Code e notas fiscais (NFC-e / SAT).
Decodifica imagens contendo QR-Codes e extrai informações essenciais como valor total,
chave de acesso e dados do cupom fiscal.
"""
import io
import re
import urllib.parse
from typing import Optional, Dict, Any

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageOps
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


def _tentar_decodificar_opencv(detector, imagem) -> Optional[str]:
    """Tenta decodificar o QR-Code com uma matriz do OpenCV."""
    try:
        data, _, _ = detector.detectAndDecode(imagem)
        if data and data.strip():
            return data.strip()
    except Exception:
        pass
    return None


def decodificar_imagem_qrcode(imagem_bytes_ou_arquivo) -> Optional[str]:
    """
    Decodifica o conteúdo de um QR-Code a partir de bytes de imagem ou arquivo em memória.
    Aplica correção de orientação EXIF (fotos de smartphone), redimensionamento multi-escala
    e filtros em cascata (CLAHE e Otsu) para notas fiscais térmicas e com sombras.
    Retorna o texto contido no QR-Code ou None se nenhum código for encontrado.
    """
    if not OPENCV_AVAILABLE:
        return None

    try:
        if hasattr(imagem_bytes_ou_arquivo, 'read'):
            conteudo = imagem_bytes_ou_arquivo.read()
            if hasattr(imagem_bytes_ou_arquivo, 'seek'):
                imagem_bytes_ou_arquivo.seek(0)
        else:
            conteudo = imagem_bytes_ou_arquivo

        pil_img = Image.open(io.BytesIO(conteudo))
        # Normaliza a orientação da foto utilizando metadados EXIF
        try:
            pil_img = ImageOps.exif_transpose(pil_img)
        except Exception:
            pass

        pil_img = pil_img.convert('RGB')
        np_img = np.array(pil_img)
        bgr_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

        detector = cv2.QRCodeDetector()

        # Prepara escalas para testar (resoluções muito altas de celular dificultam a detecção)
        h, w = bgr_img.shape[:2]
        escalas_bgr = [bgr_img]

        maior_dim = max(h, w)
        if maior_dim > 1600:
            fator_1 = 1280.0 / maior_dim
            escalas_bgr.append(cv2.resize(bgr_img, (int(w * fator_1), int(h * fator_1)), interpolation=cv2.INTER_AREA))
            fator_2 = 800.0 / maior_dim
            escalas_bgr.append(cv2.resize(bgr_img, (int(w * fator_2), int(h * fator_2)), interpolation=cv2.INTER_AREA))
        elif maior_dim > 1000:
            fator = 800.0 / maior_dim
            escalas_bgr.append(cv2.resize(bgr_img, (int(w * fator), int(h * fator)), interpolation=cv2.INTER_AREA))

        for img in escalas_bgr:
            # 1. BGR direto
            res = _tentar_decodificar_opencv(detector, img)
            if res:
                return res

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # 2. Escala de cinza
            res = _tentar_decodificar_opencv(detector, gray)
            if res:
                return res

            # 3. CLAHE (equalização adaptativa para papel térmico com sombras/desbotado)
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gray_clahe = clahe.apply(gray)
                res = _tentar_decodificar_opencv(detector, gray_clahe)
                if res:
                    return res
            except Exception:
                pass

            # 4. Binarização adaptativa Otsu
            try:
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                res = _tentar_decodificar_opencv(detector, otsu)
                if res:
                    return res

                # Invertido (fundo escuro / código claro)
                res = _tentar_decodificar_opencv(detector, cv2.bitwise_not(otsu))
                if res:
                    return res
            except Exception:
                pass

        # Tentativa final: rotações de 90° caso a foto tenha sido tirada inclinada
        for rot in [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]:
            img_rot = cv2.rotate(escalas_bgr[-1], rot)
            res = _tentar_decodificar_opencv(detector, img_rot)
            if res:
                return res
            gray_rot = cv2.cvtColor(img_rot, cv2.COLOR_BGR2GRAY)
            res = _tentar_decodificar_opencv(detector, gray_rot)
            if res:
                return res

    except Exception:
        pass

    return None


def extrair_dados_nfce(texto_qr: str) -> Dict[str, Any]:
    """
    Interpreta o texto ou URL de um QR-Code (típico de NFC-e, SAT ou comprovantes fiscais)
    e extrai o valor total, chave de acesso de 44 dígitos e nome sugerido.
    """
    resultado = {
        'sucesso': False,
        'valor': None,
        'nome': 'Compra NFC-e',
        'chave_acesso': None,
        'qr_data': texto_qr or '',
        'mensagem': '',
    }

    if not texto_qr or not isinstance(texto_qr, str):
        resultado['mensagem'] = 'Conteúdo do QR-Code está vazio ou inválido.'
        return resultado

    texto = texto_qr.strip()

    # 1. Busca por chave de acesso de 44 dígitos
    chave_match = re.search(r'\b(\d{44})\b', texto)
    if chave_match:
        resultado['chave_acesso'] = chave_match.group(1)
        resultado['nome'] = f"Compra NFC-e {chave_match.group(1)[:8]}..."

    # 2. Se for URL (padrão SEFAZ)
    if 'http://' in texto.lower() or 'https://' in texto.lower() or '?' in texto:
        try:
            parsed = urllib.parse.urlparse(texto)
            params = urllib.parse.parse_qs(parsed.query)

            # Busca direta por parâmetro vNF ou valor
            for chave_param in ['vNF', 'vnf', 'valor', 'total', 'vProd', 'vLiq']:
                if chave_param in params and params[chave_param]:
                    val_str = params[chave_param][0].replace(',', '.')
                    try:
                        resultado['valor'] = round(float(val_str), 2)
                        break
                    except ValueError:
                        pass

            # Caso o parâmetro 'p' contenha dados delimitados por pipe (|)
            # Padrão SEFAZ v2: chNFe|versao|tpAmb|cDest|dhEmi|vNF|vICMS|...
            if resultado['valor'] is None and 'p' in params and params['p']:
                payload_p = params['p'][0]
                resultado['valor'] = _extrair_valor_de_pipe(payload_p)

        except Exception:
            pass

    # 3. Se for string pura delimitada por pipe (sem URL completa)
    if resultado['valor'] is None and '|' in texto:
        resultado['valor'] = _extrair_valor_de_pipe(texto)

    # 4. Busca heurística por padrões de valor monetário no texto livre
    if resultado['valor'] is None:
        # Padrões: vNF=123.45, R$ 123,45, Total: 123.45, etc.
        padroes = [
            r'(?:vNF|vnf|total|valor|r\$)\s*[:=]?\s*([0-9]+[.,][0-9]{2})',
            r'\b([0-9]{1,6}[.,][0-9]{2})\b',
        ]
        for padrao in padroes:
            matches = re.findall(padrao, texto, flags=re.IGNORECASE)
            for m in matches:
                val_limpo = m.replace(',', '.')
                try:
                    val_float = float(val_limpo)
                    if val_float > 0:
                        resultado['valor'] = round(val_float, 2)
                        break
                except ValueError:
                    continue
            if resultado['valor'] is not None:
                break

    if resultado['valor'] is not None:
        resultado['sucesso'] = True
        resultado['mensagem'] = f"Dados extraídos com sucesso: R$ {resultado['valor']:.2f}"
    else:
        resultado['sucesso'] = bool(resultado['chave_acesso'] or texto)
        resultado['mensagem'] = "QR-Code lido. Valor não identificado automaticamente; por favor, informe o valor."

    return resultado


def _extrair_valor_de_pipe(texto_pipe: str) -> Optional[float]:
    """
    Auxiliar para inspecionar campos separados por pipe e identificar o valor total (vNF).
    """
    partes = texto_pipe.split('|')
    # No padrão SEFAZ versão 2.0:
    # 0: chNFe (44 dígitos - ignorar como valor)
    # 1: versão (1 ou 2)
    # 2: tpAmb (1 ou 2)
    # Seguem campos como cDest, dhEmi, vNF, vICMS, etc.
    candidatos = []
    for parte in partes:
        p = parte.strip().replace(',', '.')
        # Ignora chaves de acesso, datas ou hashes longos
        if len(p) >= 14 or len(p) <= 1:
            continue
        if re.match(r'^\d+(\.\d{1,2})?$', p):
            try:
                val = float(p)
                # Ignora códigos de versão ou ambiente (1, 2)
                if val > 2.0 and val < 1000000:
                    # Se tiver casas decimais explícitas, tem maior prioridade
                    tem_decimal = '.' in p
                    candidatos.append((tem_decimal, val))
            except ValueError:
                pass

    if candidatos:
        # Prioriza candidatos que tenham casas decimais
        candidatos.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return round(candidatos[0][1], 2)

    return None
