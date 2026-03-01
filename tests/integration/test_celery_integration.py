# tests/integration/test_celery_integration.py - Testes de integração com Celery
# Validação de tasks assíncronas e comunicação Flask + Celery + Redis

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import Transacao, TransactionStatus, Usuario, Notificacao
from app.models import Disputa
from app.tasks.pagamentos import processar_liquidacao
from app.tasks.notificacoes_disputas import enviar_notificacao_disputa_async
from app.tasks.monitorar_transacoes_estagnadas import monitorar_transacoes_estagnadas


@pytest.mark.integration
@pytest.mark.slow
class TestCeleryIntegration:
    """Testes de integração com Celery para tasks assíncronas"""
    
    @patch('app.tasks.pagamentos.enviar_fatura_email')
    def test_processar_liquidacao_sucesso(self, mock_email, session, transacao_enviada, produtor_user):
        """Testa processamento assíncrono de liquidação com sucesso"""
        # Preparar transação para liquidação
        transacao_enviada.status = TransactionStatus.ENTREGUE
        transacao_enviada.data_entrega = datetime.now(timezone.utc)
        session.commit()
        
        # Salvar estado antes
        saldo_antes = produtor_user.saldo_disponivel or Decimal('0.00')
        status_antes = transacao_enviada.status
        
        # Executar task (simulação assíncrona)
        resultado = processar_liquidacao(transacao_enviada.id)
        
        # Verificar resultado
        assert resultado == "Liquidação concluída"
        
        # Recarregar do banco
        session.refresh(transacao_enviada)
        session.refresh(produtor_user)
        
        # Verificar mudanças
        assert transacao_enviada.status == TransactionStatus.FINALIZADO
        assert transacao_enviada.transferencia_concluida is True
        assert transacao_enviada.data_liquidacao is not None
        
        # Verificar crédito no saldo
        saldo_depois = produtor_user.saldo_disponivel
        aumento = saldo_depois - saldo_antes
        assert aumento == transacao_enviada.valor_liquido_vendedor
        
        # Verificar notificações
        notificacoes_vendedor = Notificacao.query.filter_by(
            usuario_id=produtor_user.id
        ).filter(
            Notificacao.mensagem.contains("Liquidação concluída")
        ).count()
        
        assert notificacoes_vendedor > 0
        
        # Verificar se email foi disparado
        mock_email.assert_called()
    
    def test_processar_liquidacao_transacao_invalida(self, session):
        """Testa processamento com transação inexistente"""
        with pytest.raises(ValueError, match="não encontrada"):
            processar_liquidacao(99999)  # ID inexistente
    
    def test_processar_liquidacao_status_incorreto(self, session, transacao_pendente):
        """Testa processamento com status incorreto"""
        # Tentar processar transação não entregue
        with pytest.raises(ValueError, match="inválida para liquidação"):
            processar_liquidacao(transacao_pendente.id)
    
    def test_processar_liquidacao_concorrente(self, session, transacao_enviada, produtor_user):
        """Testa processamento concorrente da mesma transação"""
        # Preparar transação
        transacao_enviada.status = TransactionStatus.ENTREGUE
        transacao_enviada.data_entrega = datetime.now(timezone.utc)
        session.commit()
        
        # Simular duas tentativas simultâneas
        from threading import Thread
        resultados = []
        
        def liquidar():
            try:
                resultado = processar_liquidacao(transacao_enviada.id)
                resultados.append(resultado)
            except Exception as e:
                resultados.append(str(e))
        
        # Executar threads simultâneas
        thread1 = Thread(target=liquidar)
        thread2 = Thread(target=liquidar)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Apenas uma deve ter sucesso
        sucessos = [r for r in resultados if r == "Liquidação concluída"]
        assert len(sucessos) == 1
        
        # Verificar estado final
        session.refresh(transacao_enviada)
        assert transacao_enviada.status == TransactionStatus.FINALIZADO
    
    @patch('app.tasks.pagamentos.processar_liquidacao.retry')
    def test_processar_liquidacao_retry_erro(self, mock_retry, session, transacao_enviada):
        """Testa retry automático em caso de erro"""
        # Simular erro de banco
        with patch('app.extensions.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("Erro de conexão")
            
            # Executar task
            with pytest.raises(Exception):
                processar_liquidacao(transacao_enviada.id)
            
            # Verificar se retry foi chamado
            mock_retry.assert_called()
    
    def test_enviar_notificacao_disputa_abertura(self, session, transacao_enviada, comprador_user, admin_user):
        """Testa envio de notificação de abertura de disputa"""
        # Criar disputa
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Teste de disputa",
            status='aberta'
        )
        session.add(disputa)
        session.commit()
        
        # Executar task
        resultado = enviar_notificacao_disputa_async(
            disputa_id=disputa.id,
            tipo_notificacao='abertura'
        )
        
        # Verificar resultado
        assert "abertura" in resultado
        assert str(disputa.id) in resultado
        
        # Verificar notificações criadas
        notificacoes_admin = Notificacao.query.filter_by(
            usuario_id=admin_user.id
        ).filter(
            Notificacao.mensagem.contains("Nova disputa")
        ).count()
        
        assert notificacoes_admin > 0
        
        notificacoes_produtor = Notificacao.query.filter_by(
            usuario_id=transacao_enviada.vendedor_id
        ).filter(
            Notificacao.mensagem.contains("Disputa aberta")
        ).count()
        
        assert notificacoes_produtor > 0
    
    def test_enviar_notificacao_disputa_resolucao(self, session, disputa_aberta, admin_user):
        """Testa envio de notificação de resolução de disputa"""
        # Executar task de resolução
        resultado = enviar_notificacao_disputa_async(
            disputa_id=disputa_aberta.id,
            tipo_notificacao='resolucao',
            decisao='comprador',
            admin_nome='Admin Test'
        )
        
        # Verificar resultado
        assert "resolucao" in resultado
        assert str(disputa_aberta.id) in resultado
        
        # Verificar notificações de resolução
        notificacoes = Notificacao.query.filter(
            Notificacao.mensagem.contains("resolvida")
        ).all()
        
        assert len(notificacoes) >= 2  # Comprador e produtor
    
    def test_monitorar_transacoes_estagnadas(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa task de monitoramento de transações estagnadas"""
        # Criar transação pendente antiga (+48h)
        transacao_antiga = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75'),
            status=TransactionStatus.PENDENTE,
            data_criacao=datetime.now(timezone.utc) - timedelta(hours=50)  # 50h atrás
        )
        session.add(transacao_antiga)
        session.commit()
        
        # Salvar estado antes
        stock_antes = safra_ativa.quantidade_disponivel
        status_antes = transacao_antiga.status
        
        # Executar task
        resultado = monitorar_transacoes_estagnadas()
        
        # Verificar resultado
        assert "concluída" in resultado.lower()
        
        # Recarregar do banco
        session.refresh(transacao_antiga)
        session.refresh(safra_ativa)
        
        # Verificar cancelamento e devolução de stock
        assert transacao_antiga.status == TransactionStatus.CANCELADO
        assert safra_ativa.quantidade_disponivel == stock_antes + transacao_antiga.quantidade_comprada
        
        # Verificar notificação ao comprador
        notificacao = Notificacao.query.filter_by(
            usuario_id=comprador_user.id
        ).filter(
            Notificacao.mensagem.contains("expirou")
        ).first()
        
        assert notificacao is not None


@pytest.mark.integration
@pytest.mark.slow
class TestCeleryPerformance:
    """Testes de performance das tasks Celery"""
    
    def test_performance_liquidacao_batch(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa performance de liquidação em lote"""
        # Criar múltiplas transações para liquidação
        transacoes = []
        for i in range(10):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('1.00'),
                valor_total_pago=Decimal('1500.75'),
                status=TransactionStatus.ENTREGUE,
                data_entrega=datetime.now(timezone.utc)
            )
            transacoes.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        # Medir tempo de processamento
        start_time = datetime.now()
        
        # Processar em lote
        for transacao in transacoes:
            processar_liquidacao(transacao.id)
        
        end_time = datetime.now()
        tempo_total = (end_time - start_time).total_seconds()
        
        # Verificações de performance
        assert tempo_total < 5.0  # Deve processar 10 transações em < 5s
        assert tempo_total / len(transacoes) < 0.5  # < 500ms por transação
        
        # Verificar que todas foram processadas
        for transacao in transacoes:
            session.refresh(transacao)
            assert transacao.status == TransactionStatus.FINALIZADO
    
    def test_memory_usage_large_batch(self, session, safra_ativa, comprador_user, produtor_user):
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
                status=TransactionStatus.ENTREGUE,
                data_entrega=datetime.now(timezone.utc)
            )
            transacoes.append(transacao)
            session.add(transacao)
        
        session.commit()
        
        # Processar lote
        for transacao in transacoes:
            processar_liquidacao(transacao.id)
            session.refresh(transacao)
        
        # Medir memória final
        memoria_final = process.memory_info().rss / 1024 / 1024  # MB
        aumento_memoria = memoria_final - memoria_inicial
        
        # Verificar uso de memória (não deve aumentar drasticamente)
        assert aumento_memoria < 100  # < 100MB de aumento


