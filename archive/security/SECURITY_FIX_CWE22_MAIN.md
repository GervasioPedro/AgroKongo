# Correção CWE-22: Path Traversal em main.py

## Vulnerabilidades Identificadas
**Localização**: `app/routes/main.py` - Linhas 244-245 e funções relacionadas  
**Funções Afetadas**: 
- `servir_privado()` (linha ~235)
- `servir_publico()` (linha ~244)
- `serve_perfil()` (linha ~253)
- `servir_documento()` (linha ~261)

**Severidade**: Alta

## Descrição do Problema

As funções de servir arquivos não sanitizavam os parâmetros `subpasta` e `filename` recebidos via URL, permitindo ataques de path traversal. Um atacante poderia usar sequências como `../` para acessar arquivos fora dos diretórios permitidos.

### Exemplos de Ataques Possíveis:
```
/media/publico/../../etc/passwd
/media/privado/../../../config.py
/uploads/perfil/../../private/documentos/documento_secreto.pdf
```

## Correções Aplicadas

### 1. Imports Adicionados
```python
import os
import hashlib
import qrcode
import io
import base64
from decimal import Decimal
```

### 2. Função `servir_privado()` - Arquivos Privados
```python
@main_bp.route('/media/privado/<subpasta>/<filename>')
@login_required
def servir_privado(subpasta, filename):
    # Sanitizar inputs para prevenir path traversal
    safe_subpasta = os.path.basename(subpasta)
    safe_filename = os.path.basename(filename)
    
    base_dir = os.path.abspath(current_app.config['UPLOAD_FOLDER_PRIVATE'])
    diretorio = os.path.join(base_dir, safe_subpasta)
    filepath = os.path.join(diretorio, safe_filename)
    
    # Validar que o caminho está dentro do diretório permitido
    if os.path.commonpath([filepath, base_dir]) != base_dir:
        abort(403)
    
    if not os.path.exists(filepath):
        abort(404)

    return send_from_directory(diretorio, safe_filename, as_attachment=False)
```

### 3. Função `servir_publico()` - Arquivos Públicos (LINHA 244-245)
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

### 4. Função `serve_perfil()` - Fotos de Perfil
```python
@main_bp.route('/uploads/perfil/<filename>')
def serve_perfil(filename):
    # Sanitizar filename para prevenir path traversal
    safe_filename = os.path.basename(filename)
    folder = os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil')
    filepath = os.path.join(folder, safe_filename)
    
    # Validar que o caminho está dentro do diretório permitido
    if os.path.commonpath([filepath, folder]) != folder:
        abort(403)
    
    return send_from_directory(folder, safe_filename)
```

### 5. Função `servir_documento()` - Documentos Privados
```python
@main_bp.route('/servir-documento/<filename>')
@login_required
def servir_documento(filename):
    # Sanitizar filename para prevenir path traversal
    safe_filename = os.path.basename(filename)
    directory = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], 'documentos')
    filepath = os.path.join(directory, safe_filename)
    
    # Validar que o caminho está dentro do diretório permitido
    if os.path.commonpath([filepath, directory]) != directory:
        abort(403)
    
    if not os.path.exists(filepath):
        abort(404)
    
    return send_from_directory(directory, safe_filename)
```

## Técnicas de Proteção Implementadas

### 1. Sanitização com `os.path.basename()`
Remove qualquer componente de diretório do path, mantendo apenas o nome do arquivo:
- `../../etc/passwd` → `passwd`
- `../../../config.py` → `config.py`
- `subpasta/../arquivo.pdf` → `arquivo.pdf`

### 2. Validação com `os.path.commonpath()`
Verifica se o caminho final está dentro do diretório permitido:
```python
if os.path.commonpath([filepath, base_dir]) != base_dir:
    abort(403)
```

Se o caminho tentar sair do diretório base, retorna HTTP 403 Forbidden.

### 3. Verificação de Existência
Antes de servir o arquivo, verifica se ele existe:
```python
if not os.path.exists(filepath):
    abort(404)
```

### 4. Autenticação em Rotas Privadas
Rotas que servem arquivos sensíveis mantêm `@login_required`:
- `/media/privado/` - Requer autenticação
- `/servir-documento/` - Requer autenticação

## Impacto das Correções

### Segurança
✅ Previne acesso a arquivos fora dos diretórios permitidos  
✅ Bloqueia tentativas de path traversal com `../`  
✅ Valida caminhos antes de servir arquivos  
✅ Retorna HTTP 403 para tentativas de acesso não autorizado  
✅ Mantém autenticação em rotas privadas  

### Funcionalidade
✅ Arquivos legítimos continuam acessíveis normalmente  
✅ Mensagens de erro apropriadas (403/404)  
✅ Performance não afetada  
✅ Compatibilidade mantida com código existente  

## Testes Recomendados

### 1. Teste de Path Traversal Básico
```bash
curl http://localhost:5000/media/publico/../../../etc/passwd
# Deve retornar 403 Forbidden
```

### 2. Teste de Path Traversal com Encoding
```bash
curl http://localhost:5000/media/publico/..%2F..%2F..%2Fetc%2Fpasswd
# Deve retornar 403 Forbidden
```

### 3. Teste de Acesso Legítimo
```bash
curl http://localhost:5000/media/publico/safras/produto.jpg
# Deve retornar o arquivo se existir
```

### 4. Teste de Arquivo Inexistente
```bash
curl http://localhost:5000/media/publico/safras/nao_existe.jpg
# Deve retornar 404 Not Found
```

### 5. Teste de Autenticação
```bash
curl http://localhost:5000/media/privado/documentos/doc.pdf
# Deve redirecionar para login se não autenticado
```

## Arquivos Relacionados Já Protegidos

As seguintes funções em `admin.py` já foram corrigidas anteriormente:
- `ver_comprovativo()` - Linha 264-275
- `eliminar_usuario()` - Linha 564-590

## Referências
- CWE-22: https://cwe.mitre.org/data/definitions/22.html
- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- Python os.path: https://docs.python.org/3/library/os.path.html
- Flask send_from_directory: https://flask.palletsprojects.com/en/2.3.x/api/#flask.send_from_directory
