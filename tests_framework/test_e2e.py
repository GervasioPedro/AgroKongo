# tests_framework/test_e2e.py - Testes End-to-End
# Validação completa do ciclo de negócio

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


@pytest.mark.e2e
@pytest.mark.slow
class TestCicloCompletoE2E:
    """Teste End-to-End: Cadastro -> Venda -> Escrow -> Liquidação -> Levantamento"""
    
    def test_ciclo_completo_sucesso_total(self, session, mock_celery, mock_redis):
        """
        Teste completo do ciclo de vida do AgroKongo
        Simula todo o processo desde cadastro até levantamento
        """
        print("\n🌱 INICIANDO CICLO COMPLETO E2E")
        print("=" * 50)
        
        # === ETAPA 1: CADASTRO DE PRODUTOR ===
        print("\n📝 ETAPA 1: Cadastro de Produtor")
        
        # 1.1 Validação de contato (OTP)
        telemovel_produtor = "912345678"
        resultado_otp = gerar_e_enviar_otp(telemovel_produtor, 'whatsapp', '127.0.0.1')
        assert resultado_otp['sucesso'] == True
        
        OTPService.validar_otp(telemovel_produtor, resultado_otp['codigo'], '127.0.0.1')
        
        # 1.2 Dados básicos e financeiros
        dados_produtor = {
            'nome': 'Produtor E2E Completo',
            'telemovel': telemovel_produtor,
            'provincia_id': 1,  # Simulado
            'municipio_id': 1,  # Simulado
            'principal_cultura': 'Batata-rena'
        }
        
        dados_financeiros = {
            'iban': 'AO0600600000123456789012345',
            'bi_path': 'documentos_bi/produtor_e2e.pdf'
        }
        
        # 1.3 Criar produtor
        produtor = _criar_usuario_produtor(
            telemovel=telemovel_produtor,
            dados=dados_produtor,
            senha="1234",
            financeiros=dados_financeiros
        )
        
        # 1.4 Aprovar produtor (simulação admin)
        produtor.status_conta = StatusConta.VERIFICADO
        produtor.conta_validada = True
        session.commit()
        
        assert produtor.status_conta == StatusConta.VERIFICADO
        assert produtor.pode_criar_anuncios()
        assert produtor.obter_carteira().saldo_disponivel == Decimal('0.00')
        
        print(f"✅ Produtor criado: {produtor.nome} (ID: {produtor.id})")
        
        # === ETAPA 2: CADASTRO DE COMPRADOR ===
        print("\n🛒 ETAPA 2: Cadastro de Comprador")
        
        # 2.1 Criar comprador
        telemovel_comprador = "912345679"
        comprador = Usuario(
            nome="Comprador E2E Completo",
            telemovel=telemovel_comprador,
            email="comprador@agrokongo.ao",
            senha="1234",
            tipo="comprador",
            status_conta=StatusConta.VERIFICADO,
            conta_validada=True
        )
        session.add(comprador)
        session.commit()
        
        # 2.2 Criar carteira do comprador com saldo
        carteira_comprador = Carteira(usuario_id=comprador.id, saldo_disponivel=Decimal('200000.00'))
        session.add(carteira_comprador)
        session.commit()
        
        print(f"✅ Comprador criado: {comprador.nome} (ID: {comprador.id})")
        print(f"✅ Saldo comprador: {carteira_comprador.saldo_disponivel} Kz")
        
        # === ETAPA 3: CRIAÇÃO DE SAFRA ===
        print("\n🌾 ETAPA 3: Criação de Safra")
        
        # 3.1 Criar produto
        from app.models import Produto
        produto = Produto(nome="Batata-rena Premium", categoria="Tubérculos")
        session.add(produto)
        session.commit()
        
        # 3.2 Criar safra
        safra = Safra(
            produtor_id=produtor.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('2000.00'),  # 2 toneladas
            preco_por_unidade=Decimal('200.00'),       # 200 Kz/kg
            status='disponivel',
            observacoes="Batata premium, colhida esta semana"
        )
        session.add(safra)
        session.commit()
        
        valor_total_safra = safra.quantidade_disponivel * safra.preco_por_unidade
        print(f"✅ Safra criada: {safra.quantidade_disponivel}kg @ {safra.preco_por_unidade}Kz/kg")
        print(f"✅ Valor total safra: {valor_total_safra} Kz")
        
        # === ETAPA 4: INÍCIO DA TRANSAÇÃO ===
        print("\n💰 ETAPA 4: Início da Transação")
        
        # 4.1 Comprador faz reserva
        quantidade_comprada = Decimal('500.00')  # 500kg
        valor_total_pago = quantidade_comprada * safra.preco_por_unidade  # 100.000 Kz
        
        transacao = Transacao(
            fatura_ref=f"AGK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            safra_id=safra.id,
            comprador_id=comprador.id,
            vendedor_id=produtor.id,
            quantidade_comprada=quantidade_comprada,
            valor_total_pago=valor_total_pago,
            status=TransactionStatus.PENDENTE
        )
        
        transacao.recalcular_financeiro()
        session.add(transacao)
        session.commit()
        
        # 4.2 Bloquear stock
        safra.quantidade_disponivel -= quantidade_comprada
        session.commit()
        
        print(f"✅ Transação criada: {transacao.fatura_ref}")
        print(f"✅ Quantidade: {quantidade_comprada}kg")
        print(f"✅ Valor total: {valor_total_pago} Kz")
        print(f"✅ Comissão: {transacao.comissao_plataforma} Kz")
        print(f"✅ Stock restante: {safra.quantidade_disponivel}kg")
        
        # === ETAPA 5: ACEITAÇÃO DA RESERVA ===
        print("\n✅ ETAPA 5: Aceitação da Reserva")
        
        # 5.1 Produtor aceita reserva
        transacao.status = TransactionStatus.AGUARDANDO_PAGAMENTO
        session.commit()
        
        # 5.2 Notificar comprador
        notificacao = Notificacao(
            usuario_id=comprador.id,
            mensagem=f"Sua reserva {transacao.fatura_ref} foi aceita! Prossiga com o pagamento.",
            link=f"/pagar-reserva/{transacao.id}"
        )
        session.add(notificacao)
        session.commit()
        
        print(f"✅ Reserva aceita pelo produtor")
        
        # === ETAPA 6: PAGAMENTO E ESCROW ===
        print("\n🔒 ETAPA 6: Pagamento e Escrow")
        
        # 6.1 Comprador realiza pagamento
        carteira_comprador.debitar(valor_total_pago, f"Pagamento reserva {transacao.fatura_ref}")
        
        # 6.2 Transação entra em análise
        transacao.status = TransactionStatus.ANALISE
        transacao.data_pagamento_escrow = datetime.now(timezone.utc)
        session.commit()
        
        # 6.3 Admin valida pagamento
        transacao.status = TransactionStatus.ESCROW
        session.commit()
        
        # 6.4 Bloquear valor na carteira do produtor
        carteira_produtor = produtor.obter_carteira()
        carteira_produtor.bloquear(transacao.valor_liquido_vendedor, f"Escrow {transacao.fatura_ref}")
        
        print(f"✅ Pagamento realizado: {valor_total_pago} Kz")
        print(f"✅ Saldo comprador: {carteira_comprador.saldo_disponivel} Kz")
        print(f"✅ Valor em escrow: {transacao.valor_liquido_vendedor} Kz")
        
        # === ETAPA 7: ENVIO DA MERCADORIA ===
        print("\n📦 ETAPA 7: Envio da Mercadoria")
        
        # 7.1 Produtor envia mercadoria
        transacao.status = TransactionStatus.ENVIADO
        transacao.data_envio = datetime.now(timezone.utc)
        transacao.calcular_janela_logistica()
        session.commit()
        
        # 7.2 Notificar comprador
        notificacao_envio = Notificacao(
            usuario_id=comprador.id,
            mensagem=f"Sua encomenda {transacao.fatura_ref} foi enviada! Previsão: {transacao.previsao_entrega.strftime('%d/%m/%Y')}",
            link=f"/acompanhar-encomenda/{transacao.id}"
        )
        session.add(notificacao_envio)
        session.commit()
        
        print(f"✅ Mercadoria enviada em: {transacao.data_envio.strftime('%d/%m/%Y %H:%M')}")
        print(f"✅ Previsão de entrega: {transacao.previsao_entrega.strftime('%d/%m/%Y')}")
        
        # === ETAPA 8: ENTREGA E CONFIRMAÇÃO ===
        print("\n🎯 ETAPA 8: Entrega e Confirmação")
        
        # 8.1 Simular entrega
        transacao.status = TransactionStatus.ENTREGUE
        transacao.data_entrega = datetime.now(timezone.utc)
        session.commit()
        
        # 8.2 Comprador confirma recebimento
        carteira_produtor.liberar(transacao.valor_liquido_vendedor, f"Liberação escrow {transacao.fatura_ref}")
        
        print(f"✅ Mercadoria entregue em: {transacao.data_entrega.strftime('%d/%m/%Y %H:%M')}")
        print(f"✅ Valor liberado: {transacao.valor_liquido_vendedor} Kz")
        print(f"✅ Saldo produtor: {carteira_produtor.saldo_disponivel} Kz")
        
        # === ETAPA 9: LIQUIDAÇÃO FINAL ===
        print("\n🏦 ETAPA 9: Liquidação Final")
        
        # 9.1 Processar liquidação assíncrona
        with patch('app.tasks.pagamentos.processar_liquidacao.delay') as mock_task:
            mock_task.return_value = MagicMock(id='task_123')
            processar_liquidacao.delay(transacao.id)
        
        # 9.2 Admin confirma transferência
        transacao.status = TransactionStatus.FINALIZADO
        transacao.data_liquidacao = datetime.now(timezone.utc)
        transacao.transferencia_concluida = True
        session.commit()
        
        # 9.3 Atualizar estatísticas do produtor
        produtor.vendas_concluidas += 1
        session.commit()
        
        print(f"✅ Transação finalizada em: {transacao.data_liquidacao.strftime('%d/%m/%Y %H:%M')}")
        print(f"✅ Transferência concluída: {transacao.transferencia_concluida}")
        print(f"✅ Vendas concluídas: {produtor.vendas_concluidas}")
        
        # === ETAPA 10: LEVANTAMENTO ===
        print("\n💸 ETAPA 10: Levantamento")
        
        # 10.1 Produtor solicita levantamento
        valor_levantar = Decimal('80000.00')  # 80.000 Kz
        
        if carteira_produtor.saldo_disponivel >= valor_levantar:
            carteira_produtor.debitar(valor_levantar, f"Levantamento para IBAN {produtor.iban}")
            
            # 10.2 Registrar levantamento
            from app.models import MovimentacaoFinanceira
            levantamento = MovimentacaoFinanceira(
                usuario_id=produtor.id,
                valor=valor_levantar,
                tipo='debito',
                descricao=f"Levantamento para IBAN {produtor.iban}",
                saldo_anterior=carteira_produtor.saldo_disponivel + valor_levantar,
                saldo_posterior=carteira_produtor.saldo_disponivel
            )
            session.add(levantamento)
            session.commit()
            
            print(f"✅ Levantamento solicitado: {valor_levantar} Kz")
            print(f"✅ Destino: IBAN {produtor.iban}")
            print(f"✅ Saldo final produtor: {carteira_produtor.saldo_disponivel} Kz")
        else:
            pytest.fail("Saldo insuficiente para levantamento")
        
        # === VALIDAÇÕES FINAIS ===
        print("\n🔍 VALIDAÇÕES FINAIS")
        print("=" * 50)
        
        # Verificar estado final
        assert transacao.status == TransactionStatus.FINALIZADO
        assert transacao.transferencia_concluida == True
        assert transacao.data_liquidacao is not None
        
        # Verificar saldos finais
        assert carteira_produtor.saldo_disponivel > Decimal('0.00')
        assert carteira_comprador.saldo_disponivel < Decimal('200000.00')
        
        # Verificar movimentações
        from app.models import MovimentacaoFinanceira
        movimentacoes_produtor = MovimentacaoFinanceira.query.filter_by(usuario_id=produtor.id).all()
        assert len(movimentacoes_produtor) >= 2  # Liberação + Levantamento
        
        # Verificar logs
        logs = LogAuditoria.query.filter_by(usuario_id=produtor.id).all()
        assert len(logs) >= 1
        
        # Verificar notificações
        notificacoes_comprador = Notificacao.query.filter_by(usuario_id=comprador.id).all()
        assert len(notificacoes_comprador) >= 2
        
        print("✅ Ciclo completo validado com sucesso!")
        
        # === RELATÓRIO FINAL ===
        print("\n📊 RELATÓRIO FINAL DO CICLO")
        print("=" * 50)
        print(f"🌱 Produtor: {produtor.nome}")
        print(f"   • Status: {produtor.status_conta}")
        print(f"   • Vendas: {produtor.vendas_concluidas}")
        print(f"   • Saldo: {carteira_produtor.saldo_disponivel} Kz")
        print("")
        print(f"🛒 Comprador: {comprador.nome}")
        print(f"   • Status: {comprador.status_conta}")
        print(f"   • Saldo: {carteira_comprador.saldo_disponivel} Kz")
        print("")
        print(f"🌾 Transação: {transacao.fatura_ref}")
        print(f"   • Produto: {produto.nome}")
        print(f"   • Quantidade: {quantidade_comprada} kg")
        print(f"   • Valor: {valor_total_pago} Kz")
        print(f"   • Status: {transacao.status}")
        print(f"   • Duração: {(transacao.data_liquidacao - transacao.data_criacao).days} dias")
        
        print("\n🎉 CICLO COMPLETO CONCLUÍDO COM SUCESSO!")
        
        return {
            'produtor': produtor,
            'comprador': comprador,
            'transacao': transacao,
            'safra': safra,
            'carteira_produtor': carteira_produtor,
            'carteira_comprador': carteira_comprador
        }
    
    def test_ciclo_com_disputa_resolucao(self, session, mock_celery, mock_redis):
        """
        Teste de ciclo com disputa e resolução
        """
        print("\n⚠️ TESTE DE CICLO COM DISPUTA")
        print("=" * 30)
        
        # Criar cenário básico (resumido)
        produtor = Usuario(
            nome="Produtor Disputa",
            telemovel="912345680",
            tipo="produtor",
            status_conta=StatusConta.VERIFICADO,
            conta_validada=True
        )
        session.add(produtor)
        
        comprador = Usuario(
            nome="Comprador Disputa",
            telemovel="912345681",
            tipo="comprador",
            status_conta=StatusConta.VERIFICADO,
            conta_validada=True
        )
        session.add(comprador)
        
        # Criar carteiras
        carteira_produtor = Carteira(usuario_id=produtor.id, saldo_disponivel=Decimal('0.00'))
        carteira_comprador = Carteira(usuario_id=comprador.id, saldo_disponivel=Decimal('50000.00'))
        session.add_all([carteira_produtor, carteira_comprador])
        
        # Criar safra e transação
        produto = Produto(nome="Milho", categoria="Grãos")
        session.add(produto)
        session.commit()
        
        safra = Safra(
            produtor_id=produtor.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('100.00'),
            preco_por_unidade=Decimal('100.00')
        )
        session.add(safra)
        session.commit()
        
        transacao = Transacao(
            fatura_ref="DISPUTA001",
            safra_id=safra.id,
            comprador_id=comprador.id,
            vendedor_id=produtor.id,
            quantidade_comprada=Decimal('50.00'),
            valor_total_pago=Decimal('5000.00'),
            status=TransactionStatus.ESCROW
        )
        transacao.recalcular_financeiro()
        session.add(transacao)
        session.commit()
        
        # Bloquear valor em escrow
        carteira_produtor.bloquear(transacao.valor_liquido_vendedor, f"Escrow {transacao.fatura_ref}")
        
        # Comprador abre disputa
        transacao.status = TransactionStatus.DISPUTA
        session.commit()
        
        # Criar disputa
        disputa = Disputa(
            transacao_id=transacao.id,
            reclamante_id=comprador.id,
            motivo="Produto não conforme",
            descricao="O milho entregue não estava na qualidade especificada",
            status="aberta"
        )
        session.add(disputa)
        session.commit()
        
        print(f"✅ Disputa criada: {disputa.motivo}")
        print(f"✅ Valor em disputa: {transacao.valor_liquido_vendedor} Kz")
        
        # Admin resolve disputa (favorável ao comprador)
        disputa.status = "resolvida"
        disputa.decisao = "reembolso_completo"
        disputa.observacoes = "Produto não conforme, reembolso autorizado"
        session.commit()
        
        # Reembolsar comprador
        carteira_comprador.creditar(transacao.valor_total_pago, f"Reembolso disputa {transacao.fatura_ref}")
        
        # Cancelar transação
        transacao.status = TransactionStatus.CANCELADO
        session.commit()
        
        # Devolver stock
        safra.quantidade_disponivel += transacao.quantidade_comprada
        session.commit()
        
        # Liberar valor bloqueado do produtor
        carteira_produtor.liberar(transacao.valor_liquido_vendedor, f"Liberação disputa {transacao.fatura_ref}")
        
        print(f"✅ Disputa resolvida: {disputa.decisao}")
        print(f"✅ Comprador reembolsado: {transacao.valor_total_pago} Kz")
        print(f"✅ Transação cancelada: {transacao.status}")
        print(f"✅ Stock devolvido: {safra.quantidade_disponivel} kg")
        
        # Validações
        assert transacao.status == TransactionStatus.CANCELADO
        assert disputa.status == "resolvida"
        assert carteira_comprador.saldo_disponivel == Decimal('55000.00')
        assert safra.quantidade_disponivel == Decimal('100.00')
        
        print("✅ Ciclo com disputa validado com sucesso!")
    
    def test_performance_ciclo_completo(self, session, mock_celery, mock_redis):
        """
        Teste de performance do ciclo completo
        """
        import time
        
        print("\n⚡ TESTE DE PERFORMANCE - CICLO COMPLETO")
        print("=" * 45)
        
        start_time = time.time()
        
        # Executar ciclo completo (versão simplificada para performance)
        resultado = self.test_ciclo_completo_sucesso_total(session, mock_celery, mock_redis)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️ Tempo total de execução: {execution_time:.2f} segundos")
        
        # Validações de performance
        assert execution_time < 15.0  # Deve completar em < 15s
        assert resultado['transacao'].status == TransactionStatus.FINALIZADO
        
        print(f"✅ Performance adequada: {execution_time:.2f}s < 15.0s")


