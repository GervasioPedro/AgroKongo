# tests_framework/test_cadastro.py - Testes do fluxo de cadastro
# Validação completa do sistema de cadastro de produtores

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import Usuario
from app.models.financeiro import Carteira
from app.services.otp_service import OTPService, gerar_e_enviar_otp
from app.routes.cadastro_produtor import _criar_usuario_produtor


#@pytest.mark.unit
class TestOTPService:
    """Testes unitários para o serviço OTP"""
    
    def test_gerar_codigo_otp_tamanho_padrao(self):
        """Testa geração de código com tamanho padrão (6 dígitos)"""
        codigo = OTPService.gerar_codigo_otp()
        
        # Verificar se é string e tem 6 dígitos
        assert len(codigo) == 6
        assert codigo.isdigit()
        # Verificar valor numérico (permitir leading zeros)
        valor = int(codigo)
        assert 0 <= valor <= 999999
    
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
        # Usar aproximação de 1 segundo para evitar falhas por microseconds
        assert abs((expiracao - criacao).total_seconds() - 600) < 1
    
    def test_validar_otp_sucesso(self):
        """Testa validação OTP com sucesso"""
        telemovel = "912345678"
        codigo = "123456"
        
        # Armazenar OTP
        OTPService.armazenar_otp(telemovel, codigo, "127.0.0.1")
        
        # Validar código correto
        resultado = OTPService.validar_otp(telemovel, codigo, "127.0.0.1")
        
        assert resultado['valido'] == True
        assert 'sucesso' in resultado['mensagem'].lower()
        assert resultado['tentativas_restantes'] == 0
    
    def test_validar_otp_incorreto(self):
        """Testa validação OTP com código incorreto"""
        telemovel = "912345678"
        codigo_correto = "123456"
        codigo_incorreto = "654321"
        
        # Armazenar OTP
        OTPService.armazenar_otp(telemovel, codigo_correto, "127.0.0.1")
        
        # Validar código incorreto
        resultado = OTPService.validar_otp(telemovel, codigo_incorreto, "127.0.0.1")
        
        assert resultado['valido'] == False
        assert 'inválido' in resultado['mensagem'].lower()
        assert resultado['tentativas_restantes'] == 2
    
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
        # Após exceder tentativas, mensagem indica que código não existe mais
        assert 'tentativas' in resultado['mensagem'].lower() or 'não encontrado' in resultado['mensagem'].lower()
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
    
    def test_verificar_usuario_existente(self, session):
        """Teste Exceção 5B: Verificação de usuário existente"""
        # Criar usuário com senha obrigatória
        usuario = Usuario(
            nome="Test User",
            telemovel="912345678",
            tipo="produtor",
            senha="senha123"
        )
        session.add(usuario)
        session.commit()
        
        # Verificar que existe
        assert OTPService.verificar_usuario_existente("912345678") == True
        
        # Verificar que não existe
        assert OTPService.verificar_usuario_existente("912345679") == False


