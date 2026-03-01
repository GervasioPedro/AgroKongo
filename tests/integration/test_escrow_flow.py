# tests/integration/test_escrow_flow.py - Testes de integração do fluxo de Escrow
# Validação completa da comunicação entre tabelas e estados da transação

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import (
    Usuario, Safra, Transacao, TransactionStatus, 
    Notificacao, LogAuditoria, HistoricoStatus
)
from app.models import Disputa
from app.models import StatusConta
from app.tasks.pagamentos import processar_liquidacao


@pytest.mark.integration
@pytest.mark.financial
class TestEscrowFlowSuccess:
    """Teste de integração - Cenário de Sucesso do Fluxo de Escrow"""
    
    def test_fluxo_escrow_completo_sucesso(self, session, safra_ativa, comprador_user, produtor_user, mock_celery):
        """
        Teste completo do fluxo de escrow do início ao fim:
        PENDENTE -> ANALISE -> ESCROW -> ENVIADO -> ENTREGUE -> FINALIZADO
        """
        # 1. Estado Inicial - Criar Transação (Status: PENDENTE)
        stock_inicial = safra_ativa.quantidade_disponivel
        saldo_inicial_vendedor = produtor_user.saldo_disponivel or Decimal('0.00')
        
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('10.00'),
            valor_total_pago=Decimal('15007.50')
        )
        
        session.add(transacao)
        session.commit()
        
        # Verificar estado inicial
        assert transacao.status == TransactionStatus.PENDENTE
        assert transacao.fatura_ref is not None
        assert transacao.uuid is not None
        assert transacao.comissao_plataforma == Decimal('1500.75')  # 10%
        assert transacao.valor_liquido_vendedor == Decimal('13506.75')
        
        # 2. Simular Upload de Comprovativo (Status: ANALISE)
        transacao.status = TransactionStatus.ANALISE
        transacao.comprovativo_path = 'comprovativo_teste.pdf'
        session.add(HistoricoStatus(
            transacao_id=transacao.id,
            status_anterior=TransactionStatus.PENDENTE,
            status_novo=TransactionStatus.ANALISE,
            observacao="Comprovativo submetido"
        ))
        session.commit()
        
        assert transacao.status == TransactionStatus.ANALISE
        assert transacao.comprovativo_path is not None
        
        # 3. Admin Aprova Pagamento (Status: ESCROW)
        transacao.status = TransactionStatus.ESCROW
        transacao.data_pagamento_escrow = datetime.now(timezone.utc)
        session.add(HistoricoStatus(
            transacao_id=transacao.id,
            status_anterior=TransactionStatus.ANALISE,
            status_novo=TransactionStatus.ESCROW,
            observacao="Pagamento validado pelo admin"
        ))
        session.commit()
        
        assert transacao.status == TransactionStatus.ESCROW
        assert transacao.data_pagamento_escrow is not None
        
        # 4. Vendedor Envia (Status: ENVIADO)
        transacao.status = TransactionStatus.ENVIADO
        transacao.data_envio = datetime.now(timezone.utc)
        transacao.calcular_janela_logistica()
        session.add(HistoricoStatus(
            transacao_id=transacao.id,
            status_anterior=TransactionStatus.ESCROW,
            status_novo=TransactionStatus.ENVIADO,
            observacao="Mercadoria enviada"
        ))
        session.commit()
        
        assert transacao.status == TransactionStatus.ENVIADO
        assert transacao.data_envio is not None
        assert transacao.previsao_entrega is not None
        
        # 5. Comprador Confirma (Status: ENTREGUE)
        transacao.status = TransactionStatus.ENTREGUE
        transacao.data_entrega = datetime.now(timezone.utc)
        session.add(HistoricoStatus(
            transacao_id=transacao.id,
            status_anterior=TransactionStatus.ENVIADO,
            status_novo=TransactionStatus.ENTREGUE,
            observacao="Recebimento confirmado pelo comprador"
        ))
        session.commit()
        
        assert transacao.status == TransactionStatus.ENTREGUE
        assert transacao.data_entrega is not None
        
        # 6. Liquidação Final (Status: FINALIZADO)
        # Creditar saldo do vendedor
        produtor_user.saldo_disponivel = saldo_inicial_vendedor + transacao.valor_liquido_vendedor
        transacao.status = TransactionStatus.FINALIZADO
        transacao.data_liquidacao = datetime.now(timezone.utc)
        transacao.transferencia_concluida = True
        
        session.add(HistoricoStatus(
            transacao_id=transacao.id,
            status_anterior=TransactionStatus.ENTREGUE,
            status_novo=TransactionStatus.FINALIZADO,
            observacao="Transação finalizada e saldo creditado"
        ))
        session.commit()
        
        # Verificação Final - Sucesso
        assert transacao.status == TransactionStatus.FINALIZADO
        assert transacao.transferencia_concluida is True
        assert transacao.data_liquidacao is not None
        
        # Verificar saldo do vendedor aumentou exatamente o valor líquido
        saldo_final_vendedor = produtor_user.saldo_disponivel
        aumento_esperado = transacao.valor_liquido_vendedor
        aumento_real = saldo_final_vendedor - saldo_inicial_vendedor
        
        assert aumento_real == aumento_esperado
        assert aumento_real == Decimal('13506.75')
        
        # Verificar histórico completo
        historico = HistoricoStatus.query.filter_by(transacao_id=transacao.id).order_by(
            HistoricoStatus.data_mudanca.asc()
        ).all()
        
        assert len(historico) == 5  # PENDENTE->ANALISE->ESCROW->ENVIADO->ENTREGUE->FINALIZADO
        assert historico[0].status_novo == TransactionStatus.ANALISE
        assert historico[-1].status_novo == TransactionStatus.FINALIZADO
        
        # Verificar notificações criadas
        notificacoes = Notificacao.query.filter(
            Notificacao.mensagem.contains(transacao.fatura_ref)
        ).all()
        
        assert len(notificacoes) > 0  # Deve haver notificações
    
    def test_comunicacao_tabelas_transacao(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa comunicação entre tabelas relacionadas à transação"""
        # Criar transação completa
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
        assert transacao.safra.produto.nome == safra_ativa.produto.nome
        assert transacao.comprador.id == comprador_user.id
        assert transacao.vendedor.id == produtor_user.id
        
        # Verificar dados relacionados
        assert transacao.quantidade_comprada <= safra_ativa.quantidade_disponivel
        assert transacao.valor_total_pago == (transacao.quantidade_comprada * safra_ativa.preco_por_unidade)
        
        # Verificar consistência de IDs
        assert transacao.comprador_id != transacao.vendedor_id
        assert transacao.safra.produtor_id == transacao.vendedor_id
    
    def test_estados_transacao_consistentes(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa consistência dos estados da transação ao longo do fluxo"""
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('8.00'),
            valor_total_pago=Decimal('12006.00')
        )
        
        session.add(transacao)
        session.commit()
        
        # Sequência válida de estados
        estados_validos = [
            TransactionStatus.PENDENTE,
            TransactionStatus.AGUARDANDO_PAGAMENTO,
            TransactionStatus.ANALISE,
            TransactionStatus.ESCROW,
            TransactionStatus.ENVIADO,
            TransactionStatus.ENTREGUE,
            TransactionStatus.FINALIZADO
        ]
        
        # Simular progressão pelos estados
        for i, estado in enumerate(estados_validos):
            transacao.status = estado
            
            # Adicionar timestamps apropriados
            if estado == TransactionStatus.ANALISE:
                transacao.comprovativo_path = f'comprovativo_{i}.pdf'
            elif estado == TransactionStatus.ESCROW:
                transacao.data_pagamento_escrow = datetime.now(timezone.utc)
            elif estado == TransactionStatus.ENVIADO:
                transacao.data_envio = datetime.now(timezone.utc)
                transacao.calcular_janela_logistica()
            elif estado == TransactionStatus.ENTREGUE:
                transacao.data_entrega = datetime.now(timezone.utc)
            elif estado == TransactionStatus.FINALIZADO:
                transacao.data_liquidacao = datetime.now(timezone.utc)
                transacao.transferencia_concluida = True
            
            session.commit()
            
            # Verificar estado atual
            transacao_atualizada = Transacao.query.get(transacao.id)
            assert transacao_atualizada.status == estado
            
            # Verificar campos relacionados ao estado
            if estado == TransactionStatus.ANALISE:
                assert transacao_atualizada.comprovativo_path is not None
            elif estado == TransactionStatus.ENVIADO:
                assert transacao_atualizada.data_envio is not None
                assert transacao_atualizada.previsao_entrega is not None
            elif estado == TransactionStatus.FINALIZADO:
                assert transacao_atualizada.transferencia_concluida is True


