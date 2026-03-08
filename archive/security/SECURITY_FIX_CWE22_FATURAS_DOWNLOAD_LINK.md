# Correção CWE-22: Path Traversal em faturas.py (download_link)

## Vulnerabilidade Identificada
**Ficheiro:** `app/tasks/faturas.py`  
**Linhas:** 131 (dentro da construção do download_link)  
**Severidade:** MÉDIA-ALTA  
**CWE:** CWE-22 (Path Traversal)

## Descrição da Vulnerabilidade

### Link de Download com Filename Não Sanitizado
- **Problema:** `url_for()` usava `filename` em vez de `safe_filename`
- **Risco:** Link de download pode conter sequências `../` se sanitização falhar
- **Impacto:** Utilizador pode receber link malicioso que tenta aceder ficheiros fora do diretório autorizado

### Inconsistência de Segurança
**Antes:**
```python
# Ficheiro salvo com safe_filename (sanitizado)
path = os.path.join(base_dir, safe_filename)

# Mas link usa filename (não sanitizado) ❌
download_link = url_for('main.servir_arquivo', subpasta=subpasta, filename=filename, _external=True)
```

### Cenário de Exploração
1. Atacante manipula `fatura_ref` para `../../etc/passwd`
2. `safe_filename` = `passwd_ABC123.pdf` (sanitizado)
3. `filename` = `../../etc/passwd_ABC123.pdf` (não sanitizado)
4. Ficheiro salvo em: `/data_storage/faturas/passwd_ABC123.pdf` ✅
5. Link gerado: `/servir_arquivo?subpasta=faturas&filename=../../etc/passwd_ABC123.pdf` ❌
6. Rota `servir_arquivo` pode ser explorada se não tiver proteção adequada

## Correção Implementada

### Uso Consistente de safe_filename

**Antes:**
```python
download_link = url_for('main.servir_arquivo', subpasta=subpasta, filename=filename, _external=True)
```

**Depois:**
```python
download_link = url_for('main.servir_arquivo', subpasta=subpasta, filename=safe_filename, _external=True)
```

## Camadas de Proteção

1. ✅ **safe_filename usado no path**: Ficheiro salvo com nome sanitizado
2. ✅ **safe_filename usado no link**: Link gerado com nome sanitizado
3. ✅ **Consistência**: Mesmo nome usado em ambos os locais
4. ✅ **Defense in depth**: Mesmo que rota `servir_arquivo` tenha proteção, não recebe input malicioso

## Impacto da Correção

### Segurança
- ✅ Link de download sempre contém filename sanitizado
- ✅ Previne tentativas de path traversal via URL
- ✅ Consistência entre ficheiro salvo e link gerado

### Integridade
- ✅ Utilizador recebe link para o ficheiro correto
- ✅ Notificação contém URL válido e seguro
- ✅ Auditoria regista path correto

### Defense in Depth
- ✅ Primeira camada: Sanitização em `safe_filename`
- ✅ Segunda camada: Uso de `safe_filename` no path
- ✅ Terceira camada: Uso de `safe_filename` no link
- ✅ Quarta camada: Rota `servir_arquivo` deve ter proteção própria (verificar separadamente)

## Verificação Adicional Necessária

### Rota servir_arquivo
A rota `main.servir_arquivo` deve ter proteções próprias:
```python
@main.route('/servir_arquivo')
def servir_arquivo():
    subpasta = request.args.get('subpasta')
    filename = request.args.get('filename')
    
    # DEVE TER:
    # 1. Sanitização: os.path.basename(filename)
    # 2. Validação: os.path.commonpath()
    # 3. Autorização: verificar ownership
    # 4. Whitelist: subpasta in ['faturas', 'fotos', ...]
```

## Testes Recomendados

1. **Referência Normal:** `AK-123456` → Link: `filename=AK-123456_ABC123.pdf` ✅
2. **Path Traversal:** `../../etc/passwd` → Link: `filename=passwd_ABC123.pdf` ✅
3. **Consistência:** Ficheiro salvo e link usam mesmo nome ✅
4. **Notificação:** Link funciona e baixa ficheiro correto ✅

## Status
✅ **CORRIGIDO** - Link de download usa safe_filename sanitizado, prevenindo path traversal via URL
