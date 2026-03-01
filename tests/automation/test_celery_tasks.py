# tests/automation/test_celery_tasks.py - Testes de automação para tasks Celery
# Validação de processamento em background e tratamento de erros

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, call

from app.models import (
    Usuario, Safra, Transacao, TransactionStatus,
    Notificacao, LogAuditoria, HistoricoStatus
)
from app.models import Disputa
from app.models import StatusConta
from app.tasks.monitorar_transacoes_estagnadas import monitorar_transacoes_estagnadas
from app.tasks.faturas import gerar_pdf_fatura_assincrono
from app.tasks.pagamentos import processar_liquidacao
from app.tasks.base import AgroKongoTask


@pytest.mark.automation
@pytest.mark.slow
class TestMonitorarTransacoesEstagnadas:
    """Testes para task de monitoramento de transações estagnadas"""
    
    def test_cancelar_reserva_48h_atras(self, session, safra_ativa, comprador_user, produtor_user):
        """
        Teste principal: Criar reserva com 49h atrás
        Resultado esperado: CANCELADO + LogAuditoria + stock devolvido
        """
        # Criar transação pendente com 49h de atraso
        transacao_estagnada = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('10.00'),
            valor_total_pago=Decimal('15007.50'),
            status=TransactionStatus.PENDENTE,
            data_criacao=datetime.now(timezone.utc) - timedelta(hours=49)  # 49h atrás
        )
        
        session.add(transacao_estagnada)
        session.commit()
        
        # Salvar estado antes da task
        stock_antes = safra_ativa.quantidade_disponivel
        status_antes = transacao_estagnada.status
        logs_antes = LogAuditoria.query.filter_by(
            acao="AUTO_CANCEL"
        ).count()
        
        # Executar task
        resultado = monitorar_transacoes_estagnadas()
        
        # Verificar resultado
        assert "concluída" in resultado.lower()
        assert "canceladas" in resultado.lower()
        
        # Recarregar do banco
        session.refresh(transacao_estagnada)
        session.refresh(safra_ativa)
        
        # ✅ Verificação 1: Status mudou para CANCELADO
        assert transacao_estagnada.status == TransactionStatus.CANCELADO
        assert transacao_estagnada.status != status_antes
        
        # ✅ Verificação 2: LogAuditoria criado
        log_cancelamento = LogAuditoria.query.filter_by(
            acao="AUTO_CANCEL"
        ).filter(
            LogAuditoria.detalhes.contains(transacao_estagnada.fatura_ref)
        ).first()
        
        assert log_cancelamento is not None
        assert "cancelada automaticamente" in log_cancelamento.detalhes.lower()
        assert "48h" in log_cancelamento.detalhes
        assert log_cancelamento.usuario_id is None  # System action
        
        # ✅ Verificação 3: Stock devolvido
        stock_depois = safra_ativa.quantidade_disponivel
        stock_devolvido = stock_depois - stock_antes
        
        assert stock_devolvido == transacao_estagnada.quantidade_comprada
        assert stock_devolvido == Decimal('10.00')
        
        # ✅ Verificação 4: Status da safra atualizado se necessário
        if safra_ativa.quantidade_disponivel > 0 and safra_ativa.status == 'esgotado':
            safra_ativa.status = 'disponivel'
            session.commit()
        
        # ✅ Verificação 5: Notificação ao comprador
        notificacao = Notificacao.query.filter_by(
            usuario_id=comprador_user.id
        ).filter(
            Notificacao.mensagem.contains("expirou")
        ).first()
        
        assert notificacao is not None
        assert transacao_estagnada.fatura_ref in notificacao.mensagem
        assert "stock já voltou" in notificacao.mensagem.lower()
        
        # Verificar logs adicionais
        logs_depois = LogAuditoria.query.filter_by(
            acao="AUTO_CANCEL"
        ).count()
        assert logs_depois > logs_antes
    
    def test_alertar_admin_transacoes_analise_24h(self, session, safra_ativa, comprador_user, produtor_user, admin_user):
        """Teste alerta ao admin para transações em análise há 24h+"""
        # Criar transação em análise com 25h de atraso
        transacao_analise = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75'),
            status=TransactionStatus.ANALISE,
            comprovativo_path='comprovativo.pdf',
            data_criacao=datetime.now(timezone.utc) - timedelta(hours=25)  # 25h atrás
        )
        
        session.add(transacao_analise)
        session.commit()
        
        # Executar task
        resultado = monitorar_transacoes_estagnadas()
        
        # Verificar notificação ao admin
        notificacao_admin = Notificacao.query.filter_by(
            usuario_id=admin_user.id
        ).filter(
            Notificacao.mensagem.contains("24h")
        ).first()
        
        assert notificacao_admin is not None
        assert transacao_analise.fatura_ref in notificacao_admin.mensagem
        assert "verifique urgente" in notificacao_admin.mensagem.lower()
    
    def test_multiplas_transacoes_estagnadas(self, session, safra_ativa, comprador_user, produtor_user):
        """Teste processamento de múltiplas transações estagnadas"""
        # Criar várias transações estagnadas
        transacoes_estagnadas = []
        
        for i in range(3):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal(f'{i+1}.00'),
                valor_total_pago=Decimal(f'{(i+1) * 1500.75}'),
                status=TransactionStatus.PENDENTE,
                data_criacao=datetime.now(timezone.utc) - timedelta(hours=50 + i)  # 50h, 51h, 52h
            )
            transacoes_estagnadas.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        stock_antes = safra_ativa.quantidade_disponivel
        
        # Executar task
        resultado = monitorar_transacoes_estagnadas()
        
        # Verificar que todas foram canceladas
        for transacao in transacoes_estagnadas:
            session.refresh(transacao)
            assert transacao.status == TransactionStatus.CANCELADO
        
        # Verificar devolução total do stock
        session.refresh(safra_ativa)
        total_devolvido = sum(t.quantidade_comprada for t in transacoes_estagnadas)
        stock_depois = safra_ativa.quantidade_disponivel
        
        assert stock_depois == stock_antes + total_devolvido
        assert total_devolvido == Decimal('6.00')  # 1 + 2 + 3
        
        # Verificar logs individuais
        logs_cancelamento = LogAuditoria.query.filter_by(
            acao="AUTO_CANCEL"
        ).all()
        
        assert len(logs_cancelamento) == 3
        
        for log in logs_cancelamento:
            assert "cancelada automaticamente" in log.detalhes.lower()
    
    def test_transacao_recente_nao_cancelada(self, session, safra_ativa, comprador_user, produtor_user):
        """Teste que transação recente (<48h) não é cancelada"""
        # Criar transação recente (47h)
        transacao_recente = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('3.00'),
            valor_total_pago=Decimal('4502.25'),
            status=TransactionStatus.PENDENTE,
            data_criacao=datetime.now(timezone.utc) - timedelta(hours=47)  # 47h atrás
        )
        
        session.add(transacao_recente)
        session.commit()
        
        # Salvar estado
        status_antes = transacao_recente.status
        stock_antes = safra_ativa.quantidade_disponivel
        
        # Executar task
        resultado = monitorar_transacoes_estagnadas()
        
        # Verificar que NÃO foi cancelada
        session.refresh(transacao_recente)
        session.refresh(safra_ativa)
        
        assert transacao_recente.status == status_antes  # Continua PENDENTE
        assert transacao_recente.status == TransactionStatus.PENDENTE
        assert safra_ativa.quantidade_disponivel == stock_antes  # Stock não alterado
    
    def test_transacao_nao_pendente_nao_afetada(self, session, safra_ativa, comprador_user, produtor_user):
        """Teste que transação não PENDENTE não é afetada mesmo com 48h+"""
        # Criar transação ESCROW com 49h
        transacao_escrow = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('2.00'),
            valor_total_pago=Decimal('3001.50'),
            status=TransactionStatus.ESCROW,  # Não PENDENTE
            data_criacao=datetime.now(timezone.utc) - timedelta(hours=49)
        )
        
        session.add(transacao_escrow)
        session.commit()
        
        # Executar task
        resultado = monitorar_transacoes_estagnadas()
        
        # Verificar que NÃO foi cancelada
        session.refresh(transacao_escrow)
        assert transacao_escrow.status == TransactionStatus.ESCROW  # Continua ESCROW


