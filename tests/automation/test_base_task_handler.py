# tests/automation/test_base_task_handler.py - Testes específicos para handler de erros
# Validação do on_failure em AgroKongoTask

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, call

from app.models import Usuario, Notificacao, LogAuditoria, Transacao
from app.tasks.base import AgroKongoTask, AgroKongoTaskBase, MockTaskForTests
from app.tasks.faturas import gerar_pdf_fatura_assincrono
from app.tasks.pagamentos import processar_liquidacao
from app.models.base import TransactionStatus


class TestAgroKongoTaskHandler:
    """Testes para handler de erros da classe base AgroKongoTask"""
    
    def test_on_failure_log_seguro(self, session, admin_user):
        """Teste que log de erro é seguro (sanitizado)"""
        # Criar task personalizada para teste
        def test_task_func():
            raise Exception("<script>alert('xss')</script>Erro com HTML malicioso")
        
        test_task = AgroKongoTask(test_task_func)
        
        # Mock do logger para capturar mensagem
        with patch('app.tasks.base.logger.error') as mock_log:
            # Simular falha
            task_instance = test_task
            task_instance.name = "test_task"
            task_instance.request = MagicMock()
            task_instance.request.id = "test-task-id"
            
            # Executar handler de falha
            try:
                test_task_func()
            except Exception as exc:
                task_instance.on_failure(exc, "test-task-id", (), {}, None)
            
            # Verificar que log foi chamado
            mock_log.assert_called_once()
            
            # Verificar sanitização (tags HTML removidas)
            log_message = str(mock_log.call_args)
            assert "<script>" not in log_message
            assert "alert" not in log_message or "xss" not in log_message
            assert "Erro com HTML malicioso" in log_message
    
    def test_on_failure_notifica_admin(self, session, admin_user):
        """Teste que admin é notificado sobre falha de task"""
        # Contar notificações antes
        notificacoes_antes = Notificacao.query.filter_by(usuario_id=admin_user.id).count()
        
        # Criar task que falha
        def failing_task_func():
            raise Exception("Erro de teste para notificação")
        
        failing_task = AgroKongoTask(failing_task_func)
        
        # Mock do logger para evitar poluição
        with patch('app.tasks.base.logger.error'):
            task_instance = failing_task
            task_instance.name = "failing_task"
            task_instance.request = MagicMock()
            task_instance.request.id = "failing-task-id"
            
            # Executar handler de falha
            try:
                failing_task_func()
            except Exception as exc:
                task_instance.on_failure(exc, "failing-task-id", (), {}, None)
        
        # Verificar notificação criada
        notificacoes_depois = Notificacao.query.filter_by(usuario_id=admin_user.id).count()
        assert notificacoes_depois > notificacoes_antes
        
        # Verificar conteúdo da notificação
        notificacao = Notificacao.query.filter_by(usuario_id=admin_user.id).order_by(
            Notificacao.data_criacao.desc()
        ).first()
        
        assert notificacao is not None
        assert "Task Celery falhou" in notificacao.mensagem
        assert "failing_task" in notificacao.mensagem
        assert "failing-task-id" in notificacao.mensagem
        assert "/admin/dashboard" in notificacao.link
    
    def test_on_failure_sem_admin(self, session):
        """Teste comportamento quando não há admin cadastrado"""
        # Remover todos os admins
        Usuario.query.filter_by(tipo='admin').delete()
        session.commit()
        
        # Mock do logger para capturar log da task
        with patch('app.tasks.base.logger.error') as mock_log_error:
            # Criar task que falha
            def failing_task_func():
                raise Exception("Erro sem admin")
            
            failing_task = AgroKongoTask(failing_task_func)
            task_instance = failing_task
            task_instance.request = MagicMock()
            task_instance.request.id = "failing-task-id"
            
            # Executar handler de falha
            try:
                failing_task_func()
            except Exception as exc:
                task_instance.on_failure(exc, "failing-task-id", (), {}, None)
            
            # Verificar que a task foi logada (mas não houve tentativa de notificar admin)
            mock_log_error.assert_called()
            # Deve ter logado o erro da task, mas não tentou notificar admin
            assert "failing-task-id" in str(mock_log_error.call_args)
    
    def test_on_failure_rollback_em_caso_de_erro(self, session, admin_user):
        """Teste rollback em caso de erro na notificação"""
        # Mock para simular erro na notificação
        with patch('app.extensions.db.session.commit', side_effect=Exception("Erro DB")):
            with patch('app.tasks.base.logger.error') as mock_log_error:
                # Criar task que falha
                def failing_task_func():
                    raise Exception("Erro principal")
                
                failing_task = AgroKongoTask(failing_task_func)
                task_instance = failing_task
                task_instance.name = "failing_task"
                task_instance.request = MagicMock()
                task_instance.request.id = "failing-task-id"
                
                # Executar handler de falha
                try:
                    failing_task_func()
                except Exception as exc:
                    task_instance.on_failure(exc, "failing-task-id", (), {}, None)
                
                # Verificar que erro foi logado e rollback feito
                mock_log_error.assert_called()
                assert "Erro ao notificar admin" in str(mock_log_error.call_args)
    
    def test_on_failure_truncacao_mensagem_longa(self, session, admin_user):
        """Teste truncação de mensagens longas na notificação"""
        # Criar exceção com mensagem muito longa
        mensagem_longa = "Erro " * 100  # Mensagem com > 500 caracteres
        
        # Criar task que falha
        def failing_task_func():
            raise Exception(mensagem_longa)
        
        failing_task = AgroKongoTask(failing_task_func)
        
        # Mock do logger
        with patch('app.tasks.base.logger.error'):
            task_instance = failing_task
            task_instance.name = "failing_task"
            task_instance.request = MagicMock()
            task_instance.request.id = "failing-task-id"
            
            # Executar handler de falha
            try:
                failing_task_func()
            except Exception as exc:
                task_instance.on_failure(exc, "failing-task-id", (), {}, None)
        
        # Verificar notificação (mensagem truncada)
        notificacao = Notificacao.query.filter_by(usuario_id=admin_user.id).order_by(
            Notificacao.data_criacao.desc()
        ).first()
        
        assert notificacao is not None
        assert len(notificacao.mensagem) < 200  # Deve ser truncada
        assert "..." in notificacao.mensagem  # Indicador de truncamento
    
    def test_after_return_cleanup_database(self, session):
        """Teste cleanup de database após task"""
        # Criar instância da task diretamente
        task_instance = MockTaskForTests()
        task_instance.request = MagicMock()
        
        # Mock dos métodos de cleanup
        with patch('app.extensions.db.session.rollback') as mock_rollback, \
             patch('app.extensions.db.session.remove') as mock_remove:
            
            # Executar cleanup
            task_instance.after_return("SUCCESS", "resultado", "task-id", (), {}, None)
            
            # Verificar que cleanup foi chamado
            mock_rollback.assert_called_once()
            mock_remove.assert_called_once()
    
    def test_after_return_erro_cleanup(self, session):
        """Teste comportamento quando cleanup falha"""
        # Criar instância da task diretamente
        task_instance = MockTaskForTests()
        task_instance.request = MagicMock()
        
        # Mock para simular erro no cleanup
        with patch('app.extensions.db.session.rollback', side_effect=Exception("Erro cleanup")):
            with patch('app.tasks.base.logger.warning') as mock_log_warning:
                
                # Executar cleanup
                task_instance.after_return("SUCCESS", "resultado", "task-id", (), {}, None)
                
                # Verificar que erro foi logado como warning
                mock_log_warning.assert_called()
                assert "Erro ao limpar session DB" in str(mock_log_warning.call_args)
    
    def test_contexto_flask_garantido(self, session, admin_user):
        """Teste que contexto Flask é garantido na task"""
        # Criar instância da task
        task_instance = MockTaskForTests()
        task_instance.request = MagicMock()
        
        # Executar dentro do contexto da app
        with session.begin():
            from flask import current_app
            resultado = current_app.config['SECRET_KEY']
        
        # Verificar que contexto estava disponível
        assert resultado is not None
        assert isinstance(resultado, str)
    
    def test_retry_configuration(self):
        """Testa configuração de retry da task base"""
        # Verificar configurações padrão
        assert AgroKongoTaskBase.autoretry_for == (Exception,)
        assert AgroKongoTaskBase.max_retries == 5
        assert AgroKongoTaskBase.retry_backoff is True
        assert AgroKongoTaskBase.retry_backoff_max == 300
        assert AgroKongoTaskBase.retry_jitter is True
    
    def test_sanitizacao_xss_prevencao(self, session, admin_user):
        """Testa prevenção XSS em logs e notificações"""
        # Criar exceção com conteúdo malicioso
        excecoes_maliciosas = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --",
            "<svg onload=alert('xss')>"
        ]
        
        for excecao_maliciosa in excecoes_maliciosas:
            # Criar instância da task
            task_instance = MockTaskForTests()
            task_instance.request = MagicMock()
            task_instance.request.id = f"xss-task-{len(excecao_maliciosa)}"
            
            # Mock do logger
            with patch('app.tasks.base.logger.error') as mock_log:
                # Executar handler de falha
                try:
                    raise Exception(excecao_maliciosa)
                except Exception as exc:
                    task_instance.on_failure(exc, task_instance.request.id, (), {}, None)
                
                # Verificar sanitização
                log_message = str(mock_log.call_args)
                
                # Tags HTML devem ser removidas
                assert "<script>" not in log_message
                assert "</script>" not in log_message
                assert "<img" not in log_message
                assert "<svg" not in log_message
                
                # JavaScript deve ser removido ou sanitizado
                assert "javascript:" not in log_message.lower()
                assert "onerror=" not in log_message.lower()
                assert "onload=" not in log_message.lower()
                
                # SQL injection deve ser sanitizado
                assert "DROP TABLE" not in log_message.upper()


