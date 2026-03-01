# Correção CWE-22 - Path Traversal em auth.py linhas 196-197

## Vulnerabilidade Identificada
**Localização**: `app/routes/auth.py` linha 196-197  
**Função**: `editar_perfil()`  
**CWE**: CWE-22 (Path Traversal)  
**Severidade**: High

## Problema
A função `editar_perfil()` removia arquivos antigos de foto de perfil sem sanitização adequada do caminho, permitindo path traversal:

```python
# ANTES - Vulnerável
if current_user.foto_perfil and current_user.foto_perfil != 'default_user.jpg':
    caminho_antigo = os.path.join(pasta_perfis, current_user.foto_perfil)
    if os.path.exists(caminho_antigo):
        os.remove(caminho_antigo)  # ← Vulnerável a path traversal
```

**Riscos**:
- Atacante poderia manipular `foto_perfil` no banco de dados
- Uso de `../` para navegar para diretórios superiores
- Remoção de arquivos críticos do sistema
- Exemplo: `foto_perfil = "../../config/database.yml"` seria removido
- Possível negação de serviço (DoS) removendo arquivos essenciais

## Correção Implementada
Adicionada sanitização com `os.path.basename()` e validação com `os.path.commonpath()`:

```python
# Apagar a antiga com proteção contra path traversal
if current_user.foto_perfil and current_user.foto_perfil != 'default_user.jpg':
    # Sanitizar filename para prevenir path traversal
    safe_filename = os.path.basename(current_user.foto_perfil)
    caminho_antigo = os.path.join(pasta_perfis, safe_filename)
    
    # Validar que o caminho está dentro do diretório permitido
    caminho_antigo_abs = os.path.abspath(caminho_antigo)
    pasta_perfis_abs = os.path.abspath(pasta_perfis)
    
    if os.path.commonpath([caminho_antigo_abs, pasta_perfis_abs]) == pasta_perfis_abs:
        if os.path.exists(caminho_antigo_abs):
            os.remove(caminho_antigo_abs)

current_user.foto_perfil = nome_arquivo
```

## Proteções Adicionadas (3 Camadas)

### Camada 1: Sanitização
```python
safe_filename = os.path.basename(current_user.foto_perfil)
```
- Remove qualquer componente de diretório
- `../../etc/passwd` → `passwd`
- `../config/app.py` → `app.py`

### Camada 2: Canonicalização
```python
caminho_antigo_abs = os.path.abspath(caminho_antigo)
pasta_perfis_abs = os.path.abspath(pasta_perfis)
```
- Resolve caminhos absolutos
- Elimina `.` e `..` do caminho
- Normaliza separadores de diretório

### Camada 3: Validação de Diretório
```python
if os.path.commonpath([caminho_antigo_abs, pasta_perfis_abs]) == pasta_perfis_abs:
```
- Verifica que o arquivo está dentro do diretório permitido
- Bloqueia qualquer tentativa de sair do diretório `perfil/`
- Fail-safe: se validação falhar, arquivo não é removido

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Atacante modifica DB: `foto_perfil = "../../config/database.yml"`
- ❌ Usuário atualiza foto de perfil
- ❌ Sistema tenta remover arquivo antigo
- ❌ Path traversal: `data_storage/public/perfil/../../config/database.yml`
- ❌ Arquivo crítico `config/database.yml` é removido
- ❌ Sistema fica inoperante (DoS)

### Depois (Protegido)
- ✅ Atacante modifica DB: `foto_perfil = "../../config/database.yml"`
- ✅ Usuário atualiza foto de perfil
- ✅ Sistema sanitiza: `os.path.basename()` → `database.yml`
- ✅ Caminho construído: `data_storage/public/perfil/database.yml`
- ✅ Validação: caminho está dentro de `perfil/`
- ✅ Arquivo `database.yml` não existe em `perfil/`, nada é removido
- ✅ Sistema protegido contra path traversal

## Exemplos de Payloads Bloqueados

| Payload Malicioso | Após Sanitização | Resultado |
|-------------------|------------------|-----------|
| `../../etc/passwd` | `passwd` | ✅ Bloqueado |
| `../config/app.py` | `app.py` | ✅ Bloqueado |
| `../../run.py` | `run.py` | ✅ Bloqueado |
| `../../../Windows/System32/config/sam` | `sam` | ✅ Bloqueado |
| `foto123.jpg` | `foto123.jpg` | ✅ Permitido (legítimo) |

## Impacto de Segurança
- **Antes**: Atacante poderia remover arquivos críticos do sistema
- **Depois**: Apenas arquivos dentro de `data_storage/public/perfil/` podem ser removidos
- **Proteção adicional**: 3 camadas de defesa (sanitização, canonicalização, validação)

## Defense in Depth
1. **Sanitização**: Remove componentes de diretório
2. **Canonicalização**: Resolve caminhos absolutos
3. **Validação**: Verifica diretório permitido
4. **Fail-safe**: Se validação falhar, arquivo não é removido

## Arquivos Protegidos
- Configurações da aplicação
- Código-fonte Python
- Banco de dados
- Arquivos de sistema
- Documentos privados de outros usuários
- Qualquer arquivo fora de `data_storage/public/perfil/`

## Status
✅ **CORRIGIDO** - Proteção contra path traversal implementada com 3 camadas
🔒 **HIGH** - Esta correção previne remoção não autorizada de arquivos do sistema
🛡️ **DEFENSE IN DEPTH** - Múltiplas camadas de proteção garantem segurança
