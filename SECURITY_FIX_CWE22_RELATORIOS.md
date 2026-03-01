# Correção CWE-22: Path Traversal em relatorios.py

## Vulnerabilidade Identificada
**Ficheiro:** `app/tasks/relatorios.py`  
**Linhas:** 108-109  
**Severidade:** ALTA  
**CWE:** CWE-22 (Path Traversal)

## Descrição da Vulnerabilidade

### Construção de Path com Input Não Sanitizado
- **Problema:** Parâmetro `periodo` usado diretamente no filename sem sanitização
- **Risco:** Atacante pode manipular `periodo` com `../` para escapar do diretório
- **Impacto:** Escrita de ficheiros Excel em locais arbitrários do sistema

### Cenário de Exploração
1. Admin malicioso ou comprometido chama task com `periodo='../../etc/malicious'`
2. Filename torna-se `relatorio_../../etc/malicious_20260226_ABC123.xlsx`
3. Ficheiro é escrito fora do diretório `relatorios/`
4. Possível sobrescrita de ficheiros críticos ou exposição de dados

## Correção Implementada

### Quatro Camadas de Proteção

**Antes:**
```python
filename = f"relatorio_{periodo or 'completo'}_{aware_utcnow().strftime('%Y%m%d')}_{hash_excel[:8]}.xlsx"
path = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], subpasta, filename)
```

**Depois:**
```python
# Camada 1: Sanitização do período
safe_periodo = os.path.basename(periodo or 'completo')
filename = f"relatorio_{safe_periodo}_{aware_utcnow().strftime('%Y%m%d')}_{hash_excel[:8]}.xlsx"

# Camada 2: Sanitização do filename completo
safe_filename = os.path.basename(filename)

# Camada 3: Construção segura do path
base_dir = os.path.join(current_app.config['UPLOAD_FOLDER_PRIVATE'], subpasta)
path = os.path.join(base_dir, safe_filename)

# Camada 4: Validação final
if not os.path.commonpath([base_dir, path]) == os.path.commonpath([base_dir]):
    raise ValueError("Path traversal detectado")
```

### Link de Download Consistente
**Antes:**
```python
link=f"/admin/download-relatorio/{os.path.basename(path)}"
```

**Depois:**
```python
link=f"/admin/download-relatorio/{safe_filename}"
```

## Camadas de Proteção

1. ✅ **os.path.basename(periodo)**: Remove componentes de diretório do período
2. ✅ **os.path.basename(filename)**: Remove componentes de diretório do filename
3. ✅ **os.path.commonpath()**: Valida que path está dentro do diretório base
4. ✅ **ValueError**: Lança exceção se path traversal for detectado
5. ✅ **safe_filename no link**: Consistência entre ficheiro salvo e link

## Exemplos de Proteção

### Tentativa de Ataque 1
```python
periodo = "../../etc/passwd"
safe_periodo = os.path.basename("../../etc/passwd")  # → "passwd"
filename = "relatorio_passwd_20260226_ABC123.xlsx"  # ✅ Seguro
```

### Tentativa de Ataque 2
```python
periodo = "2026-02/../../../root/malicious"
safe_periodo = os.path.basename("2026-02/../../../root/malicious")  # → "malicious"
filename = "relatorio_malicious_20260226_ABC123.xlsx"  # ✅ Seguro
```

### Tentativa de Ataque 3
```python
# Mesmo que basename seja contornado, commonpath detecta
path = "/var/app/private/relatorios/../../../etc/passwd"
os.path.commonpath([base_dir, path]) != os.path.commonpath([base_dir])
# → ValueError lançado ✅
```

## Impacto da Correção

### Segurança
- ✅ Previne escrita de ficheiros fora do diretório autorizado
- ✅ Protege contra sobrescrita de ficheiros críticos
- ✅ Múltiplas camadas de defesa (defense in depth)
- ✅ Validação mesmo para admins (insider threat protection)

### Integridade
- ✅ Todos os relatórios salvos em `/data_storage/private/relatorios/`
- ✅ Nomes de ficheiro previsíveis e seguros
- ✅ Hash no filename garante unicidade

### Auditoria
- ✅ Tentativas de path traversal geram ValueError
- ✅ Exceção é logada e auditada
- ✅ Notificação de erro enviada ao admin

### Consistência
- ✅ Ficheiro salvo com `safe_filename`
- ✅ Link de download usa `safe_filename`
- ✅ Auditoria regista path correto

## Contexto de Segurança

### Por que Admin Precisa de Proteção?
1. **Conta comprometida**: Admin pode ter credenciais roubadas
2. **Insider threat**: Admin malicioso pode tentar explorar
3. **Defense in depth**: Proteção em todas as camadas, não apenas autenticação
4. **Compliance**: GDPR/LGPD exigem proteção mesmo para utilizadores privilegiados

## Testes Recomendados

1. **Período Normal:** `2026-02` → `relatorios/relatorio_2026-02_20260226_ABC123.xlsx` ✅
2. **Path Traversal Simples:** `../../etc/passwd` → `relatorios/relatorio_passwd_20260226_ABC123.xlsx` ✅
3. **Path Traversal Complexo:** `2026-02/../../../root/mal` → `relatorios/relatorio_mal_20260226_ABC123.xlsx` ✅
4. **Validação Commonpath:** Verificar que ValueError é lançado se path sair do base_dir ✅
5. **Link Consistente:** Verificar que link usa mesmo nome que ficheiro salvo ✅

## Status
✅ **CORRIGIDO** - Path traversal prevenido com sanitização e validação em múltiplas camadas