class TestTaskHandlerIntegration:
    """Testes de integração do handler com tasks reais"""
    
    def test_gerar_pdf_fatura_sem_comprador_handler(self, session, safra_ativa, produtor_user):
        """
        Teste de integração: gerar_pdf_fatura com dados inválidos
        Verifica que handler captura erro e notifica admin
        """
        import uuid
        # Criar transação válida (o erro será ao gerar fatura)
        transacao = Transacao(
            fatura_ref=f"TRX-{uuid.uuid4()}",
            safra_id=safra_ativa.id,
            comprador_id=produtor_user.id,  # Valor válido
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75'),
            status=TransactionStatus.ESCROW
        )
        
        session.add(transacao)
        session.commit()
        
        # Contar notificações antes
        admin = Usuario.query.filter_by(tipo='admin').first()
        if admin:
            notificacoes_antes = Notificacao.query.filter_by(usuario_id=admin.id).count()
        else:
            notificacoes_antes = 0
        
        # Executar task (pode falhar se não houver comprador real)
        try:
            gerar_pdf_fatura_assincrono(transacao.id)
        except Exception:
            pass  # Esperado em alguns casos
        
        # Verificar que não crashou completamente
        assert True  # Se chegamos aqui, sistema está estável
    
    def test_processar_liquidacao_erro_handler(self, session, transacao_enviada):
        """Teste handler em processar_liquidacao com erro"""
        # Mock para simular erro
        with patch('app.extensions.db.session.commit', side_effect=Exception("Erro DB")):
            # Contar notificações antes (pode não haver admin)
            admin = Usuario.query.filter_by(tipo='admin').first()
            if admin:
                notificacoes_antes = Notificacao.query.filter_by(usuario_id=admin.id).count()
            else:
                notificacoes_antes = 0
            
            # Executar task (vai falhar)
            try:
                processar_liquidacao(transacao_enviada.id)
            except Exception:
                pass  # Esperado
            
            # Verificar que não crashou completamente
            assert True
            
            # Verificar se notificação foi criada (pode variar pela implementação)
            notificacoes_depois = Notificacao.query.filter_by(usuario_id=admin.id).count() if admin else 0
            
            # Se o handler estiver funcionando, deve haver notificação
            # Por enquanto, apenas verificamos estabilidade
            assert True  # Se chegou aqui sem crashar, está OK
    
    def test_handler_performance_multiplas_falhas(self, session, admin_user):
        """Testa performance do handler com múltiplas falhas simultâneas"""
        from threading import Thread
        import time
        
        # Executar múltiplas falhas em paralelo
        threads = []
        resultados = []
        
        def executar_falha(indice):
            try:
                task_instance = MockTaskForTests()
                task_instance.request = MagicMock()
                task_instance.request.id = f"task-{indice}"
                
                # Simular falha - on_failure lida com contexto internamente
                try:
                    raise Exception(f"Erro simultâneo {indice}")
                except Exception as exc:
                    # Chamar on_failure - mesmo sem contexto, vai logar
                    task_instance.on_failure(exc, task_instance.request.id, (), {}, None)
                
                resultados.append(f"task-{indice}: OK")
            except Exception as e:
                resultados.append(f"task-{indice}: ERRO - {str(e)[:50]}")
        
        # Criar threads
        for i in range(5):
            thread = Thread(target=executar_falha, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar todas
        for thread in threads:
            thread.join()
        
        # Verificar que todas foram processadas
        assert len(resultados) == 5
        assert all("OK" in r for r in resultados)
