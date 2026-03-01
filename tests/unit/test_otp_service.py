# tests/unit/test_otp_service.py - Testes unitários específicos para OTP
# Validação completa do sistema de verificação OTP

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.services.otp_service import OTPService, gerar_e_enviar_otp, reenviar_otp


class TestOTPServiceUnit:
    """Testes unitários detalhados do serviço OTP"""
    
    def test_gerar_codigo_otp_tamanho_padrao(self):
        """Testa geração de código com tamanho padrão (6 dígitos)"""
        codigo = OTPService.gerar_codigo_otp()
        
        assert len(codigo) == 6
        assert codigo.isdigit()
        assert 100000 <= int(codigo) <= 999999
    
    def test_gerar_codigo_otp_tamanho_customizado(self):
        """Testa geração de código com tamanho customizado"""
        codigo_4 = OTPService.gerar_codigo_otp(4)
        codigo_8 = OTPService.gerar_codigo_otp(8)
        
        assert len(codigo_4) == 4
        assert len(codigo_8) == 8
        assert codigo_4.isdigit()
        assert codigo_8.isdigit()
    
    def test_gerar_hash_otp_consistencia(self):
        """Testa consistência do hash OTP"""
        codigo = "123456"
        telemovel = "912345678"
        
        hash1 = OTPService.gerar_hash_otp(codigo, telemovel)
        hash2 = OTPService.gerar_hash_otp(codigo, telemovel)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length
        assert hash1 != codigo  # Hash não é igual ao código original
    
    def test_gerar_hash_otp_unicidade(self):
        """Testa unicidade do hash para diferentes entradas"""
        telemovel = "912345678"
        
        hash1 = OTPService.gerar_hash_otp("123456", telemovel)
        hash2 = OTPService.gerar_hash_otp("654321", telemovel)
        hash3 = OTPService.gerar_hash_otp("123456", "912345679")
        
        assert hash1 != hash2  # Código diferente
        assert hash1 != hash3  # Telemóvel diferente
        assert hash2 != hash3  # Ambos diferentes
    
    def test_armazenar_otp_dados_completos(self):
        """Testa armazenamento com todos os metadados"""
        telemovel = "912345678"
        codigo = "123456"
        ip = "192.168.1.1"
        
        otp_data = OTPService.armazenar_otp(telemovel, codigo, ip)
        
        # Verificar campos obrigatórios
        assert 'hash' in otp_data
        assert 'codigo' in otp_data
        assert 'telemovel' in otp_data
        assert 'data_criacao' in otp_data
        assert 'data_expiracao' in otp_data
        assert 'tentativas' in otp_data
        assert 'max_tentativas' in otp_data
        assert 'ip_address' in otp_data
        assert 'validado' in otp_data
        
        # Verificar valores
        assert otp_data['telemovel'] == telemovel
        assert otp_data['codigo'] == codigo
        assert otp_data['tentativas'] == 0
        assert otp_data['max_tentativas'] == 3
        assert otp_data['validado'] == False
        assert otp_data['ip_address'] == ip
        
        # Verificar tempo de expiração (10 minutos)
        expiracao = otp_data['data_expiracao']
        criacao = otp_data['data_criacao']
        assert expiracao > criacao
        assert expiracao - criacao == timedelta(minutes=10)
    
    def test_validar_otp_sucesso_limpeza(self):
        """Testa que OTP válido é removido após validação"""
        telemovel = "912345678"
        codigo = "123456"
        
        # Armazenar OTP
        OTPService.armazenar_otp(telemovel, codigo, "127.0.0.1")
        
        # Verificar que existe
        assert OTPService.obter_status_otp(telemovel) is not None
        
        # Validar com sucesso
        resultado = OTPService.validar_otp(telemovel, codigo, "127.0.0.1")
        
        # Verificar resultado
        assert resultado['valido'] == True
        
        # Verificar que foi limpo
        assert OTPService.obter_status_otp(telemovel) is None
    
    def test_validar_otp_tentativas_excedidas(self):
        """Teste Exceção 2A: Tentativas máximas excedidas"""
        telemovel = "912345678"
        codigo_correto = "123456"
        codigo_incorreto = "654321"
        
        # Armazenar OTP
        OTPService.armazenar_otp(telemovel, codigo_correto, "127.0.0.1")
        
        # Fazer 3 tentativas incorretas
        for i in range(3):
            resultado = OTPService.validar_otp(telemovel, codigo_incorreto, "127.0.0.1")
            assert resultado['valido'] == False
            assert resultado['tentativas_restantes'] == 2 - i
        
        # Tentativa 4 (depois de excedido)
        resultado = OTPService.validar_otp(telemovel, codigo_correto, "127.0.0.1")
        assert resultado['valido'] == False
        assert 'não encontrado' in resultado['mensagem'].lower()
        assert resultado['tentativas_restantes'] == 0
    
    def test_validar_otp_expirado(self):
        """Teste OTP expirado"""
        telemovel = "912345678"
        codigo = "123456"
        
        # Armazenar OTP
        otp_data = OTPService.armazenar_otp(telemovel, codigo, "127.0.0.1")
        
        # Simular expiração manualmente
        otp_data['data_expiracao'] = datetime.now(timezone.utc) - timedelta(minutes=1)
        OTPService._otp_cache[telemovel] = otp_data
        
        # Tentar validar
        resultado = OTPService.validar_otp(telemovel, codigo, "127.0.0.1")
        
        assert resultado['valido'] == False
        assert 'expirado' in resultado['mensagem'].lower()
        assert resultado['tentativas_restantes'] == 0
    
    def test_envio_sms_simulado(self):
        """Teste envio SMS em modo simulado"""
        resultado = OTPService.enviar_otp_sms("912345678", "123456")
        
        assert resultado == True  # Modo simulado sempre retorna True
    
    def test_envio_whatsapp_simulado(self):
        """Teste envio WhatsApp em modo simulado"""
        resultado = OTPService.enviar_otp_whatsapp("912345678", "123456")
        
        assert resultado == True  # Modo simulado sempre retorna True
    
    @patch('requests.post')
    def test_envio_sms_api_real(self, mock_post):
        """Teste envio SMS com API real (mock)"""
        # Configurar mock
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "SMS sent successfully"
        
        # Configurar app com API
        with patch('app.services.otp_service.current_app.config.get') as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                'SMS_API_URL': 'https://api.sms.com/send',
                'SMS_API_KEY': 'test_key'
            }.get(key, default)
            
            resultado = OTPService.enviar_otp_sms("912345678", "123456")
            
            assert resultado == True
            mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_envio_whatsapp_api_real(self, mock_post):
        """Teste envio WhatsApp com API real (mock)"""
        # Configurar mock
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "WhatsApp sent successfully"
        
        # Configurar app com API
        with patch('app.services.otp_service.current_app.config.get') as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                'WHATSAPP_API_URL': 'https://api.whatsapp.com/send',
                'WHATSAPP_TOKEN': 'test_token'
            }.get(key, default)
            
            resultado = OTPService.enviar_otp_whatsapp("912345678", "123456")
            
            assert resultado == True
            mock_post.assert_called_once()
    
    def test_limpar_otps_expirados_vazio(self):
        """Teste limpeza quando não há OTPs expirados"""
        expirados = OTPService.limpar_otps_expirados()
        assert expirados == 0
    
    def test_limpar_otps_expirados_com_dados(self):
        """Teste limpeza com OTPs expirados"""
        # Criar OTP expirado
        telemovel = "912345678"
        otp_data = OTPService.armazenar_otp(telemovel, "123456", "127.0.0.1")
        
        # Forçar expiração
        otp_data['data_expiracao'] = datetime.now(timezone.utc) - timedelta(minutes=1)
        OTPService._otp_cache[telemovel] = otp_data
        
        # Limpar expirados
        expirados = OTPService.limpar_otps_expirados()
        
        assert expirados == 1
        assert OTPService.obter_status_otp(telemovel) is None


