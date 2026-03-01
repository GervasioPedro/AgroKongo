#!/usr/bin/env python3
# security_scan.py - Scan de segurança para vulnerabilidades altas
# Validação de segurança antes do release

import subprocess
import sys
import os
import json
from datetime import datetime

# Cores para output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_status(msg):
    print(f"{BLUE}[INFO]{NC} {msg}")

def print_success(msg):
    print(f"{GREEN}[SUCCESS]{NC} {msg}")

def print_warning(msg):
    print(f"{YELLOW}[WARNING]{NC} {msg}")

def print_error(msg):
    print(f"{RED}[ERROR]{NC} {msg}")

def run_command(cmd, check=True):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr

def check_bandit():
    """Verifica vulnerabilidades com Bandit"""
    print_status("Executando scan de segurança com Bandit...")
    
    # Instalar bandit se não existir
    run_command("pip install bandit[toml]", check=False)
    
    # Executar scan
    returncode, stdout, stderr = run_command("bandit -r app/ -f json -o bandit_report.json")
    
    if returncode == 0:
        print_success("✅ Bandit: Nenhuma vulnerabilidade alta encontrada")
        return True, []
    else:
        # Analisar resultados
        try:
            with open('bandit_report.json', 'r') as f:
                report = json.load(f)
            
            high_vulns = []
            for result in report.get('results', []):
                if result.get('issue_severity') == 'HIGH':
                    high_vulns.append({
                        'file': result.get('filename'),
                        'line': result.get('line_number'),
                        'test': result.get('test_name'),
                        'message': result.get('issue_text')
                    })
            
            if high_vulns:
                print_error(f"❌ Bandit: {len(high_vulns)} vulnerabilidades altas encontradas")
                for vuln in high_vulns[:5]:  # Mostrar primeiras 5
                    print_error(f"   • {vuln['file']}:{vuln['line']} - {vuln['test']}")
                    print_error(f"     {vuln['message']}")
                return False, high_vulns
            else:
                print_warning("⚠️ Bandit: Vulnerabilidades médias/baixas encontradas, mas nenhuma alta")
                return True, []
                
        except Exception as e:
            print_error(f"❌ Erro ao analisar relatório Bandit: {e}")
            return False, []

def check_safety():
    """Verifica vulnerabilidades em dependências com Safety"""
    print_status("Verificando dependências com Safety...")
    
    # Instalar safety se não existir
    run_command("pip install safety", check=False)
    
    # Gerar requirements se não existir
    if not os.path.exists('requirements.txt'):
        run_command("pip freeze > requirements.txt", check=False)
    
    # Executar scan
    returncode, stdout, stderr = run_command("safety check --json --output safety_report.json")
    
    if returncode == 0:
        print_success("✅ Safety: Nenhuma vulnerabilidade encontrada nas dependências")
        return True, []
    else:
        # Analisar resultados
        try:
            with open('safety_report.json', 'r') as f:
                report = json.load(f)
            
            vulns = report.get('vulnerabilities', [])
            high_vulns = [v for v in vulns if v.get('severity', 'unknown').lower() in ['high', 'critical']]
            
            if high_vulns:
                print_error(f"❌ Safety: {len(high_vulns)} vulnerabilidades altas/críticas em dependências")
                for vuln in high_vulns[:5]:
                    print_error(f"   • {vuln.get('package', 'unknown')} - {vuln.get('vulnerability_id', 'unknown')}")
                    print_error(f"     {vuln.get('advisory', 'Sem descrição')}")
                return False, high_vulns
            else:
                print_warning("⚠️ Safety: Vulnerabilidades médias/baixas encontradas, mas nenhuma alta/crítica")
                return True, []
                
        except Exception as e:
            print_error(f"❌ Erro ao analisar relatório Safety: {e}")
            return False, []

def check_secrets():
    """Verifica se há secrets expostos no código"""
    print_status("Verificando secrets expostos com TruffleHog...")
    
    # Instalar trufflehog se não existir
    run_command("pip install trufflehog", check=False)
    
    # Executar scan
    returncode, stdout, stderr = run_command("trufflehog filesystem --json --output trufflehog_report.json .")
    
    if returncode == 0:
        print_success("✅ TruffleHog: Nenhum secret encontrado")
        return True, []
    else:
        # Analisar resultados
        try:
            with open('trufflehog_report.json', 'r') as f:
                report = json.load(f)
            
            if report and len(report) > 0:
                print_error(f"❌ TruffleHog: {len(report)} secrets encontrados")
                for secret in report[:3]:  # Mostrar primeiros 3
                    print_error(f"   • {secret.get('source', 'unknown')} - {secret.get('detector', 'unknown')}")
                return False, report
            else:
                print_success("✅ TruffleHog: Nenhum secret encontrado")
                return True, []
                
        except Exception as e:
            print_error(f"❌ Erro ao analisar relatório TruffleHog: {e}")
            return False, []

