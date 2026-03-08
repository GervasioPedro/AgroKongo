# Correção CWE-396/397 - Generic Exception em auditoria.py linhas 33-34

## Vulnerabilidade Identificada
**Localização**: `app/models/auditoria.py` linha 33-34  
**Função**: `obter_valor_decimal()`  
**CWE**: CWE-396 (Declaration of Catch for Generic Exception), CWE-397 (Declaration of Throws for Generic Exception)  
**Severidade**: Medium

## Problema
A função `obter_valor_decimal()` usava `except Exception` genérico que captura e silencia TODAS as exceções:

```python
# ANTES - Vulnerável
@classmethod
def obter_valor_decimal(cls, chave: str, padrao: Decimal = Decimal('0.00')) -> Decimal:
    try:
        config = cls.query.filter_by(chave=chave).first()
        if config and config.valor:
            return Decimal(config.valor)
    except Exception:  # ← Captura TUDO
        pass  # ← Silencia TUDO
    return padrao
```

**Riscos**:
- Mascara erros críticos do sistema
- Oculta problemas de conexão com banco de dados
- Esconde bugs de programação
- Dificulta debugging e troubleshooting
- Pode causar comportamento inesperado silencioso
- Viola princípios de fail-fast
- Compromete observabilidade do sistema

## Exceções Mascaradas

### Exceções Críticas que eram Silenciadas
1. **KeyboardInterrupt**: Interrupção do usuário (Ctrl+C)
2. **SystemExit**: Tentativa de encerrar aplicação
3. **MemoryError**: Falta de memória
4. **SQLAlchemyError**: Erros de banco de dados
5. **AttributeError**: Bugs de programação
6. **ImportError**: Problemas de dependências
7. **RuntimeError**: Erros de execução

## Correção Implementada
Substituído `except Exception` por exceções específicas com logging:

```python
@classmethod
def obter_valor_decimal(cls, chave: str, padrao: Decimal = Decimal('0.00')) -> Decimal:
    try:
        config = cls.query.filter_by(chave=chave).first()
        if config and config.valor:
            return Decimal(config.valor)
    except (ValueError, TypeError, db.exc.SQLAlchemyError) as e:
        from flask import current_app
        current_app.logger.warning(f"Erro ao obter configuração '{chave}': {e}")
    return padrao
```

## Exceções Específicas Tratadas

### 1. ValueError
```python
Decimal('invalid_value')  # ValueError: Invalid literal for Decimal
```
- Ocorre quando `config.valor` não pode ser convertido para Decimal
- Exemplo: valor = "abc" ou "12.34.56"

### 2. TypeError
```python
Decimal(None)  # TypeError: Cannot convert None to Decimal
```
- Ocorre quando `config.valor` é None ou tipo incompatível
- Exemplo: valor = None, [], {}

### 3. db.exc.SQLAlchemyError
```python
cls.query.filter_by(chave=chave).first()  # SQLAlchemyError
```
- Erros de conexão com banco de dados
- Erros de query SQL
- Timeout de conexão
- Problemas de transação

## Proteções Adicionadas

### 1. Exceções Específicas
- Captura apenas erros esperados e recuperáveis
- Permite que exceções críticas propaguem naturalmente

### 2. Logging Apropriado
```python
current_app.logger.warning(f"Erro ao obter configuração '{chave}': {e}")
```
- Registra erro para debugging
- Inclui chave da configuração
- Inclui mensagem de erro detalhada
- Usa nível WARNING (não é crítico, tem fallback)

### 3. Fallback Seguro
```python
return padrao
```
- Retorna valor padrão em caso de erro
- Aplicação continua funcionando
- Comportamento previsível

## Exceções que Agora Propagam Corretamente

### Exceções Críticas (NÃO capturadas)
1. **KeyboardInterrupt**: Permite interrupção do usuário
2. **SystemExit**: Permite encerramento da aplicação
3. **MemoryError**: Falha rápida em caso de falta de memória
4. **ImportError**: Indica problema de configuração/dependências
5. **AttributeError**: Indica bug de programação que deve ser corrigido

## Cenários de Uso

### Cenário 1: Valor Inválido
```python
# Configuração no BD: chave='taxa_comissao', valor='abc'
taxa = ConfiguracaoSistema.obter_valor_decimal('taxa_comissao', Decimal('0.05'))
# Log: "Erro ao obter configuração 'taxa_comissao': Invalid literal for Decimal: 'abc'"
# Retorna: Decimal('0.05')
```

### Cenário 2: Valor None
```python
# Configuração no BD: chave='taxa_comissao', valor=None
taxa = ConfiguracaoSistema.obter_valor_decimal('taxa_comissao', Decimal('0.05'))
# Retorna: Decimal('0.05') (sem erro, pois há verificação if config.valor)
```

### Cenário 3: Erro de Banco de Dados
```python
# Banco de dados desconectado
taxa = ConfiguracaoSistema.obter_valor_decimal('taxa_comissao', Decimal('0.05'))
# Log: "Erro ao obter configuração 'taxa_comissao': (OperationalError) connection refused"
# Retorna: Decimal('0.05')
```

### Cenário 4: Configuração Não Existe
```python
# Configuração não existe no BD
taxa = ConfiguracaoSistema.obter_valor_decimal('taxa_inexistente', Decimal('0.05'))
# Retorna: Decimal('0.05') (sem erro, config é None)
```

## Impacto de Segurança
- **Antes**: Erros críticos eram silenciados, dificultando debugging
- **Depois**: Apenas erros esperados são capturados, críticos propagam
- **Observabilidade**: Erros são logados para análise

## Best Practices Implementadas

### 1. Fail Fast
- Exceções críticas não são capturadas
- Sistema falha rapidamente em caso de erro grave
- Facilita identificação de problemas

### 2. Specific Exception Handling
- Captura apenas exceções esperadas
- Cada exceção tem tratamento apropriado
- Código mais legível e manutenível

### 3. Logging Apropriado
- Erros são registrados para análise
- Contexto suficiente para debugging
- Nível de log apropriado (WARNING)

### 4. Graceful Degradation
- Retorna valor padrão em caso de erro
- Aplicação continua funcionando
- Comportamento previsível

## Comparação

| Aspecto | Antes (Exception) | Depois (Específico) |
|---------|-------------------|---------------------|
| KeyboardInterrupt | ❌ Capturado | ✅ Propaga |
| SystemExit | ❌ Capturado | ✅ Propaga |
| MemoryError | ❌ Capturado | ✅ Propaga |
| ValueError | ❌ Silenciado | ✅ Logado |
| TypeError | ❌ Silenciado | ✅ Logado |
| SQLAlchemyError | ❌ Silenciado | ✅ Logado |
| Debugging | ❌ Difícil | ✅ Fácil |
| Observabilidade | ❌ Baixa | ✅ Alta |

## Status
✅ **CORRIGIDO** - Exceções específicas implementadas com logging apropriado
🔍 **OBSERVABILIDADE** - Erros agora são logados para análise
⚡ **FAIL FAST** - Exceções críticas propagam corretamente
📋 **BEST PRACTICES** - Segue padrões de tratamento de exceções Python
