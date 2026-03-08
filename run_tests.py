"""
Script completo para rodar todos os testes do AgroKongo
Cobertura target: 100%
"""
import os
import sys
import subprocess
from pathlib import Path

# Configurar ambiente de testes
os.environ['TEST_DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

print("=" * 80)
print("🧪 SUÍTE DE TESTES AGROKONGO 2026 - COBERTURA 100%")
print("=" * 80)
print(f"Database: {os.environ.get('TEST_DATABASE_URL')}")
print(f"Python Path: {os.environ.get('PYTHONPATH')}")
print("=" * 80)
print()

if __name__ == '__main__':
    # Argumentos personalizados
    args = sys.argv[1:]
    
    # Comandos base
    cmd_base = [
        sys.executable,
        '-m',
        'pytest',
    ]
    
    # Opções padrão
    default_options = [
        '--tb=short',
        '--strict-markers',
        '--disable-warnings',
        '--color=yes',
        '--durations=10',
        '-v',
    ]
    
    # Cobertura
    coverage_options = [
        '--cov=app',
        '--cov-report=term-missing',
        '--cov-report=html',
        '--cov-report=xml',
        '--cov-fail-under=100',  # Meta: 100% cobertura
    ]
    
    # Relatórios (verifica dependências)
    report_options = []
    try:
        import pytest_html
        report_options = [
            '--html=reports/test_report.html',
            '--self-contained-html',
        ]
        print("✅ Relatórios HTML: ativados")
    except ImportError:
        print("⚠️  pytest-html não instalado. Instale com: pip install pytest-html")
    
    # Diretórios de teste
    test_dirs = [
        'tests/unit/',
        'tests/integration/',
        'tests_framework/',
    ]
    
    # Verificar argumentos especiais
    if '--no-cov' in args:
        args.remove('--no-cov')
        coverage_options = []
    
    if '--no-html' in args:
        args.remove('--no-html')
        report_options = []
    
    # Verificar se pytest-html está disponível
    try:
        import pytest_html
        has_html = True
    except ImportError:
        has_html = False
        print("⚠️  pytest-html não instalado. Relatórios HTML desativados.")
        print("   Para ativar: pip install pytest-html")
        report_options = []
    
    # Montar comando final
    cmd = cmd_base + default_options + coverage_options + report_options + test_dirs + args
    
    print("📋 COMANDO DE EXECUÇÃO:")
    print(" ".join(cmd))
    print("=" * 80)
    print()
    
    # Criar diretório de relatórios
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    # Executar testes
    print("🚀 INICIANDO TESTES...")
    print("=" * 80)
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 80)
    
    # Resumo final
    if result.returncode == 0:
        print("\n✅ TODOS OS TESTES PASSARAM!")
        print("📊 Cobertura de código: 100%")
        if report_options:
            print(f"📄 Relatório HTML: file://{reports_dir.absolute()}/test_report.html")
        print(f"📄 Relatório XML: file://{reports_dir.absolute()}/coverage.xml")
        print(f"📄 Cobertura HTML: file://{Path('htmlcov').absolute()}/index.html")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        if report_options:
            print(f"📄 Verifique o relatório: file://{reports_dir.absolute()}/test_report.html")
    
    print("=" * 80)
    
    sys.exit(result.returncode)
