# tests_framework/test_models_fixed.py - Testes de modelos corrigidos
# Versão corrigida para funcionar com models.py atualizado

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.models import (
    Usuario, Safra, Transacao, TransactionStatus,
    Notificacao, Produto, Provincia, Municipio
)
from app.models_carteiras import Carteira


@pytest.mark.unit
class TestUsuario:
    """Testes do modelo Usuario"""
    
    def test_criacao_usuario_basica(self, session):
        """Testa criação básica de usuário"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            email="test@example.com",
            tipo="produtor"
        )
        usuario.set_senha("senha123")  # Usar método set_senha
        session.add(usuario)
        session.commit()
        
        assert usuario.id is not None
        assert usuario.nome == "Test User"
        assert usuario.telemovel == "923456789"
        assert usuario.tipo == "produtor"
        assert usuario.conta_validada == False
    
    def test_status_conta_pendente_verificacao(self, session):
        """Testa status inicial da conta como não validada"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            usuario.set_senha("senha123")  # Usar método set_senha
            tipo="produtor"
        )
        session.add(usuario)
        session.commit()
        
        assert usuario.conta_validada == False
        assert not usuario.pode_criar_anuncios()
    
    def test_status_conta_verificado_pode_criar_anuncios(self, session):
        """Testa que usuário VERIFICADO pode criar anúncios"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            usuario.set_senha("senha123")  # Usar método set_senha
            tipo="produtor",
            conta_validada=True
        )
        session.add(usuario)
        session.commit()
        
        assert usuario.conta_validada == True
        assert usuario.pode_criar_anuncios()
    
    def test_status_conta_rejeitado_nao_pode_criar_anuncios(self, session):
        """Testa que produtor não validado não pode criar anúncios"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            usuario.set_senha("senha123")  # Usar método set_senha
            tipo="produtor",
            conta_validada=False
        )
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
                usuario.set_senha("senha123")  # Usar método set_senha
                tipo="produtor"
            )
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
                    usuario.set_senha("senha123")  # Usar método set_senha
                    tipo="produtor"
                )
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
        usuario.set_senha("senha123")  # Usar método set_senha
        session.add(usuario)
        session.commit()
        
        assert usuario.verificar_senha("senha123") == True
        assert usuario.verificar_senha("senha_errada") == False
    
    def test_verificar_e_atualizar_perfil_completo(self, session):
        """Testa verificação de perfil completo"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            usuario.set_senha("senha123")  # Usar método set_senha
            tipo="produtor",
            nif="123456789",
            iban="AO0600600000123456789012345"
        )
        session.add(usuario)
        session.commit()
        
        # Adicionar província e município
        provincia = Provincia(nome="Luanda")
        session.add(provincia)
        session.commit()
        
        municipio = Municipio(nome="Luanda", provincia_id=provincia.id)
        session.add(municipio)
        session.commit()
        
        usuario.provincia_id = provincia.id
        usuario.municipio_id = municipio.id
        session.commit()
        
        assert usuario.verificar_e_atualizar_perfil() == True
        assert usuario.perfil_completo == True
    
    def test_verificar_e_atualizar_perfil_incompleto(self, session):
        """Testa verificação de perfil incompleto"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            usuario.set_senha("senha123")  # Usar método set_senha
            tipo="produtor"
        )
        session.add(usuario)
        session.commit()
        
        assert usuario.verificar_e_atualizar_perfil() == False
        assert usuario.perfil_completo == False
    
    def test_obter_carteira(self, session):
        """Testa obtenção/criação de carteira do usuário"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            usuario.set_senha("senha123")  # Usar método set_senha
            tipo="produtor"
        )
        session.add(usuario)
        session.commit()
        
        carteira = usuario.obter_carteira()
        assert carteira is not None
        assert carteira.usuario_id == usuario.id
        assert carteira.saldo_disponivel == Decimal('0.00')
    
    def test_to_dict(self, session):
        """Testa serialização para dicionário"""
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            usuario.set_senha("senha123")  # Usar método set_senha
            email="test@example.com",
            tipo="produtor"
        )
        session.add(usuario)
        session.commit()
        
        user_dict = usuario.to_dict()
        
        assert user_dict['id'] == usuario.id
        assert user_dict['nome'] == "Test User"
        assert user_dict['telemovel'] == "923456789"
        assert user_dict['tipo'] == "produtor"
        assert user_dict['conta_validada'] == False


@pytest.mark.unit
class TestSafra:
    """Testes do modelo Safra"""
    
    def test_criacao_safra_basica(self, session, produtor_user):
        """Testa criação básica de safra"""
        produto = Produto(nome="Milho", categoria="Grãos")
        session.add(produto)
        session.commit()
        
        safra = Safra(
            produtor_id=produtor_user.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('1000.00'),
            preco_por_unidade=Decimal('150.00'),
            descricao="Milho de alta qualidade"
        )
        session.add(safra)
        session.commit()
        
        assert safra.id is not None
        assert safra.produtor_id == produtor_user.id
        assert safra.quantidade_disponivel == Decimal('1000.00')
        assert safra.preco_por_unidade == Decimal('150.00')
        assert safra.status == 'disponivel'
    
    def test_valor_total_safra(self, session, produtor_user):
        """Testa cálculo de valor total da safra"""
        produto = Produto(nome="Milho", categoria="Grãos")
        session.add(produto)
        session.commit()
        
        safra = Safra(
            produtor_id=produtor_user.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('500.00'),
            preco_por_unidade=Decimal('200.00')
        )
        session.add(safra)
        session.commit()
        
        valor_total = safra.valor_total()
        assert valor_total == Decimal('100000.00')
    
    def test_to_dict(self, session, produtor_user):
        """Testa serialização para dicionário"""
        produto = Produto(nome="Milho", categoria="Grãos")
        session.add(produto)
        session.commit()
        
        safra = Safra(
            produtor_id=produtor_user.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('100.00'),
            preco_por_unidade=Decimal('50.00')
        )
        session.add(safra)
        session.commit()
        
        safra_dict = safra.to_dict()
        
        assert safra_dict['id'] == safra.id
        assert safra_dict['produto'] == "Milho"
        assert safra_dict['quantidade_disponivel'] == 100.00
        assert safra_dict['preco_por_unidade'] == 50.00
        assert safra_dict['valor_total'] == 5000.00


@pytest.mark.unit
class TestTransacao:
    """Testes do modelo Transacao"""
    
    def test_criacao_transacao_basica(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa criação básica de transação"""
        transacao = Transacao(
            fatura_ref="AGK001",
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
        assert transacao.fatura_ref == "AGK001"
        assert transacao.status == TransactionStatus.PENDENTE
        assert transacao.quantidade_comprada == Decimal('100.00')
        assert transacao.valor_total_pago == Decimal('15000.00')
    
    def test_recalcular_financeiro(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa recálculo financeiro da transação"""
        transacao = Transacao(
            fatura_ref="AGK002",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('200.00'),
            valor_total_pago=Decimal('30000.00'),
            status=TransactionStatus.PENDENTE
        )
        session.add(transacao)
        session.commit()
        
        # Recalcular financeiro
        transacao.recalcular_financeiro()
        session.commit()
        
        # Verificar cálculos
        assert transacao.comissao_plataforma == Decimal('3000.00')  # 10% de 30000
        assert transacao.valor_liquido_vendedor == Decimal('27000.00')  # 30000 - 3000
        assert transacao.comissao_plataforma + transacao.valor_liquido_vendedor == transacao.valor_total_pago
    
    def test_calcular_janela_logistica(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa cálculo de janela logística"""
        transacao = Transacao(
            fatura_ref="AGK003",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('50.00'),
            valor_total_pago=Decimal('7500.00'),
            status=TransactionStatus.ENVIADO
        )
        session.add(transacao)
        session.commit()
        
        # Definir data de envio
        data_envio = datetime.now(timezone.utc)
        transacao.data_envio = data_envio
        transacao.calcular_janela_logistica()
        session.commit()
        
        # Verificar previsão (3 dias úteis)
        previsao_esperada = data_envio + timedelta(days=3)
        assert transacao.previsao_entrega == previsao_esperada
    
    def test_to_dict(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa serialização para dicionário"""
        transacao = Transacao(
            fatura_ref="AGK004",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('75.00'),
            valor_total_pago=Decimal('11250.00'),
            status=TransactionStatus.PENDENTE
        )
        transacao.recalcular_financeiro()
        session.add(transacao)
        session.commit()
        
        transacao_dict = transacao.to_dict()
        
        assert transacao_dict['id'] == transacao.id
        assert transacao_dict['fatura_ref'] == "AGK004"
        assert transacao_dict['status'] == TransactionStatus.PENDENTE
        assert transacao_dict['quantidade_comprada'] == 75.00
        assert transacao_dict['valor_total_pago'] == 11250.00
        assert transacao_dict['comissao_plataforma'] == 1125.00
        assert transacao_dict['valor_liquido_vendedor'] == 10125.00


@pytest.mark.unit
class TestNotificacao:
    """Testes do modelo Notificacao"""
    
    def test_criacao_notificacao_basica(self, session, produtor_user):
        """Testa criação básica de notificação"""
        notificacao = Notificacao(
            usuario_id=produtor_user.id,
            mensagem="Nova reserva recebida!",
            link="/reservas/1"
        )
        session.add(notificacao)
        session.commit()
        
        assert notificacao.id is not None
        assert notificacao.usuario_id == produtor_user.id
        assert notificacao.mensagem == "Nova reserva recebida!"
        assert notificacao.lida == False
    
    def test_marcar_como_lida(self, session, produtor_user):
        """Testa marcação de notificação como lida"""
        notificacao = Notificacao(
            usuario_id=produtor_user.id,
            mensagem="Teste de notificação"
        )
        session.add(notificacao)
        session.commit()
        
        # Marcar como lida
        notificacao.marcar_como_lida()
        
        assert notificacao.lida == True
        assert notificacao.data_leitura is not None