def check_code_quality():
    """Verifica qualidade do código com flake8"""
    print_status("Verificando qualidade do código com Flake8...")
    
    # Instalar flake8 se não existir
    run_command("pip install flake8", check=False)
    
    # Executar scan
    returncode, stdout, stderr = run_command("flake8 app/ --max-line-length=120 --ignore=E203,W503")
    
    if returncode == 0:
        print_success("✅ Flake8: Código dentro dos padrões de qualidade")
        return True
    else:
        print_warning("⚠️ Flake8: Problemas de qualidade encontrados (não críticos)")
        print(f"   {stdout[:500]}...")
        return True  # Não é crítico para release

def check_dependencies():
    """Verifica dependências desatualizadas"""
    print_status("Verificando dependências desatualizadas...")
    
    # Instalar pip-audit se não existir
    run_command("pip install pip-audit", check=False)
    
    # Executar audit
    returncode, stdout, stderr = run_command("pip-audit --format=json --output=audit_report.json")
    
    if returncode == 0:
        print_success("✅ Pip-audit: Nenhuma vulnerabilidade encontrada")
        return True, []
    else:
        print_warning("⚠️ Pip-audit: Algumas vulnerabilidades encontradas (verificar relatório)")
        return True  # Não bloqueante para release

def generate_security_report(results):
    """Gera relatório de segurança"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'scan_results': results,
        'summary': {
            'total_scans': len(results),
            'passed_scans': sum(1 for r in results if r['passed']),
            'failed_scans': sum(1 for r in results if not r['passed']),
            'high_vulnerabilities': sum(len(r.get('vulnerabilities', [])) for r in results if not r['passed'])
        }
    }
    
    with open('security_summary.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Função principal de scan de segurança"""
    print("🔒 AGROKONGO - SCAN DE SEGURANÇA")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('app/__init__.py'):
        print_error("Execute este script a partir do diretório raiz do projeto")
        sys.exit(1)
    
    results = []
    
    # Executar scans
    scans = [
        ('Bandit - Code Analysis', check_bandit),
        ('Safety - Dependencies', check_safety),
        ('TruffleHog - Secrets', check_secrets),
        ('Flake8 - Code Quality', check_code_quality),
        ('Pip-audit - Dependencies', check_dependencies)
    ]
    
    for scan_name, scan_func in scans:
        print(f"\n🔍 {scan_name}")
        print("-" * 40)
        
        try:
            if scan_name in ['Bandit - Code Analysis', 'Safety - Dependencies', 'TruffleHog - Secrets']:
                passed, vulns = scan_func()
                results.append({
                    'scan': scan_name,
                    'passed': passed,
                    'vulnerabilities': vulns
                })
            else:
                passed = scan_func()
                results.append({
                    'scan': scan_name,
                    'passed': passed,
                    'vulnerabilities': []
                })
        except Exception as e:
            print_error(f"❌ Erro no scan {scan_name}: {e}")
            results.append({
                'scan': scan_name,
                'passed': False,
                'vulnerabilities': [{'error': str(e)}]
            })
    
    # Gerar relatório
    report = generate_security_report(results)
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📊 RESUMO DO SCAN DE SEGURANÇA")
    print("=" * 50)
    
    summary = report['summary']
    print(f"📋 Total de scans: {summary['total_scans']}")
    print(f"✅ Scans passados: {summary['passed_scans']}")
    print(f"❌ Scans falhados: {summary['failed_scans']}")
    print(f"🚨 Vulnerabilidades altas: {summary['high_vulnerabilities']}")
    
    # Verificar critérios de release
    critical_scans = ['Bandit - Code Analysis', 'Safety - Dependencies', 'TruffleHog - Secrets']
    critical_failed = [r for r in results if r['scan'] in critical_scans and not r['passed']]
    
    print(f"\n🎯 CRITÉRIOS DE RELEASE:")
    print(f"   • Vulnerabilidades altas: {'✅ OK' if len(critical_failed) == 0 else '❌ BLOQUEADO'}")
    print(f"   • Scan Bandit: {'✅ OK' if results[0]['passed'] else '❌ FALHOU'}")
    print(f"   • Scan Safety: {'✅ OK' if results[1]['passed'] else '❌ FALHOU'}")
    print(f"   • Scan Secrets: {'✅ OK' if results[2]['passed'] else '❌ FALHOU'}")
    
    # Relatórios gerados
    print(f"\n📄 RELATÓRIOS GERADOS:")
    print(f"   • security_summary.json - Resumo completo")
    print(f"   • bandit_report.json - Detalhes Bandit")
    print(f"   • safety_report.json - Detalhes Safety")
    print(f"   • trufflehog_report.json - Detalhes Secrets")
    
    # Decisão final
    if len(critical_failed) == 0:
        print_success("\n🎉 SEGURANÇA APROVADA PARA RELEASE!")
        print("✅ Zero vulnerabilidades altas encontradas")
        return True
    else:
        print_error("\n🚫 SEGURANÇA BLOQUEIA RELEASE!")
        print(f"❌ {len(critical_failed)} scans críticos falharam")
        print("\n🔧 AÇÕES NECESSÁRIAS:")
        for result in critical_failed:
            print(f"   • Corrigir vulnerabilidades em {result['scan']}")
            for vuln in result['vulnerabilities'][:3]:
                if 'error' not in vuln:
                    print(f"     - {vuln.get('file', 'unknown')}: {vuln.get('message', 'unknown')}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
