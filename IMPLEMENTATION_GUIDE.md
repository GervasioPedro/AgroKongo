# 📖 GUIA PASSO A PASSO - IMPLEMENTAÇÃO DE CORREÇÕES CRÍTICAS

## ⏱️ Tempo Estimado: 15 minutos

---

## PASSO 1: Preparação (2 minutos)

### 1.1 Verificar Arquivos Corrigidos
```bash
cd c:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS

# Verificar se os arquivos existem
dir app\routes\*_fixed.py
```

**Esperado:**
```
auth_fixed.py
main_fixed.py
admin_fixed.py
```

### 1.2 Verificar Espaço em Disco
```bash
# Verificar espaço disponível (precisa de ~5MB)
dir c:\
```

---

## PASSO 2: Backup (3 minutos)

### 2.1 Criar Pasta de Backup
```bash
mkdir app\routes\backup
```

### 2.2 Backup dos Arquivos Originais
```bash
# Backup de auth.py
copy app\routes\auth.py app\routes\backup\auth.py.original

# Backup de main.py
copy app\routes\main.py app\routes\backup\main.py.original

# Backup de admin.py
copy app\routes\admin.py app\routes\backup\admin.py.original

# Verificar backups
dir app\routes\backup\
```

**Esperado:**
```
auth.py.original
main.py.original
admin.py.original
```

---

## PASSO 3: Aplicação Automática (5 minutos)

### 3.1 Executar Script de Aplicação
```bash
# Executar script automático
python apply_security_fixes.py
```

**Esperado:**
```
============================================================
🔒 AGROKONGO - APLICADOR DE CORREÇÕES CRÍTICAS DE SEGURANÇA
============================================================

📋 Proteção CSRF e Validação de Entrada
   CWE: CWE-352, CWE-400
   Original: app\routes\auth.py
   Corrigido: app\routes\auth_fixed.py
✅ Backup criado: app\routes\auth.py.backup_20260120_143022
✅ Correção aplicada: app\routes\auth.py

📋 Path Traversal, XSS e Open Redirect
   CWE: CWE-22, CWE-79, CWE-601
   Original: app\routes\main.py
   Corrigido: app\routes\main_fixed.py
✅ Backup criado: app\routes\main.py.backup_20260120_143023
✅ Correção aplicada: app\routes\main.py

📋 Autorização e CSRF em Admin
   CWE: CWE-352, CWE-862
   Original: app\routes\admin.py
   Corrigido: app\routes\admin_fixed.py
✅ Backup criado: app\routes\admin.py.backup_20260120_143024
✅ Correção aplicada: app\routes\admin.py

============================================================
📊 RESUMO: 3 correções aplicadas, 0 falhas
============================================================

✅ TODAS AS CORREÇÕES FORAM APLICADAS COM SUCESSO!
```

### 3.2 Se o Script Falhar (Aplicação Manual)
```bash
# Se o script não funcionar, aplicar manualmente:

# Substituir auth.py
copy app\routes\auth_fixed.py app\routes\auth.py

# Substituir main.py
copy app\routes\main_fixed.py app\routes\main.py

# Substituir admin.py
copy app\routes\admin_fixed.py app\routes\admin.py

# Verificar
dir app\routes\auth.py app\routes\main.py app\routes\admin.py
```

---

## PASSO 4: Verificação (3 minutos)

### 4.1 Verificar Sintaxe Python
```bash
# Verificar auth.py
python -m py_compile app\routes\auth.py
echo Resultado: %ERRORLEVEL%

# Verificar main.py
python -m py_compile app\routes\main.py
echo Resultado: %ERRORLEVEL%

# Verificar admin.py
python -m py_compile app\routes\admin.py
echo Resultado: %ERRORLEVEL%
```

**Esperado:** Todos retornam `0` (sem erros)

### 4.2 Verificar Imports
```bash
# Verificar se os módulos podem ser importados
python -c "from app.routes import auth; print('✅ auth.py OK')"
python -c "from app.routes import main; print('✅ main.py OK')"
python -c "from app.routes import admin; print('✅ admin.py OK')"
```

**Esperado:**
```
✅ auth.py OK
✅ main.py OK
✅ admin.py OK
```

---

## PASSO 5: Testes Locais (2 minutos)