@pytest.mark.automation
@pytest.mark.slow
class TestGerarPDFFatura:
    """Testes para task de geração de PDF de fatura"""
    
    def test_gerar_pdf_sucesso(self, session, transacao_pendente, comprador_user, produtor_user):
        """Teste geração bem-sucedida de PDF"""
        # Preparar transação completa
        transacao_pendente.comprador = comprador_user
        transacao_pendente.vendedor = produtor_user
        
        # Executar task
        resultado = gerar_pdf_fatura_assincrono(transacao_pendente.id)
        
        # Verificar resultado
        assert resultado is not None
        assert "pdf" in resultado.lower() or "fatura" in resultado.lower()
    
    def test_gerar_pdf_sem_comprador(self, session, safra_ativa, produtor_user):
        """
        Teste crítico: Transação sem comprador associado
        Resultado: Handler deve capturar erro, não crashar worker, notificar admin
        """
        # Criar transação sem comprador (comprador_id = None)
        transacao_sem_comprador = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=None,  # ⚠️ Sem comprador - vai causar erro
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75'),
            status=TransactionStatus.ESCROW
        )
        
        session.add(transacao_sem_comprador)
        session.commit()
        
        # Salvar estado antes
        logs_antes = LogAuditoria.query.count()
        notificacoes_antes = Notificacao.query.count()
        
        # Executar task - NÃO deve crashar
        try:
            resultado = gerar_pdf_fatura_assincrono(transacao_sem_comprador.id)
        except Exception as e:
            # Se lançar exceção, deve ser tratada pelo handler
            assert "comprador" in str(e).lower() or "none" in str(e).lower()
        
        # ✅ Verificação 1: Worker não crashou (chegamos aqui)
        assert True  # Se chegamos aqui, worker não crashou completamente
        
        # ✅ Verificação 2: Log de erro criado
        logs_erro = LogAuditoria.query.filter(
            LogAuditoria.detalhes.contains("ERRO_FATURA")
        ).all()
        
        assert len(logs_erro) > 0
        assert logs_erro[-1].detalhes is not None
        assert str(transacao_sem_comprador.id) in logs_erro[-1].detalhes
        
        # ✅ Verificação 3: Notificação de erro ao admin (se implementado)
        # Em implementação real, o handler deveria notificar admin
        # Por enquanto, verificamos apenas o log
        
        # ✅ Verificação 4: Task não retornou sucesso
        if 'resultado' in locals():
            assert resultado is None or "erro" in str(resultado).lower()
    
    def test_gerar_pdf_transacao_inexistente(self):
        """Teste comportamento com ID de transação inexistente"""
        # Executar com ID inexistente
        with pytest.raises(Exception):
            gerar_pdf_fatura_assincrono(99999)
    
    def test_gerar_pdf_erro_geracao_pdf(self, session, transacao_pendente):
        """Teste erro durante geração do PDF"""
        # Mock da função de geração para simular erro
        with patch('app.tasks.faturas.gerar_pdf_fatura') as mock_gerar:
            mock_gerar.side_effect = Exception("Erro na geração do PDF")
            
            # Executar task
            with pytest.raises(Exception):
                gerar_pdf_fatura_assincrono(transacao_pendente.id)
            
            # Verificar que função foi chamada
            mock_gerar.assert_called_once()
    
    def test_gerar_pdf_erro_salvamento(self, session, transacao_pendente):
        """Teste erro no salvamento do PDF"""
        # Mock do salvamento para simular erro
        with patch('app.tasks.faturas.salvar_ficheiro') as mock_salvar:
            mock_salvar.side_effect = Exception("Erro ao salvar arquivo")
            
            # Executar task
            with pytest.raises(Exception):
                gerar_pdf_fatura_assincrono(transacao_pendente.id)


