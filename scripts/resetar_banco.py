#!/usr/bin/env python3
"""
Script para resetar e recriar o banco com as credenciais corretas

Uso:
    python scripts/resetar_banco.py
"""
import os
import sys
import subprocess

print("=" * 70)
print("🔄 RESETAR BANCO DE DADOS")
print("=" * 70)

print("\n⚠️  ATENÇÃO: Este script vai PARAR e RECRIAR o banco de dados!")
print("💾 Todos os dados serão PERDIDOS (exceto se tiver backup)")
print("\n💡 Use este script apenas em ambiente de desenvolvimento!")

resposta = input("\n❓ Tem certeza que deseja continuar? (yes/no): ")

if resposta.lower() != 'yes':
    print("\n❌ Operação cancelada.")
    sys.exit(0)

print("\n" + "=" * 70)
print("📋 VERIFICANDO DOCKER...")
print("=" * 70)

# Verificar se docker-compose está rodando
try:
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    if 'agrokongo_db' not in result.stdout:
        print("\n⚠️  Docker container não está rodando!")
        print("💡 Iniciando docker-compose...")
        subprocess.run(['docker-compose', 'up', '-d', 'db'])
    else:
        print("✅ Docker container está rodando!")
except Exception as e:
    print(f"❌ Erro ao verificar Docker: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("🛑 PARANDO CONTAINER...")
print("=" * 70)

# Parar container
try:
    subprocess.run(['docker-compose', 'stop', 'db'])
    print("✅ Container parado!")
except Exception as e:
    print(f"❌ Erro ao parar container: {e}")

print("\n" + "=" * 70)
print("🗑️  REMOVENDO VOLUME (dados antigos)...")
print("=" * 70)

# Remover volume
try:
    subprocess.run(['docker-compose', 'down', '-v'])
    print("✅ Volume removido!")
except Exception as e:
    print(f"❌ Erro ao remover volume: {e}")

print("\n" + "=" * 70)
print("🚀 SUBINDO NOVO BANCO...")
print("=" * 70)

# Subir novo banco
try:
    subprocess.run(['docker-compose', 'up', '-d', 'db'])
    print("✅ Novo banco criado!")
except Exception as e:
    print(f"❌ Erro ao subir banco: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("⏳ AGUARDANDO BANCO INICIAR...")
print("=" * 70)

import time
time.sleep(5)

print("\n✅ Banco reiniciado com sucesso!")
print("\n📊 CREDENCIAIS:")
print("   Usuário: agrokongo_user")
print("   Senha:   agrokongo_pass")
print("   Database: agrokongo_dev")
print("   Host:    localhost:5432")

print("\n" + "=" * 70)
print("🧪 APLICANDO MIGRATIONS...")
print("=" * 70)

# Aplicar migrations
try:
    print("📦 Executando flask db upgrade...")
    result = subprocess.run(['flask', 'db', 'upgrade'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Migrations aplicadas com sucesso!")
    else:
        print(f"⚠️  Aviso: {result.stderr}")
except Exception as e:
    print(f"❌ Erro ao aplicar migrations: {e}")
    print("\n💡 Você pode aplicar manualmente depois:")
    print("   flask db upgrade")

print("\n" + "=" * 70)
print("✅ PROCESSO CONCLUÍDO!")
print("=" * 70)

print("\n🎯 PRÓXIMOS PASSOS:")
print("   1. Valide os índices: python scripts/validar_indices_simples.py")
print("   2. Aplique a migration: flask db upgrade add_strategic_indexes_2026")
print("   3. Teste performance: python scripts/test_query_performance.py")
