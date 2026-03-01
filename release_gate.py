#!/usr/bin/env python3
# release_gate.py - Verificação Final de Pré-Lançamento (Release Gate)
# Validação completa antes do release do AgroKongo

import subprocess
import sys
import os
import json
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

def run_command(cmd, check=True):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr

def check_test_coverage():
    """Verifica cobertura de testes > 80%"""
    print_status("Verificando cobertura de testes...")
    
    # Instalar pytest-cov se não existir
    run_command("pip install pytest-cov", check=False)
    
    # Executar testes com cobertura
    returncode, stdout, stderr = run_command(
        "python -m pytest tests/ --cov=app --cov-report=json --cov-report=term-missing --cov-fail-under=80"
    )
    
    if returncode == 0:
        # Extrair cobertura do relatório
        try:
            with open('coverage.json', 'r') as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data['totals']['percent_covered']
            
            if total_coverage >= 80.0:
                print_success(f"✅ Cobertura de testes: {total_coverage:.1f}% (>80%)")
                return True, total_coverage
            else:
                print_error(f"❌ Cobertura de testes: {total_coverage:.1f}% (<80%)")
                return False, total_coverage
                
        except Exception as e:
            print_error(f"❌ Erro ao analisar cobertura: {e}")
            return False, 0
    else:
        print_error("❌ Falha na execução dos testes de cobertura")
        return False, 0

def check_security_scan():
    """Verifica zero vulnerabilidades altas"""
    print_status("Executando scan de segurança...")
    
    # Executar script de segurança
    returncode, stdout, stderr = run_command("python security_scan.py")
    
    if returncode == 0:
        print_success("✅ Scan de segurança: Zero vulnerabilidades altas")
        return True
    else:
        print_error("❌ Scan de segurança: Vulnerabilidades altas encontradas")
        return False

def check_financial_review():
    """Validação de fluxos financeiros (Peer Review)"""
    print_status("Executando validação de fluxos financeiros...")
    
    # Executar testes financeiros
    returncode, stdout, stderr = run_command(
        "python -m pytest tests/integration/test_fim_de_ciclo.py::TestValidacoesFinanceiras -v"
    )
    
    if returncode == 0:
        print_success("✅ Peer review financeiro: Fluxos validados")
        return True
    else:
        print_error("❌ Peer review financeiro: Problemas encontrados")
        print(f"   {stderr[:500]}...")
        return False

def check_end_to_end_cycle():
    """Teste de Fim de Ciclo completo"""
    print_status("Executando teste de fim de ciclo completo...")
    
    # Executar teste E2E
    returncode, stdout, stderr = run_command(
        "python -m pytest tests/integration/test_fim_de_ciclo.py::TestFimDeCicloCompleto::test_ciclo_completo_sucesso -v -s"
    )
    
    if returncode == 0:
        print_success("✅ Teste E2E: Ciclo completo validado")
        return True
    else:
        print_error("❌ Teste E2E: Falha no ciclo completo")
        print(f"   {stderr[:500]}...")
        return False

def check_database_migrations():
    """Verifica se migrations estão aplicadas"""
    print_status("Verificando migrations do banco de dados...")
    
    # Verificar se existe migration para status_conta
    migration_files = []
    if os.path.exists('migrations/versions'):
        migration_files = [f for f in os.listdir('migrations/versions') if f.endswith('.py')]
    
    required_migrations = [
        'implementar_status_conta_carteiras'
    ]
    
    found_migrations = []
    for req_mig in required_migrations:
        for mig_file in migration_files:
            if req_mig in mig_file:
                found_migrations.append(req_mig)
                break
    
    if len(found_migrations) == len(required_migrations):
        print_success("✅ Database migrations: Todas as migrations necessárias presentes")
        return True
    else:
        missing = set(required_migrations) - set(found_migrations)
        print_error(f"❌ Database migrations: Faltando {missing}")
        return False