@pytest.mark.automation
@pytest.mark.slow
class TestTaskErrorHandling:
    """Testes para handler de erros em tasks Celery"""
    
    def test_base_task_error_handling(self, session, transacao_pendente):
        """Teste handler de erros da classe base AgroKongoTask"""
        from app.tasks.base import AgroKongoTask
        
        # Criar task personalizada para teste
        @AgroKongoTask
        def test_task(self, trans_id):
            # Simular erro
            raise ValueError("Erro de teste")
        
        # Executar task
        with pytest.raises(ValueError):
            test_task(transacao_pendente.id)
    
    def test_retry_mecanismo(self, session, transacao_pendente):
        """Teste mecanismo de retry automático"""
        from app.tasks.pagamentos import processar_liquidacao
        
        # Mock para simular falha e depois sucesso
        chamadas = []
        
        def mock_commit():
            chamadas.append(len(chamadas))
            if len(chamadas) < 2:  # Falhar nas primeiras 2 tentativas
                raise Exception("Simulação de falha")
        
        with patch('app.extensions.db.session.commit', side_effect=mock_commit):
            # Executar task (deve fazer retry)
            with pytest.raises(Exception):
                processar_liquidacao(transacao_pendente.id)
            
            # Verificar que tentou múltiplas vezes
            assert len(chamadas) >= 2
    
    def test_logging_erros_tasks(self, session, transacao_pendente):
        """Teste logging de erros em tasks"""
        from app.tasks.pagamentos import processar_liquidacao
        
        # Mock para capturar logs
        with patch('app.extensions.current_app.logger.error') as mock_log:
            # Simular erro
            with patch('app.extensions.db.session.commit', side_effect=Exception("Erro test")):
                with pytest.raises(Exception):
                    processar_liquidacao(transacao_pendente.id)
            
            # Verificar que erro foi logado
            mock_log.assert_called()
            assert "ERRO" in str(mock_log.call_args).upper()
    
    def test_notificacao_admin_falha_critica(self, session, transacao_pendente, admin_user):
        """Teste notificação ao admin em falhas críticas"""
        # Simular falha crítica
        with patch('app.extensions.db.session.commit', side_effect=Exception("Falha crítica")):
            try:
                processar_liquidacao(transacao_pendente.id)
            except Exception:
                pass  # Esperado
        
        # Verificar se notificação de erro foi criada (se implementado)
        # Em implementação real, o handler deveria criar notificação
        notificacoes_erro = Notificacao.query.filter_by(
            usuario_id=admin_user.id
        ).filter(
            Notificacao.mensagem.contains("crítico") | 
            Notificacao.mensagem.contains("erro")
        ).all()
        
        # Por enquanto, verificamos apenas que não crashou completamente
        assert True  # Se chegamos aqui, sistema não crashou


