"""
Testes de Transações Financeiras e Pagamentos
Cobertura: Escrow, Validação de Faturas, Taxas, Disputas
"""
import os
import sys
from pathlib import Path

# Adicionar root do projeto ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pytest
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import (
    Usuario, Transacao, Safra, Produto, Carteira, 
    MovimentacaoFinanceira, Disputa, HistoricoStatus
)
from app.models.base import TransactionStatus
from app.extensions import db


class TestTransacaoFinanceiro:
    """Testes de lógica financeira de transações"""
    
    def test_recalcular_financeiro_com_taxa_padrao(self, app):
        """Testa recálculo financeiro com taxa padrão"""
        with app.app_context():
            # Mock da configuração
            with patch('app.models.auditoria.ConfiguracaoSistema.obter_valor_decimal') as mock_config:
                mock_config.return_value = Decimal('0.10')  # 10%
                
                transacao = Transacao(
                    valor_total_pago=Decimal('1000.00'),
                    status=TransactionStatus.PENDENTE
                )
                
                transacao.recalcular_financeiro()
                
                # Comissão: 1000 * 0.10 = 100
                assert transacao.comissao_plataforma == Decimal('100.00')
                # Líquido: 1000 - 100 = 900
                assert transacao.valor_liquido_vendedor == Decimal('900.00')
    
    def test_recalcular_financeiro_com_taxa_customizada(self):
        """Testa recálculo com taxa customizada"""
        transacao = Transacao(
            valor_total_pago=Decimal('2000.00'),
            status=TransactionStatus.PENDENTE
        )
        
        # Taxa de 5%
        transacao.recalcular_financeiro(taxa_plataforma=Decimal('0.05'))
        
        # Comissão: 2000 * 0.05 = 100
        assert transacao.comissao_plataforma == Decimal('100.00')
        # Líquido: 2000 - 100 = 1900
        assert transacao.valor_liquido_vendedor == Decimal('1900.00')
    
    def test_recalcular_financeiro_taxa_float(self):
        """Testa conversão automática de float para Decimal"""
        transacao = Transacao(
            valor_total_pago=Decimal('1500.00'),
            status=TransactionStatus.PENDENTE
        )
        
        # Taxa como float
        transacao.recalcular_financeiro(taxa_plataforma=0.08)
        
        # Comissão: 1500 * 0.08 = 120
        assert transacao.comissao_plataforma == Decimal('120.00')
        assert transacao.valor_liquido_vendedor == Decimal('1380.00')
    
    def test_recalcular_financeiro_arredondamento(self):
        """Testa arredondamento correto (ROUND_HALF_UP)"""
        transacao = Transacao(
            valor_total_pago=Decimal('999.99'),
            status=TransactionStatus.PENDENTE
        )
        
        # Taxa que gera dízima
        transacao.recalcular_financeiro(taxa_plataforma=Decimal('0.075'))
        
        # Comissão: 999.99 * 0.075 = 74.99925 -> 75.00 (ROUND_HALF_UP)
        assert transacao.comissao_plataforma == Decimal('75.00')
    
    def test_calcular_janela_logistica(self):
        """Testa cálculo da previsão de entrega"""
        data_envio = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
        
        transacao = Transacao(
            data_envio=data_envio,
            status=TransactionStatus.ENVIADO
        )
        
        transacao.calcular_janela_logistica()
        
        # Previsão: 3 dias após envio
        expected = data_envio + timedelta(days=3)
        assert transacao.previsao_entrega == expected
    
    def test_calcular_janela_logistica_sem_envio(self):
        """Testa que não calcula sem data de envio"""
        transacao = Transacao(
            data_envio=None,
            status=TransactionStatus.PENDENTE
        )
        
        transacao.calcular_janela_logistica()
        
        assert transacao.previsao_entrega is None
    
    def test_to_dict(self):
        """Testa serialização para dicionário"""
        agora = datetime.now(timezone.utc)
        
        transacao = Transacao(
            id=1,
            fatura_ref='FAT-2026-001',
            status=TransactionStatus.ESCROW,
            quantidade_comprada=Decimal('100.000'),
            valor_total_pago=Decimal('5000.00'),
            comissao_plataforma=Decimal('500.00'),
            valor_liquido_vendedor=Decimal('4500.00'),
            data_criacao=agora,
            previsao_entrega=agora + timedelta(days=3)
        )
        
        data_dict = transacao.to_dict()
        
        assert data_dict['id'] == 1
        assert data_dict['fatura_ref'] == 'FAT-2026-001'
        assert data_dict['status'] == 'pago_escrow'
        assert data_dict['quantidade_comprada'] == 100.0
        assert data_dict['valor_total_pago'] == 5000.0
        assert data_dict['comissao_plataforma'] == 500.0
        assert data_dict['valor_liquido_vendedor'] == 4500.0
        assert 'data_criacao' in data_dict
        assert 'previsao_entrega' in data_dict


