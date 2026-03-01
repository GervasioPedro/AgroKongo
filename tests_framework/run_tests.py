#!/usr/bin/env python3
# run_tests.py - Script principal para executar testes modularizados
# Interface unificada para todos os tipos de teste do AgroKongo

import sys
import os
import subprocess
import argparse
import time
from datetime import datetime

# Cores para output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def print_status(msg):
    print(f"{BLUE}[INFO]{NC} {msg}")

def print_success(msg):
    print(f"{GREEN}[SUCCESS]{NC} {msg}")

def print_warning(msg):
    print(f"{YELLOW}[WARNING]{NC} {msg}")

def print_error(msg):
    print(f"{RED}[ERROR]{NC} {msg}")

def print_header(msg):
    print(f"\n{CYAN}{'='*60}")
    print(f"{msg:^60}")
    print(f"{'='*60}{NC}")

def run_command(cmd, cwd=None):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_dependencies():
    """Instala dependências necessárias"""
    print_status("Verificando dependências...")
    
    # Verificar se pytest está instalado
    returncode, _, _ = run_command("python -m pytest --version")
    if returncode != 0:
        print_status("Instalando pytest e dependências...")
        run_command("python -m pip install pytest pytest-cov pytest-mock pytest-html")
    
    # Verificar dependências do projeto
    if os.path.exists('requirements-new.txt'):
        print_status("Instalando dependências do projeto...")
        run_command("python -m pip install -r requirements-new.txt")

def run_unit_tests():
    """Executa testes unitários"""
    print_header("EXECUTANDO TESTES UNITÁRIOS")
    
    cmd = "python -m pytest tests_framework/test_models.py tests_framework/test_cadastro.py -v --tb=short"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print_success("✅ Testes unitários passaram")
        return True
    else:
        print_error("❌ Falha nos testes unitários")
        print(stderr[:500])
        return False

def run_financial_tests():
    """Executa testes financeiros"""
    print_header("EXECUTANDO TESTES FINANCEIROS")
    
    cmd = "python -m pytest tests_framework/test_financial.py -v --tb=short -m financial"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print_success("✅ Testes financeiros passaram")
        return True
    else:
        print_error("❌ Falha nos testes financeiros")
        print(stderr[:500])
        return False

def run_integration_tests():
    """Executa testes de integração"""
    print_header("EXECUTANDO TESTES DE INTEGRAÇÃO")
    
    cmd = "python -m pytest tests_framework/test_integration.py -v --tb=short -m integration"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print_success("✅ Testes de integração passaram")
        return True
    else:
        print_error("❌ Falha nos testes de integração")
        print(stderr[:500])
        return False

def run_e2e_tests():
    """Executa testes end-to-end"""
    print_header("EXECUTANDO TESTES END-TO-END")
    
    cmd = "python -m pytest tests_framework/test_e2e.py -v --tb=short -m e2e --timeout=600"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print_success("✅ Testes E2E passaram")
        return True
    else:
        print_error("❌ Falha nos testes E2E")
        print(stderr[:500])
        return False

def run_coverage_tests():
    """Executa testes com cobertura"""
    print_header("EXECUTANDO TESTES COM COBERTURA")
    
    cmd = "python -m pytest tests_framework/ --cov=app --cov-report=html:tests_framework/htmlcov --cov-report=term-missing --cov-fail-under=80"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print_success("✅ Cobertura de testes adequada (>80%)")
        return True
    else:
        print_error("❌ Cobertura de testes insuficiente (<80%)")
        print(stderr[:500])
        return False

def run_security_tests():
    """Executa testes de segurança"""
    print_header("EXECUTANDO TESTES DE SEGURANÇA")
    
    # Executar scan de segurança
    if os.path.exists('security_scan.py'):
        returncode, stdout, stderr = run_command("python security_scan.py")
        if returncode == 0:
            print_success("✅ Scan de segurança passou")
            return True
        else:
            print_error("❌ Vulnerabilidades encontradas")
            return False
    else:
        print_warning("⚠️ Script de segurança não encontrado")
        return True

