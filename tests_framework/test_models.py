# tests_framework/test_models.py - Testes unitários dos modelos
# Validação da lógica de negócio isolada

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.models import Usuario
from app.models.financeiro import Carteira
from app.models.disputa import Disputa
from app.models.transacao import Transacao
from app.models.produto import Safra, Produto
from app.models.transacao import TransactionStatus

#@pytest.mark.unit
class TestUsuario:
    """Testes unitários para o modelo Usuario"""
    
    def test_criacao_usuario_basica(self, session):
        """Testa criação básica de usuário"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            email="test@example.com",
            tipo="produtor"
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        assert usuario.id is not None
        assert usuario.nome == "Test User"
        assert usuario.telemovel == "923456789"
        assert usuario.tipo == "produtor"
        # Teste com conta_validada em vez de status_conta
        assert usuario.conta_validada == False
    
    def test_status_conta_pendente_verificacao(self, session):
        """Testa status inicial da conta como não validada"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            tipo="produtor"
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        assert usuario.conta_validada == False
        assert not usuario.pode_criar_anuncios()
    
    def test_status_conta_verificado_pode_criar_anuncios(self, session):
        """Testa que usuário VERIFICADO pode criar anúncios"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            tipo="produtor",
            conta_validada=True
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        assert usuario.conta_validada == True
        assert usuario.pode_criar_anuncios()
    
    def test_status_conta_rejeitado_nao_pode_criar_anuncios(self, session):
        """Testa que produtor não validado não pode criar anúncios"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            tipo="produtor",
            conta_validada=False
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        assert usuario.conta_validada == False
        assert not usuario.pode_criar_anuncios()
    
    def test_validacao_telemovel_formato_angolano(self, session):
        """Testa validação de formato de telemóvel angolano"""
        # Telemóveis válidos
        telemoveis_validos = ["912345678", "923456789", "934567890"]
        
        for telemovel in telemoveis_validos:
            usuario = Usuario(
                nome="Test User",
                telemovel=telemovel,
                tipo="produtor"
            )
            usuario.set_senha("senha123")
            session.add(usuario)
            session.commit()
            
            assert usuario.telemovel == telemovel
            session.delete(usuario)
            session.commit()
        
        # Telemóveis inválidos devem lançar exceção
        telemoveis_invalidos = ["812345678", "712345678", "91234567", "9123456789"]
        
        for telemovel in telemoveis_invalidos:
            with pytest.raises(ValueError):
                usuario = Usuario(
                    nome="Test User",
                    telemovel=telemovel,
                    tipo="produtor"
                )
                usuario.set_senha("senha123")
                session.add(usuario)
                session.commit()
    
    def test_verificar_senha_correta(self, session):
        """Testa verificação de senha correta"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            email="test@example.com",
            tipo="produtor"
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        assert usuario.verificar_senha("senha123") is True
    
    def test_verificar_senha_incorreta(self, session):
        """Testa verificação de senha incorreta"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            email="test@example.com",
            tipo="produtor"
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        assert usuario.verificar_senha("senha_errada") is False
    
    def test_verificar_e_atualizar_perfil_completo(self, session, provincia, municipio):
        """Testa verificação e atualização de perfil completo"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            tipo="produtor",
            provincia_id=provincia.id,
            municipio_id=municipio.id,
            nif="123456789",
            iban="AO0600600000123456789012345"
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        # Verificar perfil completo
        resultado = usuario.verificar_e_atualizar_perfil()
        assert resultado is True
        assert usuario.perfil_completo is True
    
    def test_verificar_e_atualizar_perfil_incompleto(self, session):
        """Testa verificação de perfil incompleto"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            tipo="produtor"
            # Faltando campos obrigatórios
        )
        usuario.set_senha("senha123")
        session.add(usuario)
        session.commit()
        
        # Verificar perfil incompleto
        resultado = usuario.verificar_e_atualizar_perfil()
        assert resultado is False
        assert usuario.perfil_completo is False


#@pytest.mark.unit
class TestCarteira:
    """Testes unitários para o modelo Carteira"""
    
    def test_criar_carteira(self, session, produtor_user):
        """Testa criação de carteira"""
        # Produtor já tem carteira criada pelo fixture, apenas verificar
        carteira = produtor_user.obter_carteira()
        
        assert carteira.usuario_id == produtor_user.id
        assert carteira.saldo_disponivel >= Decimal('0.00')
        assert carteira.get_saldo_total() >= Decimal('0.00')
    
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


