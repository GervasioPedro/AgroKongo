# Correção CWE-862: Missing Authorization em main.py (Linhas 210, 222)

## Vulnerabilidades Identificadas
**Localização**: `app/routes/main.py` - Linhas 210, 222 e função relacionada  
**Funções Afetadas**: 
- `servir_privado()` (linha ~210)
- `visualizar_fatura()` (linha ~222)
- `servir_documento()` (linha ~295)

**Severidade**: Alta

## Descrição dos Problemas

### 1. Linha 210 - Função `servir_privado()`
**Problema**: A função tinha `@login_required` mas não verificava se o usuário autenticado tinha permissão para acessar o arquivo específico solicitado.

**Risco**:
- Usuário A poderia acessar documentos privados do Usuário B
- Comprador poderia ver comprovativos de outras transações
- Acesso não autorizado a documentos de identidade de terceiros

**Exemplo de Ataque**:
```
# Usuário malicioso tenta acessar documento de outro usuário
GET /media/privado/documentos/documento_usuario_123.pdf
# Sem verificação, qualquer usuário autenticado poderia acessar
```

### 2. Linha 222 - Função `visualizar_fatura()`
**Problema**: Tinha comentário "Verifica se o user faz parte da transação" mas não implementava a verificação.

**Risco**:
- Qualquer usuário autenticado poderia visualizar faturas de outras transações
- Exposição de informações financeiras sensíveis
- Violação de privacidade de dados comerciais

**Exemplo de Ataque**:
```python
# Usuário malicioso itera IDs de transações
for trans_id in range(1, 1000):
    GET /fatura/visualizar/{trans_id}
    # Sem verificação, veria todas as faturas
```

### 3. Função `servir_documento()`
**Problema**: Similar ao `servir_privado()`, não verificava propriedade do documento.

**Risco**:
- Acesso não autorizado a documentos de identidade
- Exposição de dados pessoais (BI, passaporte, etc.)

## Correções Aplicadas

### 1. Autorização em `servir_privado()` (LINHA 210)
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

**Proteções Implementadas**:
- Administradores têm acesso total
- Comprovativos: apenas comprador e vendedor da transação
- Documentos pessoais: apenas o proprietário
- Subpastas não reconhecidas: acesso negado

### 2. Autorização em `visualizar_fatura()` (LINHA 222)
```python
@main_bp.route('/fatura/visualizar/<int:trans_id>')
@login_required
def visualizar_fatura(trans_id):
    venda = Transacao.query.get_or_404(trans_id)
    
    # Verificação de autorização: apenas comprador, vendedor ou admin
    if current_user.tipo != 'admin':
        if current_user.id not in [venda.comprador_id, venda.vendedor_id]:
            abort(403)
    
    return render_template('documentos/fatura_geral.html', venda=venda)
```

**Proteções Implementadas**:
- Verifica se usuário é admin, comprador ou vendedor
- Retorna HTTP 403 para usuários não autorizados
- Implementa a verificação que estava apenas comentada

### 3. Autorização em `servir_documento()`
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
    
    # Verificação de autorização: apenas admin ou dono do documento
    if current_user.tipo != 'admin':
        if safe_filename != current_user.documento_pdf:
            abort(403)
    
    return send_from_directory(directory, safe_filename)
```

**Proteções Implementadas**:
- Verifica propriedade do documento
- Apenas admin ou dono pode acessar
- Retorna HTTP 403 para acesso não autorizado

## Matriz de Autorização

### Arquivos Privados (`/media/privado/`)

| Subpasta | Admin | Proprietário | Comprador | Vendedor | Outros |
|----------|-------|--------------|-----------|----------|--------|
| comprovativos | ✅ | N/A | ✅ (sua transação) | ✅ (sua transação) | ❌ |
| documentos | ✅ | ✅ | ❌ | ❌ | ❌ |
| identidade | ✅ | ✅ | ❌ | ❌ | ❌ |

### Faturas (`/fatura/visualizar/`)

| Papel | Acesso |
|-------|--------|
| Admin | ✅ Todas as faturas |
| Comprador | ✅ Apenas suas compras |
| Vendedor | ✅ Apenas suas vendas |
| Outros | ❌ Nenhuma fatura |

## Cenários de Ataque Bloqueados

### 1. Acesso a Documento de Outro Usuário
```python
# ANTES (Vulnerável)
# Usuário ID 5 tenta acessar documento do Usuário ID 10
GET /media/privado/documentos/doc_usuario_10.pdf
# Retornaria o documento

# DEPOIS (Protegido)
# Verifica: safe_filename != current_user.documento_pdf
# Retorna: HTTP 403 Forbidden
```

### 2. Acesso a Comprovativo de Outra Transação
```python
# ANTES (Vulnerável)
# Comprador da Transação 1 tenta ver comprovativo da Transação 2
GET /media/privado/comprovativos/talao_transacao_2.jpg
# Retornaria o comprovativo

