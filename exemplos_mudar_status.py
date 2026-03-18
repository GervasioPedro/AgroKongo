"""
Exemplos de uso dos novos métodos de mudança de status

Este arquivo demonstra como usar os métodos refatorados:
1. mudar_status() com auto_add
2. mudar_status_em_lote()
3. pode_mudar_para()
4. validar_transicao
"""

from app import create_app
from app.extensions import db
from app.models import Transacao, TransactionStatus
from app.utils.status_helper import status_to_value


app = create_app('dev')

with app.app_context():
    print("=" * 80)
    print("EXEMPLOS DE USO DOS NOVOS MÉTODOS DE STATUS")
    print("=" * 80)
    
    # ========================================================================
    # EXEMPLO 1: Uso básico com auto_add (padrão)
    # ========================================================================
    print("\n1️⃣ USO BÁSICO COM AUTO_ADD:")
    print("-" * 80)
    print("Código antigo:")
    print("""
    historico = transacao.mudar_status(STATUS_NOVO, "obs")
    if historico:
        db.session.add(historico)
    """)
    
    print("\nCódigo novo (auto-add automático):")
    print("""
    transacao.mudar_status(STATUS_NOVO, "obs")
    # Histórico adicionado automaticamente!
    """)
    
    # ========================================================================
    # EXEMPLO 2: Validação de transição
    # ========================================================================
    print("\n2️⃣ VALIDAÇÃO DE TRANSIÇÃO:")
    print("-" * 80)
    
    # Buscar uma transação de exemplo
    transacao = Transacao.query.first()
    if transacao:
        print(f"Transação {transacao.fatura_ref} está com status: {transacao.status}")
        
        # Verificar se pode mudar para determinado status
        pode_cancelar = transacao.pode_mudar_para(
            status_to_value(TransactionStatus.CANCELADO)
        )
        print(f"Pode cancelar? {pode_cancelar}")
        
        # Usar validação automática (lança exceção se inválido)
        try:
            transacao.mudar_status(
                status_to_value(TransactionStatus.CANCELADO),
                "Cancelando com validação",
                validar_transicao=True  # Valida antes de mudar
            )
            print("✅ Transição válida e executada!")
        except ValueError as e:
            print(f"❌ Transição inválida: {e}")
    
    # ========================================================================
    # EXEMPLO 3: Mudança em lote
    # ========================================================================
    print("\n3️⃣ MUDANÇA EM LOTE:")
    print("-" * 80)
    print("""
    # Cancelar múltiplas transações de uma vez
    ids_transacoes = [1, 2, 3]
    resultados = Transacao.mudar_status_em_lote(
        transacoes=ids_transacoes,
        novo_status=status_to_value(TransactionStatus.CANCELADO),
        observacao="Cancelamento em lote"
    )
    
    for transacao, historico in resultados:
        print(f"Transação {transacao.fatura_ref}: {historico.status_novo}")
    """)
    
    # ========================================================================
    # EXEMPLO 4: Auto-add desativado (casos especiais)
    # ========================================================================
    print("\n4️⃣ AUTO-ADD DESATIVADO:")
    print("-" * 80)
    print("""
    # Quando você quer controle manual do histórico
    historico = transacao.mudar_status(
        status_to_value(TransactionStatus.CANCELADO),
        "obs",
        auto_add=False  # Não adiciona automaticamente
    )
    
    # Fazer outras operações...
    db.session.add(historico)  # Adiciona manualmente quando quiser
    db.session.commit()
    """)
    
    # ========================================================================
    # EXEMPLO 5: Observações personalizadas em lote
    # ========================================================================
    print("\n5️⃣ OBSERVAÇÕES PERSONALIZADAS EM LOTE:")
    print("-" * 80)
    print("""
    # Cada transação com sua própria observação
    ids_transacoes = [1, 2, 3]
    observacoes = [
        "Cancelado: motivo 1",
        "Cancelado: motivo 2", 
        "Cancelado: motivo 3"
    ]
    
    resultados = Transacao.mudar_status_em_lote(
        transacoes=ids_transacoes,
        novo_status=status_to_value(TransactionStatus.CANCELADO),
        observacao=observacoes  # Lista de observações
    )
    """)
    
    print("\n" + "=" * 80)
    print("✅ TODOS OS RECURSOS ESTÃO DISPONÍVEIS!")
    print("=" * 80)
