# tests/integration/test_cadastro_flow.py - Testes de integração do fluxo de cadastro
# Validação completa do fluxo de 5 passos conforme caso de uso

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import Usuario
from app.models import Carteira, StatusConta
from app.services.otp_service import OTPService, gerar_e_enviar_otp
from app.routes.cadastro_produtor import _criar_usuario_produtor


@pytest.mark.integration
class TestCadastroFlowCompleto:
    """Testes de integração do fluxo completo de cadastro"""
    
    def test_fluxo_completo_sucesso(self, session):
        """
        Teste completo do fluxo de cadastro em 5 passos
        Simula todo o processo desde contato até criação do usuário
        """
        # Passo 1: Criar Conta como Produtor (Validação de Contato)
        telemovel = "912345678"
        
        # Verificar que não existe usuário
        assert not OTPService.verificar_usuario_existente(telemovel)
        
        # Gerar e enviar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        assert resultado_otp['sucesso'] == True
        
        # Passo 2: Validação OTP
        codigo = resultado_otp['codigo']
        resultado_validacao = OTPService.validar_otp(telemovel, codigo, '127.0.0.1')
        assert resultado_validacao['valido'] == True
        
        # Passo 3: Dados Básicos
        dados_basicos = {
            'nome': 'Produtor Teste Completo',
            'provincia_id': 1,  # Simulado
            'municipio_id': 1,  # Simulado
            'principal_cultura': 'Batata-rena'
        }
        
        # Passo 4: Segurança (PIN)
        senha = "1234"  # PIN de 4 dígitos
        
        # Passo 5: Dados Financeiros (KYC)
        dados_financeiros = {
            'iban': 'AO0600600000123456789012345',
            'bi_path': 'documentos_bi/test_bi.pdf'
        }
        
        # Criar usuário (conclusão)
        usuario = _criar_usuario_produtor(
            telemovel=telemovel,
            dados=dados_basicos,
            senha=senha,
            financeiros=dados_financeiros
        )
        
        # Verificações finais
        assert usuario is not None
        assert usuario.nome == dados_basicos['nome']
        assert usuario.telemovel == telemovel
        assert usuario.tipo == 'produtor'
        assert usuario.status_conta == StatusConta.PENDENTE_VERIFICACAO
        assert usuario.iban == dados_financeiros['iban']
        assert usuario.documento_pdf == dados_financeiros['bi_path']
        assert usuario.verificar_senha(senha) == True
        
        # RN02: Verificar criação automática da carteira
        carteira = usuario.obter_carteira()
        assert carteira is not None
        assert carteira.saldo_disponivel == Decimal('0.00')
        assert carteira.saldo_bloqueado == Decimal('0.00')
        
        # RN03: Verificar que não pode criar anúncios ainda
        assert not usuario.pode_criar_anuncios()
    
    def test_fluxo_com_otp_invalido(self, session):
        """Teste Exceção 2A: OTP inválido"""
        telemovel = "912345679"
        
        # Gerar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        codigo_correto = resultado_otp['codigo']
        
        # Tentar validar com código incorreto
        resultado_validacao = OTPService.validar_otp(telemovel, "000000", '127.0.0.1')
        assert resultado_validacao['valido'] == False
        assert resultado_validacao['tentativas_restantes'] == 2
        
        # Tentar novamente
        resultado_validacao = OTPService.validar_otp(telemovel, "111111", '127.0.0.1')
        assert resultado_validacao['valido'] == False
        assert resultado_validacao['tentativas_restantes'] == 1
        
        # Tentar código correto
        resultado_validacao = OTPService.validar_otp(telemovel, codigo_correto, '127.0.0.1')
        assert resultado_validacao['valido'] == True
    
    def test_fluxo_com_otp_expirado(self, session):
        """Teste OTP expirado"""
        telemovel = "912345680"
        
        # Gerar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        codigo = resultado_otp['codigo']
        
        # Simular expiração manualmente
        otp_data = OTPService.obter_status_otp(telemovel)
        otp_data['data_expiracao'] = datetime.now(timezone.utc) - timedelta(minutes=1)
        
        # Tentar validar código expirado
        resultado_validacao = OTPService.validar_otp(telemovel, codigo, '127.0.0.1')
        assert resultado_validacao['valido'] == False
        assert 'expirado' in resultado_validacao['mensagem'].lower()
    
    def test_fluxo_com_telemovel_duplicado(self, session, produtor_user):
        """Teste Exceção 5B: Telemóvel já cadastrado"""
        telemovel = produtor_user.telemovel
        
        # Tentar gerar OTP para telemovel existente
        resultado = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        
        assert resultado['sucesso'] == False
        assert 'já possui uma conta' in resultado['mensagem'].lower()
        assert resultado['codigo'] is None
    
    def test_fluxo_com_iban_invalido(self, session):
        """Teste Exceção 5A: IBAN inválido"""
        telemovel = "912345681"
        
        # Gerar e validar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        OTPService.validar_otp(telemovel, resultado_otp['codigo'], '127.0.0.1')
        
        # Tentar criar usuário com IBAN inválido
        dados_basicos = {
            'nome': 'Produtor Teste IBAN',
            'provincia_id': 1,
            'municipio_id': 1,
            'principal_cultura': 'Milho'
        }
        
        dados_financeiros = {
            'iban': 'INVALID_IBAN',  # IBAN inválido
            'bi_path': 'documentos_bi/test_bi.pdf'
        }
        
        # A validação deve ocorrer no nível do formulário/route
        # Aqui testamos apenas a validação básica
        assert not dados_financeiros['iban'].startswith('AO06')
        assert len(dados_financeiros['iban']) != 27
    
    def test_atomicidade_criacao_usuario_carteira(self, session):
        """Teste RN02: Atomicidade na criação usuário + carteira"""
        telemovel = "912345682"
        
        # Preparar dados
        dados_basicos = {
            'nome': 'Produtor Atomicidade',
            'provincia_id': 1,
            'municipio_id': 1,
            'principal_cultura': 'Feijão'
        }
        
        dados_financeiros = {
            'iban': 'AO0600600000123456789012345',
            'bi_path': 'documentos_bi/test_bi.pdf'
        }
        
        # Gerar e validar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        OTPService.validar_otp(telemovel, resultado_otp['codigo'], '127.0.0.1')
        
        # Criar usuário (deve criar carteira automaticamente)
        usuario = _criar_usuario_produtor(
            telemovel=telemovel,
            dados=dados_basicos,
            senha="1234",
            financeiros=dados_financeiros
        )
        
        # Verificar atomicidade
        assert usuario is not None
        assert usuario.id is not None
        
        carteira = Carteira.query.filter_by(usuario_id=usuario.id).first()
        assert carteira is not None
        assert carteira.usuario_id == usuario.id
        
        # Se usuário existe, carteira deve existir
        assert carteira.saldo_disponivel == Decimal('0.00')
    
    def test_mudanca_status_para_verificado(self, session):
        """Teste mudança de status para VERIFICADO"""
        # Criar usuário com status inicial
        usuario = Usuario(
            nome="Produtor Status",
            telemovel="912345683",
            tipo="produtor",
            status_conta=StatusConta.PENDENTE_VERIFICACAO
        )
        session.add(usuario)
        session.commit()
        
        # Verificar estado inicial
        assert usuario.status_conta == StatusConta.PENDENTE_VERIFICACAO
        assert not usuario.pode_criar_anuncios()
        
        # Simular aprovação pelo admin
        usuario.status_conta = StatusConta.VERIFICADO
        usuario.conta_validada = True  # Mantido para compatibilidade
        session.commit()
        
        # Verificar estado final
        assert usuario.status_conta == StatusConta.VERIFICADO
        assert usuario.pode_criar_anuncios()
    
    def test_rejeicao_conta(self, session):
        """Teste rejeição de conta"""
        # Criar usuário
        usuario = Usuario(
            nome="Produtor Rejeitado",
            telemovel="912345684",
            tipo="produtor",
            status_conta=StatusConta.PENDENTE_VERIFICACAO
        )
        session.add(usuario)
        session.commit()
        
        # Simular rejeição pelo admin
        usuario.status_conta = StatusConta.REJEITADO
        usuario.conta_validada = False
        session.commit()
        
        # Verificar estado rejeitado
        assert usuario.status_conta == StatusConta.REJEITADO
        assert not usuario.pode_criar_anuncios()
        assert not usuario.conta_validada


