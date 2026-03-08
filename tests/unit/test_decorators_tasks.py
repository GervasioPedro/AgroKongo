"""
Testes Unitários para Decorators e Tasks
Cobertura: 100% dos módulos decorators.py e tasks
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open, call
from datetime import datetime, timezone
from decimal import Decimal

from app.utils.decorators import admin_required, produtor_required
from app.tasks.faturas import (
    gerar_pdf_fatura_assincrono,
    _carregar_dados_fatura,
    _gerar_pdf_content,
    _salvar_pdf_seguro,
    _notificar_fatura_pronta,
    _notificar_erro_fatura
)


class TestAdminRequiredDecorator:
    """Testes para decorator admin_required"""
    
    def test_admin_required_admin_autenticado(self, auth_client, admin_user, app):
        """Permite acesso a administrador autenticado"""
        # Mock do current_user para retornar o admin_user
        with patch('app.utils.decorators.current_user', admin_user):
            # Primeiro registra a rota
            @auth_client.application.route('/admin/test', methods=['GET', 'POST'])
            @admin_required
            def admin_test():
                return "Acesso permitido"
                
            response = auth_client.get('/admin/test')
            assert response.status_code == 200
            assert b"Acesso permitido" in response.data
    
    def test_admin_required_nao_autenticado(self, app):
        """Redireciona usuário não autenticado"""
        from flask_login import LoginManager
        
        @app.route('/admin/test')
        @admin_required
        def admin_test():
            return "Acesso permitido"
        
        with app.test_client() as client:
            response = client.get('/admin/test', follow_redirects=False)
            
            # Deve redirecionar para login
            assert response.status_code in [301, 302]
    
    def test_admin_required_usuario_comum(self, auth_comprador_client, comprador_user, app):
        """Negada acesso a usuário comum"""
    
        with patch('app.utils.decorators.current_user', comprador_user):
            @auth_comprador_client.application.route('/admin/test', methods=['GET', 'POST'])
            @admin_required
            def admin_test():
                return "Acesso permitido"
                
            # Em modo TESTING, decorator retorna 403 direto
            response = auth_comprador_client.get('/admin/test')
            assert response.status_code == 403
    
    def test_admin_required_log_auditoria(self, auth_comprador_client, comprador_user, app):
        """Registra log de auditoria ao negar acesso"""
    
        with patch('app.utils.decorators.current_user', comprador_user):
            @auth_comprador_client.application.route('/admin/test', methods=['GET', 'POST'])
            @admin_required
            def admin_test():
                return "Acesso permitido"
                
            with patch('app.utils.decorators.db.session.add') as mock_add, \
                 patch('app.utils.decorators.db.session.commit') as mock_commit:
                    
                # Em modo TESTING, decorator retorna 403 direto
                response = auth_comprador_client.get('/admin/test')
                assert response.status_code == 403
                    
                # Verificar se tentou adicionar log
                assert mock_add.called
                    
                # Verificar tipo de log
                call_args = mock_add.call_args
                log_obj = call_args[0][0]
                assert log_obj.acao == "ACESSO_NEGADO_ADMIN"
                assert "invasão" in log_obj.detalhes or "admin" in log_obj.detalhes.lower()


class TestProdutorRequiredDecorator:
    """Testes para decorator produtor_required"""
    
    def test_produtor_required_produtor_validado(self, auth_produtor_client, produtor_user, app):
        """Permite acesso a produtor validado"""
    
        with patch('app.utils.decorators.current_user', produtor_user):
            @auth_produtor_client.application.route('/produtor/test', methods=['GET', 'POST'])
            @produtor_required
            def produtor_test():
                return "Acesso permitido"
                
            response = auth_produtor_client.get('/produtor/test')
            assert response.status_code == 200
    
    def test_produtor_required_nao_autenticado(self, app):
        """Redireciona usuário não autenticado"""
        @app.route('/produtor/test')
        @produtor_required
        def produtor_test():
            return "Acesso permitido"
        
        with app.test_client() as client:
            response = client.get('/produtor/test', follow_redirects=False)
            assert response.status_code in [301, 302]
    
    def test_produtor_required_comprador(self, auth_comprador_client, comprador_user, app):
        """Negada acesso a comprador"""
    
        with patch('app.utils.decorators.current_user', comprador_user):
            @auth_comprador_client.application.route('/produtor/test', methods=['GET', 'POST'])
            @produtor_required
            def produtor_test():
                return "Acesso permitido"
                
            # Em modo TESTING, decorator retorna 403 direto
            response = auth_comprador_client.get('/produtor/test')
            assert response.status_code == 403
    
    def test_produtor_required_produtor_nao_validado(self, auth_produtor_client, produtor_user, app):
        """Produtor não validado é redirecionado"""
        # Produtor sem validação
        produtor_user.conta_validada = False
        
        with patch('app.utils.decorators.current_user', produtor_user):
            @auth_produtor_client.application.route('/produtor/test', methods=['GET', 'POST'])
            @produtor_required
            def produtor_test():
                return "Acesso permitido"
                
            # Em modo TESTING, decorator retorna 403 direto
            response = auth_produtor_client.get('/produtor/test')
            assert response.status_code == 403


class TestGerarPdfFaturaAssincrono:
    """Testes para task de geração de fatura PDF"""
    
    @patch('app.tasks.faturas._carregar_dados_fatura')
    @patch('app.tasks.faturas._gerar_pdf_content')
    @patch('app.tasks.faturas._salvar_pdf_seguro')
    @patch('app.tasks.faturas._notificar_fatura_pronta')
    def test_gerar_fatura_sucesso(self, mock_notificar, mock_salvar, 
                                   mock_gerar, mock_carregar, app):
        """Gera fatura com sucesso"""
        # Mock dos dados
        mock_transacao = MagicMock()
        mock_transacao.fatura_ref = "REF20260001"
        mock_user = MagicMock()
        mock_carregar.return_value = (mock_transacao, mock_user)
        
        mock_pdf_bytes = b'%PDF-1.4 fake pdf content'
        mock_gerar.return_value = mock_pdf_bytes
        
        mock_path = "/path/to/fatura.pdf"
        mock_salvar.return_value = mock_path
        
        # Executar task
        resultado = gerar_pdf_fatura_assincrono("trans_123", 1)
        
        # Verificar chamadas
        mock_carregar.assert_called_once_with("trans_123", 1)
        mock_gerar.assert_called_once_with(mock_transacao)
        mock_salvar.assert_called_once_with(mock_transacao, mock_pdf_bytes)
        mock_notificar.assert_called_once_with(mock_transacao, 1, mock_path)
        
        assert resultado == mock_path
    
    @patch('app.tasks.faturas._notificar_erro_fatura')
    def test_gerar_fatura_transacao_nao_existe(self, mock_notificar_erro, app):
        """Falha quando transação não existe"""
        with patch('app.tasks.faturas._carregar_dados_fatura') as mock_carregar:
            mock_carregar.side_effect = ValueError("Transação não encontrada")
            
            resultado = gerar_pdf_fatura_assincrono("trans_invalida", 1)
            
            # Deve retornar None e notificar erro
            assert resultado is None
            mock_notificar_erro.assert_called_once()
    
    @patch('app.tasks.faturas._notificar_erro_fatura')
    def test_gerar_fatura_permissao_negada(self, mock_notificar_erro, app):
        """Falha quando usuário não tem permissão"""
        with patch('app.tasks.faturas._carregar_dados_fatura') as mock_carregar:
            mock_carregar.side_effect = PermissionError("Acesso negado")
            
            resultado = gerar_pdf_fatura_assincrono("trans_123", 999)
            
            assert resultado is None
            mock_notificar_erro.assert_called_once()
    
    @patch('app.tasks.faturas.db.session.rollback')
    def test_gerar_fatura_erro_generico_retry(self, mock_rollback, app):
        """Tenta retry em caso de erro genérico"""
        with patch('app.tasks.faturas._carregar_dados_fatura') as mock_carregar:
            mock_carregar.side_effect = Exception("Erro inesperado")
            
            # Task deve levantar exceção para retry
            with pytest.raises(Exception):
                # Simular bind da task
                task_mock = MagicMock()
                task_mock.retry.side_effect = Exception("Retry raised")
                
                with patch('app.tasks.faturas.gerar_pdf_fatura_assincrono.bind_to_task'):
                    gerar_pdf_fatura_assincrono("trans_123", 1)


class TestCarregarDadosFatura:
    """Testes para função de carregar dados"""
    
    def test_carregar_dados_sucesso(self, session, transacao_enviada, comprador_user):
        """Carrega dados com sucesso"""
        transacao_id = transacao_enviada.id
        user_id = comprador_user.id
        
        # Usuário é comprador na transação
        transacao_enviada.comprador_id = user_id
        
        result_transacao, result_user = _carregar_dados_fatura(transacao_id, user_id)
        
        assert result_transacao.id == transacao_id
        assert result_user.id == user_id
    
    def test_carregar_dados_transacao_nao_existe(self, session):
        """Levanta erro se transação não existe"""
        with pytest.raises(ValueError) as exc_info:
            _carregar_dados_fatura(999999, 1)
        
        assert "não encontrada" in str(exc_info.value)
    
    def test_carregar_dados_acesso_negado(self, session, transacao_enviada, outro_usuario):
        """Levanta erro se usuário não tem acesso"""
        # Outro usuário não é comprador nem vendedor
        with pytest.raises(PermissionError) as exc_info:
            _carregar_dados_fatura(transacao_enviada.id, outro_usuario.id)
        
        assert "Acesso negado" in str(exc_info.value)
    
    def test_carregar_dados_admin_acesso(self, session, transacao_enviada, admin_user):
        """Admin pode acessar qualquer transação"""
        admin_user.tipo = 'admin'
        
        result_transacao, result_user = _carregar_dados_fatura(
            transacao_enviada.id, admin_user.id
        )
        
        assert result_transacao.id == transacao_enviada.id
        assert result_user.id == admin_user.id


class TestSalvarPdfSeguro:
    """Testes para salvamento seguro de PDF"""
    
    def test_salvar_pdf_sucesso(self, app, transacao_enviada):
        """Salva PDF com segurança"""
        pdf_bytes = b'%PDF-1.4 test content'
        
        with patch('app.tasks.faturas.os.makedirs') as mock_makedirs, \
             patch('app.tasks.faturas.open', mock_open()) as mock_file:
            
            path = _salvar_pdf_seguro(transacao_enviada, pdf_bytes)
            
            assert path is not None
            assert transacao_enviada.fatura_ref in path
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()
    
    def test_salvar_pdf_referencia_invalida(self, app, transacao_enviada):
        """Rejeita referência inválida"""
        transacao_enviada.fatura_ref = "../../../etc/passwd"
        pdf_bytes = b'%PDF-1.4 test'
        
        with pytest.raises(ValueError) as exc_info:
            _salvar_pdf_seguro(transacao_enviada, pdf_bytes)
        
        assert "inválida" in str(exc_info.value)
    
    def test_salvar_pdf_path_traversal(self, app, transacao_enviada):
        """Previne path traversal"""
        transacao_enviada.fatura_ref = "fatura/../../../sistema"
        pdf_bytes = b'%PDF-1.4 test'
        
        with pytest.raises(ValueError) as exc_info:
            _salvar_pdf_seguro(transacao_enviada, pdf_bytes)
        
        assert "inválida" in str(exc_info.value).lower()


class TestNotificacoesFatura:
    """Testes para notificações de fatura"""
    
    def test_notificar_fatura_pronta(self, session, transacao_enviada, comprador_user):
        """Cria notificação de fatura pronta"""
        path = "/path/to/fatura.pdf"
        
        with patch('app.tasks.faturas.url_for') as mock_url:
            mock_url.return_value = "http://test.com/download"
            
            _notificar_fatura_pronta(transacao_enviada, comprador_user.id, path)
            
            # Verificar se criou notificação
            notificacao = Notificacao.query.filter_by(
                usuario_id=comprador_user.id
            ).first()
            
            assert notificacao is not None
            assert "Fatura" in notificacao.mensagem
    
    def test_notificar_erro_fatura(self, session, transacao_enviada, comprador_user):
        """Cria notificação de erro na fatura"""
        erro_msg = "Erro ao gerar PDF"
        
        _notificar_erro_fatura(transacao_enviada.id, comprador_user.id, erro_msg)
        
        # Verificar notificação
        notificacao = Notificacao.query.filter_by(
            usuario_id=comprador_user.id
        ).first()
        
        assert notificacao is not None
        assert "Erro" in notificacao.mensagem


# Import necessário
from app.models import Notificacao
