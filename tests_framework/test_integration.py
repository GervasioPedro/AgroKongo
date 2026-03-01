# tests_framework/test_integration.py - Testes de integração
# Validação da comunicação entre componentes

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import (
    Usuario, Safra, Transacao, TransactionStatus,
    Notificacao, LogAuditoria, HistoricoStatus
)
from app.models_carteiras import Carteira, StatusConta
from app.models_disputa import Disputa
from app.services.otp_service import gerar_e_enviar_otp, OTPService
from app.routes.cadastro_produtor import _criar_usuario_produtor


@pytest.mark.integration
class TestCadastroFlowIntegration:
    """Testes de integração do fluxo completo de cadastro"""
    
    def test_fluxo_completo_cadastro_produtor(self, session, provincia, municipio):
        """Teste completo: Cadastro -> OTP -> Validação -> Criação"""
        # Passo 1: Gerar OTP
        telemovel = "912345678"
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        assert resultado_otp['sucesso'] == True
        codigo = resultado_otp['codigo']
        
        # Passo 2: Validar OTP
        resultado_validacao = OTPService.validar_otp(telemovel, codigo, '127.0.0.1')
        assert resultado_validacao['valido'] == True
        
        # Passo 3: Dados básicos
        dados_basicos = {
            'nome': 'Produtor Integração',
            'provincia_id': provincia.id,
            'municipio_id': municipio.id,
            'principal_cultura': 'Milho'
        }
        
        # Passo 4: Dados financeiros
        dados_financeiros = {
            'iban': 'AO0600600000123456789012345',
            'bi_path': 'documentos_bi/integracao.pdf'
        }
        
        # Passo 5: Criar usuário
        usuario = _criar_usuario_produtor(
            telemovel=telemovel,
            dados=dados_basicos,
            senha="1234",
            financeiros=dados_financeiros
        )
        
        # Validações finais
        assert usuario is not None
        assert usuario.nome == dados_basicos['nome']
        assert usuario.telemovel == telemovel
        assert usuario.tipo == 'produtor'
        assert usuario.status_conta == StatusConta.PENDENTE_VERIFICACAO
        assert usuario.iban == dados_financeiros['iban']
        assert usuario.verificar_senha("1234") == True
        
        # RN02: Verificar carteira criada
        carteira = usuario.obter_carteira()
        assert carteira is not None
        assert carteira.usuario_id == usuario.id
        assert carteira.saldo_disponivel == Decimal('0.00')
        
        # RN03: Verificar limitação inicial
        assert not usuario.pode_criar_anuncios()
    
    def test_fluxo_com_otp_invalido(self, session):
        """Teste Exceção 2A: OTP inválido no fluxo"""
        telemovel = "912345679"
        
        # Gerar OTP
        resultado_otp = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        codigo_correto = resultado_otp['codigo']
        
        # Tentar validar com código incorreto
        resultado_validacao = OTPService.validar_otp(telemovel, "000000", '127.0.0.1')
        assert resultado_validacao['valido'] == False
        assert resultado_validacao['tentativas_restantes'] == 2
        
        # Tentar novamente
        resultado_validacao = OTPService.validar_otp(telemovel, "111111", '127.0.0.1')
        assert resultado_validacao['valido'] == False
        assert resultado_validacao['tentativas_restantes'] == 1
        
        # Tentar código correto
        resultado_validacao = OTPService.validar_otp(telemovel, codigo_correto, '127.0.0.1')
        assert resultado_validacao['valido'] == True
    
    def test_fluxo_com_usuario_existente(self, session, produtor_user):
        """Teste Exceção 5B: Usuário já existente"""
        telemovel = produtor_user.telemovel
        
        # Tentar gerar OTP para telemovel existente
        resultado = gerar_e_enviar_otp(telemovel, 'whatsapp', '127.0.0.1')
        
        assert resultado['sucesso'] == False
        assert 'já possui uma conta' in resultado['mensagem'].lower()
        assert resultado['codigo'] is None