# DEPOIS (Protegido)
# Busca transação: Transacao.query.filter_by(comprovativo_path=...)
# Verifica: current_user.id in [transacao.comprador_id, transacao.vendedor_id]
# Retorna: HTTP 403 Forbidden
```

### 3. Visualização de Fatura de Terceiros
```python
# ANTES (Vulnerável)
# Usuário não relacionado tenta ver fatura
GET /fatura/visualizar/123
# Retornaria a fatura

# DEPOIS (Protegido)
# Verifica: current_user.id in [venda.comprador_id, venda.vendedor_id]
# Retorna: HTTP 403 Forbidden
```

### 4. Enumeração de Documentos
```python
# ANTES (Vulnerável)
for i in range(1, 1000):
    GET /servir-documento/documento_{i}.pdf
    # Poderia baixar todos os documentos

# DEPOIS (Protegido)
# Cada requisição verifica propriedade
# Apenas documentos do próprio usuário são servidos
```

## Impacto das Correções

### Segurança
✅ Previne acesso não autorizado a documentos privados  
✅ Protege informações financeiras sensíveis  
✅ Impede enumeração de recursos  
✅ Garante privacidade de dados pessoais  
✅ Implementa princípio de menor privilégio  
✅ Administradores mantêm acesso para gestão  

### Funcionalidade
✅ Usuários legítimos mantêm acesso aos seus recursos  
✅ Transações permitem acesso a ambas as partes  
✅ Mensagens de erro apropriadas (403/404)  
✅ Performance não afetada  
✅ Compatibilidade com código existente  

## Testes Recomendados

### 1. Teste de Acesso a Documento Próprio
```python
# Login como Usuário A
# Acessar documento do Usuário A
GET /servir-documento/documento_usuario_a.pdf
# Deve retornar: 200 OK com o arquivo
```

### 2. Teste de Acesso a Documento de Terceiro
```python
# Login como Usuário A
# Tentar acessar documento do Usuário B
GET /servir-documento/documento_usuario_b.pdf
# Deve retornar: 403 Forbidden
```

### 3. Teste de Acesso a Comprovativo da Própria Transação
```python
# Login como Comprador da Transação 1
GET /media/privado/comprovativos/talao_transacao_1.jpg
# Deve retornar: 200 OK com o arquivo
```

### 4. Teste de Acesso a Comprovativo de Outra Transação
```python
# Login como Comprador da Transação 1
GET /media/privado/comprovativos/talao_transacao_2.jpg
# Deve retornar: 403 Forbidden
```

### 5. Teste de Visualização de Fatura Própria
```python
# Login como Vendedor da Transação 5
GET /fatura/visualizar/5
# Deve retornar: 200 OK com a fatura
```

### 6. Teste de Visualização de Fatura de Terceiro
```python
# Login como Usuário não relacionado
GET /fatura/visualizar/5
# Deve retornar: 403 Forbidden
```

### 7. Teste de Acesso Admin
```python
# Login como Admin
GET /servir-documento/qualquer_documento.pdf
GET /fatura/visualizar/qualquer_id
# Deve retornar: 200 OK (admin tem acesso total)
```

## Outras Funções com Autorização Adequada

As seguintes funções já possuem verificações corretas:
- `baixar_fatura()` - Verifica se usuário é parte da transação (linha ~235)
- `ler_notificacao()` - Verifica `notif.usuario_id != current_user.id` (linha ~125)
- `api_wallet()` - Filtra por `usuario_id=current_user.id` (linha ~160)

## Recomendações Adicionais

### 1. Logging de Tentativas de Acesso Não Autorizado
```python
if current_user.id not in [venda.comprador_id, venda.vendedor_id]:
    current_app.logger.warning(
        f"Tentativa de acesso não autorizado: User {current_user.id} "
        f"tentou acessar fatura {trans_id}"
    )
    abort(403)
```

### 2. Rate Limiting em Endpoints Sensíveis
```python
from flask_limiter import Limiter

@main_bp.route('/fatura/visualizar/<int:trans_id>')
@login_required
@limiter.limit("10 per minute")
def visualizar_fatura(trans_id):
    # ...
```

### 3. Auditoria de Acessos
```python
# Registrar acesso a documentos sensíveis
LogAuditoria(
    usuario_id=current_user.id,
    acao="ACESSO_DOCUMENTO",
    detalhes=f"Acessou documento: {safe_filename}"
)
db.session.add(log)
```

## Referências
- CWE-862: https://cwe.mitre.org/data/definitions/862.html
- OWASP Authorization: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/
- Flask-Login: https://flask-login.readthedocs.io/
- Principle of Least Privilege: https://en.wikipedia.org/wiki/Principle_of_least_privilege
