"""
Validacao segura de ficheiros para uploads no AgroKongo.
Inclui validacao de MIME type, extensao e tamanho.
"""
import os
from typing import Tuple, Optional
from flask import current_app


# Configurações de segurança
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf'}
ALLOWED_MIME_TYPES = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
    'application/pdf': '.pdf'
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB (deve bater com MAX_CONTENT_LENGTH)


def validar_mime_type(file_stream) -> Tuple[bool, Optional[str]]:
    """
    Valida o MIME type real do ficheiro lendo seu conteúdo.
    Usa deteccao por magic bytes (alternativa ao imghdr removido do Python 3.13+).
    
    Args:
        file_stream: Stream do ficheiro (file.read())
        
    Returns:
        Tuple[is_valid, mime_type ou erro]
    """
    try:
        # Detecta tipo de imagem por magic bytes
        file_stream.seek(0)
        header = file_stream.read(8)  # Le primeiros 8 bytes
        
        # JPEG: FF D8 FF
        if header[:3] == b'\xFF\xD8\xFF':
            return True, 'image/jpeg'
        
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        if header[:8] == b'\x89PNG\r\n\x1a\n':
            return True, 'image/png'
        
        # GIF: 47 49 46 38
        if header[:4] == b'GIF8':
            return True, 'image/gif'
        
        # WebP: RIFF + tamanho (4 bytes) + WEBP
        if header[:4] == b'RIFF':
            file_stream.seek(0)
            webp_header = file_stream.read(12)
            if len(webp_header) >= 12 and webp_header[8:12] == b'WEBP':
                return True, 'image/webp'
        
        # BMP: 42 4D
        if header[:2] == b'BM':
            return True, 'image/bmp'
        
        # PDF: %PDF
        file_stream.seek(0)
        pdf_header = file_stream.read(4)
        if pdf_header == b'%PDF':
            return True, 'application/pdf'
        
        return False, "Nao foi possivel identificar o tipo de ficheiro"
        
    except Exception as e:
        return False, f"Erro na validacao: {str(e)}"


def validar_extensao(filename: str, allowed_extensions: set) -> bool:
    """
    Valida a extensão do ficheiro.
    
    Args:
        filename: Nome do ficheiro
        allowed_extensions: Set de extensões permitidas
        
    Returns:
        bool: True se extensão for válida
    """
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def validar_tamanho(file_stream) -> Tuple[bool, int]:
    """
    Valida o tamanho do ficheiro.
    
    Args:
        file_stream: Stream do ficheiro
        
    Returns:
        Tuple[is_valid, tamanho_em_bytes]
    """
    file_stream.seek(0, 2)  # Vai para o final
    size = file_stream.tell()
    file_stream.seek(0)  # Volta para o início
    
    return size <= MAX_FILE_SIZE, size


def validar_ficheiro_completo(file, allowed_types: str = 'all') -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validação completa de ficheiro: extensão, MIME type e tamanho.
    
    Args:
        file: FileStorage do Flask
        allowed_types: 'images', 'documents', ou 'all'
        
    Returns:
        Tuple[is_valid, mensagem_erro, mime_type]
    """
    if not file or file.filename == '':
        return False, "Nenhum ficheiro selecionado", None
    
    filename = file.filename.lower()
    
    # 1. Validar extensão
    if allowed_types == 'images':
        if not validar_extensao(filename, ALLOWED_IMAGE_EXTENSIONS):
            return False, f"Extensão não permitida. Aceitamos: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}", None
    elif allowed_types == 'documents':
        if not validar_extensao(filename, ALLOWED_DOCUMENT_EXTENSIONS):
            return False, f"Extensão não permitida. Aceitamos: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}", None
    else:  # all
        all_ext = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS
        if not validar_extensao(filename, all_ext):
            return False, f"Extensão não permitida.", None
    
    # 2. Validar tamanho
    valido, tamanho = validar_tamanho(file.stream)
    if not valido:
        return False, f"Ficheiro muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB", None
    
    # 3. Validar MIME type
    file.stream.seek(0)
    valido, mime_result = validar_mime_type(file.stream)
    if not valido:
        return False, mime_result, None
    
    file.stream.seek(0)  # Reset stream
    
    return True, None, mime_result


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza o nome do ficheiro para evitar problemas de segurança.
    
    Args:
        filename: Nome original do ficheiro
        
    Returns:
        str: Nome sanitizado
    """
    from werkzeug.utils import secure_filename
    import uuid
    
    # Remove caracteres perigosos
    safe_name = secure_filename(filename)
    
    # Gera UUID único para evitar colisões
    name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
    unique_name = f"{uuid.uuid4().hex[:12]}.{ext}" if ext else uuid.uuid4().hex[:12]
    
    return unique_name.lower()
