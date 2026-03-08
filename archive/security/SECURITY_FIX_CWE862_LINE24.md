# Correção CWE-862 - Missing Authorization em main.py linha 24

## Vulnerabilidade Identificada
**Localização**: `app/routes/main.py` linha 24  
**Função**: `health_check()`  
**CWE**: CWE-862 (Missing Authorization)  
**Severidade**: Medium

## Problema
O endpoint `/health` estava público e expunha informações sensíveis sobre o estado da infraestrutura:
- Status da base de dados (healthy/unhealthy)
- Timestamp do servidor
- Estado geral da aplicação

Qualquer utilizador não autenticado poderia aceder a estas informações, facilitando reconhecimento para ataques.

## Correção Implementada
Adicionada autorização em duas camadas:

```python
@main_bp.route('/health')
@login_required  # ← Camada 1: Requer autenticação
def health_check():
    """Health check endpoint para monitoring"""
    # Camada 2: Requer tipo admin
    if current_user.tipo != 'admin':
        abort(403)
    
    try:
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200 if db_status == 'healthy' else 503
```

## Proteções Adicionadas
1. **`@login_required`**: Bloqueia acesso anónimo
2. **Verificação de tipo**: Apenas `current_user.tipo == 'admin'` pode aceder
3. **HTTP 403**: Retorna Forbidden para utilizadores não autorizados

## Impacto
- Endpoint agora acessível apenas por administradores autenticados
- Informações de infraestrutura protegidas contra reconhecimento
- Mantém funcionalidade para monitoring legítimo por admins

## Status
✅ **CORRIGIDO** - Autorização implementada com sucesso