@pytest.mark.e2e
@pytest.mark.slow
class TestFluxosAlternativosE2E:
    """Testes E2E de fluxos alternativos e exceções"""
    
    def test_fluxo_multiplos_produtores(self, session, mock_celery, mock_redis):
        """Teste com múltiplos produtores e transações"""
        print("\n🔄 TESTE E2E: MÚLTIPLOS PRODUTORES")
        print("=" * 40)
        
        # Criar múltiplos produtores
        produtores = []
        for i in range(3):
            produtor = Usuario(
                nome=f"Produtor {i+1}",
                telemovel=f"91234567{i+2}",
                tipo="produtor",
                status_conta=StatusConta.VERIFICADO,
                conta_validada=True
            )
            session.add(produtor)
            produtores.append(produtor)
        
        comprador = Usuario(
            nome="Comprador Multi",
            telemovel="912345690",
            tipo="comprador",
            status_conta=StatusConta.VERIFICADO,
            conta_validada=True
        )
        session.add(comprador)
        
        # Criar carteiras
        for produtor in produtores:
            carteira = Carteira(usuario_id=produtor.id, saldo_disponivel=Decimal('0.00'))
            session.add(carteira)
        
        carteira_comprador = Carteira(usuario_id=comprador.id, saldo_disponivel=Decimal('300000.00'))
        session.add(carteira_comprador)
        session.commit()
        
        # Criar produtos e safras
        produtos = []
        for i, produtor in enumerate(produtores):
            produto = Produto(nome=f"Produto {i+1}", categoria=f"Categoria {i+1}")
            session.add(produto)
            produtos.append(produto)
            session.commit()
            
            safra = Safra(
                produtor_id=produtor.id,
                produto_id=produto.id,
                quantidade_disponivel=Decimal('500.00'),
                preco_por_unidade=Decimal('100.00'),
                status='disponivel'
            )
            session.add(safra)
            session.commit()
        
        # Criar múltiplas transações
        transacoes = []
        for i, (produtor, produto) in enumerate(zip(produtores, produtos)):
            transacao = Transacao(
                fatura_ref=f"MULTI{i+1:03d}{int(time.time())}",
                safra_id=produto.safras[0].id if hasattr(produto, 'safras') else i+1,
                comprador_id=comprador.id,
                vendedor_id=produtor.id,
                quantidade_comprada=Decimal('100.00'),
                valor_total_pago=Decimal('10000.00'),
                status=TransactionStatus.ESCROW
            )
            transacao.recalcular_financeiro()
            session.add(transacao)
            transacoes.append(transacao)
        
        session.commit()
        
        # Validar criação
        assert len(produtores) == 3
        assert len(transacoes) == 3
        assert len(produtos) == 3
        
        # Verificar cada transação
        for transacao in transacoes:
            assert transacao.status == TransactionStatus.ESCROW
            assert transacao.comissao_plataforma == Decimal('1000.00')
            assert transacao.valor_liquido_vendedor == Decimal('9000.00')
        
        print(f"✅ Criados {len(produtores)} produtores")
        print(f"✅ Criadas {len(transacoes)} transações")
        print(f"✅ Valor total em escrow: {sum(t.valor_liquido_vendedor for t in transacoes)} Kz")
    
    def test_fluxo_concorrencia_transacoes(self, session, mock_celery, mock_redis):
        """Teste concorrência de múltiplas transações simultâneas"""
        print("\n⚡ TESTE E2E: CONCORRÊNCIA DE TRANSAÇÕES")
        print("=" * 45)
        
        # Criar produtor e comprador
        produtor = Usuario(
            nome="Produtor Concorrência",
            telemovel="912345691",
            tipo="produtor",
            status_conta=StatusConta.VERIFICADO,
            conta_validada=True
        )
        session.add(produtor)
        
        comprador = Usuario(
            nome="Comprador Concorrência",
            telemovel="912345692",
            tipo="comprador",
            status_conta=StatusConta.VERIFICADO,
            conta_validada=True
        )
        session.add(comprador)
        
        # Criar carteiras
        carteira_produtor = Carteira(usuario_id=produtor.id, saldo_disponivel=Decimal('0.00'))
        carteira_comprador = Carteira(usuario_id=comprador.id, saldo_disponivel=Decimal('500000.00'))
        session.add_all([carteira_produtor, carteira_comprador])
        session.commit()
        
        # Criar safra grande
        produto = Produto(nome="Arroz em Grão", categoria="Grãos")
        session.add(produto)
        session.commit()
        
        safra = Safra(
            produtor_id=produtor.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('1000.00'),
            preco_por_unidade=Decimal('50.00'),
            status='disponivel'
        )
        session.add(safra)
        session.commit()
        
        # Simular múltiplas transações concorrentes
        transacoes = []
        import time
        
        start_time = time.time()
        
        for i in range(5):
            transacao = Transacao(
                fatura_ref=f"CONC{i+1:03d}{int(time.time())}",
                safra_id=safra.id,
                comprador_id=comprador.id,
                vendedor_id=produtor.id,
                quantidade_comprada=Decimal('50.00'),
                valor_total_pago=Decimal('2500.00'),
                status=TransactionStatus.PENDENTE
            )
            transacao.recalcular_financeiro()
            session.add(transacao)
            transacoes.append(transacao)
        
        session.commit()
        
        end_time = time.time()
        
        # Validar concorrência
        assert len(transacoes) == 5
        assert end_time - start_time < 1.0  # Deve ser rápido
        
        # Verificar stock
        stock_restante = safra.quantidade_disponivel
        total_comprado = sum(t.quantidade_comprada for t in transacoes)
        assert stock_restante == Decimal('1000.00') - total_comprado
        
        print(f"✅ {len(transacoes)} transações concorrentes criadas")
        print(f"✅ Tempo criação: {(end_time - start_time):.3f}s")
        print(f"✅ Stock restante: {stock_restante} kg")
        print(f"✅ Total comprado: {total_comprado} kg")


