#!/usr/bin/env python3
"""
Script para testar performance das queries antes e depois dos índices

Uso:
    python scripts/test_query_performance.py
"""
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Adiciona o projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar environment para evitar imports desnecessários
os.environ['FLASK_ENV'] = 'dev'
os.environ['SECRET_KEY'] = 'test-secret-key-for-script'
os.environ['DATABASE_URL'] = 'postgresql://agrokongo_user:agrokongo_pass@localhost:5432/agrokongo_dev'

from app.extensions import db
from app.models import Transacao, Safra, Usuario, Produto
from app.models.base import TransactionStatus


def format_tempo(segundos: float) -> str:
    """Formata tempo em ms ou s"""
    if segundos < 1:
        return f"{segundos * 1000:.2f}ms"
    return f"{segundos:.2f}s"


def testar_query(nome: str, query, expected_rows: int = None):
    """Testa performance de uma query"""
    print(f"\n📊 Testando: {nome}")
    
    # Warmup (primeira execução pode ser lenta)
    _ = query.all()
    
    # Média de 3 execuções
    tempos = []
    for i in range(3):
        start = time.time()
        resultados = query.all()
        end = time.time()
        tempos.append(end - start)
    
    media = sum(tempos) / len(tempos)
    min_tempo = min(tempos)
    max_tempo = max(tempos)
    
    print(f"   Resultados: {len(resultados)} rows")
    if expected_rows:
        status = "✅" if len(resultados) == expected_rows else "❌"
        print(f"   {status} Esperado: {expected_rows}, Obtido: {len(resultados)}")
    print(f"   ⏱️  Tempo médio: {format_tempo(media)}")
    print(f"   📈 Min: {format_tempo(min_tempo)}, Máx: {format_tempo(max_tempo)}")
    
    return media


def main():
    print("=" * 70)
    print("🚀 TESTE DE PERFORMANCE - ÍNDICES DE DATABASE")
    print("=" * 70)
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Objetivo: Validar impacto dos índices estratégicos")
    print("=" * 70)
    
    # Import create_app apenas dentro da função para evitar issues de inicialização
    from app import create_app
    
    app = create_app('dev')
    
    with app.app_context():
        print("\n📋 VERIFICAÇÃO INICIAL")
        print("-" * 70)
        
        # Contagem de registros
        total_transacoes = Transacao.query.count()
        total_safras = Safra.query.count()
        total_usuarios = Usuario.query.count()
        
        print(f"📊 Transações: {total_transacoes}")
        print(f"📊 Safras: {total_safras}")
        print(f"📊 Usuários: {total_usuarios}")
        
        if total_transacoes < 10:
            print("\n⚠️  AVISO: Poucos dados para teste significativo")
            print("💡 Dica: Execute seed.py para popular o banco")
            return
        
        print("\n" + "=" * 70)
        print("🧪 EXECUTANDO TESTES DE PERFORMANCE")
        print("=" * 70)
        
        resultados = {}
        
        # === TESTE 1: Transações por Status ===
        resultados['trans_status'] = testar_query(
            "Transações por Status (pendente)",
            Transacao.query.filter_by(status=TransactionStatus.PENDENTE),
            expected_rows=None
        )
        
        # === TESTE 2: Transações do Comprador ===
        resultados['trans_comprador'] = testar_query(
            "Transações do Comprador ID=1",
            Transacao.query.filter_by(comprador_id=1)
        )
        
        # === TESTE 3: Transações do Vendedor ===
        resultados['trans_vendedor'] = testar_query(
            "Transações do Vendedor ID=1",
            Transacao.query.filter_by(vendedor_id=1)
        )
        
        # === TESTE 4: Transações Comprador + Status ===
        resultados['trans_comprador_status'] = testar_query(
            "Transações Comprador + Status (comprador_id=1, status=pendente)",
            Transacao.query.filter_by(comprador_id=1, status=TransactionStatus.PENDENTE)
        )
        
        # === TESTE 5: Safras por Produto + Status ===
        resultados['safras_produto_status'] = testar_query(
            "Safras por Produto + Status (produto_id=1, status=disponivel)",
            Safra.query.filter_by(produto_id=1, status='disponivel')
        )
        
        # === TESTE 6: Safras do Produtor ===
        resultados['safras_produtor'] = testar_query(
            "Safras do Produtor ID=1",
            Safra.query.filter_by(produtor_id=1)
        )
        
        # === TESTE 7: Usuários por Tipo ===
        resultados['usuarios_tipo'] = testar_query(
            "Usuários por Tipo (produtor)",
            Usuario.query.filter_by(tipo='produtor')
        )
        
        # === TESTE 8: Usuários Tipo + Validado ===
        resultados['usuarios_tipo_validado'] = testar_query(
            "Usuários Tipo + Validado (produtor, conta_validada=True)",
            Usuario.query.filter_by(tipo='produtor', conta_validada=True)
        )
        
        # === TESTE 9: Notificações Não Lidas ===
        from app.models import Notificacao
        resultados['notificacoes_nao_lidas'] = testar_query(
            "Notificações Não Lidas (usuario_id=1, lida=False)",
            Notificacao.query.filter_by(usuario_id=1, lida=False)
        )
        
        # === RELATÓRIO FINAL ===
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DE PERFORMANCE")
        print("=" * 70)
        
        total_geral = sum(resultados.values())
        media_geral = total_geral / len(resultados)
        
        print(f"\n⏱️  Tempo médio geral: {format_tempo(media_geral)} por query")
        print(f"📈 Total testado: {len(resultados)} queries")
        
        # Classificação de performance
        print("\n📋 CLASSIFICAÇÃO:")
        for nome, tempo in sorted(resultados.items(), key=lambda x: x[1], reverse=True):
            status = "✅" if tempo < 0.05 else "⚠️" if tempo < 0.2 else "❌"
            print(f"   {status} {nome}: {format_tempo(tempo)}")
        
        print("\n" + "=" * 70)
        print("💡 INTERPRETAÇÃO DOS RESULTADOS")
        print("=" * 70)
        print("""
✅ Excelente: < 50ms  → Índices estão funcionando bem
⚠️  Aceitável: 50-200ms → Pode melhorar com mais dados
❌ Crítico: > 200ms → Índices necessários ou otimização urgente

📊 PRÓXIMOS PASSOS:
1. Se os tempos estiverem > 200ms, aplicar índices é CRÍTICO
2. Executar migration: flask db upgrade
3. Reexecutar este teste para validar melhoria
4. Monitorar em produção com ferramentas de APM
        """)
        
        print("=" * 70)
        print("✅ Teste concluído!")
        print("=" * 70)


if __name__ == '__main__':
    main()
