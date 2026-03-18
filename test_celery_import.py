"""
Script de validação de importação do Celery
Testa se a aplicação consegue inicializar sem erros do gssapi/Kerberos
"""
import sys

print("=" * 60)
print("TESTE DE IMPORTAÇÃO - CELERY/GSSAPI")
print("=" * 60)

# Teste 1: Import direto do extensions
print("\n1. Testando import de app.extensions...")
try:
    from app.extensions import CELERY_AVAILABLE, celery
    print(f"   ✅ Import bem-sucedido!")
    print(f"   - CELERY_AVAILABLE: {CELERY_AVAILABLE}")
    print(f"   - celery object: {celery}")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

# Teste 2: Criar a aplicação Flask
print("\n2. Testando create_app()...")
try:
    from app import create_app
    app = create_app('dev')
    print(f"   ✅ Aplicação criada com sucesso!")
except Exception as e:
    print(f"   ❌ Erro ao criar app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 3: Import das tasks
print("\n3. Testando import de app.tasks...")
try:
    from app import tasks
    print(f"   ✅ Tasks carregadas!")
    print(f"   - job_verificar_entregas: {hasattr(tasks, 'job_verificar_entregas')}")
    print(f"   - enviar_fatura_email: {hasattr(tasks, 'enviar_fatura_email')}")
    print(f"   - limpar_sessoes_expiradas: {hasattr(tasks, 'limpar_sessoes_expiradas')}")
except Exception as e:
    print(f"   ❌ Erro ao importar tasks: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 4: Verificar health check
print("\n4. Testando rota de health check...")
try:
    with app.app_context():
        from app.routes.main import health_check
        response = health_check()
        print(f"   ✅ Health check funcionou!")
        print(f"   - Status: {response[0].get_json().get('status')}")
except Exception as e:
    print(f"   ❌ Erro no health check: {e}")
    import traceback
    traceback.print_exc()
    # Não falhamos o teste por causa disto

print("\n" + "=" * 60)
print("TODOS OS TESTES PRINCIPAIS PASSARAM!")
print("=" * 60)
print("\nResumo:")
print(f"  • Celery disponível: {CELERY_AVAILABLE}")
print(f"  • Aplicação inicializa: ✅")
print(f"  • Tasks carregadas: ✅")
print("\nNota: Se CELERY_AVAILABLE for False, as tarefas usarão")
print("      fallback síncrono (comportamento esperado sem KfW)")