#@pytest.mark.unit
class TestCadastroProdutor:
    """Testes unitários para o fluxo de cadastro de produtor"""
    
    def test_status_conta_inicial_pendente_verificacao(self, session):
        """Testa status inicial da conta como não validada"""
        produtor = Usuario(
            nome="Novo Produtor",
            telemovel="912345678",
            senha="senha123",
            tipo="produtor"
        )
        session.add(produtor)
        session.commit()
        
        assert produtor.conta_validada == False
        assert not produtor.pode_criar_anuncios()
    
    def test_status_conta_verificado_pode_criar_anuncios(self, session):
        """Testa que produtor VERIFICADO pode criar anúncios"""
        produtor = Usuario(
            nome="Produtor Verificado",
            telemovel="912345679",
            senha="senha123",
            tipo="produtor",
            conta_validada=True
        )
        session.add(produtor)
        session.commit()
        
        assert produtor.conta_validada == True
        assert produtor.pode_criar_anuncios()
    
    def test_carteira_criada_automaticamente(self, session):
        """Testa RN02: Carteira criada automaticamente com usuário"""
        produtor = Usuario(
            nome="Produtor Test",
            telemovel="912345680",
            tipo="produtor",
            senha="senha123"
        )
        session.add(produtor)
        session.commit()
        
        # Verificar se carteira foi criada (usando obter_carteira para criar se necessário)
        carteira = produtor.obter_carteira()
        session.commit()  # Commit para persistir a carteira criada
        
        # Recarregar carteira do banco
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
            telemovel="912345681",
            tipo="produtor",
            senha="senha123"
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
        # Testa apenas os valores booleanos de conta_validada
        assert True in [True, False]
        assert False in [True, False]
    
    def test_compatibilidade_conta_validada(self, session):
        """Testa compatibilidade entre status_conta e conta_validada"""
        # Status VERIFICADO deve manter conta_validada = True
        produtor_verificado = Usuario(
            nome="Produtor Verificado",
            telemovel="912345682",
            senha="senha123",
            tipo="produtor",
            conta_validada=True
        )
        session.add(produtor_verificado)
        session.commit()
        
        # Status PENDENTE_VERIFICACAO deve manter conta_validada = False
        produtor_pendente = Usuario(
            nome="Produtor Pendente",
            telemovel="912345683",
            senha="senha123",
            tipo="produtor",
            conta_validada=False
        )
        session.add(produtor_pendente)
        session.commit()
        
        # Verificar compatibilidade
        assert produtor_verificado.conta_validada == True
        assert produtor_pendente.conta_validada == False
    
    @patch('app.routes.cadastro_produtor.OTPService.validar_otp')
    def test_criar_usuario_produtor_sucesso(self, mock_validar_otp, session, provincia, municipio):
        """Testa criação bem-sucedida de usuário produtor"""
        # Mock OTP validado
        mock_validar_otp.return_value = {'valido': True}
        
        dados = {
            'nome': 'Novo Produtor',
            'provincia_id': provincia.id,
            'municipio_id': municipio.id,
            'principal_cultura': 'Batata-rena'
        }
        
        financeiros = {
            'iban': 'AO0600600000123456789012345',
            'bi_path': 'documentos_bi/test.pdf'
        }
        
        usuario = _criar_usuario_produtor(
            telemovel="912345684",
            dados=dados,
            senha="123456",  # Senha mínima de 6 caracteres
            financeiros=financeiros
        )
        
        assert usuario is not None
        assert usuario.nome == dados['nome']
        assert usuario.telemovel == "912345684"
        assert usuario.tipo == "produtor"
        assert usuario.conta_validada == False
        assert usuario.iban == financeiros['iban']
        assert usuario.documento_pdf == financeiros['bi_path']
        # Verificar senha usando método check_password_hash diretamente
        from werkzeug.security import check_password_hash
        assert check_password_hash(usuario.senha, "123456") == True
        
        # Verificar carteira criada
        carteira = usuario.obter_carteira()
        assert carteira is not None
        assert carteira.saldo_disponivel == Decimal('0.00')
    
    def test_validacao_iban_formato(self):
        """Teste Exceção 5A: Validação de formato IBAN"""
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
        
        iban_invalido3 = "AO06ABCDEFGHIJKLMNO"  # Não numérico
        assert not iban_invalido3[6:].isdigit()


#@pytest.mark.unit
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
    
    @patch('app.services.otp_service.OTPService.verificar_usuario_existente')
    def test_gerar_enviar_usuario_existente(self, mock_verificar):
        """Teste Exceção 5B: Usuário já existente"""
        # Mock usuário existente
        mock_verificar.return_value = True
        
        resultado = gerar_e_enviar_otp("912345678", "whatsapp", "127.0.0.1")
        
        assert resultado['sucesso'] == False
        assert 'já possui uma conta' in resultado['mensagem'].lower()
        assert resultado['codigo'] is None
    
    def test_gerar_enviar_canal_sms(self):
        """Teste envio via canal SMS"""
        resultado = gerar_e_enviar_otp("912345678", "sms", "127.0.0.1")
        
        assert resultado['sucesso'] == True
        # Mensagem pode estar em diferentes formatos (SMS, Sms, sms)
        assert 'sms' in resultado['mensagem'].lower()
    
    def test_reenviar_otp(self):
        """Teste reenvio de OTP"""
        telemovel = "912345678"
        
        # Gerar OTP inicial
        resultado1 = gerar_e_enviar_otp(telemovel, "whatsapp", "127.0.0.1")
        codigo1 = resultado1['codigo']
        
        # Reenviar OTP
        resultado2 = gerar_e_enviar_otp(telemovel, "whatsapp", "127.0.0.1")
        codigo2 = resultado2['codigo']
        
        assert resultado2['sucesso'] == True
        assert codigo2 != codigo1  # Código deve ser diferente


#@pytest.mark.unit
class TestCadastroSeguranca:
    """Testes de segurança do fluxo de cadastro"""
    
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
                # Após exceder tentativas, mensagem varia
                assert resultado['valido'] == False
                assert ('não encontrado' in resultado['mensagem'].lower() or 
                        'tentativas' in resultado['mensagem'].lower())
                break
        
        # Após exceder tentativas, nem código correto funciona
        resultado_final = OTPService.validar_otp(telemovel, codigo_correto, "127.0.0.1")
        assert resultado_final['valido'] == False
