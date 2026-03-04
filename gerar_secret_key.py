#!/usr/bin/env python3
"""
Gera SECRET_KEY segura para produção
"""
import secrets

print("=" * 60)
print("🔐 SECRET_KEY para Produção")
print("=" * 60)
print()
print("Copie esta chave e adicione no Render como variável de ambiente:")
print()
print(f"SECRET_KEY={secrets.token_hex(32)}")
print()
print("=" * 60)
print("⚠️  NUNCA compartilhe esta chave!")
print("=" * 60)