@pytest.mark.integration
class TestTransacaoFlowIntegration:
    """Testes de integração do fluxo de transações"""
    
    def test_fluxo_transacao_completo(self, session, safra_ativa, comprador_user, produtor_user):
        """Teste completo: Reserva -> Pagamento -> Escrow -> Entrega -> Liquidação"""
        # Passo 1: Criar reserva
        transacao = Transacao(
            fatura_ref=f"AGK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('100.00'),
            valor_total_pago=Decimal('15000.00'),
            status=TransactionStatus.PENDENTE
        )
        transacao.recalcular_financeiro()
        session.add(transacao)
        session.commit()
        
        # Passo 2: Aceitar reserva
        transacao.status = TransactionStatus.AGUARDANDO_PAGAMENTO
        session.commit()
        
        # Passo 3: Pagamento
        carteira_comprador = comprador_user.obter_carteira()
        carteira_comprador.debitar(transacao.valor_total_pago, f"Pagamento {transacao.fatura_ref}")
        
        transacao.status = TransactionStatus.ANALISE
        transacao.data_pagamento_escrow = datetime.now(timezone.utc)
        session.commit()
        
        # Passo 4: Validação e Escrow
        transacao.status = TransactionStatus.ESCROW
        session.commit()
        
        carteira_vendedor = produtor_user.obter_carteira()
        carteira_vendedor.bloquear(transacao.valor_liquido_vendedor, f"Escrow {transacao.fatura_ref}")
        
        # Passo 5: Envio
        transacao.status = TransactionStatus.ENVIADO
        transacao.data_envio = datetime.now(timezone.utc)
        transacao.calcular_janela_logistica()
        session.commit()
        
        # Passo 6: Entrega
        transacao.status = TransactionStatus.ENTREGUE
        transacao.data_entrega = datetime.now(timezone.utc)
        session.commit()
        
        # Passo 7: Liquidação
        carteira_vendedor.liberar(transacao.valor_liquido_vendedor, f"Liquidação {transacao.fatura_ref}")
        
        transacao.status = TransactionStatus.FINALIZADO
        transacao.data_liquidacao = datetime.now(timezone.utc)
        transacao.transferencia_concluida = True
        session.commit()
        
        # Validações finais
        assert transacao.status == TransactionStatus.FINALIZADO
        assert transacao.transferencia_concluida == True
        assert transacao.data_liquidacao is not None
        assert transacao.previsao_entrega is not None
        
        # Verificar saldos
        assert carteira_vendedor.saldo_disponivel == transacao.valor_liquido_vendedor
        assert carteira_vendedor.saldo_bloqueado == Decimal('0.00')
    
    def test_fluxo_com_disputa(self, session, safra_ativa, comprador_user, produtor_user):
        """Teste fluxo com disputa"""
        # Criar transação em escrow
        transacao = Transacao(
            fatura_ref=f"DISPUTA{datetime.now().strftime('%Y%m%d%H%M%S')}",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('50.00'),
            valor_total_pago=Decimal('7500.00'),
            status=TransactionStatus.ESCROW,
            data_pagamento_escrow=datetime.now(timezone.utc)
        )
        transacao.recalcular_financeiro()
        session.add(transacao)
        session.commit()
        
        # Bloquear valor
        carteira_vendedor = produtor_user.obter_carteira()
        carteira_vendedor.bloquear(transacao.valor_liquido_vendedor, f"Escrow {transacao.fatura_ref}")
        
        # Abrir disputa
        transacao.status = TransactionStatus.DISPUTA
        session.commit()
        
        disputa = Disputa(
            transacao_id=transacao.id,
            reclamante_id=comprador_user.id,
            motivo="Produto não conforme",
            descricao="Teste de disputa",
            status="aberta"
        )
        session.add(disputa)
        session.commit()
        
        # Resolver disputa (favorável ao comprador)
        disputa.status = "resolvida"
        disputa.decisao = "reembolso_completo"
        session.commit()
        
        # Reembolsar comprador
        carteira_comprador = comprador_user.obter_carteira()
        carteira_comprador.creditar(transacao.valor_total_pago, f"Reembolso {transacao.fatura_ref}")
        
        # Cancelar transação
        transacao.status = TransactionStatus.CANCELADO
        session.commit()
        
        # Devolver stock
        safra_ativa.quantidade_disponivel += transacao.quantidade_comprada
        session.commit()
        
        # Liberar valor bloqueado do produtor
        carteira_vendedor.liberar(transacao.valor_liquido_vendedor, f"Cancelamento {transacao.fatura_ref}")
        
        # Validações
        assert transacao.status == TransactionStatus.CANCELADO
        assert disputa.status == "resolvida"
        assert carteira_comprador.saldo_disponivel == Decimal('107500.00')  # 100000 + 7500
        assert safra_ativa.quantidade_disponivel == Decimal('1050.00')  # 1000 + 50


