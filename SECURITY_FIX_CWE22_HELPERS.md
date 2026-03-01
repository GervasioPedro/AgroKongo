# Correção CWE-22: Path Traversal em helpers.py

## Vulnerabilidade Identificada
**Ficheiro:** `app/utils/helpers.py`  
**Linhas:** 43-44  
**Severidade:** CRÍTICA  
**CWE:** CWE-22 (Path Traversal)

## Descrição da Vulnerabilidade

### Construção de Path com Subpasta Não Sanitizada
- **Problema:** Parâmetro `subpasta` usado diretamente em `os.path.join()` sem sanitização
- **Risco:** Atacante pode usar `../` para escapar do diretório base
- **Impacto:** Escrita de ficheiros em locais arbitrários do sistema

### Código Vulnerável

**Antes:**
```python
diretorio_final = os.path.join(base_folder, subpasta)
os.makedirs(diretorio_final, exist_ok=True)
```

### Cenário de Exploração

#### Ataque 1: Sobrescrita de Ficheiros Críticos
```python
# Atacante chama função com:
salvar_ficheiro(ficheiro, subpasta='../../etc/passwd')

# Path resultante:
diretorio_final = "/var/app/storage/public/../../etc/passwd"
# → "/etc/passwd"

# Ficheiro é escrito em /etc/passwd ❌
```

#### Ataque 2: Exposição de Dados Privados
```python
# Atacante chama função com:
salvar_ficheiro(ficheiro, subpasta='../../../var/www/html/uploads')

# Ficheiro privado é salvo em diretório público ❌
```

#### Ataque 3: Bypass de Isolamento Privado/Público
```python
# Atacante chama função com privado=True:
salvar_ficheiro(ficheiro, subpasta='../../public/safras', privado=True)

# Ficheiro "privado" é salvo em pasta pública ❌
```

## Correção Implementada

### Três Camadas de Proteção

**Depois:**
```python
# Camada 1: Sanitização com basename
safe_subpasta = os.path.basename(subpasta)

# Camada 2: Validação whitelist
subpastas_permitidas = {'safras', 'fotos', 'taloes', 'faturas', 'relatorios', 'perfis'}
if safe_subpasta not in subpastas_permitidas:
    current_app.logger.warning(f"Subpasta inválida: {subpasta}")
    return None

# Camada 3: Construção do path
diretorio_final = os.path.join(base_folder, safe_subpasta)

# Camada 4: Validação final com commonpath
if not os.path.commonpath([base_folder, diretorio_final]) == os.path.commonpath([base_folder]):
    current_app.logger.error(f"Path traversal detectado: {subpasta}")
    return None

os.makedirs(diretorio_final, exist_ok=True)
```

## Camadas de Proteção (Total: 4)

1. ✅ **os.path.basename(subpasta)**: Remove componentes de diretório
2. ✅ **Whitelist**: Apenas subpastas permitidas são aceites
3. ✅ **os.path.commonpath()**: Valida que path está dentro do base_folder
4. ✅ **Logging + Return None**: Regista tentativas e falha graciosamente

## Whitelist de Subpastas

### Subpastas Permitidas
```python
subpastas_permitidas = {
    'safras',      # Fotos de produtos agrícolas
    'fotos',       # Fotos de perfil de utilizadores
    'taloes',      # Talões bancários (privado)
    'faturas',     # Faturas PDF (privado)
    'relatorios',  # Relatórios Excel (privado)
    'perfis'       # Fotos de perfil
}
```

### Por que Whitelist?
- **Segurança**: Apenas valores conhecidos são aceites
- **Manutenibilidade**: Lista clara de subpastas válidas
- **Auditoria**: Fácil verificar quais subpastas existem
- **Fail-safe**: Qualquer valor não listado é rejeitado

## Exemplos de Proteção

### Tentativa 1: Path Traversal Simples
```python
subpasta = "../../etc/passwd"
safe_subpasta = os.path.basename("../../etc/passwd")  # → "passwd"

# Whitelist bloqueia:
if "passwd" not in subpastas_permitidas:  # True
    return None  # ✅ Bloqueado
```

### Tentativa 2: Path Traversal Complexo
```python
subpasta = "safras/../../../etc/passwd"
safe_subpasta = os.path.basename("safras/../../../etc/passwd")  # → "passwd"

# Whitelist bloqueia:
if "passwd" not in subpastas_permitidas:  # True
    return None  # ✅ Bloqueado
```

