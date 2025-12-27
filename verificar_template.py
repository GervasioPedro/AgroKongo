"""
Script de diagnóstico para verificar estrutura de templates
"""
import os
from pathlib import Path

# Caminho base do projeto
base_path = Path(__file__).parent
templates_path = base_path / "templates"

print(f"📁 Caminho base: {base_path}")
print(f"📁 Pasta templates: {templates_path}")
print(f"📁 Templates existe: {templates_path.exists()}")

if templates_path.exists():
    print("\n📋 Conteúdo da pasta templates:")
    for item in templates_path.rglob("*"):
        relative_path = item.relative_to(templates_path)
        print(f"  - {relative_path}")

    # Verificar se publico/index.html existe
    publico_index = templates_path / "publico" / "index.html"
    print(f"\n🔍 Template publico/index.html existe: {publico_index.exists()}")

    if not publico_index.exists():
        print("❌ Template publico/index.html NÃO EXISTE!")
        print("💡 Crie a pasta templates/publico/ e o arquivo index.html")
    else:
        print("✅ Template publico/index.html encontrado!")
else:
    print("❌ Pasta templates NÃO EXISTE!")
    print("💡 Crie a pasta templates/ e subpastas necessárias")