@pytest.mark.integration
@pytest.mark.financial
class TestEscrowFlowFailure:
    """Teste de integração - Cenário de Falha e Rollback"""
    
    def test_rollback_liquidacao_falha_credito(self, session, safra_ativa, comprador_user, produtor_user):
        """
        Teste de rollback: Simular falha no crédito da carteira do produtor
        Verificar atomicidade: status não deve mudar se operação financeira falhar
        """
        # Preparar transação em estado ENTREGUE (pronta para liquidação)
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('10.00'),
            valor_total_pago=Decimal('15007.50'),
            status=TransactionStatus.ENTREGUE,
            data_entrega=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        session.add(transacao)
        session.commit()
        
        # Salvar estado antes da operação
        status_antes = transacao.status
        saldo_vendedor_antes = produtor_user.saldo_disponivel or Decimal('0.00')
        transferencia_antes = transacao.transferencia_concluida
        
        assert status_antes == TransactionStatus.ENTREGUE
        assert transferencia_antes is False
        
        # Simular falha no crédito usando rollback explícito
        try:
            # Iniciar operação que deve falhar
            transacao.status = TransactionStatus.FINALIZADO
            transacao.data_liquidacao = datetime.now(timezone.utc)
            transacao.transferencia_concluida = True
            
            # Simular falha no crédito (ex: limite excedido)
            # Em implementação real, isso poderia ser uma exceção do banco
            raise Exception("Simulação de falha no crédito da carteira")
            
        except Exception as e:
            # Rollback manual para simular falha real
            session.rollback()
            
            # Recarregar objetos do banco
            session.refresh(transacao)
            session.refresh(produtor_user)
        
        # Verificação - Rollback bem sucedido
        assert transacao.status == status_antes  # Deve voltar para ENTREGUE
        assert transacao.status == TransactionStatus.ENTREGUE
        assert transacao.transferencia_concluida == transferencia_antes  # Deve continuar False
        assert produtor_user.saldo_disponivel == saldo_vendedor_antes  # Saldo não alterado
        
        # Verificar que não foi criado histórico de status final
        historico_final = HistoricoStatus.query.filter_by(
            transacao_id=transacao.id,
            status_novo=TransactionStatus.FINALIZADO
        ).first()
        
        assert historico_final is None  # Não deve existir
    
    def test_atomicidade_operacoes_financeiras(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa atomicidade de múltiplas operações financeiras"""
        # Criar múltiplas transações para testar atomicidade em lote
        transacoes = []
        
        for i in range(3):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('5.00'),
                valor_total_pago=Decimal('7503.75'),
                status=TransactionStatus.ENTREGUE,
                data_entrega=datetime.now(timezone.utc)
            )
            transacoes.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        # Salvar estado antes das operações
        saldos_antes = [t.valor_liquido_vendedor for t in transacoes]
        status_antes = [t.status for t in transacoes]
        
        # Simular falha na terceira operação
        try:
            for i, transacao in enumerate(transacoes):
                transacao.status = TransactionStatus.FINALIZADO
                transacao.transferencia_concluida = True
                transacao.data_liquidacao = datetime.now(timezone.utc)
                
                # Simular falha na última operação
                if i == 2:
                    raise Exception("Falha simulada na operação 3")
                
                # Creditar saldo (só para as primeiras)
                produtor_user.saldo_disponivel = (produtor_user.saldo_disponivel or 0) + transacao.valor_liquido_vendedor
            
            session.commit()
            
        except Exception:
            session.rollback()
        
        # Verificar atomicidade - nada deve ter sido persistido
        for i, transacao in enumerate(transacoes):
            session.refresh(transacao)
            
            # Status deve ter voltado ao original
            assert transacao.status == status_antes[i]
            assert transacao.status == TransactionStatus.ENTREGUE
            assert transacao.transferencia_concluida is False
        
        # Saldo do produtor não deve ter mudado
        session.refresh(produtor_user)
        assert produtor_user.saldo_disponivel == 0  # Continua zero
    
    @patch('app.tasks.pagamentos.processar_liquidacao')
    def test_falha_task_assincrona_rollback(self, mock_task, session, safra_ativa, comprador_user, produtor_user):
        """Testa falha em task assíncrona mantém atomicidade"""
        # Configurar mock para simular falha
        mock_task.side_effect = Exception("Falha na task assíncrona")
        
        # Preparar transação para liquidação
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75'),
            status=TransactionStatus.ENTREGUE,
            data_entrega=datetime.now(timezone.utc)
        )
        
        session.add(transacao)
        session.commit()
        
        # Tentar processar liquidação (vai falhar)
        from app.tasks.pagamentos import processar_liquidacao
        
        try:
            # Chamada síncrona para teste (em produção seria async)
            processar_liquidacao(transacao.id)
        except Exception:
            pass  # Falha esperada
        
        # Verificar que estado não mudou
        session.refresh(transacao)
        assert transacao.status == TransactionStatus.ENTREGUE
        assert transacao.transferencia_concluida is False
        
        # Task deve ter sido chamada
        assert mock_task.called
        assert mock_task.call_count == 1


@pytest.mark.integration
@pytest.mark.dispute
class TestEscrowFlowWithDisputes:
    """Testes de integração do fluxo de escrow com disputas"""
    
    def test_fluxo_com_disputa_resolucao(self, session, transacao_enviada, comprador_user, admin_user):
        """Testa fluxo completo com abertura e resolução de disputa"""
        # Criar disputa
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Produto de qualidade inferior",
            status='aberta'
        )
        
        session.add(disputa)
        session.commit()
        
        # Verificar bloqueio da transação
        transacao_enviada.status = TransactionStatus.DISPUTA
        session.commit()
        
        assert transacao_enviada.status == TransactionStatus.DISPUTA
        assert disputa.status == 'aberta'
        
        # Resolver disputa a favor do produtor
        disputa.resolver_favor_produtor(
            admin_id=admin_user.id,
            justificativa="Produto entregue conforme especificado",
            ip_address="127.0.0.1",
            user_agent="Test-Agent"
        )
        
        session.commit()
        
        # Verificar resolução
        assert disputa.status == 'resolvida_favor_produtor'
        assert transacao_enviada.status == TransactionStatus.FINALIZADO
        assert transacao_enviada.transferencia_concluida is True
        
        # Verificar auditoria
        logs = LogAuditoria.query.filter(
            LogAuditoria.acao.contains("RESOLUCAO_DISPUTA")
        ).all()
        
        assert len(logs) > 0
        assert logs[0].usuario_id == admin_user.id
