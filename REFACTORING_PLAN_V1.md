# PLANO DE REFATORAÇÃO PROFUNDA - AGROKONGO MARKETPLACE

**Arquitetura de Refatoração v1.0**  
**Data:** 04 de Março de 2026  
**Arquiteta:** Engenheiro de Software Sênior  

---

## 1. VISÃO GERAL DA REFATORAÇÃO

### 1.1 Objetivos

| Objetivo | Descrição | Prioridade |
|----------|-----------|------------|
| **Segurança** | Criptografar dados sensíveis (NIF, IBAN) | CRÍTICA |
| **Qualidade** | Implementar Repository Pattern | ALTA |
| **Manutenibilidade** | Command/Query Separation (CQRS) | ALTA |
| **Validação** | Adicionar Pydantic para DTOs | MÉDIA |
| **Observabilidade** | Logging estruturado | MÉDIA |
| **Testabilidade** | Cobertura de testes > 70% | ALTA |

### 1.2 Estrutura Alvo (Domain-Driven Design)

```
app/
├── domain/                 # Entidades e lógica de negócio
│   ├── entities/          # User, Transacao, Safra, Produto
│   ├── value_objects/     # NIF, IBAN, Telefone
│   ├── repositories/      # Interfaces abstratas
│   └── services/         # Domain Services
├── application/          # Casos de uso
│   ├── commands/         # Write operations
│   ├── queries/          # Read operations
│   └── dto/              # Data Transfer Objects
├── infrastructure/        # Implementações externas
│   ├── persistence/      # SQLAlchemy repositories
│   ├── security/         # Encryption, Auth
│   └── external/         # APIs externas
├── api/                  # Controllers/Routes
└── shared/               # Utils, Helpers, Exceptions
```

---

## 2. IMPLEMENTAÇÕES PRIORITÁRIAS

### 2.1 CRÍTICA: Criptografia de Dados Sensíveis

**Problema:** NIF e IBAN armazenados em texto plano

**Solução:** Implementar campo cifrado com SQLAlchemy-Utils

```python
# app/domain/value_objects/campos_cifrados.py
from sqlalchemy_utils import EncryptedType
from sqlalchemy import String

class CampoCifrado:
    """Mixin para campos que requerem criptografia."""
    
    @staticmethod
    def criar_campo_encrypted(secret_key: str, tipo=String(50)):
        return EncryptedType(tipo, secret_key)
```

**Arquivo a criar:** `app/domain/value_objects/campos_cifrados.py`

---

### 2.2 ALTA: Repository Pattern

**Problema:** Lógica de acesso a dados acoplada aos modelos

**Solução:** Criar interfaces abstratas e implementações

```python
# app/domain/repositories/usuario_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List

class UsuarioRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional['Usuario']:
        pass
    
    @abstractmethod
    def buscar_por_telemovel(self, telefone: str) -> Optional['Usuario']:
        pass
    
    @abstractmethod
    def listar_todos(self, limite: int = 100) -> List['Usuario']:
        pass
```

**Arquivo a criar:** `app/domain/repositories/__init__.py`

---

### 2.3 ALTA: Command/Query Separation (CQRS)

**Problema:** Rotas misturam leitura e escrita

**Solução:** Separar Commands epython
# app Queries

```/application/commands/criar_transacao_command.py
from pydantic import BaseModel, Field
from decimal import Decimal

class CriarTransacaoCommand(BaseModel):
    comprador_id: int
    vendedor_id: int
    safra_id: int
    quantidade: Decimal = Field(gt=0)
    valor_total: Decimal = Field(gt=0)
```

---

### 2.4 MÉDIA: Logging Estruturado

**Problema:** Logs inconsistentes

**Solução:** Implementar structlog

```python
# app/shared/logging.py
import structlog
from structlog.processors import JSONRenderer

def configurar_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
```

---

## 3. ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Fundações (Semana 1)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 1 | Criar estrutura DDD | 2h | `app/domain/*` |
| 2 | Implementar campos cifrados | 4h | `app/models/usuario.py` |
| 3 | Criar exceptions customizadas | 2h | `app/shared/exceptions.py` |

### Fase 2: Repository Pattern (Semana 2)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 4 | Criar interfaces de repositório | 4h | `app/domain/repositories/*` |
| 5 | Implementar concrete repositories | 8h | `app/infrastructure/persistence/*` |
| 6 | Migrar rotas para usar repositories | 8h | `app/routes/*` |

### Fase 3: CQRS (Semana 3)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 7 | Criar Command handlers | 6h | `app/application/commands/*` |
| 8 | Criar Query handlers | 6h | `app/application/queries/*` |
| 9 | Integrar com Pydantic | 4h | `app/application/dto/*` |

### Fase 4: Observabilidade (Semana 4)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 10 | Configurar structlog | 2h | `app/shared/logging.py` |
| 11 | Adicionar métricas | 4h | `app/metrics/*` |
| 12 | Health checks detalhados | 2h | `app/routes/health.py` |

---

## 4. PADRÕES APLICADOS

### 4.1 SOLID Principles

| Princípio | Aplicação |
|-----------|-----------|
| **S**ingle Responsibility | Cada classe tem uma responsabilidade |
| **O**pen/Closed | Extender comportamento sem modificar código |
| **L**iskov Substitution | Subclasses substituíveis |
| **I**nterface Segregation | Interfaces pequenas e específicas |
| **D**ependency Inversion | Depender de abstrações, não concreções |

### 4.2 Domain-Driven Design

- **Entities:** Usuario, Transacao, Safra
- **Value Objects:** NIF, IBAN, TelefoneAngola
- **Aggregates:** Transacao (raiz), Usuario (raiz)
- **Domain Services:** EscrowService
- **Application Services:** TransacaoService

### 4.3 Enterprise Integration Patterns

- **Unit of Work:** SQLAlchemy session
- **Repository:** Interfaces abstratas
- **Mapper:** SQLAlchemy ORM
- **Factory:** UserFactory, TransacaoFactory

---

## 5. CRITÉRIOS DE ACEITE

### Antes da Refatoração

- [ ] Todos os testes existentes passam
- [ ] Backup da base de dados realizado
- [ ] Ambiente de staging configurado

### Depois da Refatoração

- [ ] NIF e IBAN criptografados no banco
- [ ] Repository Pattern implementado
- [ ] Commands/Queries separados
- [ ] Cobertura de testes > 70%
- [ ] Logs estruturados funcionando
- [ ] Performance: response time < 200ms

---

## 6. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Quebra de funcionalidade | Alta | Alto | Testes E2E antes/depois |
| Performance degradada | Média | Médio | Benchmarks antes/depois |
| Tempo de implementação | Alta | Médio | Fases incrementais |
| Dados existentes | Alta | Crítico | Migração com rollback |

---

## 7. PRÓXIMOS PASSOS

1. **Implementar campos cifrados** - Prioridade CRÍTICA
2. **Criar estrutura de diretórios DDD**
3. **Implementar primeiro Repository**
4. **Escrever testes para fluxo de escrow**

---

**Documento aprovado para implementação:** _________________  
**Data:** _________________
