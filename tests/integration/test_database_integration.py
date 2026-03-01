# tests/integration/test_database_integration.py - Testes de integração com banco de dados
# Validação de relacionamentos, constraints e performance

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError

from app.models import (
    Usuario, Safra, Transacao, TransactionStatus,
    Notificacao, LogAuditoria, HistoricoStatus,
    Provincia, Municipio, Produto
)
from app.models import Disputa


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseConstraints:
    """Testa constraints e validações do banco de dados"""
    
    def test_constraint_comprador_diferente_vendedor(self, session, safra_ativa, produtor_user):
        """Testa constraint que impede compra do próprio produto"""
        with pytest.raises(IntegrityError):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=produtor_user.id,  # Mesmo usuário
                vendedor_id=produtor_user.id,  # Mesmo usuário
                quantidade_comprada=Decimal('5.00'),
                valor_total_pago=Decimal('7503.75')
            )
            session.add(transacao)
            session.commit()
    
    def test_constraint_valor_total_positivo(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa constraint que impede valor total negativo"""
        with pytest.raises(IntegrityError):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('5.00'),
                valor_total_pago=Decimal('-100.00')  # Negativo
            )
            session.add(transacao)
            session.commit()
    
    def test_constraint_stock_positivo(self, session, produtor_user, produto):
        """Testa constraint que impede stock negativo na safra"""
        with pytest.raises(IntegrityError):
            safra = Safra(
                produtor_id=produtor_user.id,
                produto_id=produto.id,
                quantidade_disponivel=Decimal('-10.00'),  # Negativo
                preco_por_unidade=Decimal('1500.75')
            )
            session.add(safra)
            session.commit()
    
    def test_constraint_preco_positivo(self, session, produtor_user, produto):
        """Testa constraint que impede preço negativo"""
        with pytest.raises(IntegrityError):
            safra = Safra(
                produtor_id=produtor_user.id,
                produto_id=produto.id,
                quantidade_disponivel=Decimal('100.00'),
                preco_por_unidade=Decimal('-1500.75')  # Negativo
            )
            session.add(safra)
            session.commit()
    
    def test_foreign_key_cascade_delete_usuario(self, session, produtor_user, produto):
        """Testa cascade delete ao remover usuário"""
        # Criar safra do produtor
        safra = Safra(
            produtor_id=produtor_user.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('100.00'),
            preco_por_unidade=Decimal('1500.75')
        )
        session.add(safra)
        session.commit()
        
        safra_id = safra.id
        
        # Remover produtor (deve remover safras em cascade)
        session.delete(produtor_user)
        session.commit()
        
        # Verificar que safra foi removida
        safra_removida = Safra.query.get(safra_id)
        assert safra_removida is None
    
    def test_unique_constraint_fatura_ref(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa unique constraint na referência da fatura"""
        # Criar primeira transação
        transacao1 = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75')
        )
        session.add(transacao1)
        session.commit()
        
        # Tentar criar segunda com mesma fatura_ref (deve falhar)
        transacao2 = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('3.00'),
            valor_total_pago=Decimal('4502.25'),
            fatura_ref=transacao1.fatura_ref  # Mesma referência
        )
        
        with pytest.raises(IntegrityError):
            session.add(transacao2)
            session.commit()


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseRelationships:
    """Testa relacionamentos e integridade referencial"""
    
    def test_relacionamento_transacao_safra(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa relacionamento entre transação e safra"""
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75')
        )
        
        session.add(transacao)
        session.commit()
        
        # Verificar relacionamentos
        assert transacao.safra.id == safra_ativa.id
        assert transacao.safra.produto.id == safra_ativa.produto.id
        assert transacao.safra.produtor.id == safra_ativa.produtor.id
        
        # Verificar relacionamento inverso
        assert transacao in safra_ativa.transacoes
    
    def test_relacionamento_transacao_usuarios(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa relacionamentos com comprador e vendedor"""
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('3.00'),
            valor_total_pago=Decimal('4502.25')
        )
        
        session.add(transacao)
        session.commit()
        
        # Verificar relacionamentos
        assert transacao.comprador.id == comprador_user.id
        assert transacao.vendedor.id == produtor_user.id
        assert transacao.comprador.tipo == 'comprador'
        assert transacao.vendedor.tipo == 'produtor'
        
        # Verificar relacionamentos inversos
        assert transacao in comprador_user.compras
        assert transacao in produtor_user.vendas
    
    def test_relacionamento_disputa_transacao(self, session, transacao_enviada, comprador_user):
        """Testa relacionamento entre disputa e transação"""
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Teste de disputa"
        )
        
        session.add(disputa)
        session.commit()
        
        # Verificar relacionamentos
        assert disputa.transacao.id == transacao_enviada.id
        assert disputa.comprador.id == comprador_user.id
        
        # Verificar relacionamento inverso
        assert transacao_enviada.disputa.id == disputa.id
    
    def test_relacionamento_historico_status(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa relacionamento com histórico de status"""
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('2.00'),
            valor_total_pago=Decimal('3001.50')
        )
        
        session.add(transacao)
        session.commit()
        
        # Adicionar histórico
        historico = HistoricoStatus(
            transacao_id=transacao.id,
            status_anterior=TransactionStatus.PENDENTE,
            status_novo=TransactionStatus.AGUARDANDO_PAGAMENTO,
            observacao="Status atualizado"
        )
        
        session.add(historico)
        session.commit()
        
        # Verificar relacionamentos
        assert historico.transacao.id == transacao.id
        assert historico in transacao.historico_status
    
    def test_relacionamento_notificacoes_usuario(self, session, comprador_user):
        """Testa relacionamento entre notificações e usuário"""
        notificacao = Notificacao(
            usuario_id=comprador_user.id,
            mensagem="Teste de notificação",
            link="/test"
        )
        
        session.add(notificacao)
        session.commit()
        
        # Verificar relacionamentos
        assert notificacao.usuario.id == comprador_user.id
        assert notificacao in comprador_user.notificacoes
    
    def test_relacionamento_log_auditoria_usuario(self, session, admin_user):
        """Testa relacionamento entre log de auditoria e usuário"""
        log = LogAuditoria(
            usuario_id=admin_user.id,
            acao="TESTE_AUDITORIA",
            detalhes="Teste de log de auditoria",
            ip="127.0.0.1"
        )
        
        session.add(log)
        session.commit()
        
        # Verificar relacionamentos
        assert log.usuario.id == admin_user.id


@pytest.mark.integration
@pytest.mark.database
class TestDatabasePerformance:
    """Testa performance e eficiência de consultas"""
    
    def test_query_otimizada_transacoes_usuario(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa consulta otimizada de transações do usuário"""
        # Criar múltiplas transações
        transacoes = []
        for i in range(10):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('1.00'),
                valor_total_pago=Decimal('1500.75')
            )
            transacoes.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        # Consulta otimizada usando índices
        start_time = datetime.now()
        
        transacoes_usuario = Transacao.query.filter(
            Transacao.comprador_id == comprador_user.id
        ).order_by(Transacao.data_criacao.desc()).all()
        
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        # Verificações
        assert len(transacoes_usuario) == 10
        assert all(t.comprador_id == comprador_user.id for t in transacoes_usuario)
        assert query_time < 0.1  # Consulta deve ser rápida (< 100ms)
    
    def test_query_agregada_estatisticas(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa consulta agregada para estatísticas"""
        from sqlalchemy import func
        
        # Criar transações com diferentes status
        status_list = [
            TransactionStatus.PENDENTE,
            TransactionStatus.ESCROW,
            TransactionStatus.FINALIZADO,
            TransactionStatus.CANCELADO
        ]
        
        for i, status in enumerate(status_list):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('2.00'),
                valor_total_pago=Decimal('3001.50'),
                status=status
            )
            session.add(transacao)
        
        session.commit()
        
        # Consulta agregada
        start_time = datetime.now()
        
        estatisticas = session.query(
            Transacao.status,
            func.count(Transacao.id).label('quantidade'),
            func.sum(Transacao.valor_total_pago).label('valor_total')
        ).filter(
            Transacao.vendedor_id == produtor_user.id
        ).group_by(Transacao.status).all()
        
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        # Verificações
        assert len(estatisticas) == 4  # 4 status diferentes
        assert all(stat.quantidade > 0 for stat in estatisticas)
        assert query_time < 0.1  # Consulta agregada deve ser rápida
    
    def test_join_otimizado_transacoes_detalhadas(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa consulta com joins otimizados"""
        from sqlalchemy.orm import joinedload
        
        # Criar transação
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('3.00'),
            valor_total_pago=Decimal('4502.25')
        )
        
        session.add(transacao)
        session.commit()
        
        # Consulta com joinedload para evitar N+1
        start_time = datetime.now()
        
        transacao_detalhada = Transacao.query.options(
            joinedload(Transacao.safra).joinedload(Safra.produto),
            joinedload(Transacao.comprador),
            joinedload(Transacao.vendedor)
        ).filter_by(id=transacao.id).first()
        
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        # Verificações
        assert transacao_detalhada is not None
        assert transacao_detalhada.safra.produto.nome is not None
        assert transacao_detalhada.comprador.nome is not None
        assert transacao_detalhada.vendedor.nome is not None
        assert query_time < 0.05  # Com joinedload deve ser muito rápido
    
    def test_index_performance_fatura_ref(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa performance de consulta por fatura_ref (com índice)"""
        # Criar múltiplas transações
        transacoes = []
        for i in range(100):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('1.00'),
                valor_total_pago=Decimal('1500.75')
            )
            transacoes.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        # Buscar por fatura_ref (deve usar índice)
        ref_buscada = transacoes[50].fatura_ref
        
        start_time = datetime.now()
        
        transacao_encontrada = Transacao.query.filter_by(
            fatura_ref=ref_buscada
        ).first()
        
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        # Verificações
        assert transacao_encontrada is not None
        assert transacao_encontrada.fatura_ref == ref_buscada
        assert query_time < 0.01  # Com índice deve ser muito rápido


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseTransactions:
    """Testa transações e atomicidade no nível do banco"""
    
    def test_transacao_automatica_rollback(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa rollback automático em caso de erro"""
        # Salvar estado inicial
        transacoes_antes = Transacao.query.count()
        
        try:
            # Iniciar operação múltipla
            transacao1 = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('2.00'),
                valor_total_pago=Decimal('3001.50')
            )
            session.add(transacao1)
            session.flush()  # Força escrita mas não commit
            
            # Operação que vai falhar
            transacao2 = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('2.00'),
                valor_total_pago=Decimal('-100.00')  # Vai causar erro de constraint
            )
            session.add(transacao2)
            session.commit()
            
        except Exception:
            session.rollback()
        
        # Verificar rollback
        transacoes_depois = Transacao.query.count()
        assert transacoes_depois == transacoes_antes
        
        # Nenhuma transação deve ter sido persistida
        transacao1_salva = Transacao.query.filter_by(
            valor_total_pago=Decimal('3001.50')
        ).first()
        assert transacao1_salva is None
    
    def test_nested_transactions_savepoints(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa savepoints para transações aninhadas"""
        # Criar savepoint inicial
        session.begin_nested()
        
        # Primeira operação
        transacao1 = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('1.00'),
            valor_total_pago=Decimal('1500.75')
        )
        session.add(transacao1)
        session.flush()
        
        transacao1_id = transacao1.id
        
        # Criar segundo savepoint
        session.begin_nested()
        
        try:
            # Operação que vai falhar
            transacao2 = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('1.00'),
                valor_total_pago=Decimal('-100.00')
            )
            session.add(transacao2)
            session.commit()
            
        except Exception:
            # Rollback apenas do savepoint interno
            session.rollback()
        
        # Commit do savepoint externo
        session.commit()
        
        # Verificar que primeira transação foi salva
        transacao1_salva = Transacao.query.get(transacao1_id)
        assert transacao1_salva is not None
        assert transacao1_salva.valor_total_pago == Decimal('1500.75')
        
        # Segunda transação não deve existir
        transacao2_salva = Transacao.query.filter_by(
            valor_total_pago=Decimal('-100.00')
        ).first()
        assert transacao2_salva is None