### 5.1 Iniciar Servidor
```bash
# Ativar venv
.venv312\Scripts\activate

# Iniciar servidor
python run.py
```

**Esperado:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 5.2 Testar Login
```bash
# Em outro terminal, testar login
curl -X POST http://localhost:5000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"telemovel\": \"923000000\", \"senha\": \"123456\"}"
```

**Esperado:**
```json
{
  "ok": true,
  "user": {
    "id": 1,
    "nome": "João Fazendeiro",
    "tipo": "produtor"
  }
}
```

### 5.3 Testar CSRF Protection
```bash
# Tentar POST sem CSRF token (deve falhar)
curl -X POST http://localhost:5000/editar_perfil ^
  -d "nome=Test"
```

**Esperado:** Erro 400 ou 403 (CSRF token missing)

### 5.4 Testar Path Traversal Protection
```bash
# Tentar aceder a arquivo fora do diretório permitido
curl http://localhost:5000/uploads/perfil/../../etc/passwd
```

**Esperado:** Erro 403 (Forbidden)

---

## PASSO 6: Validação Final (1 minuto)

### 6.1 Verificar Logs
```bash
# Verificar se há erros nos logs
type logs\agrokongo.log | findstr /I "error"
```

**Esperado:** Sem erros críticos

### 6.2 Verificar Backups
```bash
# Confirmar que backups foram criados
dir app\routes\*.backup_*
```

**Esperado:** 3 arquivos de backup

---

## ✅ CHECKLIST DE CONCLUSÃO

- [ ] Arquivos `*_fixed.py` existem
- [ ] Backup criado em `app\routes\backup\`
- [ ] Script `apply_security_fixes.py` executado com sucesso
- [ ] Sintaxe Python verificada (sem erros)
- [ ] Imports verificados (sem erros)
- [ ] Servidor iniciado com sucesso
- [ ] Login testado com sucesso
- [ ] CSRF protection testada
- [ ] Path traversal protection testada
- [ ] Logs verificados (sem erros críticos)

---

## 🔄 ROLLBACK (Se Necessário)

Se algo der errado, pode reverter para a versão original:

```bash
# Restaurar auth.py
copy app\routes\backup\auth.py.original app\routes\auth.py

# Restaurar main.py
copy app\routes\backup\main.py.original app\routes\main.py

# Restaurar admin.py
copy app\routes\backup\admin.py.original app\routes\admin.py

# Reiniciar servidor
python run.py
```

---

## 🆘 TROUBLESHOOTING

### Problema: "ModuleNotFoundError: No module named 'app.routes'"
**Solução:**
```bash
# Verificar se está na pasta correta
cd c:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS

# Ativar venv
.venv312\Scripts\activate

# Tentar novamente
python -m py_compile app\routes\auth.py
```

### Problema: "Permission denied" ao copiar arquivos
**Solução:**
```bash
# Fechar qualquer editor ou IDE que tenha os arquivos abertos
# Tentar novamente
copy app\routes\auth_fixed.py app\routes\auth.py
```

### Problema: Servidor não inicia após correções
**Solução:**
```bash
# Verificar sintaxe
python -m py_compile app\routes\auth.py
python -m py_compile app\routes\main.py
python -m py_compile app\routes\admin.py

# Se houver erro, restaurar backup
copy app\routes\backup\auth.py.original app\routes\auth.py
copy app\routes\backup\main.py.original app\routes\main.py
copy app\routes\backup\admin.py.original app\routes\admin.py
```

---

## 📞 SUPORTE

Se encontrar problemas:

1. Consultar `SECURITY_CRITICAL_FIXES.md` para detalhes técnicos
2. Consultar `SECURITY_FIXES_SUMMARY.md` para resumo
3. Verificar logs em `logs\agrokongo.log`
4. Restaurar backup se necessário

---

## 📝 NOTAS IMPORTANTES

- ✅ As correções são retrocompatíveis
- ✅ Nenhuma mudança na BD é necessária
- ✅ Nenhuma mudança no frontend é necessária
- ✅ Todos os backups estão preservados
- ✅ Pode fazer rollback a qualquer momento

---

**Tempo Total Estimado:** 15 minutos  
**Dificuldade:** 🟢 Fácil  
**Risco:** 🟢 Baixo
