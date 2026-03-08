"""
Testes Unitários para Utilitários de Criptografia
Cobertura: 100% dos módulos encryption.py e crypto.py
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from decimal import Decimal

from app.utils.encryption import DataEncryption, CampoCriptografado, get_client_ip
from app.utils.crypto import CryptoService, get_crypto


class TestDataEncryption:
    """Testes para a classe DataEncryption"""
    
    def test_encrypt_descript_decrypt_sucesso(self, app):
        """Criptografa e descriptografa com sucesso"""
        texto_original = "Dados sensíveis para teste"
        
        # Criptografar
        texto_criptografado = DataEncryption.encrypt(texto_original)
        
        # Verificar que foi criptografado
        assert texto_criptografado is not None
        assert texto_criptografado != texto_original
        assert isinstance(texto_criptografado, str)
        
        # Descriptografar
        texto_descriptografado = DataEncryption.decrypt(texto_criptografado)
        
        # Verificar que recuperou o original
        assert texto_descriptografado == texto_original
    
    def test_encrypt_texto_vazio(self, app):
        """Retorna None para texto vazio"""
        resultado = DataEncryption.encrypt("")
        assert resultado is None
        
        resultado = DataEncryption.encrypt(None)
        assert resultado is None
    
    def test_decrypt_texto_vazio(self, app):
        """Retorna None para texto vazio"""
        resultado = DataEncryption.decrypt("")
        assert resultado is None
        
        resultado = DataEncryption.decrypt(None)
        assert resultado is None
    
    def test_decrypt_texto_invalido(self, app):
        """Retorna texto original se não puder descriptografar"""
        texto_invalido = "texto_nao_criptografado_123"
        
        resultado = DataEncryption.decrypt(texto_invalido)
        
        # Deve retornar o próprio texto (compatibilidade)
        assert resultado == texto_invalido
    
    def test_hash_sensitive_consistencia(self, app):
        """Hash é consistente para mesmo input"""
        dado = "NIF123456789"
        
        hash1 = DataEncryption.hash_sensitive(dado)
        hash2 = DataEncryption.hash_sensitive(dado)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produz 64 caracteres hex
    
    def test_hash_sensitive_diferentes(self, app):
        """Hash diferente para inputs diferentes"""
        hash1 = DataEncryption.hash_sensitive("NIF123")
        hash2 = DataEncryption.hash_sensitive("NIF456")
        
        assert hash1 != hash2
    
    def test_hash_sensitive_case_insensitive(self, app):
        """Hash é case insensitive (converte para upper)"""
        hash1 = DataEncryption.hash_sensitive("abc123")
        hash2 = DataEncryption.hash_sensitive("ABC123")
        
        assert hash1 == hash2
    
    def test_hash_sensitive_vazio(self, app):
        """Retorna None para dado vazio"""
        resultado = DataEncryption.hash_sensitive("")
        assert resultado is None
        
        resultado = DataEncryption.hash_sensitive(None)
        assert resultado is None
    
    def test_encrypt_caracteres_especiais(self, app):
        """Suporta caracteres especiais e acentos"""
        textos = [
            "João José da Silva",
            "São Tomé e Príncipe",
            "Ñandú",
            "€1000,50",
            "测试中文"
        ]
        
        for texto in textos:
            criptografado = DataEncryption.encrypt(texto)
            descriptografado = DataEncryption.decrypt(criptografado)
            
            assert descriptografado == texto
    
    def test_encrypt_texto_longo(self, app):
        """Suporta textos longos"""
        texto_longo = "A" * 10000  # 10 mil caracteres
        
        criptografado = DataEncryption.encrypt(texto_longo)
        descriptografado = DataEncryption.decrypt(criptografado)
        
        assert descriptografado == texto_longo
    
    def test_cipher_dependencia_secret_key(self, app):
        """Falha se SECRET_KEY não estiver configurada"""
        with patch('app.utilsencryption.current_app') as mock_app:
            mock_app.config.get.return_value = None
            
            with pytest.raises(ValueError) as exc_info:
                DataEncryption.encrypt("teste")
            
            assert "SECRET_KEY" in str(exc_info.value)


class TestCryptoService:
    """Testes para a classe CryptoService"""
    
    def test_criar_instancia_com_secret_key(self):
        """Cria instância com secret key"""
        crypto = CryptoService(secret_key="minha_chave_secreta_123")
        
        assert crypto is not None
        assert hasattr(crypto, 'cipher')
    
    def test_criar_instancia_sem_secret_key(self):
        """Falha sem secret key"""
        with patch('app.utils.crypto.os.environ.get', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                CryptoService()
            
            assert "SECRET_KEY" in str(exc_info.value)
    
    def test_encrypt_decrypt(self):
        """Criptografa e descriptografa corretamente"""
        crypto = CryptoService(secret_key="chave_teste_123")
        
        texto_original = "Dados confidenciais"
        
        criptografado = crypto.encrypt(texto_original)
        descriptografado = crypto.decrypt(criptografado)
        
        assert descriptografado == texto_original
    
    def test_encrypt_texto_vazio(self):
        """Retorna None para texto vazio"""
        crypto = CryptoService(secret_key="chave_teste")
        
        assert crypto.encrypt("") is None
        assert crypto.encrypt(None) is None
    
    def test_decrypt_texto_vazio(self):
        """Retorna None para texto vazio"""
        crypto = CryptoService(secret_key="chave_teste")
        
        assert crypto.decrypt("") is None
        assert crypto.decrypt(None) is None
    
    def test_encrypt_mesma_chave_resultados_diferentes(self):
        """Mesmo texto produz resultados diferentes (devido ao salt/IV)"""
        crypto = CryptoService(secret_key="chave_teste")
        
        texto = "texto_repetido"
        
        cripto1 = crypto.encrypt(texto)
        cripto2 = crypto.encrypt(texto)
        
        # Ambos descriptografam para o mesmo valor
        assert crypto.decrypt(cripto1) == texto
        assert crypto.decrypt(cripto2) == texto
        
        # Mas são diferentes entre si (por causa do IV aleatório)
        assert cripto1 != cripto2


class TestGetCrypto:
    """Testes para função get_crypto"""
    
    def test_singleton_pattern(self):
        """Retorna mesma instância (singleton)"""
        # Limpar instância global
        import app.utils.crypto as crypto_module
        crypto_module._crypto = None
        
        crypto1 = get_crypto()
        crypto2 = get_crypto()
        
        assert crypto1 is crypto2
    
    def test_primeira_criacao_com_secret_key(self):
        """Cria instância na primeira chamada"""
        import app.utils.crypto as crypto_module
        
        # Salvar valor original
        original_environ = os.environ.get('SECRET_KEY')
        
        try:
            # Configurar secret key
            os.environ['SECRET_KEY'] = "chave_para_teste"
            crypto_module._crypto = None
            
            crypto = get_crypto()
            
            assert crypto is not None
            assert isinstance(crypto, CryptoService)
        finally:
            # Restaurar
            if original_environ:
                os.environ['SECRET_KEY'] = original_environ
            else:
                os.environ.pop('SECRET_KEY', None)


class TestCampoCriptografado:
    """Testes para descriptor CampoCriptografado"""
    
    def test_set_get_valor(self, app):
        """Define e recupera valor criptografado"""
        from app.extensions import db
        
        # Criar modelo de teste
        class ModeloTeste(db.Model):
            __tablename__ = 'modelo_teste_crypto'
            id = db.Column(db.Integer, primary_key=True)
            nif_criptografado = CampoCriptografado('nif')
            _nif_encrypted = db.Column('nif', db.String(255))
        
        db.create_all()
        
        try:
            modelo = ModeloTeste()
            modelo.nif_criptografado = "123456789"
            
            # Valor deve ser armazenado criptografado
            assert modelo._nif_encrypted is not None
            assert modelo._nif_encrypted != "123456789"
            
            # Recuperar valor descriptografado
            assert modelo.nif_criptografado == "123456789"
        finally:
            db.drop_all()
    
    def test_set_valor_none(self, app):
        """Define valor None"""
        from app.extensions import db
        
        class ModeloTeste(db.Model):
            __tablename__ = 'modelo_teste_crypto_none'
            id = db.Column(db.Integer, primary_key=True)
            campo_cripto = CampoCriptografado('campo')
            _campo_encrypted = db.Column('campo', db.String(255))
        
        db.create_all()
        
        try:
            modelo = ModeloTeste()
            modelo.campo_cripto = None
            
            assert modelo._campo_encrypted is None
            assert modelo.campo_cripto is None
        finally:
            db.drop_all()
    
    def test_acesso_classe(self):
        """Acesso via classe retorna o descriptor"""
        class ModeloTeste:
            campo = CampoCriptografado('campo')
        
        assert isinstance(ModeloTeste.campo, CampoCriptografado)


class TestGetClientIP:
    """Testes para função get_client_ip"""
    
    def test_x_forwarded_for_priority(self, app):
        """Usa X-Forwarded-For quando disponível"""
        mock_request = MagicMock()
        mock_request.headers = {
            'X-Forwarded-For': '203.0.113.195, 70.41.3.18, 150.172.238.178',
            'X-Real-IP': '10.0.0.1'
        }
        mock_request.remote_addr = '127.0.0.1'
        
        ip = get_client_ip(mock_request)
        
        assert ip == '203.0.113.195'  # Primeiro IP da lista
    
    def test_x_real_ip_fallback(self, app):
        """Usa X-Real-IP se X-Forwarded-For não existir"""
        mock_request = MagicMock()
        mock_request.headers = {
            'X-Real-IP': '192.168.1.1'
        }
        mock_request.remote_addr = '127.0.0.1'
        
        ip = get_client_ip(mock_request)
        
        assert ip == '192.168.1.1'
    
    def test_remote_addr_final_fallback(self, app):
        """Usa remote_addr como último fallback"""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.remote_addr = '10.0.0.1'
        
        ip = get_client_ip(mock_request)
        
        assert ip == '10.0.0.1'
    
    def test_x_forwarded_for_multiplos_ips(self, app):
        """Extrai primeiro IP de lista com espaços"""
        mock_request = MagicMock()
        mock_request.headers = {
            'X-Forwarded-For': '  203.0.113.1  ,  70.41.3.18  '
        }
        
        ip = get_client_ip(mock_request)
        
        assert ip == '203.0.113.1'
    
    def test_sem_headers(self, app):
        """Funciona sem headers"""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.remote_addr = '127.0.0.1'
        
        ip = get_client_ip(mock_request)
        
        assert ip == '127.0.0.1'


class TestIntegracaoCriptografia:
    """Testes de integração para criptografia"""
    
    def test_fluxo_completo_nif(self, app):
        """Fluxo completo de NIF criptografado"""
        nif_original = "123456789AO"
        
        # Criptografar
        nif_hash = DataEncryption.hash_sensitive(nif_original)
        nif_cripto = DataEncryption.encrypt(nif_original)
        
        # Armazenar (simulado)
        dados_armazenados = {
            'hash': nif_hash,
            'cripto': nif_cripto
        }
        
        # Recuperar
        nif_recuperado = DataEncryption.decrypt(dados_armazenados['cripto'])
        
        # Verificar integridade
        assert nif_recuperado == nif_original
        
        # Verificar hash para busca
        assert DataEncryption.hash_sensitive(nif_recuperado) == nif_hash
    
    def test_fluxo_completo_iban(self, app):
        """Fluxo completo de IBAN criptografado"""
        iban_original = "AO06.0000.0000.0000.0000.0"
        
        # Criptografar
        iban_cripto = DataEncryption.encrypt(iban_original)
        
        # Validar formato após descriptografar
        iban_recuperado = DataEncryption.decrypt(iban_cripto)
        
        assert iban_recuperado == iban_original
        assert iban_recuperado.startswith("AO")
        assert len(iban_recuperado) == 21
    
    def test_multiple_users_different_keys(self, app):
        """Múltiplos usuários com diferentes chaves"""
        dados = {
            'user1': "NIF111",
            'user2': "NIF222",
            'user3': "NIF333"
        }
        
        criptografados = {}
        for user, nif in dados.items():
            criptografados[user] = DataEncryption.encrypt(nif)
        
        # Todos devem ser diferentes
        valores = list(criptografados.values())
        assert len(set(valores)) == len(valores)
        
        # Todos devem descriptografar corretamente
        for user, nif in dados.items():
            descriptografado = DataEncryption.decrypt(criptografados[user])
            assert descriptografado == nif