### Tentativa 3: Subpasta Inválida
```python
subpasta = "malicious"
safe_subpasta = os.path.basename("malicious")  # → "malicious"

# Whitelist bloqueia:
if "malicious" not in subpastas_permitidas:  # True
    return None  # ✅ Bloqueado
```

### Tentativa 4: Bypass de Commonpath (Impossível)
```python
# Mesmo que basename e whitelist sejam contornados (impossível):
subpasta = "safras"
safe_subpasta = "safras"  # ✅ Passa whitelist
diretorio_final = "/var/app/storage/public/safras"

# Commonpath valida:
os.path.commonpath([base_folder, diretorio_final]) == os.path.commonpath([base_folder])
# → True ✅ Permitido

# Se alguém manipular diretorio_final:
diretorio_final = "/etc/passwd"
os.path.commonpath([base_folder, diretorio_final]) == os.path.commonpath([base_folder])
# → False ✅ Bloqueado
```

## Impacto da Correção

### Segurança
- ✅ Previne escrita de ficheiros fora do diretório autorizado
- ✅ Protege contra sobrescrita de ficheiros críticos do sistema
- ✅ Mantém isolamento entre ficheiros privados e públicos
- ✅ Múltiplas camadas de defesa (defense in depth)

### Integridade
- ✅ Todos os uploads salvos em subpastas autorizadas
- ✅ Estrutura de diretórios previsível e segura
- ✅ Isolamento privado/público mantido

### Auditoria
- ✅ Tentativas de path traversal são logadas
- ✅ Subpastas inválidas são logadas
- ✅ Função retorna None em caso de erro (fail-safe)

### Usabilidade
- ✅ Uploads legítimos continuam funcionando
- ✅ Nomes de ficheiro únicos (UUID) mantidos
- ✅ Conversão WebP e otimização mantidas

## Contexto de Risco

### Por que Esta Vulnerabilidade é Crítica?
1. **Função Central**: Usada em múltiplas rotas (safras, perfis, talões)
2. **Ficheiros Sensíveis**: Talões bancários, faturas, dados pessoais
3. **Isolamento Crítico**: Privado vs Público deve ser mantido
4. **Sobrescrita de Sistema**: Pode comprometer servidor inteiro

### Impacto Potencial Sem Correção
- ❌ Sobrescrita de `/etc/passwd` → Comprometimento total do servidor
- ❌ Exposição de talões bancários → Violação GDPR/LGPD
- ❌ Bypass de isolamento → Ficheiros privados acessíveis publicamente
- ❌ Negação de serviço → Enchimento de disco em locais críticos

## Testes Recomendados

1. **Subpasta Normal:** `'safras'` → `/storage/public/safras/` ✅
2. **Path Traversal Simples:** `'../../etc/passwd'` → Bloqueado ✅
3. **Path Traversal Complexo:** `'safras/../../../etc'` → Bloqueado ✅
4. **Subpasta Inválida:** `'malicious'` → Bloqueado ✅
5. **Isolamento Privado:** `privado=True, subpasta='taloes'` → `/storage/private/taloes/` ✅
6. **Isolamento Público:** `privado=False, subpasta='safras'` → `/storage/public/safras/` ✅

## Comparação com Outras Funções

### Consistência no Projeto
- ✅ **faturas.py**: Usa basename + commonpath
- ✅ **relatorios.py**: Usa basename + whitelist + commonpath
- ✅ **helpers.py**: Agora usa basename + whitelist + commonpath

### Padrão de Segurança Unificado
```python
# Padrão aplicado em todo o projeto:
safe_param = os.path.basename(param)
if safe_param not in whitelist:
    return None
path = os.path.join(base_dir, safe_param)
if not os.path.commonpath([base_dir, path]) == os.path.commonpath([base_dir]):
    return None
```

## Chamadas da Função no Projeto

### Locais que Usam salvar_ficheiro()
1. **Safras**: Upload de fotos de produtos
2. **Perfis**: Upload de fotos de perfil
3. **Talões**: Upload de comprovantes bancários (privado)
4. **Admin**: Upload de documentos diversos

### Todas Protegidas Agora
- ✅ Todas as chamadas passam por sanitização
- ✅ Whitelist garante apenas subpastas válidas
- ✅ Commonpath valida path final

## Status
✅ **CORRIGIDO** - Path traversal prevenido com sanitização, whitelist e validação em 4 camadas
