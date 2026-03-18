import os
import uuid
import re
from PIL import Image, ImageOps
from flask import current_app
from werkzeug.utils import secure_filename
from decimal import Decimal, InvalidOperation
from .file_validator import validar_ficheiro_completo, sanitize_filename

# Proteção contra ataques de negação de serviço via imagens (Decompression Bombs)
Image.MAX_IMAGE_PIXELS = 10_000_000


def salvar_ficheiro(ficheiro, subpasta='safras', privado=False):
    """
    Gestão de Ativos AgroKongo: Validação MIME, Conversão WebP, Redimensionamento e Isolamento.
    Esta função é crítica para a segurança e performance.

    Args:
        ficheiro (FileStorage): O objeto de ficheiro enviado pelo formulário.
        subpasta (str): A subpasta dentro de UPLOAD_FOLDER_PUBLIC ou UPLOAD_FOLDER_PRIVATE.
        privado (bool): Se o ficheiro deve ser guardado na pasta privada (ex: comprovativos).

    Returns:
        str: O nome único do ficheiro guardado, ou None em caso de erro/validação falha.
    """
    if not ficheiro or not ficheiro.filename:
        return None

    # 1. Validação completa com MIME type
    permitido, erro, mime_type = validar_ficheiro_completo(
        ficheiro, 
        allowed_types='documents' if privado else 'images'
    )
    
    if not permitido:
        current_app.logger.warning(f"Upload rejeitado: {erro}")
        return None
    
    current_app.logger.info(f"Ficheiro validado: MIME={mime_type}, Size OK")

    # 2. Definição de Destino (Isolamento de Talões Bancários vs Fotos Públicas)
    # Em produção, UPLOAD_FOLDER_PRIVATE deve estar fora da pasta static/
    base_folder = current_app.config.get('UPLOAD_FOLDER_PRIVATE') if privado else current_app.config.get(
        'UPLOAD_FOLDER_PUBLIC')

    # Fallback de segurança caso a config não esteja carregada
    if not base_folder:
        current_app.logger.error("UPLOAD_FOLDER_PUBLIC ou UPLOAD_FOLDER_PRIVATE não configurado.")
        return None

    diretorio_final = os.path.join(base_folder, subpasta)
    os.makedirs(diretorio_final, exist_ok=True)

    # 3. Nome Único e Extensão de Destino
    # PDFs mantêm-se, imagens viram WebP (o formato mais eficiente para a internet atual)
    ext_destino = 'pdf' if mime_type == 'application/pdf' else 'webp'
    
    # Sanitiza e gera nome único
    nome_unico = sanitize_filename(ficheiro.filename)
    if not nome_unico.endswith(f'.{ext_destino}'):
        nome_unico = f"{uuid.uuid4().hex}.{ext_destino}"
    
    caminho_completo = os.path.join(diretorio_final, nome_unico)

    try:
        if ext_destino == 'pdf':
            ficheiro.save(caminho_completo)
        else:
            # 4. Processamento de Imagem Profissional
            with Image.open(ficheiro) as img:
                # Corrige rotação automática de telemóveis (EXIF)
                img = ImageOps.exif_transpose(img)

                # Garante compatibilidade WebP (remove canal Alpha se necessário)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Redimensionamento Inteligente (LANCZOS para nitidez)
                # 1200px é o "sweet spot" para ver detalhes de produtos sem pesar
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)

                # Compressão Lossy otimizada para Web
                img.save(caminho_completo, "WEBP", quality=75, optimize=True)

        # Retornamos o nome para gravar na BD.
        # Importante: A rota de exibição deve saber que está na 'subpasta'.
        return nome_unico

    except Exception as e:
        current_app.logger.error(f"ERRO CRÍTICO UPLOAD de {ficheiro.filename}: {str(e)}")
        return None


def formatar_moeda_kz(valor):
    """
    Padrão de Moeda Angola (AOA/Kz).
    Resultado esperado: 1.500,00 Kz
    """
    if valor is None: return "0,00 Kz"
    try:
        # Garante que o valor é um Decimal para evitar erros de ponto flutuante
        v = Decimal(str(valor)).quantize(Decimal('0.01'))
        # Usamos o ponto para milhares e vírgula para decimais
        return f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " Kz"
    except InvalidOperation:
        current_app.logger.warning(f"Tentativa de formatar valor inválido para moeda: {valor}")
        return "0,00 Kz"
    except Exception as e:
        current_app.logger.error(f"Erro inesperado ao formatar moeda {valor}: {e}")
        return "0,00 Kz"


def formatar_nif(nif):
    """Limpeza para evitar erros de validação em documentos fiscais."""
    if not nif: return ""
    return re.sub(r'[^A-Z0-9]', '', str(nif).upper())