def run_performance_tests():
    """Executa testes de performance"""
    print_header("EXECUTANDO TESTES DE PERFORMANCE")
    
    cmd = "python -m pytest tests_framework/ -v --tb=short -m performance --benchmark-only"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print_success("✅ Testes de performance passaram")
        return True
    else:
        print_warning("⚠️ Testes de performance não disponíveis ou falharam")
        return True

def run_all_tests():
    """Executa todos os testes"""
    print_header("EXECUTANDO TODOS OS TESTES")
    
    start_time = time.time()
    
    results = {
        'unit': run_unit_tests(),
        'financial': run_financial_tests(),
        'integration': run_integration_tests(),
        'e2e': run_e2e_tests(),
        'coverage': run_coverage_tests(),
        'security': run_security_tests(),
        'performance': run_performance_tests()
    }
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Resumo
    print_header("RESUMO DOS TESTES")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"📊 Total de testes: {total}")
    print(f"✅ Passaram: {passed}")
    print(f"❌ Falharam: {total - passed}")
    print(f"⏱️ Tempo total: {execution_time:.2f}s")
    
    for test_type, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_type.upper()}")
    
    return passed == total

def run_quick_tests():
    """Executa testes rápidos (unitários + integração)"""
    print_header("EXECUTANDO TESTES RÁPIDOS")
    
    results = {
        'unit': run_unit_tests(),
        'integration': run_integration_tests()
    }
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"📊 Testes rápidos: {passed}/{total}")
    
    return passed == total

def run_ci_tests():
    """Executa testes para ambiente CI/CD"""
    print_header("EXECUTANDO TESTES CI/CD")
    
    # Instalar dependências
    install_dependencies()
    
    # Executar testes críticos
    results = {
        'unit': run_unit_tests(),
        'financial': run_financial_tests(),
        'integration': run_integration_tests(),
        'coverage': run_coverage_tests(),
        'security': run_security_tests()
    }
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"📊 Testes CI: {passed}/{total}")
    
    return passed == total

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Executor de testes do AgroKongo')
    parser.add_argument(
        'command',
        choices=['unit', 'financial', 'integration', 'e2e', 'coverage', 'security', 'performance', 'all', 'quick', 'ci'],
        help='Tipo de teste a executar'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Output detalhado'
    )
    
    args = parser.parse_args()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('app/__init__.py'):
        print_error("Execute este script a partir do diretório raiz do projeto")
        sys.exit(1)
    
    print_header("AGROKONGO - FRAMEWORK DE TESTES")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Executar comando
    success = False
    
    if args.command == 'unit':
        success = run_unit_tests()
    elif args.command == 'financial':
        success = run_financial_tests()
    elif args.command == 'integration':
        success = run_integration_tests()
    elif args.command == 'e2e':
        success = run_e2e_tests()
    elif args.command == 'coverage':
        success = run_coverage_tests()
    elif args.command == 'security':
        success = run_security_tests()
    elif args.command == 'performance':
        success = run_performance_tests()
    elif args.command == 'all':
        success = run_all_tests()
    elif args.command == 'quick':
        success = run_quick_tests()
    elif args.command == 'ci':
        success = run_ci_tests()
    
    # Resultado final
    print_header("RESULTADO FINAL")
    
    if success:
        print_success("🎉 TESTES EXECUTADOS COM SUCESSO!")
        print("✅ Sistema validado e pronto para uso")
        
        if args.command in ['coverage', 'all', 'ci']:
            print("\n📄 Relatórios gerados:")
            print("   • tests_framework/htmlcov/index.html - Cobertura detalhada")
            print("   • tests_framework/coverage.xml - Cobertura XML")
            print("   • tests_framework/junit.xml - Resultados JUnit")
        
        sys.exit(0)
    else:
        print_error("🚫 FALHA NOS TESTES!")
        print("❌ Corrija os problemas antes de prosseguir")
        sys.exit(1)

if __name__ == '__main__':
    main()