class TestCarteiraOperacoes:
    """Testes de operações de carteira"""
    
    def test_creditar_valor_positivo(self, app):
        """Testa crédito de valor positivo"""
        with app.app_context():
            usuario = Usuario(
                nome='Test User',
                telemovel='912345680',  # Telemovel obrigatório
                email='test@example.com',
                senha='senha123',
                tipo='produtor'
            )
            db.session.add(usuario)
            db.session.commit()
            
            carteira = Carteira(
                usuario_id=usuario.id,
                saldo_disponivel=Decimal('100.00')
            )
            db.session.add(carteira)
            db.session.commit()
            
            # Creditar
            carteira.creditar(Decimal('50.00'), motivo='Pagamento recebido')
            
            assert carteira.saldo_disponivel == Decimal('150.00')
    
    def test_creditar_valor_invalido(self, app):
        """Testa rejeição de crédito com valor negativo"""
        with app.app_context():
            usuario = Usuario(
                nome='Test User 2',
                telemovel='912345681',  # Telemovel obrigatório
                email='test2@example.com',
                senha='senha123',
                tipo='produtor'
            )
            db.session.add(usuario)
            db.session.commit()
            
            carteira = Carteira(
                usuario_id=usuario.id,
                saldo_disponivel=Decimal('100.00')
            )
            db.session.add(carteira)
            db.session.commit()
            
            with pytest.raises(ValueError, match="Valor de crédito deve ser positivo"):
                carteira.creditar(Decimal('-50.00'))
    
    def test_debitar_valor_valido(self, app):
        """Testa débito de valor válido"""
        with app.app_context():
            usuario = Usuario(
                nome='Test User 3',
                telemovel='912345682',  # Telemovel obrigatório
                email='test3@example.com',
                senha='senha123',
                tipo='comprador'
            )
            db.session.add(usuario)
            db.session.commit()
            
            carteira = Carteira(
                usuario_id=usuario.id,
                saldo_disponivel=Decimal('200.00')
            )
            db.session.add(carteira)
            db.session.commit()
            
            # Debitar
            carteira.debitar(Decimal('75.00'), motivo='Compra de produtos')
            
            assert carteira.saldo_disponivel == Decimal('125.00')
    
    def test_debitar_saldo_insuficiente(self, app):
        """Testa rejeição de débito com saldo insuficiente"""
        with app.app_context():
            usuario = Usuario(
                nome='Test User 4',
                telemovel='912345683',  # Telemovel obrigatório
                email='test4@example.com',
                senha='senha123',
                tipo='comprador'
            )
            db.session.add(usuario)
            db.session.commit()
            
            carteira = Carteira(
                usuario_id=usuario.id,
                saldo_disponivel=Decimal('50.00')
            )
            db.session.add(carteira)
            db.session.commit()
            
            with pytest.raises(ValueError, match="Saldo insuficiente"):
                carteira.debitar(Decimal('100.00'))
    
    def test_get_saldo_total(self):
        """Testa obtenção do saldo total"""
        carteira = Carteira(
            saldo_disponivel=Decimal('100.00'),
            saldo_bloqueado=Decimal('50.00')
        )
        
        total = carteira.get_saldo_total()
        assert total == Decimal('150.00')
    
    def test_carteira_to_dict(self):
        """Testa serialização de carteira"""
        agora = datetime.now(timezone.utc)
        
        carteira = Carteira(
            id=1,
            usuario_id=1,
            saldo_disponivel=Decimal('500.00'),
            saldo_bloqueado=Decimal('100.00'),
            data_criacao=agora,
            data_ultima_atualizacao=agora
        )
        
        data_dict = carteira.to_dict()
        
        assert data_dict['id'] == 1
        assert data_dict['usuario_id'] == 1
        assert data_dict['saldo_disponivel'] == 500.0
        assert data_dict['saldo_bloqueado'] == 100.0
        assert data_dict['saldo_total'] == 600.0
        assert 'data_criacao' in data_dict


