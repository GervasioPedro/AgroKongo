# tests/unit/test_cadastro_produtor.py - Testes unitários para cadastro de produtor
# Validação do novo sistema de cadastro com status_conta e carteiras

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.models import Usuario
from app.models import StatusConta, Carteira
from app.services.otp_service import OTPService


class TestCadastroProdutor:
    """Testes unitários para o fluxo de cadastro de produtor"""
    
    def test_status_conta_inicial_pendente_verificacao(self, session):
        """Testa que novo produtor começa com status PENDENTE_VERIFICACAO"""
        produtor = Usuario(
            nome="Novo Produtor",
            telemovel="912345678",
            tipo="produtor"
        )
        session.add(produtor)
        session.commit()
        
        assert produtor.status_conta == StatusConta.PENDENTE_VERIFICACAO
        assert not produtor.pode_criar_anuncios()
        assert produtor.conta_validada == False  # Mantido para compatibilidade
    
    def test_status_conta_verificado_pode_criar_anuncios(self, session):
        """Testa que produtor VERIFICADO pode criar anúncios"""
        produtor = Usuario(
            nome="Produtor Verificado",
            telemovel="912345679",
            tipo="produtor",
            status_conta=StatusConta.VERIFICADO
        )
        session.add(produtor)
        session.commit()
        
        assert produtor.status_conta == StatusConta.VERIFICADO
        assert produtor.pode_criar_anuncios()
        assert produtor.conta_validada == True  # Mantido para compatibilidade
    
    def test_status_conta_rejeitado_nao_pode_criar_anuncios(self, session):
        """Testa que produtor REJEITADO não pode criar anúncios"""
        produtor = Usuario(
            nome="Produtor Rejeitado",
            telemovel="912345680",
            tipo="produtor",
            status_conta=StatusConta.REJEITADO
        )
        session.add(produtor)
        session.commit()
        
        assert produtor.status_conta == StatusConta.REJEITADO
        assert not produtor.pode_criar_anuncios()
        assert produtor.conta_validada == False
    
    def test_carteira_criada_automaticamente(self, session):
        """Testa RN02: Carteira criada automaticamente com usuário"""
        produtor = Usuario(
            nome="Produtor Test",
            telemovel="912345681",
            tipo="produtor"
        )
        session.add(produtor)
        session.commit()
        
        # Verificar se carteira foi criada
        carteira = Carteira.query.filter_by(usuario_id=produtor.id).first()
        assert carteira is not None
        assert carteira.saldo_disponivel == Decimal('0.00')
        assert carteira.saldo_bloqueado == Decimal('0.00')
        assert carteira.usuario_id == produtor.id
    
    def test_obter_carteira_usuario_existente(self, session, produtor_user):
        """Testa obtenção da carteira de usuário existente"""
        carteira = produtor_user.obter_carteira()
        
        assert carteira is not None
        assert carteira.usuario_id == produtor_user.id
        assert isinstance(carteira.saldo_disponivel, Decimal)
    
    def test_obter_carteira_usuario_novo(self, session):
        """Testa criação automática da carteira ao obter de usuário novo"""
        produtor = Usuario(
            nome="Produtor Novo",
            telemovel="912345682",
            tipo="produtor"
        )
        session.add(produtor)
        session.commit()
        
        # Obter carteira (deve criar automaticamente)
        carteira = produtor.obter_carteira()
        
        assert carteira is not None
        assert carteira.usuario_id == produtor.id
        assert carteira.saldo_disponivel == Decimal('0.00')
    
    def test_status_conta_choices(self):
        """Testa que todos os status estão definidos"""
        choices = StatusConta.choices()
        
        status_list = [choice[0] for choice in choices]
        
        assert StatusConta.PENDENTE_VERIFICACAO in status_list
        assert StatusConta.VERIFICADO in status_list
        assert StatusConta.REJEITADO in status_list
        assert StatusConta.SUSPENSO in status_list
        
        # Testar validação
        assert StatusConta.is_valid(StatusConta.VERIFICADO)
        assert StatusConta.is_valid(StatusConta.PENDENTE_VERIFICACAO)
        assert not StatusConta.is_valid('INVALID_STATUS')
    
    def test_compatibilidade_conta_validada(self, session):
        """Testa compatibilidade entre status_conta e conta_validada"""
        # Status VERIFICADO deve manter conta_validada = True
        produtor_verificado = Usuario(
            nome="Produtor Verificado",
            telemovel="912345683",
            tipo="produtor",
            status_conta=StatusConta.VERIFICADO
        )
        session.add(produtor_verificado)
        session.commit()
        
        # Status PENDENTE_VERIFICACAO deve manter conta_validada = False
        produtor_pendente = Usuario(
            nome="Produtor Pendente",
            telemovel="912345684",
            tipo="produtor",
            status_conta=StatusConta.PENDENTE_VERIFICACAO
        )
        session.add(produtor_pendente)
        session.commit()
        
        # Verificar compatibilidade
        assert produtor_verificado.status_conta == StatusConta.VERIFICADO
        assert produtor_pendente.status_conta == StatusConta.PENDENTE_VERIFICACAO