class TestGerarEnviarOTP:
    """Testes para função gerar_e_enviar_otp"""
    
    def test_gerar_enviar_sucesso(self):
        """Teste geração e envio com sucesso"""
        resultado = gerar_e_enviar_otp("912345678", "whatsapp", "127.0.0.1")
        
        assert resultado['sucesso'] == True
        assert 'enviado' in resultado['mensagem'].lower()
        assert 'codigo' in resultado
        assert 'expiracao' in resultado
        assert 'max_tentativas' in resultado
        assert resultado['max_tentativas'] == 3
    
    def test_gerar_enviar_usuario_existente(self, session):
        """Teste Exceção 5B: Usuário já existente"""
        # Criar usuário
        usuario = Usuario(
            nome="Test User",
            telemovel="912345678",
            tipo="produtor"
        )
        session.add(usuario)
        session.commit()
        
        # Tentar gerar OTP para mesmo telemóvel
        resultado = gerar_e_enviar_otp("912345678", "whatsapp", "127.0.0.1")
        
        assert resultado['sucesso'] == False
        assert 'já possui uma conta' in resultado['mensagem'].lower()
        assert resultado['codigo'] is None
    
    def test_gerar_enviar_canal_sms(self):
        """Teste envio via canal SMS"""
        resultado = gerar_e_enviar_otp("912345678", "sms", "127.0.0.1")
        
        assert resultado['sucesso'] == True
        assert 'SMS' in resultado['mensagem']
    
    def test_reenviar_otp(self):
        """Teste reenvio de OTP"""
        telemovel = "912345678"
        
        # Gerar OTP inicial
        resultado1 = gerar_e_enviar_otp(telemovel, "whatsapp", "127.0.0.1")
        codigo1 = resultado1['codigo']
        
        # Reenviar OTP
        resultado2 = reenviar_otp(telemovel, "whatsapp", "127.0.0.1")
        codigo2 = resultado2['codigo']
        
        assert resultado2['sucesso'] == True
        assert codigo2 != codigo1  # Código deve ser diferente