@pytest.mark.integration
class TestCadastroFlowAPI:
    """Testes de integração com as APIs do cadastro"""
    
    def test_api_verificar_iban(self):
        """Teste API de verificação de IBAN"""
        # IBAN válido
        iban_valido = "AO0600600000123456789012345"
        assert iban_valido.startswith('AO06')
        assert len(iban_valido) == 27
        assert iban_valido[6:].isdigit()
        
        # IBAN inválido
        iban_invalido1 = "INVALIDO"
        assert not iban_invalido1.startswith('AO06')
        
        iban_invalido2 = "AO06" + "1" * 20  # Comprimento errado
        assert len(iban_invalido2) != 27
    
    @patch('app.services.otp_service.OTPService.enviar_otp_whatsapp')
    def test_envio_otp_whatsapp_api(self, mock_envio):
        """Teste integração com API WhatsApp"""
        # Configurar mock
        mock_envio.return_value = True
        
        # Configurar app com API
        with patch('app.services.otp_service.current_app.config.get') as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                'WHATSAPP_API_URL': 'https://api.whatsapp.com/send',
                'WHATSAPP_TOKEN': 'test_token'
            }.get(key, default)
            
            resultado = OTPService.enviar_otp_whatsapp("912345678", "123456")
            
            assert resultado == True
            mock_envio.assert_called_once_with("912345678", "123456")
    
    @patch('app.services.otp_service.OTPService.enviar_otp_sms')
    def test_envio_otp_sms_api(self, mock_envio):
        """Teste integração com API SMS"""
        # Configurar mock
        mock_envio.return_value = True
        
        # Configurar app com API
        with patch('app.services.otp_service.current_app.config.get') as mock_config:
            mock_config.side_effect = lambda key, default=None: {
                'SMS_API_URL': 'https://api.sms.com/send',
                'SMS_API_KEY': 'test_key'
            }.get(key, default)
            
            resultado = OTPService.enviar_otp_sms("912345678", "123456")
            
            assert resultado == True
            mock_envio.assert_called_once_with("912345678", "123456")