@pytest.mark.integration
@pytest.mark.slow
class TestCeleryErrorHandling:
    """Testes de tratamento de erros em tasks Celery"""
    
    def test_task_com_excecao_nao_tratada(self, session, transacao_enviada):
        """Testa comportamento com exceção não tratada"""
        # Simular exceção no meio da task
        with patch('app.extensions.db.session.commit') as mock_commit:
            mock_commit.side_effect = [None, Exception("Erro inesperado")]
            
            # Executar task
            with pytest.raises(Exception):
                processar_liquidacao(transacao_enviada.id)
            
            # Verificar estado não foi alterado
            session.refresh(transacao_enviada)
            assert transacao_enviada.status != TransactionStatus.FINALIZADO
    
    def test_task_timeout(self, session, transacao_enviada):
        """Testa comportamento em caso de timeout"""
        # Simular operação muito lenta
        with patch('time.sleep') as mock_sleep:
            mock_sleep.side_effect = lambda x: None  # Não dormir realmente
            
            # Simular timeout após operação longa
            with patch('app.tasks.pagamentos.processar_liquidacao') as mock_task:
                mock_task.side_effect = Exception("Timeout simulado")
                
                with pytest.raises(Exception):
                    processar_liquidacao(transacao_enviada.id)
    
    def test_task_recursos_insuficientes(self, session, transacao_enviada):
        """Testa comportamento com recursos insuficientes"""
        # Simular erro de recursos
        with patch('sqlalchemy.orm.Session.commit') as mock_commit:
            mock_commit.side_effect = Exception("Recursos insuficientes")
            
            # Executar task
            resultado = processar_liquidacao(transacao_enviada.id)
            
            # Task deve lidar com erro gracefully
            assert resultado is None or "erro" in str(resultado).lower()