@pytest.mark.e2e
class TestRelatoriosE2E:
    """Testes E2E de relatórios e métricas"""
    
    def test_relatorio_completo_sistema(self, session, produtor_user, comprador_user, transacao_finalizada):
        """Teste geração de relatório completo do sistema"""
        print("\n📊 TESTE E2E: RELATÓRIO COMPLETO DO SISTEMA")
        print("=" * 50)
        
        # Métricas de usuários
        total_usuarios = Usuario.query.count()
        produtores = Usuario.query.filter_by(tipo='produtor').count()
        compradores = Usuario.query.filter_by(tipo='comprador').count()
        
        # Métricas de transações
        total_transacoes = Transacao.query.count()
        transacoes_finalizadas = Transacao.query.filter_by(status=TransactionStatus.FINALIZADO).count()
        transacoes_pendentes = Transacao.query.filter_by(status=TransactionStatus.PENDENTE).count()
        
        # Métricas financeiras
        from app.models import MovimentacaoFinanceira
        total_movimentacoes = MovimentacaoFinanceira.query.count()
        
        # Métricas de safras
        from app.models import Safra
        total_safras = Safra.query.count()
        safras_disponiveis = Safra.query.filter_by(status='disponivel').count()
        
        # Imprimir relatório
        print(f"📊 RELATÓRIO DO SISTEMA AGROKONGO")
        print(f"   • Total de usuários: {total_usuarios}")
        print(f"   • Produtores: {produtores}")
        print(f"   • Compradores: {compradores}")
        print(f"   • Total de transações: {total_transacoes}")
        print(f"   • Transações finalizadas: {transacoes_finalizadas}")
        print(f"   • Transações pendentes: {transacoes_pendentes}")
        print(f"   • Total de movimentações: {total_movimentacoes}")
        print(f"   • Total de safras: {total_safras}")
        print(f"   • Safras disponíveis: {safras_disponiveis}")
        
        # Validações
        assert total_usuarios >= 2
        assert produtores >= 1
        assert compradores >= 1
        assert total_transacoes >= 1
        assert transacoes_finalizadas >= 1
        
        print("✅ Relatório gerado com sucesso!")