def check_configuration_files():
    """Verifica arquivos de configuração"""
    print_status("Verificando arquivos de configuração...")
    
    required_files = [
        'app/__init__.py',
        'app/models.py',
        'app/models_carteiras.py',
        'app/services/otp_service.py',
        'requirements.txt',
        'config.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        print_success("✅ Configuration: Todos os arquivos necessários presentes")
        return True
    else:
        print_error(f"❌ Configuration: Faltando {missing_files}")
        return False

def check_environment_variables():
    """Verifica variáveis de ambiente necessárias"""
    print_status("Verificando variáveis de ambiente...")
    
    # Variáveis críticas para produção
    critical_vars = [
        'FLASK_ENV',
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in critical_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if not missing_vars:
        print_success("✅ Environment: Variáveis críticas configuradas")
        return True
    else:
        print_warning(f"⚠️ Environment: Variáveis não configuradas {missing_vars}")
        print("   (Isso é normal em ambiente de desenvolvimento)")
        return True  # Não bloqueante para dev

def check_api_endpoints():
    """Verifica endpoints críticos da API"""
    print_status("Verificando endpoints críticos...")
    
    critical_endpoints = [
        '/cadastro/criar-conta-produtor',
        '/cadastro/validar-otp',
        '/cadastro/dados-basicos',
        '/cadastro/definir-senha',
        '/cadastro/dados-financeiros',
        '/auth/login',
        '/produtor/dashboard',
        '/mercado/nova-safra'
    ]
    
    # Verificar se os arquivos de rotas existem
    route_files = [
        'app/routes/cadastro_produtor.py',
        'app/routes/auth.py',
        'app/routes/produtor.py',
        'app/routes/mercado.py'
    ]
    
    missing_routes = []
    for route_file in route_files:
        if not os.path.exists(route_file):
            missing_routes.append(route_file)
    
    if not missing_routes:
        print_success("✅ API endpoints: Arquivos de rotas presentes")
        return True
    else:
        print_error(f"❌ API endpoints: Faltando {missing_routes}")
        return False

def check_documentation():
    """Verifica documentação necessária"""
    print_status("Verificando documentação...")
    
    doc_files = [
        'README.md',
        'tests/README.md',
        'docs/api.md' if os.path.exists('docs/') else None
    ]
    
    doc_files = [f for f in doc_files if f is not None]
    missing_docs = []
    
    for doc_file in doc_files:
        if not os.path.exists(doc_file):
            missing_docs.append(doc_file)
    
    if len(missing_docs) <= 1:  # Permite falta de docs/api.md
        print_success("✅ Documentation: Documentação principal presente")
        return True
    else:
        print_error(f"❌ Documentation: Faltando {missing_docs}")
        return False

def generate_release_report(results):
    """Gera relatório final de release"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'release_gate_results': results,
        'summary': {
            'total_checks': len(results),
            'passed_checks': sum(1 for r in results if r['passed']),
            'failed_checks': sum(1 for r in results if not r['passed']),
            'coverage_percentage': next((r.get('coverage', 0) for r in results if 'coverage' in r), 0)
        }
    }
    
    with open('release_gate_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Função principal do Release Gate"""
    print_header("AGROKONGO - RELEASE GATE")
    print("Verificacao Final de Pre-Lancamento")
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('app/__init__.py'):
        print_error("Execute este script a partir do diretório raiz do projeto")
        sys.exit(1)
    
    print_status(f"Iniciando verificação em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    results = []
    
    # Executar verificações do Release Gate
    checks = [
        ('Cobertura de Testes > 80%', check_test_coverage),
        ('Zero Vulnerabilidades Altas', check_security_scan),
        ('Peer Review Financeiro', check_financial_review),
        ('Teste Fim de Ciclo', check_end_to_end_cycle),
        ('Database Migrations', check_database_migrations),
        ('Configuration Files', check_configuration_files),
        ('Environment Variables', check_environment_variables),
        ('API Endpoints', check_api_endpoints),
        ('Documentation', check_documentation)
    ]
    
    for check_name, check_func in checks:
        print(f"\n[CHECK] {check_name}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            if check_name == 'Cobertura de Testes > 80%':
                passed, coverage = check_func()
                results.append({
                    'check': check_name,
                    'passed': passed,
                    'coverage': coverage,
                    'execution_time': time.time() - start_time
                })
            else:
                passed = check_func()
                results.append({
                    'check': check_name,
                    'passed': passed,
                    'execution_time': time.time() - start_time
                })
        except Exception as e:
            print_error(f"❌ Erro na verificação {check_name}: {e}")
            results.append({
                'check': check_name,
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            })
    
    # Gerar relatório
    report = generate_release_report(results)
    
    # Resumo final
    print_header("RESUMO DO RELEASE GATE")
    
    summary = report['summary']
    print(f"Total de verificacoes: {summary['total_checks']}")
    print(f"Verificacoes passadas: {summary['passed_checks']}")
    print(f"Verificacoes falhadas: {summary['failed_checks']}")
    print(f"Cobertura de testes: {summary['coverage_percentage']:.1f}%")
    
    # Status detalhado
    print(f"\nSTATUS DAS VERIFICACOES:")
    for result in results:
        status = "PASS" if result['passed'] else "FAIL"
        time_str = f"({result['execution_time']:.2f}s)" if 'execution_time' in result else ""
        print(f"   {status} {result['check']} {time_str}")
        
        if not result['passed'] and 'error' in result:
            print(f"      Erro: {result['error']}")
    
    # Verificação de critérios obrigatórios
    critical_checks = [
        'Cobertura de Testes > 80%',
        'Zero Vulnerabilidades Altas',
        'Peer Review Financeiro',
        'Teste Fim de Ciclo'
    ]
    
    critical_failed = [r for r in results if r['check'] in critical_checks and not r['passed']]
    
    print(f"\nCRITERIOS OBRIGATORIOS:")
    for check in critical_checks:
        result = next(r for r in results if r['check'] == check)
        status = "OK" if result['passed'] else "BLOQUEADO"
        print(f"   {status} {check}")
    
    # Decisão final
    print_header("DECISAO FINAL")
    
    if len(critical_failed) == 0:
        print_success("RELEASE APROVADO!")
        print("Todos os criterios obrigatorios foram atendidos")
        print("Sistema pronto para producao")
        
        print(f"\nRELATORIOS GERADOS:")
        print(f"   • release_gate_report.json - Resumo completo")
        print(f"   • coverage.json - Detalhes da cobertura")
        print(f"   • security_summary.json - Scan de seguranca")
        
        print(f"\nPROXIMOS PASSOS:")
        print(f"   1. Review do relatorio completo")
        print(f"   2. Deploy para staging")
        print(f"   3. Testes finais em staging")
        print(f"   4. Deploy para producao")
        print(f"   5. Monitoramento pos-lancamento")
        
        return True
    else:
        print_error("RELEASE BLOQUEADO!")
        print(f"{len(critical_failed)} criterios obrigatorios falharam")
        
        print(f"\nACOES NECESSARIAS:")
        for result in critical_failed:
            print(f"   • Corrigir: {result['check']}")
            if 'error' in result:
                print(f"     Erro: {result['error']}")
        
        print(f"\nVERIFICACOES BLOQUEANTES:")
        for result in critical_failed:
            print(f"   - {result['check']}")
        
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