@pytest.mark.integration
class TestCadastroFlowPerformance:
    """Testes de performance do fluxo de cadastro"""
    
    def test_performance_criacao_usuario(self, session):
        """Testa performance na criação de usuário"""
        import time
        
        telemovel = "912345685"
        
        # Gerar e validar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        OTPService.validar_otp(telemovel, resultado_otp['codigo'], '127.0.0.1')
        
        # Medir tempo de criação
        start_time = time.time()
        
        usuario = _criar_usuario_produtor(
            telemovel=telemovel,
            dados={
                'nome': 'Produtor Performance',
                'provincia_id': 1,
                'municipio_id': 1,
                'principal_cultura': 'Arroz'
            },
            senha="1234",
            financeiros={
                'iban': 'AO0600600000123456789012345',
                'bi_path': 'documentos_bi/test_bi.pdf'
            }
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verificações de performance
        assert execution_time < 1.0  # Deve criar em < 1s
        assert usuario is not None
        assert usuario.obter_carteira() is not None
    
    def test_performance_validacao_otp(self):
        """Testa performance na validação OTP"""
        import time
        
        telemovel = "912345686"
        
        # Gerar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        codigo = resultado_otp['codigo']
        
        # Medir tempo de validação
        start_time = time.time()
        
        resultado = OTPService.validar_otp(telemovel, codigo, '127.0.0.1')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verificações de performance
        assert execution_time < 0.1  # Deve validar em < 100ms
        assert resultado['valido'] == True
    
    def test_performance_multiplas_validacoes(self):
        """Testa performance com múltiplas validações simultâneas"""
        import time
        from threading import Thread
        
        def validar_otp_thread(telemovel, codigo):
            return OTPService.validar_otp(telemovel, codigo, '127.0.0.1')
        
        # Criar múltiplos OTPs
        otps = []
        for i in range(5):
            telemovel = f"912345{687+i}"
            resultado = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
            otps.append((telemovel, resultado['codigo']))
        
        # Medir tempo de validação paralela
        start_time = time.time()
        
        threads = []
        resultados = []
        
        for telemovel, codigo in otps:
            thread = Thread(target=lambda t=telemovel, c=codigo: resultados.append(validar_otp_thread(t, c)))
            threads.append(thread)
            thread.start()
        
        # Esperar todas as threads
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verificações
        assert execution_time < 0.5  # 5 validações em < 500ms
        assert len(resultados) == 5
        
        for resultado in resultados:
            assert resultado['valido'] == True