class TestOTPServiceSeguranca:
    """Testes de segurança do serviço OTP"""
    
    def test_hash_seguro(self):
        """Teste que hash é seguro (não reversível)"""
        codigo = "123456"
        telemovel = "912345678"
        
        hash_otp = OTPService.gerar_hash_otp(codigo, telemovel)
        
        # Hash não deve conter o código original
        assert codigo not in hash_otp
        assert telemovel not in hash_otp
        
        # Hash deve ser consistente
        hash2 = OTPService.gerar_hash_otp(codigo, telemovel)
        assert hash_otp == hash2
    
    def test_limpeza_apos_validacao(self):
        """Teste que dados são limpos após validação bem-sucedida"""
        telemovel = "912345678"
        codigo = "123456"
        
        # Armazenar OTP
        OTPService.armazenar_otp(telemovel, codigo, "127.0.0.1")
        
        # Validar
        resultado = OTPService.validar_otp(telemovel, codigo, "127.0.0.1")
        
        # Verificar limpeza
        assert resultado['valido'] == True
        assert OTPService.obter_status_otp(telemovel) is None
    
    def test_isolamento_entre_usuarios(self):
        """Teste isolamento entre diferentes usuários"""
        telemovel1 = "912345678"
        telemovel2 = "912345679"
        codigo = "123456"
        
        # Armazenar OTP para ambos usuários
        OTPService.armazenar_otp(telemovel1, codigo, "127.0.0.1")
        OTPService.armazenar_otp(telemovel2, codigo, "127.0.0.1")
        
        # Validar apenas para usuário 1
        resultado1 = OTPService.validar_otp(telemovel1, codigo, "127.0.0.1")
        
        # Usuário 1 deve ter OTP validado e limpo
        assert resultado1['valido'] == True
        assert OTPService.obter_status_otp(telemovel1) is None
        
        # Usuário 2 ainda deve ter OTP disponível
        assert OTPService.obter_status_otp(telemovel2) is not None
    
    def test_protecao_contra_brute_force(self):
        """Teste proteção contra brute force"""
        telemovel = "912345678"
        codigo_correto = "123456"
        
        # Armazenar OTP
        OTPService.armazenar_otp(telemovel, codigo_correto, "127.0.0.1")
        
        # Tentativas incorretas
        tentativas_restantes = 3
        for i in range(5):  # Mais que o limite
            resultado = OTPService.validar_otp(telemovel, "000000", "127.0.0.1")
            tentativas_restantes -= 1
            
            if tentativas_restantes > 0:
                assert resultado['valido'] == False
                assert resultado['tentativas_restantes'] == tentativas_restantes
            else:
                assert resultado['valido'] == False
                assert 'não encontrado' in resultado['mensagem'].lower()
                break
        
        # Após exceder tentativas, nem código correto funciona
        resultado_final = OTPService.validar_otp(telemovel, codigo_correto, "127.0.0.1")
        assert resultado_final['valido'] == False
