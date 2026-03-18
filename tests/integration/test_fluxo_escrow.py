"""
Testes de Integração para Fluxo Completo de Escrow
Cobre todo o ciclo: desde a compra até a finalização com pagamento.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.extensions import db
from app.models import (
    Usuario, Safra, Produto, Transacao, Provincia, Municipio,
    TransactionStatus, Notificacao, LogAuditoria
)
from app.services.compra_service import CompraService
from app.services.pagamento_service import PagamentoService
from app.utils.status_helper import status_to_value


class TestFluxoEscrowCompleto:
    """Testa todo o fluxo de uma transação com Escrow."""
    
    @pytest.fixture
    def setup_usuarios(self, app, db):
        """Cria usuários de teste: produtor e comprador."""
        # Nao usar with app.app_context() aqui para manter sessao ativa
        # Criar localização
        prov = Provincia(nome='Zaire')
        db.session.add(prov)
        db.session.flush()
        
        mun = Municipio(nome='Mbanza Kongo', provincia_id=prov.id)
        db.session.add(mun)
        db.session.flush()
        
        # Criar produtor
        produtor = Usuario(
            nome="João Produtor",
            telemovel="923000001",
            email="produtor@teste.com",
            tipo="produtor",
            nif="501234400001",
            iban="AO06004000001234567890123",
            municipio_id=mun.id,
            provincia_id=prov.id,
            perfil_completo=True,
            conta_validada=True
        )
        produtor.senha = "123456"
        db.session.add(produtor)
        
        # Criar comprador
        comprador = Usuario(
            nome="Maria Comprador",
            telemovel="931000001",
            email="comprador@teste.com",
            tipo="comprador",
            municipio_id=mun.id,
            provincia_id=prov.id,
            perfil_completo=True,
            conta_validada=True
        )
        comprador.senha = "123456"
        db.session.add(comprador)
        
        # Criar admin
        admin = Usuario(
            nome="Admin Teste",
            telemovel="900000001",
            email="admin@teste.com",
            tipo="admin",
            perfil_completo=True,
            conta_validada=True
        )
        admin.senha = "admin123"
        db.session.add(admin)
        
        db.session.commit()
        
        # Retornar dicionário com IDs
        return {
            'produtor_id': int(produtor.id),
            'comprador_id': int(comprador.id),
            'admin_id': int(admin.id)
        }
    
    @pytest.fixture
    def setup_safra(self, app, db, setup_usuarios):
        """Cria uma safra de teste."""
        # Nao usar with app.app_context() para manter sessao ativa
        produtor_id = setup_usuarios['produtor_id']
        
        # Criar produto
        produto = Produto(nome='Mandioca', categoria='Raízes')
        db.session.add(produto)
        db.session.flush()
        
        # Criar safra
        safra = Safra(
            produtor_id=produtor_id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('1000.0'),
            preco_por_unidade=Decimal('250.0'),
            status='disponivel'
        )
        db.session.add(safra)
        db.session.commit()
        
        return int(safra.id)  # Retorna ID como int
    
    def test_fluxo_completo_escrow(self, app, db, setup_usuarios, setup_safra):
        """Testa todo o fluxo de escrow passo a passo."""
        with app.app_context():
            produtor_id = setup_usuarios['produtor_id']
            comprador_id = setup_usuarios['comprador_id']
            admin_id = setup_usuarios['admin_id']
            safra_id = setup_safra
            
            # === PASSO 1: Iniciar Compra ===
            sucesso, transacao, msg = CompraService.iniciar_compra(
                safra_id=safra_id,
                comprador_id=comprador_id,
                quantidade=Decimal('10.0')
            )
            
            assert sucesso is True
            assert transacao is not None
            assert transacao.status == status_to_value(TransactionStatus.PENDENTE)
            assert transacao.valor_total_pago == Decimal('2500.00')
            
            # Guardar ID da transação
            transacao_id = transacao.id
            
            # Recarregar safra para obter valor atualizado da base de dados
            safra = Safra.query.get(safra_id)
            assert safra.quantidade_disponivel == Decimal('990.0')
            
            transacao_id = transacao.id
            
            # === PASSO 2: Aceitar Reserva pelo Produtor ===
            sucesso, msg = CompraService.aceitar_reserva(
                transacao_id=transacao_id,
                produtor_id=produtor_id
            )
            
            # Debug se falhar
            if not sucesso:
                print(f"ERRO AO ACEITAR RESERVA: {msg}")
                transacao_debug = Transacao.query.get(transacao_id)
                if transacao_debug:
                    print(f"Transacao existe: {transacao_debug.fatura_ref}")
                    print(f"Status: {transacao_debug.status}")
                    print(f"Vendedor ID: {transacao_debug.vendedor_id}, Produtor ID: {produtor_id}")
                else:
                    print(f"Transacao NAO existe no DB (ID: {transacao_id})")
            
            assert sucesso is True
            transacao = Transacao.query.get(transacao_id)
            assert transacao.status == status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO)
            
            # Verificar notificação criada
            notificacao = Notificacao.query.filter_by(usuario_id=comprador_id).first()
            assert notificacao is not None
            assert "aceite" in notificacao.mensagem.lower()
            
            # === PASSO 3: Submeter Comprovativo (simulado) ===
            transacao = Transacao.query.get(transacao_id)
            transacao.comprovativo_path = "comprovativos/teste_comprovativo.jpg"
            transacao.mudar_status(status_to_value(TransactionStatus.ANALISE), "Comprovativo enviado")
            db.session.commit()
            
            # === PASSO 4: Validar Pagamento pelo Admin ===
            sucesso, msg = PagamentoService.validar_pagamento(
                transacao_id=transacao_id,
                admin_id=admin_id
            )
            
            assert sucesso is True
            transacao = Transacao.query.get(transacao_id)
            assert transacao.status == status_to_value(TransactionStatus.ESCROW)
            
            # Verificar notificação ao produtor
            notificacao_produtor = Notificacao.query.filter_by(usuario_id=produtor_id).first()
            assert notificacao_produtor is not None
            
            # === PASSO 5: Confirmar Envio pelo Produtor ===
            sucesso, msg = CompraService.confirmar_envio(
                transacao_id=transacao_id,
                vendedor_id=produtor_id
            )
            
            assert sucesso is True
            transacao = Transacao.query.get(transacao_id)
            assert transacao.status == status_to_value(TransactionStatus.ENVIADO)
            assert transacao.data_envio is not None
            
            # === PASSO 6: Confirmar Recebimento pelo Comprador ===
            sucesso, msg = CompraService.confirmar_recebimento(
                transacao_id=transacao_id,
                comprador_id=comprador_id
            )
            
            assert sucesso is True
            transacao = Transacao.query.get(transacao_id)
            assert transacao.status == status_to_value(TransactionStatus.FINALIZADO)
            assert transacao.data_entrega is not None
            assert transacao.data_liquidacao is not None
            
            # Verificar se produtor recebeu o saldo
            produtor_atualizado = Usuario.query.get(produtor_id)
            assert produtor_atualizado.saldo_disponivel >= Decimal('2375.00')  # 2500 - 5%
            
            # Verificar vendas concluídas
            assert produtor_atualizado.vendas_concluidas >= 1
            
            # === VERIFICAÇÕES FINAIS ===
            # Histórico de status deve ter múltiplos registos
            historico_count = len(transacao.historico_status.all())
            assert historico_count >= 5  # Pelo menos 5 mudanças de status
            
            # Logs de auditoria
            logs = LogAuditoria.query.filter(
                LogAuditoria.detalhes.contains(str(transacao.fatura_ref))
            ).all()
            assert len(logs) >= 3  # Pelo menos 3 logs significativos
    
    def test_recusar_reserva_repoe_stock(self, app, db, setup_usuarios, setup_safra):
        """Testa se recusar reserva repõe o stock corretamente."""
        with app.app_context():
            produtor_id = setup_usuarios['produtor_id']
            comprador_id = setup_usuarios['comprador_id']
            safra_id = setup_safra
            
            # Buscar objetos no session atual
            safra = Safra.query.get(safra_id)
            stock_inicial = safra.quantidade_disponivel
            
            # Iniciar compra
            sucesso, transacao, msg = CompraService.iniciar_compra(
                safra_id=safra_id,
                comprador_id=comprador_id,
                quantidade=Decimal('50.0')
            )
            
            assert sucesso is True
            
            # Recarregar safra para obter valor atualizado
            safra = Safra.query.get(safra_id)
            assert safra.quantidade_disponivel == stock_inicial - Decimal('50.0')
            
            transacao_id = transacao.id
            
            # Recusar reserva
            sucesso, msg = CompraService.recusar_reserva(
                transacao_id=transacao_id,
                produtor_id=produtor_id
            )
            
            # Debug se falhar
            if not sucesso:
                print(f"ERRO AO RECUSAR RESERVA: {msg}")
                transacao_debug = Transacao.query.get(transacao_id)
                if transacao_debug:
                    print(f"Transacao existe: {transacao_debug.fatura_ref}")
                    print(f"Status: {transacao_debug.status}")
                    print(f"Vendedor ID: {transacao_debug.vendedor_id}")
                else:
                    print(f"Transacao NAO existe no DB (ID: {transacao_id})")
            
            assert sucesso is True
            
            # Verificar stock reposto
            safra_atualizada = Safra.query.get(safra_id)
            assert safra_atualizada.quantidade_disponivel == stock_inicial
            
            # Verificar status cancelado
            transacao = Transacao.query.get(transacao_id)
            assert transacao.status == status_to_value(TransactionStatus.CANCELADO)
    
    def test_validacoes_seguranca_compra(self, app, db, setup_usuarios, setup_safra):
        """Testa validações de segurança do serviço de compras."""
        with app.app_context():
            produtor_id = setup_usuarios['produtor_id']
            comprador_id = setup_usuarios['comprador_id']
            safra_id = setup_safra
            
            # Buscar objetos no session atual
            safra = Safra.query.get(safra_id)
            
            # Teste 1: Produtor tentando comprar própria safra
            sucesso, transacao, msg = CompraService.iniciar_compra(
                safra_id=safra_id,
                comprador_id=produtor_id,
                quantidade=Decimal('10.0')
            )
            
            assert sucesso is False
            # Mensagem: "Não pode comprar: Produtores não podem comprar safras."
            assert "propria" in msg.lower() or "não" in msg.lower() or "nao" in msg.lower()
            
            # Teste 2: Quantidade maior que disponível
            sucesso, transacao, msg = CompraService.iniciar_compra(
                safra_id=safra_id,
                comprador_id=comprador_id,
                quantidade=Decimal('5000.0')  # Maior que stock
            )
            
            assert sucesso is False
            # Mensagem: "Quantidade indisponível. Máximo: Xkg"
            assert "indisponi" in msg.lower() or "máxim" in msg.lower() or "maxim" in msg.lower()
            
            # Teste 3: Quantidade zero ou negativa
            sucesso, transacao, msg = CompraService.iniciar_compra(
                safra_id=safra_id,
                comprador_id=comprador_id,
                quantidade=Decimal('0')
            )
            
            assert sucesso is False
            assert "maior que zero" in msg.lower()
    
    def test_calculo_comissao_correto(self, app, db):
        """Testa se o cálculo de comissão está preciso."""
        from app.services.pagamento_service import PagamentoService
        
        valor_total = Decimal('10000.00')
        comissao, liquido = PagamentoService.calcular_comissao(valor_total)
        
        assert comissao == Decimal('500.00')  # 5% de 10000
        assert liquido == Decimal('9500.00')  # 10000 - 500
        
        # Teste com valores quebrados
        valor_total = Decimal('1234.56')
        comissao, liquido = PagamentoService.calcular_comissao(valor_total)
        
        assert comissao == Decimal('61.73')  # Arredondamento correto
        assert liquido == Decimal('1172.83')