@pytest.mark.integration
@pytest.mark.slow
class TestCeleryConfiguration:
    """Testes de configuração do Celery"""
    
    def test_broker_connection(self):
        """Testa conexão com broker Redis"""
        from app import celery
        
        # Verificar configuração do broker
        assert celery.conf.broker_url is not None
        assert "redis" in celery.conf.broker_url.lower() or "memory" in celery.conf.broker_url.lower()
    
    def test_result_backend(self):
        """Testa configuração do result backend"""
        from app import celery
        
        # Verificar configuração do backend
        assert celery.conf.result_backend is not None
        assert "redis" in celery.conf.result_backend.lower() or "memory" in celery.conf.result_backend.lower()
    
    def test_task_registration(self):
        """Testa registro de tasks"""
        from app import celery
        
        # Verificar que tasks estão registradas
        tasks_registradas = celery.tasks.keys()
        
        assert 'app.tasks.pagamentos.processar_liquidacao' in tasks_registradas
        assert 'app.tasks.notificacoes_disputas.enviar_notificacao_disputa_async' in tasks_registradas
        assert 'app.tasks.monitorar_transacoes_estagnadas.monitorar_transacoes_estagnadas' in tasks_registradas
    
    def test_task_configurations(self):
        """Testa configurações específicas das tasks"""
        from app.tasks.pagamentos import processar_liquidacao
        
        # Verificar configurações da task
        assert hasattr(processar_liquidacao, 'rate_limit')
        assert hasattr(processar_liquidacao, 'max_retries')
        
        # Verificar limites razoáveis
        assert processar_liquidacao.max_retries <= 5
        assert processar_liquidacao.rate_limit is not None