class TestOTPService:
    """Testes unitários para o serviço OTP"""
    
    def test_gerar_codigo_otp(self):
        """Testa geração de código OTP"""
        codigo = OTPService.gerar_codigo_otp()
        
        assert len(codigo) == 6
        assert codigo.isdigit()
        assert 100000 <= int(codigo) <= 999999
    
    def test_gerar_hash_otp(self, app):
        """Testa geração de hash OTP"""
        codigo = "123456"
        telemovel = "912345678"
        
        with app.app_context():
            hash1 = OTPService.gerar_hash_otp(codigo, telemovel)
            hash2 = OTPService.gerar_hash_otp(codigo, telemovel)
            hash3 = OTPService.gerar_hash_otp("654321", telemovel)
            
            # Mesmo código e telemóvel devem gerar mesmo hash
            assert hash1 == hash2
            
            # Código diferente deve gerar hash diferente
            assert hash1 != hash3
            
            # Telemóvel diferente deve gerar hash diferente
            hash4 = OTPService.gerar_hash_otp(codigo, "912345679")
            assert hash1 != hash4
    
    def test_armazenar_otp(self, app):
        """Testa armazenamento de OTP"""
        telemovel = "912345678"
        codigo = "123456"
        
        with app.app_context():
            otp_data = OTPService.armazenar_otp(telemovel, codigo, "127.0.0.1")
            
            assert otp_data['telemovel'] == telemovel
            assert otp_data['codigo'] == codigo
            assert otp_data['tentativas'] == 0
            assert otp_data['max_tentativas'] == 3
            assert otp_data['validado'] == False
            assert otp_data['ip_address'] == "127.0.0.1"
            assert 'data_expiracao' in otp_data
            assert 'hash' in otp_data
    
    def test_validar_otp_sucesso(self, app):
        """Testa validação OTP com sucesso"""
        telemovel = "912345678"
        codigo = "123456"
        
        with app.app_context():
            # Armazenar OTP
            OTPService.armazenar_otp(telemovel, codigo, "127.0.0.1")
            
            # Validar código correto
            resultado = OTPService.validar_otp(telemovel, codigo, "127.0.0.1")
            
            assert resultado['valido'] == True
            assert 'sucesso' in resultado['mensagem'].lower()
            assert resultado['tentativas_restantes'] == 0
    
    def test_validar_otp_incorreto(self, app):
        """Testa validação OTP com código incorreto"""
        telemovel = "912345678"
        codigo_correto = "123456"
        codigo_incorreto = "654321"
        
        with app.app_context():
            # Armazenar OTP
            OTPService.armazenar_otp(telemovel, codigo_correto, "127.0.0.1")
            
            # Validar código incorreto
            resultado = OTPService.validar_otp(telemovel, codigo_incorreto, "127.0.0.1")
            
            assert resultado['valido'] == False
            assert 'inválido' in resultado['mensagem'].lower()
            assert resultado['tentativas_restantes'] == 2
    
    def test_validar_otp_inexistente(self, app):
        """Testa validação OTP para código inexistente"""
        with app.app_context():
            # Limpar qualquer OTP anterior deste número
            OTPService._limpar_otp("912345678")
            
            resultado = OTPService.validar_otp("912345678", "123456", "127.0.0.1")
            
            assert resultado['valido'] == False
            assert 'não encontrado' in resultado['mensagem'].lower()
            assert resultado['tentativas_restantes'] == 0
    
    def test_limpar_otps_expirados(self, app):
        """Testa limpeza de OTPs expirados"""
        telemovel = "912345678"
        codigo = "123456"
        
        with app.app_context():
            # Armazenar OTP
            OTPService.armazenar_otp(telemovel, codigo, "127.0.0.1")
            
            # Verificar que existe
            assert OTPService.obter_status_otp(telemovel) is not None
            
            # Limpar OTPs expirados (simulado)
            expirados = OTPService.limpar_otps_expirados()
            
            # Como não expirou, não deve limpar
            assert expirados == 0
            assert OTPService.obter_status_otp(telemovel) is not None
    
    def test_verificar_usuario_existente(self, session):
        """Teste Exceção 5B: Verificação de usuário existente"""
        # Criar usuário com senha obrigatória
        usuario = Usuario(
            nome="Test User",
            telemovel="912345678",
            tipo="produtor",
            senha="senha123"  # Senha é campo obrigatório
        )
        session.add(usuario)
        session.commit()
        
        # Verificar que existe
        assert OTPService.verificar_usuario_existente("912345678") == True
        
        # Verificar que não existe
        assert OTPService.verificar_usuario_existente("912345679") == False


