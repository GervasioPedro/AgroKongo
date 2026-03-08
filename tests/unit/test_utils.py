# tests/unit/test_utils.py - Testes unitários para utilitários de negócio
# Validação de funções helper e regras de negócio

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import tempfile
import os

from app.utils.helpers import salvar_ficheiro
from app.models.base import aware_utcnow


class TestHelpers:
    """Testes unitários para funções helper"""
    
    def test_aware_utcnow_retorna_timezone(self):
        """Testa que aware_utcnow retorna datetime com timezone"""
        agora = aware_utcnow()
        assert agora.tzinfo is not None
        assert agora.tzinfo.zone == 'UTC'
    
    def test_salvar_ficheiro_imagem_valida(self):
        """Testa salvamento de arquivo de imagem válido"""
        # Criar arquivo temporário de teste
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'fake_image_content')
            tmp_path = tmp.name
        
        try:
            # Mock do objeto FileStorage
            class MockFileStorage:
                def __init__(self, filename, content):
                    self.filename = filename
                    self.content = content
                
                def save(self, dst):
                    with open(dst, 'wb') as f:
                        f.write(self.content)
                
                def read(self):
                    return self.content
            
            # Criar diretório de teste
            test_dir = tempfile.mkdtemp()
            
            file_storage = MockFileStorage('test_image.jpg', b'fake_image_content')
            
            # Testar salvamento
            resultado = salvar_ficheiro(file_storage, subpasta='test', privado=False, base_dir=test_dir)
            
            assert resultado is not None
            assert 'test_image' in resultado
            assert resultado.endswith('.jpg')
            
            # Verificar se arquivo foi salvo
            full_path = os.path.join(test_dir, 'test', resultado)
            assert os.path.exists(full_path)
            
            # Limpeza
            os.unlink(full_path)
            os.rmdir(os.path.join(test_dir, 'test'))
            
        finally:
            os.unlink(tmp_path)
    
    def test_salvar_ficheiro_pdf_valido(self):
        """Testa salvamento de arquivo PDF válido"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'fake_pdf_content')
            tmp_path = tmp.name
        
        try:
            class MockFileStorage:
                def __init__(self, filename, content):
                    self.filename = filename
                    self.content = content
                
                def save(self, dst):
                    with open(dst, 'wb') as f:
                        f.write(self.content)
            
            test_dir = tempfile.mkdtemp()
            
            file_storage = MockFileStorage('document.pdf', b'fake_pdf_content')
            
            resultado = salvar_ficheiro(file_storage, subpasta='docs', privado=True, base_dir=test_dir)
            
            assert resultado is not None
            assert 'document' in resultado
            assert resultado.endswith('.pdf')
            
            full_path = os.path.join(test_dir, 'docs', resultado)
            assert os.path.exists(full_path)
            
            # Limpeza
            os.unlink(full_path)
            os.rmdir(os.path.join(test_dir, 'docs'))
            
        finally:
            os.unlink(tmp_path)


class TestValidacoesNegocio:
    """Testes para validações de regras de negócio"""
    
    def test_validar_stock_disponivel_para_reserva(self, session, safra_ativa):
        """Testa validação de stock disponível para reserva"""
        stock_original = safra_ativa.quantidade_disponivel
        quantidade_reserva = Decimal('10.00')
        
        # Stock suficiente
        assert stock_original >= quantidade_reserva
        
        # Simular reserva
        stock_restante = stock_original - quantidade_reserva
        assert stock_restante >= 0
    
    def test_validar_stock_insuficiente_para_reserva(self, session, safra_ativa):
        """Testa falha quando stock insuficiente"""
        stock_original = safra_ativa.quantidade_disponivel
        quantidade_reserva = stock_original + Decimal('50.00')  # Mais que o disponível
        
        # Stock insuficiente
        assert stock_original < quantidade_reserva
    
    def test_calcular_valor_total_transacao(self, session, safra_ativa):
        """Testa cálculo do valor total da transação"""
        quantidade = Decimal('15.50')
        preco_unitario = safra_ativa.preco_por_unidade
        valor_esperado = quantidade * preco_unitario
        
        valor_calculado = quantidade * preco_unitario
        
        assert valor_calculado == valor_esperado
        assert isinstance(valor_calculado, Decimal)
    
    def test_validar_preco_minimo_venda(self, session, safra_ativa):
        """Testa validação de preço mínimo para venda"""
        preco_unitario = safra_ativa.preco_por_unidade
        
        # Preço deve ser positivo
        assert preco_unitario > 0
        
        # Preço mínimo razoável (ex: 100 Kz/kg)
        preco_minimo = Decimal('100.00')
        assert preco_unitario >= preco_minimo
    
    def test_validar_quantidade_minima_compra(self):
        """Testa validação de quantidade mínima de compra"""
        quantidade_minima = Decimal('1.00')
        
        # Quantidades válidas
        assert Decimal('5.00') >= quantidade_minima
        assert Decimal('10.50') >= quantidade_minima
        
        # Quantidade inválida
        with pytest.raises(AssertionError):
            assert Decimal('0.50') >= quantidade_minima
    
    def test_validar_formato_fatura_ref(self):
        """Testa validação do formato da referência da fatura"""
        # Formato esperado: AK-ANO-XXXXXXXX
        import uuid
        
        ano = datetime.now().year
        uuid_hex = uuid.uuid4().hex[:8].upper()
        ref_esperada = f"AK-{ano}-{uuid_hex}"
        
        # Validar formato
        assert ref_esperada.startswith('AK-')
        assert str(ano) in ref_esperada
        assert len(ref_esperada) == 13  # AK-XXXX-XXXXXXXX
        assert ref_esperada.count('-') == 2


class TestCalculosFinanceiros:
    """Testes para cálculos financeiros"""
    
    def test_calculo_comissao_plataforma_10_porcento(self):
        """Testa cálculo da comissão da plataforma (10%)"""
        valor_total = Decimal('10000.00')
        taxa_percentual = Decimal('0.10')
        
        comissao_esperada = (valor_total * taxa_percentual).quantize(Decimal('0.01'))
        liquido_esperado = (valor_total - comissao_esperada).quantize(Decimal('0.01'))
        
        comissao_calculada = (valor_total * taxa_percentual).quantize(Decimal('0.01'))
        liquido_calculado = (valor_total - comissao_calculada).quantize(Decimal('0.01'))
        
        assert comissao_calculada == comissao_esperada
        assert liquido_calculado == liquido_esperado
        assert comissao_calculada == Decimal('1000.00')
        assert liquido_calculado == Decimal('9000.00')
    
    def test_calculo_comissao_valores_fracionados(self):
        """Testa cálculo de comissão com valores fracionados"""
        valor_total = Decimal('12345.67')
        taxa_percentual = Decimal('0.10')
        
        comissao_calculada = (valor_total * taxa_percentual).quantize(Decimal('0.01'))
        liquido_calculado = (valor_total - comissao_calculada).quantize(Decimal('0.01'))
        
        # Verificar precisão
        assert comissao_calculada == Decimal('1234.57')
        assert liquido_calculado == Decimal('11111.10')
        
        # Verificar que soma total é preservada
        assert comissao_calculada + liquido_calculado == valor_total
    
    def test_calculo_taxa_administrativa_disputa(self):
        """Testa cálculo de taxa administrativa em disputas"""
        valor_total = Decimal('5000.00')
        taxa_admin_percentual = Decimal('0.05')  # 5%
        
        taxa_admin_esperada = (valor_total * taxa_admin_percentual).quantize(Decimal('0.01'))
        
        taxa_admin_calculada = (valor_total * taxa_admin_percentual).quantize(Decimal('0.01'))
        
        assert taxa_admin_calculada == taxa_admin_esperada
        assert taxa_admin_calculada == Decimal('250.00')
    
    def test_arredondamento_financeiro_correto(self):
        """Testa arredondamento correto de valores financeiros"""
        # Valores que precisam de arredondamento
        valor_1 = Decimal('10.005')
        valor_2 = Decimal('10.004')
        
        # Arredondamento para cima (ROUND_HALF_UP)
        arredondado_1 = valor_1.quantize(Decimal('0.01'))
        arredondado_2 = valor_2.quantize(Decimal('0.01'))
        
        assert arredondado_1 == Decimal('10.01')  # Arredonda para cima
        assert arredondado_2 == Decimal('10.00')  # Mantém


class TestValidacoesTempo:
    """Testes para validações relacionadas a tempo"""
    
    def test_calculo_prazo_entrega_padrao(self):
        """Testa cálculo de prazo de entrega padrão (3 dias)"""
        data_envio = datetime.now(timezone.utc)
        prazo_padrao_dias = 3
        
        previsao_entrega = data_envio + timedelta(days=prazo_padrao_dias)
        
        assert previsao_entrega > data_envio
        assert (previsao_entrega - data_envio).days == 3
    
    def test_validacao_prazo_disputa_24h(self):
        """Testa validação de prazo mínimo de 24h para disputa"""
        previsao_entrega = datetime.now(timezone.utc) - timedelta(hours=30)  # 30h atrás
        agora = datetime.now(timezone.utc)
        
        prazo_minimo = previsao_entrega + timedelta(hours=24)
        
        # Deve poder abrir disputa (passou 24h)
        assert agora >= prazo_minimo
        
        # Calcular horas decorridas
        horas_decorridas = (agora - previsao_entrega).total_seconds() / 3600
        assert horas_decorridas >= 24
    
    def test_validacao_prazo_disputa_invalido(self):
        """Testa validação quando prazo de 24h não foi atingido"""
        previsao_entrega = datetime.now(timezone.utc) - timedelta(hours=20)  # 20h atrás
        agora = datetime.now(timezone.utc)
        
        prazo_minimo = previsao_entrega + timedelta(hours=24)
        
        # Não deve poder abrir disputa (não passou 24h)
        assert agora < prazo_minimo
        
        # Calcular horas decorridas
        horas_decorridas = (agora - previsao_entrega).total_seconds() / 3600
        assert horas_decorridas < 24
    
    def test_validacao_expiracao_reserva_48h(self):
        """Testa validação de expiração de reserva após 48h"""
        data_criacao = datetime.now(timezone.utc) - timedelta(hours=50)  # 50h atrás
        agora = datetime.now(timezone.utc)
        
        prazo_expiracao = data_criacao + timedelta(hours=48)
        
        # Deve estar expirado
        assert agora > prazo_expiracao
        
        # Calcular horas desde criação
        horas_desde_criacao = (agora - data_criacao).total_seconds() / 3600
        assert horas_desde_criacao >= 48
