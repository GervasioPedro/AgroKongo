# Verificação CWE-22: Path Traversal em main.py (Linhas 242-243)

## Status: ✅ JÁ CORRIGIDO

**Localização**: `app/routes/main.py` - Linhas 242-243  
**Função**: `servir_publico()`  
**Data da Correção**: Anteriormente aplicada  

## Análise da Função Atual

### Código Atual (Linhas ~242-256)
```python
@main_bp.route('/media/publico/<subpasta>/<filename>')
def servir_publico(subpasta, filename):
    # Sanitizar inputs para prevenir path traversal
    safe_subpasta = os.path.basename(subpasta)
    safe_filename = os.path.basename(filename)
    
    base_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER_PUBLIC'])
    diretorio = os.path.join(base_dir, safe_subpasta)
    filepath = os.path.join(diretorio, safe_filename)
    
    # Validar que o caminho está dentro do diretório permitido
    if os.path.commonpath([filepath, base_dir]) != base_dir:
        abort(403)
    
    if not os.path.exists(filepath):
        abort(404)

    return send_from_directory(diretorio, safe_filename)
```

## Proteções Implementadas

### 1. Sanitização de Inputs ✅
```python
safe_subpasta = os.path.basename(subpasta)
safe_filename = os.path.basename(filename)
```
- Remove qualquer componente de diretório dos parâmetros
- Transforma `../../etc/passwd` em `passwd`
- Transforma `../../../config.py` em `config.py`

### 2. Validação de Caminho ✅
```python
if os.path.commonpath([filepath, base_dir]) != base_dir:
    abort(403)
```
- Verifica se o caminho final está dentro do diretório base permitido
- Bloqueia tentativas de sair do diretório com HTTP 403

### 3. Verificação de Existência ✅
```python
if not os.path.exists(filepath):
    abort(404)
```
- Retorna HTTP 404 se o arquivo não existir
- Evita exposição de estrutura de diretórios

### 4. Uso Seguro de send_from_directory ✅
```python
return send_from_directory(diretorio, safe_filename)
```
- Usa variáveis sanitizadas
- Flask adiciona proteções adicionais internamente

## Comparação: Antes vs Depois

### ❌ ANTES (Vulnerável)
```python
@main_bp.route('/media/publico/<subpasta>/<filename>')
def servir_publico(subpasta, filename):
    base_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER_PUBLIC'])
    diretorio = os.path.join(base_dir, subpasta)
    return send_from_directory(diretorio, filename)
```

**Problemas**:
- Parâmetros não sanitizados
- Sem validação de caminho
- Vulnerável a `../` sequences

### ✅ DEPOIS (Protegido)
```python
@main_bp.route('/media/publico/<subpasta>/<filename>')
def servir_publico(subpasta, filename):
    # Sanitizar inputs para prevenir path traversal
    safe_subpasta = os.path.basename(subpasta)
    safe_filename = os.path.basename(filename)
    
    base_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER_PUBLIC'])
    diretorio = os.path.join(base_dir, safe_subpasta)
    filepath = os.path.join(diretorio, safe_filename)
    
    # Validar que o caminho está dentro do diretório permitido
    if os.path.commonpath([filepath, base_dir]) != base_dir:
        abort(403)
    
    if not os.path.exists(filepath):
        abort(404)

    return send_from_directory(diretorio, safe_filename)
```

**Proteções**:
- ✅ Sanitização completa
- ✅ Validação de caminho
- ✅ Verificação de existência
- ✅ Mensagens de erro apropriadas

## Ataques Bloqueados

### 1. Path Traversal Básico
```bash
GET /media/publico/../../../etc/passwd
# safe_subpasta = basename("../../../etc") = "etc"
# safe_filename = basename("passwd") = "passwd"
# Resultado: Tenta acessar /data_storage/public/etc/passwd
# Se não existir: HTTP 404
```

### 2. Path Traversal com Encoding
```bash
GET /media/publico/..%2F..%2F..%2Fetc/passwd
# Flask decodifica automaticamente
# basename() remove componentes de diretório
# Resultado: HTTP 404 ou 403
```

### 3. Acesso a Diretório Pai
```bash
GET /media/publico/../private/documentos/secreto.pdf
# safe_subpasta = basename("../private") = "private"
# Caminho final: /data_storage/public/private/secreto.pdf
# commonpath() valida que está dentro de public/
# Resultado: HTTP 404 (não existe em public/)
```

### 4. Null Byte Injection
```bash
GET /media/publico/safras/arquivo.jpg%00../../etc/passwd
# Python 3 não é vulnerável a null bytes em paths
# basename() remove componentes de diretório
# Resultado: HTTP 404
```

## Outras Funções Protegidas

Todas as funções de servir arquivos no projeto estão protegidas:

| Função | Linha | Status | Proteção |
|--------|-------|--------|----------|
| `servir_privado()` | ~210 | ✅ | Sanitização + Validação + Autorização |
| `servir_publico()` | ~242 | ✅ | Sanitização + Validação |
| `serve_perfil()` | ~258 | ✅ | Sanitização + Validação |
| `servir_documento()` | ~270 | ✅ | Sanitização + Validação + Autorização |

## Testes de Validação

### Teste 1: Arquivo Legítimo
```bash
curl http://localhost:5000/media/publico/safras/produto.jpg
# Deve retornar: 200 OK com o arquivo
```

### Teste 2: Path Traversal Simples
```bash
curl http://localhost:5000/media/publico/../../../etc/passwd
# Deve retornar: 404 Not Found
```

### Teste 3: Path Traversal com Encoding
```bash
curl http://localhost:5000/media/publico/..%2F..%2Fprivate/doc.pdf
# Deve retornar: 404 Not Found
```

### Teste 4: Arquivo Inexistente
```bash
curl http://localhost:5000/media/publico/safras/nao_existe.jpg
# Deve retornar: 404 Not Found
```

### Teste 5: Subpasta Inválida
```bash
curl http://localhost:5000/media/publico/../../config/settings.py
# Deve retornar: 404 Not Found
```

## Documentação Relacionada

Esta correção faz parte de um conjunto de correções CWE-22 aplicadas:

1. **SECURITY_FIX_CWE22_MAIN.md** - Correção inicial de path traversal
2. **SECURITY_FIX_CWE22_ADMIN.md** - Correção em admin.py (se existir)
3. Este documento - Verificação de correção nas linhas 242-243

## Conclusão

✅ **A vulnerabilidade CWE-22 nas linhas 242-243 está COMPLETAMENTE CORRIGIDA**

A função `servir_publico()` implementa todas as melhores práticas de segurança:
- Sanitização de inputs com `os.path.basename()`
- Validação de caminho com `os.path.commonpath()`
- Verificação de existência antes de servir
- Mensagens de erro apropriadas (403/404)
- Uso seguro de `send_from_directory()`

**Nenhuma ação adicional é necessária.**

## Referências
- CWE-22: https://cwe.mitre.org/data/definitions/22.html
- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- Python os.path: https://docs.python.org/3/library/os.path.html
- Flask send_from_directory: https://flask.palletsprojects.com/en/2.3.x/api/#flask.send_from_directory