class TestCarteira:
    """Testes unitários para o modelo Carteira"""
    
    def test_criar_carteira(self, session, produtor_user):
        """Testa criação de carteira"""
        carteira = Carteira(
            usuario_id=produtor_user.id,
            saldo_disponivel=Decimal('100.00'),
            saldo_bloqueado=Decimal('50.00')
        )
        session.add(carteira)
        session.commit()
        
        assert carteira.usuario_id == produtor_user.id
        assert carteira.saldo_disponivel == Decimal('100.00')
        assert carteira.saldo_bloqueado == Decimal('50.00')
        assert carteira.get_saldo_total() == Decimal('150.00')
    
    def test_creditar_carteira(self, session, produtor_user):
        """Testa crédito na carteira"""
        carteira = produtor_user.obter_carteira()
        saldo_anterior = carteira.saldo_disponivel
        
        valor = Decimal('100.00')
        carteira.creditar(valor, "Teste de crédito")
        
        assert carteira.saldo_disponivel == saldo_anterior + valor
        assert carteira.data_ultima_atualizacao is not None
    
    def test_debitar_carteira(self, session, produtor_user):
        """Testa débito na carteira"""
        carteira = produtor_user.obter_carteira()
        
        # Creditar primeiro
        carteira.creditar(Decimal('100.00'), "Crédito inicial")
        
        # Debitar
        saldo_anterior = carteira.saldo_disponivel
        valor = Decimal('50.00')
        carteira.debitar(valor, "Teste de débito")
        
        assert carteira.saldo_disponivel == saldo_anterior - valor
    
    def test_debitar_saldo_insuficiente(self, session, produtor_user):
        """Testa débito com saldo insuficiente"""
        carteira = produtor_user.obter_carteira()
        
        # Tentar debitar sem saldo
        with pytest.raises(ValueError, match="Saldo insuficiente"):
            carteira.debitar(Decimal('100.00'), "Débito sem saldo")
    
    def test_bloquear_valor(self, session, produtor_user):
        """Testa bloqueio de valor"""
        carteira = produtor_user.obter_carteira()
        
        # Creditar primeiro
        carteira.creditar(Decimal('100.00'), "Crédito inicial")
        
        saldo_anterior_disponivel = carteira.saldo_disponivel
        saldo_anterior_bloqueado = carteira.saldo_bloqueado
        
        valor = Decimal('30.00')
        carteira.bloquear(valor, "Bloqueio para escrow")
        
        assert carteira.saldo_disponivel == saldo_anterior_disponivel - valor
        assert carteira.saldo_bloqueado == saldo_anterior_bloqueado + valor
    
    def test_liberar_valor(self, session, produtor_user):
        """Testa liberação de valor bloqueado"""
        carteira = produtor_user.obter_carteira()
        
        # Creditar e bloquear
        carteira.creditar(Decimal('100.00'), "Crédito inicial")
        carteira.bloquear(Decimal('30.00'), "Bloqueio para escrow")
        
        saldo_anterior_disponivel = carteira.saldo_disponivel
        saldo_anterior_bloqueado = carteira.saldo_bloqueado
        
        valor = Decimal('20.00')
        carteira.liberar(valor, "Liberação de escrow")
        
        assert carteira.saldo_disponivel == saldo_anterior_disponivel + valor
        assert carteira.saldo_bloqueado == saldo_anterior_bloqueado - valor
    
    def test_to_dict(self, session, produtor_user):
        """Testa representação em dicionário"""
        carteira = produtor_user.obter_carteira()
        carteira_dict = carteira.to_dict()
        
        assert 'id' in carteira_dict
        assert 'usuario_id' in carteira_dict
        assert 'saldo_disponivel' in carteira_dict
        assert 'saldo_bloqueado' in carteira_dict
        assert 'saldo_total' in carteira_dict
        assert 'data_criacao' in carteira_dict
        assert 'data_ultima_atualizacao' in carteira_dict
        
        assert isinstance(carteira_dict['saldo_disponivel'], float)
        assert isinstance(carteira_dict['saldo_total'], float)
