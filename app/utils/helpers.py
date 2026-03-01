import os
import uuid
import re
from PIL import Image, ImageOps
from flask import current_app
from werkzeug.utils import secure_filename
from decimal import Decimal

# Proteção contra ataques de negação de serviço via imagens (Decompression Bombs)
Image.MAX_IMAGE_PIXELS = 10_000_000


def salvar_ficheiro(ficheiro, subpasta='safras', privado=False):
    """
    Gestão de Ativos AgroKongo: Conversão WebP, Redimensionamento e Isolamento.
    """
    if not ficheiro or not ficheiro.filename:
        return None

    # Validação rigorosa de extensão
    ext_original = ficheiro.filename.rsplit('.', 1)[1].lower() if '.' in ficheiro.filename else ''
    permitidos = {'jpg', 'jpeg', 'png', 'webp', 'pdf'}

    if ext_original not in permitidos:
        current_app.logger.warning(f"Tentativa de upload inválida: {ext_original}")
        return None

    # 1. Definição de Destino (Isolamento de Talões Bancários vs Fotos Públicas)
    # Em produção, UPLOAD_FOLDER_PRIVATE deve estar fora da pasta static/
    base_folder = current_app.config.get('UPLOAD_FOLDER_PRIVATE') if privado else current_app.config.get(
        'UPLOAD_FOLDER_PUBLIC')

    # Fallback de segurança caso a config não esteja carregada
    if not base_folder:
        # Proteção contra path traversal: usar apenas valores seguros
        folder_type = 'private' if privado else 'public'
        base_folder = os.path.abspath(os.path.join(current_app.root_path, 'storage', folder_type))
    
    # Normalização e validação de base_folder
    base_folder = os.path.abspath(base_folder)
    
    # Validação: garante que base_folder está dentro do root_path
    root_path = os.path.abspath(current_app.root_path)
    if not base_folder.startswith(root_path):
        current_app.logger.error(f"Base folder inválido: {base_folder}")
        return None

    # Sanitização contra path traversal
    safe_subpasta = os.path.basename(subpasta)
    
    # Validação adicional contra caracteres perigosos
    if '..' in safe_subpasta or '/' in safe_subpasta or '\\' in safe_subpasta:
        current_app.logger.error(f"Path traversal detectado em subpasta: {subpasta}")
        return None
    
    # Validação whitelist de subpasta
    subpastas_permitidas = {'safras', 'fotos', 'taloes', 'faturas', 'relatorios', 'perfis'}
    if safe_subpasta not in subpastas_permitidas:
        current_app.logger.warning(f"Subpasta inválida: {subpasta}")
        return None
    
    diretorio_final = os.path.abspath(os.path.join(base_folder, safe_subpasta))
    
    # Validação robusta: garante que diretório final está dentro do base_folder
    if not diretorio_final.startswith(base_folder + os.sep):
        current_app.logger.error(f"Path traversal detectado: {subpasta}")
        return None
    
    os.makedirs(diretorio_final, exist_ok=True)

    # 2. Nome Único e Extensão de Destino
    # PDFs mantêm-se, imagens viram WebP (o formato mais eficiente para a internet atual)
    ext_destino = 'pdf' if ext_original == 'pdf' else 'webp'
    nome_unico = f"{uuid.uuid4().hex}.{ext_destino}"
    caminho_completo = os.path.join(diretorio_final, nome_unico)

    try:
        if ext_destino == 'pdf':
            ficheiro.save(caminho_completo)
        else:
            # 3. Processamento de Imagem Profissional
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
        current_app.logger.error(f"ERRO CRÍTICO UPLOAD: {str(e)}")
        return None


def formatar_moeda_kz(valor):
    """
    Padrão de Moeda Angola (AOA/Kz).
    Resultado esperado: 1.500,00 Kz
    """
    if valor is None: return "0,00 Kz"
    try:
        v = Decimal(str(valor)).quantize(Decimal('0.01'))
        # Usamos o ponto para milhares e vírgula para decimais
        return f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + " Kz"
    except:
        return "0,00 Kz"


def formatar_nif(nif):
    """Limpeza para evitar erros de validação em documentos fiscais."""
    if not nif: return ""
    return re.sub(r'[^A-Z0-9]', '', str(nif).upper())