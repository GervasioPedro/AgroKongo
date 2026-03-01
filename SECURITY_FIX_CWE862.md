# Correção CWE-862: Missing Authorization

## Vulnerabilidades Identificadas
**Localização**: `app/routes/main.py` - Linhas 32 e 38  
**Funções**: `index()` e `dashboard()`  
**Severidade**: Média/Alta

## Descrição dos Problemas

### 1. Linha 32 - Função `index()`
**Problema**: A rota pública exibia safras de todos os produtores, incluindo aqueles com contas não validadas, permitindo que produtos de usuários não verificados fossem expostos no marketplace.

**Risco**: 
- Exposição de produtos de contas fraudulentas
- Falta de controle de qualidade na vitrine pública
- Possível exibição de conteúdo malicioso

### 2. Linha 38 - Função `dashboard()`
**Problema**: Embora a rota tivesse `@login_required`, não verificava se a conta do usuário estava validada pela administração antes de permitir acesso ao dashboard.

**Risco**:
- Usuários não validados podiam acessar funcionalidades restritas
- Bypass do processo de KYC (Know Your Customer)
- Acesso não autorizado a recursos da plataforma

## Correções Aplicadas

### 1. Filtro de Autorização na Vitrine Pública
```python
@main_bp.route('/')
def index():
    """Vitrine: Otimizada para carregar produtos e imagens rapidamente."""
    # Apenas safras de produtores validados devem ser exibidas
    safras_recentes = Safra.query.join(Usuario, Safra.produtor_id == Usuario.id) \
        .filter(Safra.status == 'disponivel', Usuario.conta_validada == True) \
        .order_by(Safra.id.desc()).limit(4).all()
    return render_template('index.html', safras=safras_recentes)
```

**Proteções Implementadas**:
- JOIN com tabela Usuario para verificar status de validação
- Filtro `Usuario.conta_validada == True` garante apenas produtores aprovados
- Mantém filtro `status == 'disponivel'` para safras ativas

### 2. Verificação de Conta Validada no Dashboard
```python
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Encaminha o utilizador com base no tipo e estado de validação."""
    if not current_user.perfil_completo:
        flash("ℹ️ Quase lá! Complete o seu perfil para começar a negociar.", "info")
        return redirect(url_for('main.completar_perfil'))
    
    # Verificação de autorização: conta deve estar validada (exceto admin)
    if current_user.tipo != 'admin' and not current_user.conta_validada:
        flash("⚠️ Sua conta está pendente de validação pela administração.", "warning")
        return redirect(url_for('main.index'))

    # Redirecionamento baseado em Role
    redirecionamentos = {
        'admin': 'admin.dashboard',
        'produtor': 'produtor.dashboard',
        'comprador': 'comprador.dashboard'
    }

    endpoint = redirecionamentos.get(current_user.tipo, 'main.index')
    return redirect(url_for(endpoint))
```

**Proteções Implementadas**:
- Verificação explícita de `conta_validada` antes de permitir acesso
- Exceção para administradores (não precisam de validação)
- Mensagem clara ao usuário sobre status pendente
- Redirecionamento seguro para página inicial

## Impacto das Correções

### Segurança
✅ Apenas produtores validados têm produtos exibidos publicamente  
✅ Usuários não validados não podem acessar dashboards restritos  
✅ Processo de KYC é obrigatório antes de operar na plataforma  
✅ Redução de risco de fraude e contas maliciosas  

### Experiência do Usuário
✅ Feedback claro sobre status de validação pendente  
✅ Marketplace exibe apenas produtos de vendedores confiáveis  
✅ Administradores mantêm acesso irrestrito para gestão  

## Outras Rotas com Autorização Adequada

As seguintes rotas já possuem verificações de autorização corretas:
- `/ler-notificacao/<int:id>` - Verifica `notif.usuario_id != current_user.id`
- `/api/wallet` - Verifica `current_user.is_authenticated`
- `/media/privado/<subpasta>/<filename>` - Requer `@login_required`
- `/gerar_fatura/<int:trans_id>` - Verifica se usuário é parte da transação

## Testes Recomendados

1. **Teste de Vitrine**: Verificar que apenas safras de produtores validados aparecem
2. **Teste de Dashboard**: Tentar acessar dashboard com conta não validada
3. **Teste de Admin**: Confirmar que admin acessa dashboard sem validação
4. **Teste de Redirecionamento**: Verificar mensagens de feedback ao usuário

## Referências
- CWE-862: https://cwe.mitre.org/data/definitions/862.html
- OWASP Authorization: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/
- Flask-Login: https://flask-login.readthedocs.io/
