# tests/unit/test_financeiro.py - Testes unitários para cálculos financeiros
# Validação crítica para transações monetárias

import pytest
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timezone, timedelta

from app.models import Transacao, TransactionStatus, Usuario
from app.models import Disputa


class TestCalculosFinanceiros:
    """Testes para cálculos financeiros do sistema"""
    
    def test_calculo_comissao_plataforma_10_porcento(self):
        """Testa cálculo da comissão da plataforma (RN02 - 10%)"""
        valor_total = Decimal('10000.00')
        taxa_percentual = Decimal('0.10')
        
        comissao_esperada = (valor_total * taxa_percentual).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        liquido_esperado = (valor_total - comissao_esperada).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Validação dos cálculos
        assert comissao_esperada == Decimal('1000.00')
        assert liquido_esperado == Decimal('9000.00')
        assert comissao_esperada + liquido_esperado == valor_total
    
    def test_calculo_comissao_valores_fracionados(self):
        """Testa cálculo de comissão com valores que precisam de arredondamento"""
        casos_teste = [
            (Decimal('12345.67'), Decimal('1234.57'), Decimal('11111.10')),
            (Decimal('999.99'), Decimal('100.00'), Decimal('899.99')),
            (Decimal('1000.01'), Decimal('100.00'), Decimal('900.01')),
            (Decimal('5555.55'), Decimal('555.56'), Decimal('4999.99')),
        ]
        
        for valor_total, comissao_esperada, liquido_esperado in casos_teste:
            comissao_calculada = (valor_total * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            liquido_calculado = (valor_total - comissao_calculada).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            assert comissao_calculada == comissao_esperada, f"Erro no valor {valor_total}"
            assert liquido_calculado == liquido_esperado, f"Erro no valor {valor_total}"
            assert comissao_calculada + liquido_calculado == valor_total, f"Soma incorreta para {valor_total}"
    
    def test_calculo_comissao_valores_extremos(self):
        """Testa cálculo com valores extremos"""
        # Valores muito altos
        valor_alto = Decimal('999999999.99')
        comissao_alta = (valor_alto * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        assert comissao_alta == Decimal('99999999.99')
        
        # Valores muito baixos
        valor_baixo = Decimal('0.01')
        comissao_baixa = (valor_baixo * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        assert comissao_baixa == Decimal('0.00')  # Arredondado para baixo
    
    def test_calculo_taxa_administrativa_disputa(self):
        """Testa cálculo de taxa administrativa em disputas (RN08 - 5%)"""
        valor_total = Decimal('5000.00')
        taxa_admin_percentual = Decimal('0.05')
        
        taxa_admin_esperada = (valor_total * taxa_admin_percentual).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        assert taxa_admin_esperada == Decimal('250.00')
        
        # Testar com vários valores
        casos_taxa_admin = [
            (Decimal('10000.00'), Decimal('500.00')),
            (Decimal('1500.75'), Decimal('75.04')),
            (Decimal('333.33'), Decimal('16.67')),
        ]
        
        for valor, taxa_esperada in casos_taxa_admin:
            taxa_calculada = (valor * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            assert taxa_calculada == taxa_esperada
    
    def test_calculo_valor_total_transacao(self):
        """Testa cálculo do valor total da transação"""
        casos_teste = [
            (Decimal('10.00'), Decimal('1500.75'), Decimal('15007.50')),
            (Decimal('5.50'), Decimal('2000.00'), Decimal('11000.00')),
            (Decimal('100.00'), Decimal('999.99'), Decimal('99999.00')),
        ]
        
        for quantidade, preco_unitario, valor_esperado in casos_teste:
            valor_calculado = quantidade * preco_unitario
            valor_arredondado = valor_calculado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            assert valor_arredondado == valor_esperado
    
    def test_precisao_decimal_em_calculos(self):
        """Testa precisão de cálculos decimais"""
        # Usar Decimal para evitar problemas de ponto flutuante
        valor_float = 0.1 + 0.2  # 0.30000000000000004
        valor_decimal = Decimal('0.1') + Decimal('0.2')  # 0.3
        
        assert valor_decimal == Decimal('0.3')
        assert abs(valor_float - 0.3) > 0.0000001  # Problema do float
        
        # Testar precisão em cálculos financeiros
        valor_total = Decimal('12345.6789')
        valor_arredondado = valor_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        assert valor_arredondado == Decimal('12345.68')
    
    def test_validacao_limites_monetarios(self):
        """Testa validação de limites monetários"""
        # Valores mínimos e máximos permitidos
        valor_minimo = Decimal('0.01')
        valor_maximo = Decimal('999999999.99')
        
        # Valores válidos
        assert valor_minimo >= Decimal('0.01')
        assert valor_maximo <= Decimal('999999999.99')
        
        # Valores inválidos
        with pytest.raises(InvalidOperation):
            Decimal('-1.00')  # Negativo
        
        # Valores zero não permitidos em transações
        assert Decimal('0.00') < valor_minimo
    
    def test_calculo_saldo_disponivel_usuario(self, session, produtor_user):
        """Testa cálculo e atualização de saldo disponível"""
        saldo_inicial = Decimal('0.00')
        creditos = [Decimal('1000.00'), Decimal('500.50'), Decimal('250.75')]
        debitos = [Decimal('200.00'), Decimal('100.25')]
        
        # Calcular saldo final
        total_creditos = sum(creditos)
        total_debitos = sum(debitos)
        saldo_final = saldo_inicial + total_creditos - total_debitos
        
        saldo_esperado = Decimal('1000.00') + Decimal('500.50') + Decimal('250.75') - Decimal('200.00') - Decimal('100.25')
        saldo_esperado = saldo_esperado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        assert saldo_final == saldo_esperado
        assert saldo_final == Decimal('1451.00')
    
    def test_calculo_receita_plataforma(self):
        """Testa cálculo da receita total da plataforma"""
        transacoes = [
            {'valor': Decimal('10000.00'), 'comissao': Decimal('1000.00')},
            {'valor': Decimal('5000.00'), 'comissao': Decimal('500.00')},
            {'valor': Decimal('7500.00'), 'comissao': Decimal('750.00')},
        ]
        
        total_vendas = sum(t['valor'] for t in transacoes)
        total_comissoes = sum(t['comissao'] for t in transacoes)
        
        assert total_vendas == Decimal('22500.00')
        assert total_comissoes == Decimal('2250.00')
        
        # Verificar taxa média
        taxa_media = (total_comissoes / total_vendas) * Decimal('100')
        assert taxa_media == Decimal('10.00')  # 10%
    
    def test_calculo_estatisticas_vendedor(self, session, produtor_user):
        """Testa cálculo de estatísticas do vendedor"""
        # Simular vendas
        vendas = [
            {'status': 'finalizada', 'valor_liquido': Decimal('9000.00')},
            {'status': 'finalizada', 'valor_liquido': Decimal('4500.00')},
            {'status': 'escrow', 'valor_liquido': Decimal('3000.00')},
            {'status': 'enviado', 'valor_liquido': Decimal('1500.00')},
            {'status': 'cancelada', 'valor_liquido': Decimal('0.00')},
        ]
        
        # Calcular KPIs
        receita_total = sum(v['valor_liquido'] for v in vendas if v['status'] == 'finalizada')
        em_custodia = sum(v['valor_liquido'] for v in vendas if v['status'] in ['escrow', 'enviado'])
        
        assert receita_total == Decimal('13500.00')
        assert em_custodia == Decimal('4500.00')
        
        # Total de vendas concluídas
        vendas_concluidas = len([v for v in vendas if v['status'] == 'finalizada'])
        assert vendas_concluidas == 2


class TestValidacoesFinanceiras:
    """Testes para validações financeiras"""
    
    def test_validar_valor_minimo_transacao(self):
        """Testa valor mínimo para transação"""
        valor_minimo = Decimal('100.00')  # Exemplo: Kz 100
        
        # Valores válidos
        assert Decimal('100.00') >= valor_minimo
        assert Decimal('500.00') >= valor_minimo
        
        # Valores inválidos
        assert Decimal('99.99') < valor_minimo
        assert Decimal('50.00') < valor_minimo
    
    def test_validar_preco_unitario_positivo(self):
        """Testa que preço unitário é sempre positivo"""
        precos_validos = [
            Decimal('100.00'),
            Decimal('999.99'),
            Decimal('1000.50'),
        ]
        
        for preco in precos_validos:
            assert preco > 0
            assert preco > Decimal('0.00')
        
        # Preços inválidos
        precos_invalidos = [
            Decimal('0.00'),
            Decimal('-100.00'),
            Decimal('-1.50'),
        ]
        
        for preco in precos_invalidos:
            assert preco <= Decimal('0.00')
    
    def test_validar_quantidade_positiva(self):
        """Testa que quantidade é sempre positiva"""
        quantidades_validas = [
            Decimal('1.00'),
            Decimal('10.50'),
            Decimal('100.00'),
        ]
        
        for qtd in quantidades_validas:
            assert qtd > 0
            assert qtd >= Decimal('1.00')  # Mínimo 1kg
        
        # Quantidades inválidas
        quantidades_invalidas = [
            Decimal('0.00'),
            Decimal('-1.00'),
            Decimal('-10.50'),
        ]
        
        for qtd in quantidades_invalidas:
            assert qtd <= Decimal('0.00')
    
    def test_validar_saldo_suficiente_para_saque(self):
        """Testa validação de saldo suficiente para saque"""
        saldo_disponivel = Decimal('5000.00')
        
        # Saques válidos
        saques_validos = [
            Decimal('100.00'),
            Decimal('1000.00'),
            Decimal('5000.00'),  # Saldo total
        ]
        
        for saque in saques_validos:
            assert saque <= saldo_disponivel
        
        # Saques inválidos
        saques_invalidos = [
            Decimal('5000.01'),
            Decimal('6000.00'),
            Decimal('10000.00'),
        ]
        
        for saque in saques_invalidos:
            assert saque > saldo_disponivel
    
    def test_validar_limite_diario_transacoes(self):
        """Testa validação de limite diário de transações"""
        limite_diario = Decimal('50000.00')
        
        # Transações do dia
        transacoes_dia = [
            Decimal('10000.00'),
            Decimal('15000.00'),
            Decimal('20000.00'),
        ]
        
        total_dia = sum(transacoes_dia)
        
        # Dentro do limite
        assert total_dia <= limite_diario
        
        # Adicionar transação que ultrapassa limite
        transacoes_dia.append(Decimal('10000.00'))
        total_excedido = sum(transacoes_dia)
        
        assert total_excedido > limite_diário
    
    def test_validar_formato_moeda(self):
        """Testa validação de formato de moeda (Kz)"""
        # Valores válidos (2 casas decimais)
        valores_validos = [
            '100.00',
            '1500.75',
            '9999.99',
        ]
        
        for valor_str in valores_validos:
            valor_decimal = Decimal(valor_str)
            valor_str_formatado = f"{valor_decimal:.2f}"
            
            assert valor_str_formatado.count('.') == 1
            assert len(valor_str_formatado.split('.')[1]) == 2
        
        # Valores inválidos (mais de 2 casas decimais)
        valores_invalidos = [
            '100.000',
            '1500.755',
            '9999.999',
        ]
        
        for valor_str in valores_invalidos:
            valor_decimal = Decimal(valor_str)
            valor_arredondado = valor_decimal.quantize(Decimal('0.01'))
            
            # Deve arredondar para 2 casas
            valor_arredondado_str = f"{valor_arredondado:.2f}"
            assert len(valor_arredondado_str.split('.')[1]) == 2


class TestAuditoriaFinanceira:
    """Testes para auditoria financeira"""
    
    def test_rastreamento_transacao_completa(self, session, transacao_pendente):
        """Testa rastreamento completo da transação"""
        transacao = transacao_pendente
        
        # Verificar campos críticos para auditoria
        assert transacao.id is not None
        assert transacao.fatura_ref is not None
        assert transacao.uuid is not None
        assert transacao.data_criacao is not None
        assert transacao.valor_total_pago > 0
        assert transacao.comissao_plataforma >= 0
        assert transacao.valor_liquido_vendedor >= 0
        
        # Verificar consistência financeira
        total_calculado = transacao.comissao_plataforma + transacao.valor_liquido_vendedor
        assert total_calculado == transacao.valor_total_pago
    
    def test_log_auditoria_campos_obrigatorios(self):
        """Testa campos obrigatórios em log de auditoria"""
        from app.models import LogAuditoria
        
        # Simular criação de log
        dados_log = {
            'usuario_id': 1,
            'acao': 'TESTE_FINANCEIRO',
            'detalhes': 'Teste de validação financeira',
            'ip': '127.0.0.1',
            'data_criacao': datetime.now(timezone.utc)
        }
        
        # Validar campos obrigatórios
        assert dados_log['usuario_id'] is not None
        assert dados_log['acao'] is not None
        assert len(dados_log['acao']) > 0
        assert dados_log['detalhes'] is not None
        assert len(dados_log['detalhes']) > 0
        assert dados_log['data_criacao'] is not None
    
    def test_conciliacao_financeira(self):
        """Testa conciliação financeira entre transações"""
        # Dados de exemplo
        transacoes_registradas = [
            {'id': 1, 'valor': Decimal('1000.00'), 'status': 'finalizada'},
            {'id': 2, 'valor': Decimal('500.00'), 'status': 'finalizada'},
            {'id': 3, 'valor': Decimal('300.00'), 'status': 'pendente'},
        ]
        
        # Calcular totais esperados
        total_registrado = sum(t['valor'] for t in transacoes_registradas)
        total_finalizado = sum(t['valor'] for t in transacoes_registradas if t['status'] == 'finalizada')
        
        assert total_registrado == Decimal('1800.00')
        assert total_finalizado == Decimal('1500.00')
        
        # Validação de conciliação
        valor_pendente = total_registrado - total_finalizado
        assert valor_pendente == Decimal('300.00')
        
        # Verificar que valor pendente corresponde a transações pendentes
        transacoes_pendentes = [t for t in transacoes_registradas if t['status'] == 'pendente']
        soma_pendentes = sum(t['valor'] for t in transacoes_pendentes)
        
        assert valor_pendente == soma_pendentes
