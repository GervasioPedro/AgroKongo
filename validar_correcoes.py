"""
Validação Rápida das Correções
Verifica se os ficheiros foram modificados corretamente
"""

import sys
from pathlib import Path

def verificar_ficheiro_usuario():
    """Verifica se o modelo Usuario foi corrigido"""
    print("\n📄 Verificando app/models/usuario.py...")
    
    caminho = Path("app/models/usuario.py")
    if not caminho.exists():
        print("   ❌ Ficheiro não encontrado!")
        return False
    
    conteudo = caminho.read_text(encoding='utf-8')
    
    # Verificar se tem a correção do hasattr
    if "if hasattr(self, 'transacoes_como_comprador'):" in conteudo:
        print("   ✅ Hybrid property 'compras' corrigida")
    else:
        print("   ❌ Hybrid property 'compras' NÃO foi corrigida")
        return False
    
    if "if hasattr(self, 'transacoes_como_vendedor'):" in conteudo:
        print("   ✅ Hybrid property 'vendas' corrigida")
    else:
        print("   ❌ Hybrid property 'vendas' NÃO foi corrigida")
        return False
    
    return True

def verificar_ficheiro_base_task():
    """Verifica se o decorador AgroKongoTask foi criado"""
    print("\n📄 Verificando app/tasks/base.py...")
    
    caminho = Path("app/tasks/base.py")
    if not caminho.exists():
        print("   ❌ Ficheiro não encontrado!")
        return False
    
    conteudo = caminho.read_text(encoding='utf-8')
    
    # Verificar se tem o decorador
    if "def AgroKongoTask(func=None):" in conteudo:
        print("   ✅ Decorador AgroKongoTask criado")
    else:
        print("   ❌ Decorador AgroKongoTask NÃO foi criado")
        return False
    
    if "Decorador para criar tasks Celery com a base AgroKongoTask" in conteudo:
        print("   ✅ Documentação do decorador presente")
    else:
        print("   ⚠️  Documentação do decorador ausente")
    
    return True

def verificar_ficheiro_testes():
    """Verifica se os testes foram atualizados"""
    print("\n📄 Verificando tests/automation/test_base_task_handler.py...")
    
    caminho = Path("tests/automation/test_base_task_handler.py")
    if not caminho.exists():
        print("   ❌ Ficheiro não encontrado!")
        return False
    
    conteudo = caminho.read_text(encoding='utf-8')
    
    # Verificar imports
    if "from app.models import Usuario, Notificacao, LogAuditoria, Transacao" in conteudo:
        print("   ✅ Import de Transacao adicionado")
    else:
        print("   ⚠️  Import de Transacao pode estar em falta")
    
    if "from app.tasks.pagamentos import processar_liquidacao" in conteudo:
        print("   ✅ Import de processar_liquidacao adicionado")
    else:
        print("   ⚠️  Import de processar_liquidacao pode estar em falta")
    
    # Verificar uso do decorador
    if "test_task = AgroKongoTask(test_task_func)" in conteudo:
        print("   ✅ Uso do decorador atualizado nos testes")
    else:
        print("   ⚠️  Uso do decorador pode não estar atualizado")
    
    return True

def test_imports():
    """Testa se os imports básicos funcionam"""
    print("\n🧪 Testando imports...")
    
    try:
        from app.models.usuario import Usuario
        print("   ✅ Usuario import OK")
    except Exception as e:
        print(f"   ❌ Erro ao importar Usuario: {e}")
        return False
    
    try:
        from app.tasks.base import AgroKongoTask
        print("   ✅ AgroKongoTask import OK")
    except Exception as e:
        print(f"   ❌ Erro ao importar AgroKongoTask: {e}")
        return False
    
    return True

def main():
    print("=" * 70)
    print("🔍 VALIDAÇÃO DAS CORREÇÕES APLICADAS")
    print("=" * 70)
    
    resultados = []
    
    # Verificar ficheiros
    resultados.append(verificar_ficheiro_usuario())
    resultados.append(verificar_ficheiro_base_task())
    resultados.append(verificar_ficheiro_testes())
    
    # Testar imports
    resultados.append(test_imports())
    
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL")
    print("=" * 70)
    
    if all(resultados):
        print("\n✅ TODAS AS VERIFICAÇÕES PASSARAM!")
        print("\nPróximo passo: Executar os testes com:")
        print("   python -m pytest tests/automation/test_base_task_handler.py -v")
        return 0
    else:
        print("\n❌ ALGUMAS VERIFICAÇÕES FALHARAM!")
        print("\nRevise os ficheiros modificados.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