class TestDisputa:
    """Testes de sistema de disputas"""
    
    def test_pode_abrir_disputa_status_valido(self):
        """Testa abertura de disputa com status válido"""
        transacao = Transacao(
            status=TransactionStatus.ENVIADO,
            previsao_entrega=datetime.now(timezone.utc) - timedelta(hours=48)
        )
        
        disputa = Disputa(transacao=transacao)
        
        pode_abrir, motivo = disputa.pode_abrir_disputa()
        
        assert pode_abrir is True
        assert motivo == "Disputa pode ser aberta"
    
    def test_pode_abrir_disputa_status_invalido(self):
        """Testa rejeição com status inválido"""
        transacao = Transacao(
            status=TransactionStatus.PENDENTE,  # Status inválido
            previsao_entrega=datetime.now(timezone.utc)
        )
        
        disputa = Disputa(transacao=transacao)
        
        pode_abrir, motivo = disputa.pode_abrir_disputa()
        
        assert pode_abrir is False
        assert "Status inválido" in motivo
    
    def test_pode_abrir_disputa_sem_previsao(self):
        """Testa rejeição sem previsão de entrega"""
        transacao = Transacao(
            status=TransactionStatus.ENVIADO,
            previsao_entrega=None
        )
        
        disputa = Disputa(transacao=transacao)
        
        pode_abrir, motivo = disputa.pode_abrir_disputa()
        
        assert pode_abrir is False
        assert "Previsão de entrega não definida" in motivo
    
    def test_pode_abrir_disputa_aguardando_24h(self):
        """Testa que precisa aguardar 24h após previsão"""
        agora = datetime.now(timezone.utc)
        previsao_entrega = agora + timedelta(hours=12)  # Apenas 12h
        
        transacao = Transacao(
            status=TransactionStatus.ENVIADO,
            previsao_entrega=previsao_entrega
        )
        
        disputa = Disputa(transacao=transacao)
        
        pode_abrir, motivo = disputa.pode_abrir_disputa()
        
        assert pode_abrir is False
        assert "Aguarde 24h" in motivo
    
    def test_calcular_taxa_administrativa(self):
        """Testa cálculo de taxa administrativa"""
        transacao = Transacao(
            valor_total_pago=Decimal('1000.00')
        )
        
        disputa = Disputa(
            transacao=transacao,
            taxa_administrativa=Decimal('0.00')
        )
        
        taxa = disputa.calcular_taxa_administrativa()
        
        # Taxa padrão: 5%
        assert taxa == Decimal('50.00')


# Marcador de integração (comentado para evitar erro)
# @pytest.mark.integration
class TestTransaoIntegracao:
    """Testes de integração de transações"""
    
    def test_criar_transacao_completa(self, session):
        """Testa criação completa de transação"""
        # Criar usuários
        vendedor = Usuario(
            nome='Vendedor Test',
            telemovel='912345684',  # Telemovel obrigatório
            email='vendedor@example.com',
            senha='senha123',
            tipo='produtor',
            conta_validada=True
        )
        
        comprador = Usuario(
            nome='Comprador Test',
            telemovel='912345685',  # Telemovel obrigatório
            email='comprador@example.com',
            senha='senha123',
            tipo='comprador',
            conta_validada=True
        )
        
        produto = Produto(nome='Milho', categoria='Cereais')
        
        safra = Safra(
            produtor=vendedor,
            produto=produto,
            quantidade_disponivel=Decimal('1000.000'),
            preco_por_unidade=Decimal('50.00'),
            status='disponivel'
        )
        
        transacao = Transacao(
            fatura_ref='FAT-TEST-001',
            safra=safra,
            comprador=comprador,
            vendedor=vendedor,
            quantidade_comprada=Decimal('100.000'),
            valor_total_pago=Decimal('5000.00'),
            status=TransactionStatus.PENDENTE
        )
        
        # Recalcular financeiro
        transacao.recalcular_financeiro(taxa_plataforma=Decimal('0.10'))
        
        session.add(vendedor)
        session.add(comprador)
        session.add(produto)
        session.add(safra)
        session.add(transacao)
        session.commit()
        
        assert transacao.id is not None
        assert transacao.comissao_plataforma == Decimal('500.00')
        assert transacao.valor_liquido_vendedor == Decimal('4500.00')
        assert len(transacao.historico_status) == 0
    
    def test_historico_status_transacao(self, session):
        """Testa histórico de status da transação"""
        vendedor = Usuario(
            nome='Vendedor Hist',
            telemovel='912345686',  # Telemovel obrigatório
            email='vendedor.hist@example.com',
            senha='senha123',
            tipo='produtor'
        )
        
        comprador = Usuario(
            nome='Comprador Hist',
            telemovel='912345687',  # Telemovel obrigatório
            email='comprador.hist@example.com',
            senha='senha123',
            tipo='comprador'
        )
        
        produto = Produto(nome='Feijão', categoria='Leguminosas')
        
        safra = Safra(
            produtor=vendedor,
            produto=produto,
            quantidade_disponivel=Decimal('500.000'),
            preco_por_unidade=Decimal('30.00')
        )
        
        transacao = Transacao(
            fatura_ref='FAT-HIST-001',
            safra=safra,
            comprador=comprador,
            vendedor=vendedor,
            quantidade_comprada=Decimal('50.000'),
            valor_total_pago=Decimal('1500.00'),
            status=TransactionStatus.PENDENTE
        )
        
        session.add(vendedor)
        session.add(comprador)
        session.add(produto)
        session.add(safra)
        session.add(transacao)
        session.commit()
        
        # Adicionar mudança de status
        historico = HistoricoStatus(
            transacao_id=transacao.id,
            status_anterior=TransactionStatus.PENDENTE,
            status_novo=TransactionStatus.ESCROW,
            observacoes='Pagamento confirmado no escrow'
        )
        
        session.add(historico)
        session.commit()
        
        assert len(transacao.historico_status) == 1
        assert transacao.historico_status[0].status_novo == TransactionStatus.ESCROW