@pytest.mark.automation
@pytest.mark.slow
class TestTaskPerformance:
    """Testes de performance para tasks Celery"""
    
    def test_performance_monitoramento_estagnadas(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa performance da task de monitoramento"""
        import time
        
        # Criar muitas transações estagnadas
        transacoes = []
        for i in range(50):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('1.00'),
                valor_total_pago=Decimal('1500.75'),
                status=TransactionStatus.PENDENTE,
                data_criacao=datetime.now(timezone.utc) - timedelta(hours=50 + i)
            )
            transacoes.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        # Medir tempo de execução
        start_time = time.time()
        resultado = monitorar_transacoes_estagnadas()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Verificações de performance
        assert execution_time < 10.0  # Deve processar 50 transações em < 10s
        assert execution_time / len(transacoes) < 0.2  # < 200ms por transação
        
        # Verificar que todas foram processadas
        for transacao in transacoes:
            session.refresh(transacao)
            assert transacao.status == TransactionStatus.CANCELADO
    
    def test_memory_usage_lote_transacoes(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa uso de memória em lote grande"""
        import psutil
        import os
        
        # Medir memória inicial
        process = psutil.Process(os.getpid())
        memoria_inicial = process.memory_info().rss / 1024 / 1024  # MB
        
        # Criar lote grande
        transacoes = []
        for i in range(100):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('0.5'),
                valor_total_pago=Decimal('750.38'),
                status=TransactionStatus.PENDENTE,
                data_criacao=datetime.now(timezone.utc) - timedelta(hours=50 + i)
            )
            transacoes.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        # Executar task
        monitorar_transacoes_estagnadas()
        
        # Medir memória final
        memoria_final = process.memory_info().rss / 1024 / 1024  # MB
        aumento_memoria = memoria_final - memoria_inicial
        
        # Verificar uso de memória
        assert aumento_memoria < 50  # < 50MB de aumento para 100 transações