#@pytest.mark.unit
class TestSafra:
    """Testes unitários para o modelo Safra"""
    
    def test_criar_safra(self, session, produtor_user, produto):
        """Testa criação de safra"""
        safra = Safra(
            produtor_id=produtor_user.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('1000.00'),
            preco_por_unidade=Decimal('150.00'),
            status='disponivel'
        )
        session.add(safra)
        session.commit()
        
        assert safra.id is not None
        assert safra.produtor_id == produtor_user.id
        assert safra.produto_id == produto.id
        assert safra.quantidade_disponivel == Decimal('1000.00')
        assert safra.preco_por_unidade == Decimal('150.00')
        assert safra.status == 'disponivel'
    
    def test_valor_total_safra(self, session, safra_ativa):
        """Testa cálculo de valor total da safra"""
        valor_total = safra_ativa.quantidade_disponivel * safra_ativa.preco_por_unidade
        assert valor_total == Decimal('150000.00')  # 1000 * 150
    
    def test_verificar_disponibilidade(self, session, safra_ativa):
        """Testa verificação de disponibilidade"""
        # Safra disponível
        assert safra_ativa.quantidade_disponivel > 0
        assert safra_ativa.status == 'disponivel'
        
        # Reduzir quantidade para zero
        safra_ativa.quantidade_disponivel = Decimal('0.00')
        session.commit()
        
        # Agora não está mais disponível
        assert safra_ativa.quantidade_disponivel == Decimal('0.00')


#@pytest.mark.unit
class TestTransacao:
    """Testes unitários para o modelo Transacao"""
    
    def test_criar_transacao(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa criação de transação"""
        transacao = Transacao(
            fatura_ref="AGK20240228001",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('100.00'),
            valor_total_pago=Decimal('15000.00'),
            status=TransactionStatus.PENDENTE
        )
        session.add(transacao)
        session.commit()
        
        assert transacao.id is not None
        assert transacao.fatura_ref == "AGK20240228001"
        assert transacao.status == TransactionStatus.PENDENTE
        assert transacao.quantidade_comprada == Decimal('100.00')
    
    def test_recalcular_financeiro(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa cálculo financeiro da transação"""
        transacao = Transacao(
            fatura_ref="AGK20240228002",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('200.00'),
            valor_total_pago=Decimal('30000.00'),
            status=TransactionStatus.PENDENTE
        )
        transacao.recalcular_financeiro()
        session.add(transacao)
        session.commit()
        
        # Verificar cálculo da comissão (10%)
        comissao_esperada = (Decimal('30000.00') * Decimal('0.10')).quantize(Decimal('0.01'))
        liquido_esperado = Decimal('30000.00') - comissao_esperada
        
        assert transacao.comissao_plataforma == comissao_esperada
        assert transacao.valor_liquido_vendedor == liquido_esperado
        assert transacao.comissao_plataforma + transacao.valor_liquido_vendedor == transacao.valor_total_pago
    
    def test_calcular_janela_logistica(self, session, transacao_pendente):
        """Testa cálculo de janela logística"""
        # Definir data de envio
        transacao_pendente.data_envio = datetime.now(timezone.utc)
        transacao_pendente.calcular_janela_logistica()
        session.commit()
        
        # Verificar previsão de entrega (3 dias após envio)
        previsao_esperada = transacao_pendente.data_envio + timedelta(days=3)
        assert transacao_pendente.previsao_entrega == previsao_esperada
    
    def test_to_dict(self, session, transacao_pendente):
        """Testa representação em dicionário"""
        transacao_dict = transacao_pendente.to_dict()
        
        assert 'id' in transacao_dict
        assert 'fatura_ref' in transacao_dict
        assert 'status' in transacao_dict
        assert 'quantidade_comprada' in transacao_dict
        assert 'valor_total_pago' in transacao_dict
        assert 'comissao_plataforma' in transacao_dict
        assert 'valor_liquido_vendedor' in transacao_dict
        assert 'data_criacao' in transacao_dict
        
        assert isinstance(transacao_dict['quantidade_comprada'], float)
        assert isinstance(transacao_dict['valor_total_pago'], float)


#@pytest.mark.unit
class TestDisputa:
    """Testes unitários para o modelo Disputa"""
    
    def test_criar_disputa(self, session, transacao_escrow, comprador_user):
        """Testa criação de disputa"""
        disputa = Disputa(
            transacao_id=transacao_escrow.id,
            comprador_id=comprador_user.id,
            motivo="Produto não conforme",
            status="aberta"
        )
        session.add(disputa)
        session.commit()
        
        assert disputa.id is not None
        assert disputa.transacao_id == transacao_escrow.id
        assert disputa.comprador_id == comprador_user.id
        assert disputa.motivo == "Produto não conforme"
        assert disputa.status == "aberta"
    
    def test_resolver_disputa(self, session, disputa_ativa):
        """Testa resolução de disputa"""
        disputa_ativa.status = "resolvida"
        disputa_ativa.decisao = "reembolso_completo"
        disputa_ativa.observacoes = "Produto não conforme, reembolso autorizado"
        session.commit()
        
        assert disputa_ativa.status == "resolvida"
        assert disputa_ativa.decisao == "reembolso_completo"
        assert disputa_ativa.observacoes is not None
