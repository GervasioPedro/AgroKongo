# tests/integration/test_fim_de_ciclo.py - Teste de Fim de Ciclo Completo
# Cadastro -> Venda -> Escrow -> Liquidação -> Levantamento (Sucesso Total)

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.models import (
    Usuario, Safra, Transacao, TransactionStatus,
    Notificacao, LogAuditoria, HistoricoStatus
)
from app.models import Carteira, StatusConta
from app.models import Disputa
from app.services.otp_service import gerar_e_enviar_otp, OTPService
from app.routes.cadastro_produtor import _criar_usuario_produtor
from app.tasks.pagamentos import processar_liquidacao


@pytest.mark.integration
@pytest.mark.financial
class TestFimDeCicloCompleto:
    """
    Teste de Fim de Ciclo: Validação completa do fluxo de negócio
    [ ] Cadastro -> Venda -> Escrow -> Liquidação -> Levantamento
    """
    
    def test_ciclo_completo_sucesso(self, session, mock_celery, mock_redis):
        """
        Teste completo: Cadastro -> Venda -> Escrow -> Liquidação -> Levantamento
        Simula todo o ciclo de vida de uma transação no AgroKongo
        """
        print("\n🌱 INICIANDO CICLO COMPLETO AGROKONGO")
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
            'nome': 'Produtor Ciclo Completo',
            'provincia_id': 1,
            'municipio_id': 1,
            'principal_cultura': 'Batata-rena'
        }
        
        dados_financeiros = {
            'iban': 'AO0600600000123456789012345',
            'bi_path': 'documentos_bi/produtor_ciclo.pdf'
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
        
        # Verificações
        assert produtor.status_conta == StatusConta.VERIFICADO
        assert produtor.pode_criar_anuncios()
        assert produtor.obter_carteira().saldo_disponivel == Decimal('0.00')
        
        print(f"✅ Produtor criado: {produtor.nome} (ID: {produtor.id})")
        print(f"✅ Carteira inicial: {produtor.obter_carteira().saldo_disponivel} Kz")
        
        # === ETAPA 2: CADASTRO DE COMPRADOR ===
        print("\n🛒 ETAPA 2: Cadastro de Comprador")
        
        # 2.1 Criar comprador
        telemovel_comprador = "912345679"
        comprador = Usuario(
            nome="Comprador Ciclo Completo",
            telemovel=telemovel_comprador,
            email="comprador@agrokongo.ao",
            senha="1234",
            tipo="comprador",
            status_conta=StatusConta.VERIFICADO,
            conta_validada=True
        )
        session.add(comprador)
        session.commit()
        
        # 2.2 Criar carteira do comprador
        carteira_comprador = Carteira(usuario_id=comprador.id, saldo_disponivel=Decimal('100000.00'))
        session.add(carteira_comprador)
        session.commit()
        
        print(f"✅ Comprador criado: {comprador.nome} (ID: {comprador.id})")
        print(f"✅ Saldo comprador: {carteira_comprador.saldo_disponivel} Kz")
        
        # === ETAPA 3: CRIAÇÃO DE SAFRA (VENDA) ===
        print("\n🌾 ETAPA 3: Criação de Safra")
        
        # 3.1 Criar produto
        from app.models import Produto
        produto = Produto(nome="Batata-rena", categoria="Tubérculos")
        session.add(produto)
        session.commit()
        
        # 3.2 Criar safra
        safra = Safra(
            produtor_id=produtor.id,
            produto_id=produto.id,
            quantidade_disponivel=Decimal('1000.00'),  # 1 tonelada
            preco_por_unidade=Decimal('150.00'),       # 150 Kz/kg
            status='disponivel',
            observacoes="Batata de alta qualidade, colhida esta semana"
        )
        session.add(safra)
        session.commit()
        
        valor_total_safra = safra.quantidade_disponivel * safra.preco_por_unidade
        print(f"✅ Safra criada: {safra.quantidade_disponivel}kg @ {safra.preco_por_unidade}Kz/kg")
        print(f"✅ Valor total safra: {valor_total_safra} Kz")
        
        # === ETAPA 4: INÍCIO DA TRANSAÇÃO (RESERVA) ===
        print("\n💰 ETAPA 4: Início da Transação (Reserva)")
        
        # 4.1 Comprador faz reserva
        quantidade_comprada = Decimal('500.00')  # 500kg
        valor_total_pago = quantidade_comprada * safra.preco_por_unidade  # 75.000 Kz
        
        transacao = Transacao(
            fatura_ref=f"AGK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            safra_id=safra.id,
            comprador_id=comprador.id,
            vendedor_id=produtor.id,
            quantidade_comprada=quantidade_comprada,
            valor_total_pago=valor_total_pago,
            status=TransactionStatus.PENDENTE
        )
        
        # 4.2 Calcular comissões
        transacao.recalcular_financeiro()
        session.add(transacao)
        session.commit()
        
        # 4.3 Bloquear stock
        safra.quantidade_disponivel -= quantidade_comprada
        session.commit()
        
        print(f"✅ Transação criada: {transacao.fatura_ref}")
        print(f"✅ Quantidade: {quantidade_comprada}kg")
        print(f"✅ Valor total: {valor_total_pago} Kz")
        print(f"✅ Comissão plataforma: {transacao.comissao_plataforma} Kz")
        print(f"✅ Valor líquido produtor: {transacao.valor_liquido_vendedor} Kz")
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
        print(f"✅ Notificação enviada ao comprador")
        
        # === ETAPA 6: PAGAMENTO E ESCROW ===
        print("\n🔒 ETAPA 6: Pagamento e Escrow")
        
        # 6.1 Comprador realiza pagamento (simulado)
        carteira_comprador.debitar(valor_total_pago, f"Pagamento reserva {transacao.fatura_ref}")
        
        # 6.2 Transação entra em análise
        transacao.status = TransactionStatus.ANALISE
        transacao.data_pagamento_escrow = datetime.now(timezone.utc)
        session.commit()
        
        # 6.3 Admin valida pagamento
        transacao.status = TransactionStatus.ESCROW
        session.commit()
        
        # 6.4 Bloquear valor na carteira do produtor (simulação)
        carteira_produtor = produtor.obter_carteira()
        carteira_produtor.bloquear(transacao.valor_liquido_vendedor, f"Escrow {transacao.fatura_ref}")
        
        print(f"✅ Pagamento realizado: {valor_total_pago} Kz")
        print(f"✅ Saldo comprador: {carteira_comprador.saldo_disponivel} Kz")
        print(f"✅ Valor em escrow: {transacao.valor_liquido_vendedor} Kz")
        print(f"✅ Status: {transacao.status}")
        
        # === ETAPA 7: ENVIO DA MERCADORIA ===
        print("\n📦 ETAPA 7: Envio da Mercadoria")
        
        # 7.1 Produtor envia mercadoria
        transacao.status = TransactionStatus.ENVIADO
        transacao.data_envio = datetime.now(timezone.utc)
        transacao.calcular_janela_logistica()  # Define previsão de entrega
        session.commit()
        
        # 7.2 Notificar comprador sobre envio
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
        # 8.3 Liberar valor do escrow
        carteira_produtor.liberar(transacao.valor_liquido_vendedor, f"Liberação escrow {transacao.fatura_ref}")
        
        print(f"✅ Mercadoria entregue em: {transacao.data_entrega.strftime('%d/%m/%Y %H:%M')}")
        print(f"✅ Valor liberado para produtor: {transacao.valor_liquido_vendedor} Kz")
        print(f"✅ Saldo disponível produtor: {carteira_produtor.saldo_disponivel} Kz")
        
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
        print(f"✅ Vendas concluídas produtor: {produtor.vendas_concluidas}")
        
        # === ETAPA 10: LEVANTAMENTO ===
        print("\n💸 ETAPA 10: Levantamento")
        
        # 10.1 Produtor solicita levantamento
        valor_levantar = Decimal('50000.00')  # 50.000 Kz
        
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
        
        # Verificar estado final da transação
        assert transacao.status == TransactionStatus.FINALIZADO
        assert transacao.transferencia_concluida == True
        assert transacao.data_liquidacao is not None
        
        # Verificar saldos finais
        assert carteira_produtor.saldo_disponivel > Decimal('0.00')
        assert carteira_comprador.saldo_disponivel < Decimal('100000.00')
        
        # Verificar movimentações
        movimentacoes_produtor = MovimentacaoFinanceira.query.filter_by(usuario_id=produtor.id).all()
        assert len(movimentacoes_produtor) >= 2  # Liberação + Levantamento
        
        # Verificar logs de auditoria
        logs = LogAuditoria.query.filter_by(usuario_id=produtor.id).all()
        assert len(logs) >= 1  # Pelo menos o cadastro
        
        # Verificar notificações
        notificacoes_comprador = Notificacao.query.filter_by(usuario_id=comprador.id).all()
        assert len(notificacoes_comprador) >= 2  # Aceitação + Envio
        
        print("✅ Transação finalizada com sucesso!")
        print(f"✅ Status final: {transacao.status}")
        print(f"✅ Valor total movimentado: {valor_total_pago} Kz")
        print(f"✅ Saldo final produtor: {carteira_produtor.saldo_disponivel} Kz")
        print(f"✅ Saldo final comprador: {carteira_comprador.saldo_disponivel} Kz")
        print(f"✅ Logs de auditoria: {len(logs)} registros")
        print(f"✅ Notificações enviadas: {len(notificacoes_comprador)}")
        
        # === RELATÓRIO FINAL ===
        print("\n📊 RELATÓRIO FINAL DO CICLO")
        print("=" * 50)
        print(f"🌱 Produtor: {produtor.nome}")
        print(f"   • Status: {produtor.status_conta}")
        print(f"   • Vendas concluídas: {produtor.vendas_concluidas}")
        print(f"   • Saldo disponível: {carteira_produtor.saldo_disponivel} Kz")
        print(f"   • Saldo bloqueado: {carteira_produtor.saldo_bloqueado} Kz")
        print("")
        print(f"🛒 Comprador: {comprador.nome}")
        print(f"   • Status: {comprador.status_conta}")
        print(f"   • Saldo disponível: {carteira_comprador.saldo_disponivel} Kz")
        print("")
        print(f"🌾 Transação: {transacao.fatura_ref}")
        print(f"   • Produto: {produto.nome}")
        print(f"   • Quantidade: {quantidade_comprada} kg")
        print(f"   • Valor total: {valor_total_pago} Kz")
        print(f"   • Comissão: {transacao.comissao_plataforma} Kz")
        print(f"   • Status: {transacao.status}")
        print(f"   • Duração: {(transacao.data_liquidacao - transacao.data_criacao).days} dias")
        
        print("\n🎉 CICLO COMPLETO CONCLUÍDO COM SUCESSO!")
        print("✅ Cadastro → Venda → Escrow → Liquidação → Levantamento")
        
        return {
            'produtor': produtor,
            'comprador': comprador,
            'transacao': transacao,
            'safra': safra,
            'carteira_produtor': carteira_produtor,
            'carteira_comprador': carteira_comprador
        }
    
    def test_ciclo_com_disputa(self, session, mock_celery, mock_redis):
        """
        Teste de ciclo com disputa para validar fluxo alternativo
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
            quantidade_disponivel=Decimal('200.00'),
            preco_por_unidade=Decimal('100.00')
        )
        session.add(safra)
        session.commit()
        
        transacao = Transacao(
            fatura_ref="DISPUTA001",
            safra_id=safra.id,
            comprador_id=comprador.id,
            vendedor_id=produtor.id,
            quantidade_comprada=Decimal('100.00'),
            valor_total_pago=Decimal('10000.00'),
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
            motivo="Produto não conforme com descrição",
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
        carteira_comprador.creditar(valor_total_pago, f"Reembolso disputa {transacao.fatura_ref}")
        
        # Cancelar transação
        transacao.status = TransactionStatus.CANCELADO
        session.commit()
        
        # Devolver stock
        safra.quantidade_disponivel += transacao.quantidade_comprada
        session.commit()
        
        # Liberar valor bloqueado do produtor
        carteira_produtor.liberar(transacao.valor_liquido_vendedor, f"Liberação disputa {transacao.fatura_ref}")
        
        print(f"✅ Disputa resolvida: {disputa.decisao}")
        print(f"✅ Comprador reembolsado: {valor_total_pago} Kz")
        print(f"✅ Transação cancelada: {transacao.status}")
        print(f"✅ Stock devolvido: {safra.quantidade_disponivel} kg")
        
        # Validações
        assert transacao.status == TransactionStatus.CANCELADO
        assert disputa.status == "resolvida"
        assert carteira_comprador.saldo_disponivel == Decimal('50000.00')
        assert safra.quantidade_disponivel == Decimal('200.00')
        
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
        resultado = self.test_ciclo_completo_sucesso(session, mock_celery, mock_redis)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️ Tempo total de execução: {execution_time:.2f} segundos")
        
        # Validações de performance
        assert execution_time < 10.0  # Deve completar em < 10s
        assert resultado['transacao'].status == TransactionStatus.FINALIZADO
        
        print(f"✅ Performance adequada: {execution_time:.2f}s < 10.0s")


@pytest.mark.integration
@pytest.mark.financial
class TestValidacoesFinanceiras:
    """
    Validações específicas dos fluxos financeiros
    Peer Review dos cálculos e movimentações
    """
    
    def test_calculos_comissao_precisao(self, session):
        """
        Validação da precisão dos cálculos de comissão
        """
        print("\n💰 VALIDAÇÃO CÁLCULOS COMISSÃO")
        print("=" * 35)
        
        # Criar transação com valor fracionado
        transacao = Transacao(
            fatura_ref="COMISSAO001",
            safra_id=1,
            comprador_id=1,
            vendedor_id=1,
            quantidade_comprada=Decimal('333.33'),
            valor_total_pago=Decimal('12345.67'),
            status=TransactionStatus.PENDENTE
        )
        
        # Calcular financeiro
        transacao.recalcular_financeiro()
        
        # Validações matemáticas
        valor_esperado_comissao = (Decimal('12345.67') * Decimal('0.10')).quantize(Decimal('0.01'), rounding='ROUND_HALF_UP')
        valor_esperado_liquido = Decimal('12345.67') - valor_esperado_comissao
        
        assert transacao.comissao_plataforma == valor_esperado_comissao
        assert transacao.valor_liquido_vendedor == valor_esperado_liquido
        assert transacao.comissao_plataforma + transacao.valor_liquido_vendedor == transacao.valor_total_pago
        
        print(f"✅ Valor total: {transacao.valor_total_pago} Kz")
        print(f"✅ Comissão (10%): {transacao.comissao_plataforma} Kz")
        print(f"✅ Valor líquido: {transacao.valor_liquido_vendedor} Kz")
        print(f"✅ Soma: {transacao.comissao_plataforma + transacao.valor_liquido_vendedor} Kz")
        print("✅ Cálculos precisos validados!")
    
    def test_integridade_saldos(self, session):
        """
        Validação da integridade dos saldos durante movimentações
        """
        print("\n🔒 VALIDAÇÃO INTEGRIDADE SALDOS")
        print("=" * 35)
        
        # Criar carteira
        carteira = Carteira(
            usuario_id=1,
            saldo_disponivel=Decimal('1000.00'),
            saldo_bloqueado=Decimal('0.00')
        )
        session.add(carteira)
        session.commit()
        
        saldo_inicial = carteira.saldo_disponivel
        saldo_total_inicial = carteira.get_saldo_total()
        
        # Operações sequenciais
        operacoes = [
            ('credito', Decimal('500.00'), 'Depósito inicial'),
            ('bloqueio', Decimal('200.00'), 'Reserva para escrow'),
            ('debito', Decimal('100.00'), 'Pagamento taxa'),
            ('liberacao', Decimal('100.00'), 'Liberação parcial escrow')
        ]
        
        for tipo, valor, descricao in operacoes:
            saldo_antes = carteira.get_saldo_total()
            
            if tipo == 'credito':
                carteira.creditar(valor, descricao)
            elif tipo == 'debito':
                carteira.debitar(valor, descricao)
            elif tipo == 'bloqueio':
                carteira.bloquear(valor, descricao)
            elif tipo == 'liberacao':
                carteira.liberar(valor, descricao)
            
            saldo_depois = carteira.get_saldo_total()
            
            # Validação de integridade
            if tipo in ['credito', 'debito']:
                if tipo == 'credito':
                    assert saldo_depois == saldo_antes + valor
                else:
                    assert saldo_depois == saldo_antes - valor
            else:
                # Bloqueio/liberação não altera total
                assert saldo_depois == saldo_antes
            
            print(f"✅ {tipo.capitalize()}: {valor} Kz - Saldo total: {saldo_depois} Kz")
        
        # Validação final
        saldo_final = carteira.get_saldo_total()
        saldo_esperado = saldo_inicial + Decimal('500.00') - Decimal('100.00')  # crédito - débito
        
        assert saldo_final == saldo_esperado
        
        print(f"✅ Saldo inicial: {saldo_inicial} Kz")
        print(f"✅ Saldo final: {saldo_final} Kz")
        print(f"✅ Saldo esperado: {saldo_esperado} Kz")
        print("✅ Integridade dos saldos validada!")
    
    def test_prevencao_double_spending(self, session):
        """
        Validação de prevenção de double spending
        """
        print("\n🚫 VALIDAÇÃO PREVENÇÃO DOUBLE SPENDING")
        print("=" * 45)
        
        # Criar carteira com saldo limitado
        carteira = Carteira(
            usuario_id=1,
            saldo_disponivel=Decimal('100.00'),
            saldo_bloqueado=Decimal('0.00')
        )
        session.add(carteira)
        session.commit()
        
        # Tentativa de débito maior que saldo
        with pytest.raises(ValueError, match="Saldo insuficiente"):
            carteira.debitar(Decimal('150.00'), "Tentativa double spending")
        
        # Tentativa de bloqueio maior que disponível
        with pytest.raises(ValueError, match="Saldo insuficiente"):
            carteira.bloquear(Decimal('120.00'), "Bloqueio excessivo")
        
        # Operações válidas
        carteira.debitar(Decimal('50.00'), "Débito válido")
        assert carteira.saldo_disponivel == Decimal('50.00')
        
        carteira.bloquear(Decimal('30.00'), "Bloqueio válido")
        assert carteira.saldo_disponivel == Decimal('20.00')
        assert carteira.saldo_bloqueado == Decimal('30.00')
        
        # Tentativa de débito após bloqueio
        with pytest.raises(ValueError, match="Saldo insuficiente"):
            carteira.debitar(Decimal('25.00'), "Débito após bloqueio")
        
        print("✅ Double spending prevenido com sucesso!")
        print(f"✅ Saldo disponível final: {carteira.saldo_disponivel} Kz")
        print(f"✅ Saldo bloqueado final: {carteira.saldo_bloqueado} Kz")
        print("✅ Proteções contra fraudes validadas!")