@pytest.mark.integration
class TestDatabaseIntegration:
    """Testes de integração com banco de dados"""
    
    def test_relacionamentos_usuario_carteira(self, session, produtor_user):
        """Testa relacionamento entre usuário e carteira"""
        carteira = produtor_user.obter_carteira()
        
        # Verificar relacionamento bidirecional
        assert carteira.usuario_id == produtor_user.id
        assert carteira.usuario == produtor_user
        assert produtor_user.carteira == carteira
    
    def test_relacionamentos_transacao(self, session, transacao_pendente):
        """Testa relacionamentos da transação"""
        # Verificar relacionamentos
        assert transacao_pendente.safra is not None
        assert transacao_pendente.comprador is not None
        assert transacao_pendente.vendedor is not None
        
        # Verificar dados relacionados
        assert transacao_pendente.safra.id == transacao_pendente.safra_id
        assert transacao_pendente.comprador.id == transacao_pendente.comprador_id
        assert transacao_pendente.vendedor.id == transacao_pendente.vendedor_id
    
    def test_cascade_delete_usuario(self, session, produtor_user):
        """Testa cascade delete de usuário"""
        usuario_id = produtor_user.id
        
        # Verificar que carteira existe
        carteira = Carteira.query.filter_by(usuario_id=usuario_id).first()
        assert carteira is not None
        
        # Deletar usuário
        session.delete(produtor_user)
        session.commit()
        
        # Verificar que carteira foi deletada (cascade)
        carteira_deletada = Carteira.query.filter_by(usuario_id=usuario_id).first()
        assert carteira_deletada is None
    
    def test_constraints_unicidade(self, session):
        """Testa constraints de unicidade"""
        # Criar primeiro usuário
        usuario1 = Usuario(
            nome="Test User 1",
            telemovel="912345678",
            tipo="produtor"
        )
        session.add(usuario1)
        session.commit()
        
        # Tentar criar usuário com mesmo telemóvel (deve falhar)
        usuario2 = Usuario(
            nome="Test User 2",
            telemovel="912345678",  # Mesmo telemóvel
            tipo="comprador"
        )
        session.add(usuario2)
        
        with pytest.raises(Exception):  # Deve falhar por constraint
            session.commit()
    
    def test_transacoes_vinculadas_safra(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa transações vinculadas à safra"""
        # Criar múltiplas transações
        transacoes = []
        for i in range(3):
            transacao = Transacao(
                fatura_ref=f"AGK{datetime.now().strftime('%Y%m%d%H%M%S')}{i}",
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('10.00'),
                valor_total_pago=Decimal('1500.00'),
                status=TransactionStatus.PENDENTE
            )
            transacao.recalcular_financeiro()
            session.add(transacao)
            transacoes.append(transacao)
        
        session.commit()
        
        # Verificar relacionamento
        transacoes_safra = Transacao.query.filter_by(safra_id=safra_ativa.id).all()
        assert len(transacoes_safra) >= 3
        
        # Verificar que todas pertencem à safra
        for transacao in transacoes_safra:
            assert transacao.safra_id == safra_ativa.id
            assert transacao.safra == safra_ativa


@pytest.mark.integration
class TestNotificacoesIntegration:
    """Testes de integração do sistema de notificações"""
    
    def test_notificacoes_transacao(self, session, transacao_pendente):
        """Testa criação de notificações durante transação"""
        # Criar notificação para aceitação
        notificacao = Notificacao(
            usuario_id=transacao_pendente.comprador_id,
            mensagem=f"Sua reserva {transacao_pendente.fatura_ref} foi aceita!",
            link=f"/pagar-reserva/{transacao_pendente.id}"
        )
        session.add(notificacao)
        session.commit()
        
        # Verificar notificação
        notificacao_salva = Notificacao.query.filter_by(usuario_id=transacao_pendente.comprador_id).first()
        assert notificacao_salva is not None
        assert transacao_pendente.fatura_ref in notificacao_salva.mensagem
        assert notificacao_salva.lida == False
    
    def test_notificacoes_usuario(self, session, produtor_user):
        """Testa notificações do usuário"""
        # Criar múltiplas notificações
        notificacoes = []
        mensagens = [
            "Bem-vindo ao AgroKongo!",
            "Sua safra foi publicada",
            "Você tem uma nova reserva"
        ]
        
        for mensagem in mensagens:
            notificacao = Notificacao(
                usuario_id=produtor_user.id,
                mensagem=mensagem
            )
            session.add(notificacao)
            notificacoes.append(notificacao)
        
        session.commit()
        
        # Verificar notificações do usuário
        notificacoes_usuario = Notificacao.query.filter_by(usuario_id=produtor_user.id).all()
        assert len(notificacoes_usuario) >= 3
        
        # Verificar não lidas
        nao_lidas = [n for n in notificacoes_usuario if not n.lida]
        assert len(nao_lidas) >= 3


@pytest.mark.integration
class TestAuditoriaIntegration:
    """Testes de integração do sistema de auditoria"""
    
    def test_log_auditoria_acoes(self, session, produtor_user):
        """Testa criação de logs de auditoria"""
        # Criar log para login
        log_login = LogAuditoria(
            usuario_id=produtor_user.id,
            acao="LOGIN_SUCCESS",
            detalhes="Login via web",
            ip="127.0.0.1"
        )
        session.add(log_login)
        session.commit()
        
        # Verificar log
        log_salvo = LogAuditoria.query.filter_by(usuario_id=produtor_user.id).first()
        assert log_salvo is not None
        assert log_salvo.acao == "LOGIN_SUCCESS"
        assert log_salvo.usuario_id == produtor_user.id
    
    def test_historico_status_transacao(self, session, transacao_pendente):
        """Testa histórico de mudanças de status"""
        # Mudar status e criar histórico
        status_anterior = transacao_pendente.status
        transacao_pendente.status = TransactionStatus.AGUARDANDO_PAGAMENTO
        session.commit()
        
        # Criar histórico
        historico = HistoricoStatus(
            transacao_id=transacao_pendente.id,
            status_anterior=status_anterior,
            status_novo=transacao_pendente.status,
            observacao="Reserva aceita pelo produtor"
        )
        session.add(historico)
        session.commit()
        
        # Verificar histórico
        historico_salvo = HistoricoStatus.query.filter_by(transacao_id=transacao_pendente.id).first()
        assert historico_salvo is not None
        assert historico_salvo.status_anterior == status_anterior
        assert historico_salvo.status_novo == TransactionStatus.AGUARDANDO_PAGAMENTO


@pytest.mark.integration
class TestPerformanceIntegration:
    """Testes de performance e carga"""
    
    def test_performance_multiplas_transacoes(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa performance com múltiplas transações simultâneas"""
        import time
        
        start_time = time.time()
        
        # Criar múltiplas transações
        transacoes = []
        for i in range(10):
            transacao = Transacao(
                fatura_ref=f"PERF{i:03d}{int(time.time())}",
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('10.00'),
                valor_total_pago=Decimal('1500.00'),
                status=TransactionStatus.PENDENTE
            )
            transacao.recalcular_financeiro()
            session.add(transacao)
            transacoes.append(transacao)
        
        session.commit()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance: deve criar 10 transações em < 1 segundo
        assert execution_time < 1.0
        assert len(transacoes) == 10
        
        # Verificar que todas foram criadas corretamente
        for transacao in transacoes:
            assert transacao.id is not None
            assert transacao.comissao_plataforma == Decimal('150.00')
            assert transacao.valor_liquido_vendedor == Decimal('1350.00')
    
    def test_performance_consultas_complexas(self, session, produtor_user, comprador_user):
        """Testa performance de consultas complexas"""
        import time
        
        # Criar dados para teste
        for i in range(50):
            transacao = Transacao(
                fatura_ref=f"QUERY{i:03d}{int(time.time())}",
                safra_id=1,  # Assume safra existe
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('5.00'),
                valor_total_pago=Decimal('750.00'),
                status=TransactionStatus.PENDENTE
            )
            transacao.recalcular_financeiro()
            session.add(transacao)
        
        session.commit()
        
        # Testar consulta complexa
        start_time = time.time()
        
        # Consulta com joins e filtros
        transacoes = Transacao.query.join(Usuario).filter(
            Transacao.status == TransactionStatus.PENDENTE
        ).all()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance: consulta deve ser rápida
        assert execution_time < 0.5
        assert len(transacoes) >= 50
