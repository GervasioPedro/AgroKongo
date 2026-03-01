# tests/unit/test_models.py - Testes unitários para modelos do AgroKongo
# Validação da lógica de negócio isolada

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.models import (
    Usuario, Safra, Produto, Transacao, TransactionStatus
)
from app.models import Disputa
from app.models import StatusConta


class TestUsuario:
    """Testes unitários para o modelo Usuario"""
    
    def test_status_conta_pendente_verificacao(self, session):
        """Testa status inicial da conta como PENDENTE_VERIFICACAO"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            tipo="produtor"
        )
        session.add(usuario)
        session.commit()
        
        assert usuario.status_conta == StatusConta.PENDENTE_VERIFICACAO
        assert not usuario.pode_criar_anuncios()
    
    def test_status_conta_verificado_pode_criar_anuncios(self, session):
        """Testa que usuário VERIFICADO pode criar anúncios"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            tipo="produtor",
            status_conta=StatusConta.VERIFICADO
        )
        session.add(usuario)
        session.commit()
        
        assert usuario.status_conta == StatusConta.VERIFICADO
        assert usuario.pode_criar_anuncios()
    
    def test_obter_carteira_usuario(self, session, produtor_user):
        """Testa obtenção da carteira do usuário"""
        carteira = produtor_user.obter_carteira()
        
        assert carteira is not None
        assert carteira.usuario_id == produtor_user.id
        assert carteira.saldo_disponivel == Decimal('0.00')
        assert carteira.saldo_bloqueado == Decimal('0.00')
    
    def test_verificar_senha_correta(self, session):
        """Testa verificação de senha correta"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            email="test@example.com",
            senha="senha123"
        )
        assert usuario.verificar_senha("senha123") is True
    
    def test_verificar_senha_incorreta(self, session):
        """Testa verificação de senha incorreta"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            email="test@example.com",
            senha="senha123"
        )
        assert usuario.verificar_senha("senha_errada") is False
    
    def test_verificar_e_atualizar_perfil_completo_produtor(self, session, provincia, municipio):
        """Testa validação de perfil completo para produtor"""
        produtor = Usuario(
            nome="Produtor Test",
            telemovel="923456789",
            email="produtor@test.com",
            senha="123456",
            tipo="produtor",
            nif="123456789",
            provincia_id=provincia.id,
            municipio_id=municipio.id,
            iban="AO0600600000123456789012345"
        )
        
        result = produtor.verificar_e_atualizar_perfil()
        assert result is True
        assert produtor.perfil_completo is True
    
    def test_verificar_e_atualizar_perfil_incompleto_produtor(self, session, provincia, municipio):
        """Testa validação de perfil incompleto para produtor (sem IBAN)"""
        produtor = Usuario(
            nome="Produtor Test",
            telemovel="923456789",
            email="produtor@test.com",
            senha="123456",
            tipo="produtor",
            nif="123456789",
            provincia_id=provincia.id,
            municipio_id=municipio.id
            # IBAN faltando
        )
        
        result = produtor.verificar_e_atualizar_perfil()
        assert result is False
        assert produtor.perfil_completo is False
    
    def test_validar_telemovel_formato_ao(self, session):
        """Testa validação de formato de telemovel angolano"""
        # Formato correto
        usuario1 = Usuario(
            nome="Test 1",
            telemovel="923456789",
            email="test1@example.com",
            senha="123456"
        )
        assert usuario1.telemovel == "923456789"
        
        # Formato com prefixo internacional
        usuario2 = Usuario(
            nome="Test 2",
            telemovel="+244923456789",
            email="test2@example.com",
            senha="123456"
        )
        assert usuario2.telemovel == "923456789"


class TestSafra:
    """Testes unitários para o modelo Safra"""
    
    def test_criar_safra_valida(self, session, produtor_user, produto):
        """Testa criação de safra válida"""
        safra = Safra(
            produtor_id=produtor_user.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('100.50'),
            preco_por_unidade=Decimal('1500.75'),
            status='disponivel'
        )
        
        session.add(safra)
        session.commit()
        
        assert safra.id is not None
        assert safra.quantidade_disponivel == Decimal('100.50')
        assert safra.preco_por_unidade == Decimal('1500.75')
        assert safra.status == 'disponivel'
    
    def test_safra_quantidade_negativa_deve_falhar(self, session, produtor_user, produto):
        """Testa que safra com quantidade negativa é rejeitada"""
        with pytest.raises(Exception):  # SQLAlchemy vai levantar exceção
            safra = Safra(
                produtor_id=produtor_user.id,
                produto_id=produto.id,
                quantidade_disponivel=Decimal('-10.00'),  # Inválido
                preco_por_unidade=Decimal('1500.75'),
                status='disponivel'
            )
            session.add(safra)
            session.commit()
    
    def test_safra_preco_negativo_deve_falhar(self, session, produtor_user, produto):
        """Testa que safra com preço negativo é rejeitada"""
        with pytest.raises(Exception):  # SQLAlchemy vai levantar exceção
            safra = Safra(
                produtor_id=produtor_user.id,
                produto_id=produto.id,
                quantidade_disponivel=Decimal('100.50'),
                preco_por_unidade=Decimal('-1500.75'),  # Inválido
                status='disponivel'
            )
            session.add(safra)
            session.commit()


