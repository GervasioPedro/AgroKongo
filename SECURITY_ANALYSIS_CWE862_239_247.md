# Verificação CWE-862: Missing Authorization em main.py (Linhas 239, 247)

## Status: ✅ ADEQUADAMENTE IMPLEMENTADO

**Localização**: `app/routes/main.py` - Linhas 239, 247  
**Funções**: `servir_privado()` e `servir_publico()`  
**Data da Verificação**: Atual  

## Análise das Funções

### Linha 239: `servir_privado()` - ✅ AUTORIZAÇÃO COMPLETA

```python
@main_bp.route('/media/privado/<subpasta>/<filename>')
@login_required
def servir_privado(subpasta, filename):
    # ... sanitização e validação ...
    
    # Verificação de autorização: apenas admin ou dono do arquivo
    if current_user.tipo != 'admin':
        # Verifica se o arquivo pertence ao usuário
        if safe_subpasta == 'comprovativos':
            # Comprovativos: apenas comprador, vendedor ou admin da transação
            transacao = Transacao.query.filter_by(comprovativo_path=safe_filename).first()
            if not transacao or current_user.id not in [transacao.comprador_id, transacao.vendedor_id]:
                abort(403)
        elif safe_subpasta in ['documentos', 'identidade']:
            # Documentos pessoais: apenas o próprio usuário
            if safe_filename != current_user.documento_pdf:
                abort(403)
        else:
            abort(403)

    return send_from_directory(diretorio, safe_filename, as_attachment=False)
```

**Status**: ✅ **AUTORIZAÇÃO COMPLETA IMPLEMENTADA**

**Proteções**:
- ✅ Requer autenticação (`@login_required`)
- ✅ Verifica tipo de usuário (admin tem acesso total)
- ✅ Valida propriedade de documentos pessoais
- ✅ Valida participação em transações para comprovativos
- ✅ Nega acesso por padrão a subpastas desconhecidas

### Linha 247: `servir_publico()` - ⚠️ SEM AUTORIZAÇÃO (POR DESIGN)

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

**Status**: ⚠️ **SEM AUTORIZAÇÃO - INTENCIONAL PARA ARQUIVOS PÚBLICOS**

**Análise**:
- ❌ Sem `@login_required` - Acesso público
- ❌ Sem verificação de propriedade - Arquivos são públicos
- ✅ Sanitização contra path traversal
- ✅ Validação de caminho

## Avaliação de Risco

### `servir_publico()` - Arquivos Públicos

**Pergunta**: Esta função DEVE ter autorização?

**Análise**:
1. **Nome da rota**: `/media/publico/` indica intenção de acesso público
2. **Diretório**: `UPLOAD_FOLDER_PUBLIC` sugere conteúdo público
3. **Casos de uso típicos**:
   - Fotos de produtos (safras)
   - Imagens de perfil público
   - Recursos estáticos acessíveis a todos

**Conclusão**: ✅ **APROPRIADO - Arquivos públicos não devem ter autorização**

### Recomendação: Adicionar Validação de Subpastas Permitidas

Embora a função seja para arquivos públicos, é recomendável adicionar uma whitelist de subpastas permitidas para evitar exposição acidental de dados sensíveis.

## Correção Recomendada (Opcional)

Se desejar adicionar uma camada extra de segurança, pode-se implementar uma whitelist de subpastas:

```python
@main_bp.route('/media/publico/<subpasta>/<filename>')
def servir_publico(subpasta, filename):
    # Whitelist de subpastas públicas permitidas
    SUBPASTAS_PUBLICAS_PERMITIDAS = ['safras', 'perfil', 'produtos', 'banners']
    
    # Sanitizar inputs para prevenir path traversal
    safe_subpasta = os.path.basename(subpasta)
    safe_filename = os.path.basename(filename)
    
    # Validar subpasta contra whitelist
    if safe_subpasta not in SUBPASTAS_PUBLICAS_PERMITIDAS:
        abort(404)  # Retorna 404 em vez de 403 para não revelar estrutura
    
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

**Benefícios da Whitelist**:
- ✅ Previne acesso a subpastas não intencionais
- ✅ Reduz superfície de ataque
- ✅ Documenta explicitamente quais diretórios são públicos
- ✅ Facilita auditoria de segurança

## Matriz de Autorização Atual

| Função | Linha | Autenticação | Autorização | Público | Status |
|--------|-------|--------------|-------------|---------|--------|
| `servir_privado()` | 239 | ✅ Obrigatória | ✅ Granular | ❌ | ✅ Completo |
| `servir_publico()` | 247 | ❌ Não requer | ❌ Não requer | ✅ | ⚠️ Por design |
| `serve_perfil()` | 258 | ❌ Não requer | ❌ Não requer | ✅ | ⚠️ Por design |
| `servir_documento()` | 270 | ✅ Obrigatória | ✅ Proprietário | ❌ | ✅ Completo |

## Comparação: Privado vs Público

### Arquivos Privados (`/media/privado/`)
- ✅ Requer autenticação
- ✅ Verifica autorização
- ✅ Valida propriedade
- ✅ Nega acesso por padrão
- **Uso**: Documentos sensíveis, comprovativos, identidade

### Arquivos Públicos (`/media/publico/`)
- ❌ Não requer autenticação (intencional)
- ❌ Não verifica autorização (intencional)
- ✅ Sanitiza paths
- ✅ Valida caminhos
- **Uso**: Fotos de produtos, imagens de perfil, recursos públicos

## Cenários de Uso

### Cenário 1: Foto de Produto (Safra)
```bash
GET /media/publico/safras/milho_produto_123.jpg
```
**Esperado**: ✅ Acesso público permitido (qualquer visitante pode ver produtos)

### Cenário 2: Foto de Perfil
```bash
GET /media/publico/perfil/usuario_456.jpg
```
**Esperado**: ✅ Acesso público permitido (perfis são públicos)

### Cenário 3: Documento Privado
```bash
GET /media/privado/documentos/bi_usuario_789.pdf
```
**Esperado**: ❌ Requer autenticação e autorização

### Cenário 4: Comprovativo de Transação
```bash
GET /media/privado/comprovativos/talao_transacao_10.jpg
```
**Esperado**: ❌ Apenas comprador, vendedor ou admin

## Riscos Identificados e Mitigações

### Risco 1: Exposição Acidental de Dados Sensíveis
**Descrição**: Arquivo sensível colocado acidentalmente em diretório público

**Mitigação Atual**:
- ✅ Separação clara de diretórios (public vs private)
- ✅ Sanitização de paths previne traversal

**Mitigação Adicional Recomendada**:
- ⚠️ Implementar whitelist de subpastas públicas
- ⚠️ Adicionar validação de tipos de arquivo permitidos
- ⚠️ Implementar scanning automático de conteúdo sensível

### Risco 2: Enumeração de Arquivos
**Descrição**: Atacante pode tentar adivinhar nomes de arquivos

**Mitigação Atual**:
- ✅ Retorna 404 para arquivos inexistentes
- ✅ Não revela estrutura de diretórios

**Mitigação Adicional Recomendada**:
- ⚠️ Usar nomes de arquivo aleatórios/hash
- ⚠️ Implementar rate limiting

### Risco 3: Hotlinking/Bandwidth Theft
**Descrição**: Sites externos podem usar imagens hospedadas

**Mitigação Atual**:
- ❌ Nenhuma proteção contra hotlinking

**Mitigação Adicional Recomendada**:
- ⚠️ Verificar header `Referer`
- ⚠️ Implementar tokens temporários para imagens
- ⚠️ Usar CDN com proteção contra hotlinking

## Conclusão

### Linha 239: `servir_privado()`
✅ **AUTORIZAÇÃO COMPLETA E ADEQUADA**
- Implementa todas as verificações necessárias
- Segue princípio de menor privilégio
- Nenhuma ação necessária

### Linha 247: `servir_publico()`
⚠️ **SEM AUTORIZAÇÃO - APROPRIADO PARA ARQUIVOS PÚBLICOS**
- Comportamento intencional para conteúdo público
- Sanitização e validação de paths implementadas
- **Recomendação**: Adicionar whitelist de subpastas (opcional)

## Ação Recomendada

**Prioridade Baixa**: Implementar whitelist de subpastas públicas para defesa em profundidade

```python
SUBPASTAS_PUBLICAS_PERMITIDAS = ['safras', 'perfil', 'produtos', 'banners']

if safe_subpasta not in SUBPASTAS_PUBLICAS_PERMITIDAS:
    abort(404)
```

**Benefício**: Camada adicional de segurança sem impactar funcionalidade

## Referências
- CWE-862: https://cwe.mitre.org/data/definitions/862.html
- OWASP Authorization: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/
- Public vs Private File Serving: https://flask.palletsprojects.com/en/2.3.x/patterns/fileuploads/
