"""
Testes Unitarios de Validacao de Ficheiros
Testa a validacao de MIME type, extensao e tamanho.
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock

from app.utils.file_validator import (
    validar_mime_type,
    validar_extensao,
    validar_tamanho,
    validar_ficheiro_completo,
    sanitize_filename,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_DOCUMENT_EXTENSIONS,
    MAX_FILE_SIZE
)


class TestValidarExtensao:
    """Testa validacao de extensoes."""
    
    def test_extensoes_imagem_permitidas(self):
        """Testa extensoes de imagem validas."""
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            assert validar_extensao(f"teste.{ext}", ALLOWED_IMAGE_EXTENSIONS) is True
    
    def test_extensao_pdf_permitida(self):
        """Testa extensao PDF valida."""
        assert validar_extensao("documento.pdf", ALLOWED_DOCUMENT_EXTENSIONS) is True
    
    def test_extensoes_proibidas(self):
        """Testa extensoes nao permitidas."""
        proibidas = ['exe', 'bat', 'sh', 'php', 'asp', 'jsp']
        for ext in proibidas:
            assert validar_extensao(f"malicioso.{ext}", ALLOWED_IMAGE_EXTENSIONS) is False
    
    def test_sem_extensao(self):
        """Testa ficheiro sem extensao."""
        assert validar_extensao("sem_extensao", ALLOWED_IMAGE_EXTENSIONS) is False
    
    def test_extensao_maiuscula(self):
        """Testa que extensao em maiusculas e normalizada."""
        assert validar_extensao("imagem.JPG", ALLOWED_IMAGE_EXTENSIONS) is True


class TestValidarMimeType:
    """Testa validacao de MIME type real."""
    
    def test_detectar_jpeg(self):
        """Testa deteccao de imagem JPEG por magic bytes."""
        # Header JPEG: FF D8 FF
        jpeg_data = BytesIO(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
        
        valido, mime_result = validar_mime_type(jpeg_data)
        
        assert valido is True
        assert mime_result == 'image/jpeg'
    
    def test_detectar_png(self):
        """Testa deteccao de imagem PNG por magic bytes."""
        # Header PNG: 89 50 4E 47 0D 0A 1A 0A
        png_data = BytesIO(b'\x89PNG\r\n\x1a\n')
        
        valido, mime_result = validar_mime_type(png_data)
        
        assert valido is True
        assert mime_result == 'image/png'
    
    def test_detectar_pdf(self):
        """Testa deteccao de PDF por magic bytes."""
        # Header PDF: %PDF
        pdf_data = BytesIO(b'%PDF-1.4\n1 0 obj')
        
        valido, mime_result = validar_mime_type(pdf_data)
        
        assert valido is True
        assert mime_result == 'application/pdf'
    
    def test_detectar_webp(self):
        """Testa deteccao de WebP por magic bytes."""
        # Header WebP completo: RIFF + tamanho (4 bytes) + WEBP
        webp_data = BytesIO(b'RIFF\x24\x00\x00\x00WEBPVP8 ')
        
        valido, mime_result = validar_mime_type(webp_data)
        
        assert valido is True
        assert mime_result == 'image/webp'
    
    def test_mime_type_invalido(self):
        """Testa ficheiro com MIME type nao suportado."""
        # Dados aleatorios
        invalid_data = BytesIO(b'dados aleatorios aqui')
        
        valido, mime_result = validar_mime_type(invalid_data)
        
        assert valido is False
        assert "nao foi possivel identificar" in mime_result.lower()


class TestValidarTamanho:
    """Testa validacao de tamanho de ficheiros."""
    
    def test_ficheiro_dentro_limite(self):
        """Testa ficheiro dentro do limite permitido."""
        # Criar ficheiro de 1MB (dentro do limite de 5MB)
        small_file = BytesIO(b'x' * (1024 * 1024))
        
        valido, tamanho = validar_tamanho(small_file)
        
        assert valido is True
        assert tamanho == 1024 * 1024
    
    def test_ficheiro_acima_limite(self):
        """Testa ficheiro acima do limite."""
        # Criar ficheiro de 6MB (acima do limite de 5MB)
        large_file = BytesIO(b'x' * (6 * 1024 * 1024))
        
        valido, tamanho = validar_tamanho(large_file)
        
        assert valido is False
        assert tamanho == 6 * 1024 * 1024
    
    def test_ficheiro_vazio(self):
        """Testa ficheiro vazio."""
        empty_file = BytesIO()
        
        valido, tamanho = validar_tamanho(empty_file)
        
        assert valido is True  # Vazio e tecnicamente valido
        assert tamanho == 0


class TestValidarFicheiroCompleto:
    """Testa validacao completa de ficheiros."""
    
    @patch('app.utils.file_validator.validar_mime_type')
    def test_validacao_sucesso_imagem(self, mock_mime):
        """Testa validacao completa de imagem."""
        mock_mime.return_value = (True, 'image/jpeg')
        
        mock_file = Mock()
        mock_file.filename = "teste.jpg"
        mock_file.stream = BytesIO(b'\xFF\xD8\xFF\xE0')
        
        valido, erro, mime = validar_ficheiro_completo(mock_file, allowed_types='images')
        
        assert valido is True
        assert erro is None
        assert mime == 'image/jpeg'
    
    @patch('app.utils.file_validator.validar_mime_type')
    def test_validacao_falha_extensao(self, mock_mime):
        """Testa falha na validacao por extensao invalida."""
        mock_file = Mock()
        mock_file.filename = "malicioso.exe"
        
        valido, erro, mime = validar_ficheiro_completo(mock_file, allowed_types='images')
        
        assert valido is False
        # Mensagem pode variar, entao verificamos se contem informacao util
        assert erro is not None
        assert len(erro) > 0
        assert mime is None
    
    @patch('app.utils.file_validator.validar_mime_type')
    def test_validacao_falha_mime_type(self, mock_mime):
        """Testa falha na validacao por MIME type invalido."""
        mock_mime.return_value = (False, "MIME type nao permitido")
        
        mock_file = Mock()
        mock_file.filename = "imagem.jpg"
        mock_file.stream = BytesIO(b'dados invalidos')
        
        valido, erro, mime = validar_ficheiro_completo(mock_file, allowed_types='images')
        
        assert valido is False
        assert "nao permitido" in erro or "identificar" in erro
        assert mime is None
    
    def test_validacao_sem_ficheiro(self):
        """Testa validacao quando nao ha ficheiro."""
        valido, erro, mime = validar_ficheiro_completo(None, allowed_types='images')
        
        assert valido is False
        assert "Nenhum ficheiro" in erro
    
    @patch('app.utils.file_validator.validar_mime_type')
    def test_validacao_documento_pdf(self, mock_mime):
        """Testa validacao de documento PDF."""
        mock_mime.return_value = (True, 'application/pdf')
        
        mock_file = Mock()
        mock_file.filename = "documento.pdf"
        mock_file.stream = BytesIO(b'%PDF-1.4')
        
        valido, erro, mime = validar_ficheiro_completo(mock_file, allowed_types='documents')
        
        assert valido is True
        assert erro is None
        assert mime == 'application/pdf'


class TestSanitizeFilename:
    """Testa sanitizacao de nomes de ficheiros."""
    
    def test_sanitiza_nome_simples(self):
        """Testa sanitizacao de nome simples."""
        nome_original = "minha_imagem.jpg"
        nome_sanitizado = sanitize_filename(nome_original)
        
        assert nome_sanitizado.endswith('.jpg')
        assert len(nome_sanitizado) == len('.jpg') + 12  # UUID de 12 chars + extensao
    
    def test_sanitiza_nome_com_caracteres_especiais(self):
        """Testa sanitizacao com caracteres especiais."""
        nome_original = "imagem@#$%&!*.png"
        nome_sanitizado = sanitize_filename(nome_original)
        
        assert nome_sanitizado.endswith('.png')
        # Caracteres especiais devem ser removidos
        assert '@' not in nome_sanitizado
        assert '#' not in nome_sanitizado
    
    def test_sanitiza_nome_com_caminho(self):
        """Testa sanitizacao com caminho completo (directory traversal)."""
        nome_original = "../../etc/passwd.jpg"
        nome_sanitizado = sanitize_filename(nome_original)
        
        # Deve remover path traversal
        assert '..' not in nome_sanitizado
        assert '/' not in nome_sanitizado
        assert nome_sanitizado.endswith('.jpg')
    
    def test_sanitiza_nome_minusculo(self):
        """Testa que nome e convertido para minusculas."""
        nome_original = "IMAGEM.PNG"
        nome_sanitizado = sanitize_filename(nome_original)
        
        assert nome_sanitizado.islower()
        assert nome_sanitizado.endswith('.png')
    
    def test_sanitiza_unico_para_mesmo_nome(self):
        """Testa que mesmo nome original gera nomes unicos diferentes."""
        nome_original = "teste.jpg"
        
        nome1 = sanitize_filename(nome_original)
        nome2 = sanitize_filename(nome_original)
        
        # Devem ser diferentes (UUIDs diferentes)
        assert nome1 != nome2
        assert nome1.endswith('.jpg')
        assert nome2.endswith('.jpg')