class TestTransacao:
    """Testes unitários para o modelo Transacao"""
    
    def test_criar_transacao_valida(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa criação de transação válida"""
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('10.00'),
            valor_total_pago=Decimal('15007.50')
        )
        
        session.add(transacao)
        session.commit()
        
        assert transacao.id is not None
        assert transacao.fatura_ref is not None
        assert transacao.status == TransactionStatus.PENDENTE
        assert transacao.uuid is not None
    
    def test_recalcular_financeiro_taxa_10_porcento(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa cálculo financeiro com taxa de 10% (RN02)"""
        valor_total = Decimal('10000.00')
        taxa_esperada = Decimal('1000.00')  # 10%
        liquido_esperado = Decimal('9000.00')  # 90%
        
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=valor_total
        )
        
        session.add(transacao)
        session.commit()
        
        assert transacao.comissao_plataforma == taxa_esperada
        assert transacao.valor_liquido_vendedor == liquido_esperado
    
    def test_recalcular_financeiro_precisao_decimal(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa precisão de cálculos decimais"""
        valor_total = Decimal('12345.67')
        
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('3.33'),
            valor_total_pago=valor_total
        )
        
        session.add(transacao)
        session.commit()
        
        # Verificar arredondamento correto
        taxa_esperada = (valor_total * Decimal('0.10')).quantize(Decimal('0.01'))
        liquido_esperado = (valor_total - taxa_esperada).quantize(Decimal('0.01'))
        
        assert transacao.comissao_plataforma == taxa_esperada
        assert transacao.valor_liquido_vendedor == liquido_esperado
    
    def test_calcular_janela_logistica(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa cálculo de previsão de entrega"""
        data_envio = datetime.now(timezone.utc)
        previsao_esperada = data_envio + timedelta(days=3)
        
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75'),
            data_envio=data_envio
        )
        
        transacao.calcular_janela_logistica()
        
        assert transacao.previsao_entrega == previsao_esperada
    
    def test_transacao_auto_referencia(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa que transação não permite comprador = vendedor"""
        with pytest.raises(Exception):  # CheckConstraint vai falhar
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=produtor_user.id,  # Mesmo usuário
                vendedor_id=produtor_user.id,  # Mesmo usuário
                quantidade_comprada=Decimal('5.00'),
                valor_total_pago=Decimal('7503.75')
            )
            session.add(transacao)
            session.commit()


class TestDisputa:
    """Testes unitários para o modelo Disputa"""
    
    def test_pode_abrir_disputa_enviado_24h_apos_previsao(self, session, transacao_enviada, comprador_user):
        """Testa RN05 - Pode abrir disputa 24h após previsão de entrega"""
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Teste de disputa"
        )
        
        pode, mensagem = disputa.pode_abrir_disputa()
        
        assert pode is True
        assert "Disputa pode ser aberta" in mensagem
    
    def test_nao_pode_disputa_status_incorreto(self, session, transacao_pendente, comprador_user):
        """Testa RN05 - Não pode abrir disputa com status incorreto"""
        disputa = Disputa(
            transacao_id=transacao_pendente.id,
            comprador_id=comprador_user.id,
            motivo="Teste de disputa"
        )
        
        pode, mensagem = disputa.pode_abrir_disputa()
        
        assert pode is False
        assert "Status inválido" in mensagem
    
    def test_nao_pode_disputa_antes_24h(self, session, transacao_enviada, comprador_user):
        """Testa RN05 - Não pode abrir disputa antes de 24h"""
        # Modificar previsão para futuro (menos de 24h)
        transacao_enviada.previsao_entrega = datetime.now(timezone.utc) + timedelta(hours=12)
        session.commit()
        
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Teste de disputa"
        )
        
        pode, mensagem = disputa.pode_abrir_disputa()
        
        assert pode is False
        assert "Aguarde 24h" in mensagem
    
    def test_calcular_taxa_administrativa(self, session, transacao_enviada, comprador_user):
        """Testa RN08 - Cálculo de taxa administrativa"""
        valor_total = transacao_enviada.valor_total_pago
        taxa_esperada = (valor_total * Decimal('0.05')).quantize(Decimal('0.01'))
        
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Teste de disputa"
        )
        
        taxa_calculada = disputa.calcular_taxa_administrativa()
        
        assert taxa_calculada == taxa_esperada
    
    def test_resolver_favor_comprador(self, session, transacao_enviada, comprador_user, admin_user):
        """Testa resolução de disputa a favor do comprador"""
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Produto não entregue"
        )
        
        stock_original = transacao_enviada.safra.quantidade_disponivel
        
        disputa.resolver_favor_comprador(
            admin_id=admin_user.id,
            justificativa="Produto realmente não entregue",
            ip_address="127.0.0.1",
            user_agent="Test-Agent"
        )
        
        # Verificar mudanças
        assert disputa.status == 'resolvida_favor_comprador'
        assert disputa.admin_responsavel_id == admin_user.id
        assert transacao_enviada.status == TransactionStatus.CANCELADO
        assert transacao_enviada.safra.quantidade_disponivel == stock_original + transacao_enviada.quantidade_comprada
        assert disputa.taxa_administrativa > 0
    
    def test_resolver_favor_produtor(self, session, transacao_enviada, comprador_user, admin_user):
        """Testa resolução de disputa a favor do produtor"""
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Qualidade inferior"
        )
        
        saldo_original = transacao_enviada.vendedor.saldo_disponivel
        
        disputa.resolver_favor_produtor(
            admin_id=admin_user.id,
            justificativa="Produto entregue conforme combinado",
            ip_address="127.0.0.1",
            user_agent="Test-Agent"
        )
        
        # Verificar mudanças
        assert disputa.status == 'resolvida_favor_produtor'
        assert disputa.admin_responsavel_id == admin_user.id
        assert transacao_enviada.status == TransactionStatus.FINALIZADO
        assert transacao_enviada.vendedor.saldo_disponivel == saldo_original + transacao_enviada.valor_liquido_vendedor
