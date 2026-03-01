# 🚀 Guia Rápido - Template Frontend Angola

## ✅ O que foi criado

### 1. **Design System** (`TEMPLATE_DESIGN_SYSTEM.md`)
- Paleta de cores otimizada para Angola
- Princípios mobile-first (redes 3G)
- Estados visuais de Escrow
- Guidelines de acessibilidade

### 2. **Componentes Prontos**

#### `Badge` (`src/components/ui/badge.tsx`)
```tsx
<Badge status="escrow" />        // 🔒 Em Custódia
<Badge status="pendente" />      // ⏳ Aguardando Pagamento
<Badge status="finalizado" />    // 🎉 Finalizado
```

#### `TransactionCard` (`src/components/dashboard/transaction-card.tsx`)
```tsx
<TransactionCard
  faturaRef="AK-2024-001"
  status="escrow"
  produto="Tomate"
  quantidade={500}
  valorTotal={75000}
  tipoUsuario="produtor"
/>
```

### 3. **Utilities**

#### Formatação (`src/utils/format.ts`)
```tsx
formatCurrency(15000, "AOA")  // "15.000,00 Kz"
formatWeight(1500)            // "1.500 kg"
formatDate("2024-01-15")      // "15 Jan 2024"
```

---

## 🎯 Como Usar

### Passo 1: Atualizar Tailwind Config
Já tens as cores definidas em `tailwind.config.ts`. Adiciona apenas:

```ts
// tailwind.config.ts
colors: {
  // ... cores existentes ...
  alert: {
    pending: "#FBC02D",
    critical: "#F57C00"
  }
}
```

### Passo 2: Usar Badge nos teus componentes
```tsx
import { Badge } from "@/components/ui/badge";

// No teu dashboard
<Badge status={transacao.status} />
```

### Passo 3: Implementar TransactionCard
```tsx
import { TransactionCard } from "@/components/dashboard/transaction-card";

// Lista de transações
{transacoes.map(t => (
  <TransactionCard
    key={t.id}
    faturaRef={t.fatura_ref}
    status={t.status}
    produto={t.safra.produto}
    quantidade={t.quantidade_comprada}
    valorTotal={t.valor_total_pago}
    nomeOutraParte={t.comprador.nome}
    tipoUsuario="produtor"
    onAction={() => router.push(`/transacao/${t.id}`)}
  />
))}
```

### Passo 4: Formatar valores
```tsx
import { formatCurrency, formatDate } from "@/utils/format";

<p>{formatCurrency(transacao.valor_total_pago, "AOA")}</p>
<p>{formatDate(transacao.data_criacao)}</p>
```

---

## 📱 Exemplo Completo

Ver `EXEMPLO_DASHBOARD.tsx` para um dashboard funcional com:
- ✅ KPIs (Saldo, Vendas, Pendentes)
- ✅ Cards de transação com estados visuais
- ✅ Ações rápidas
- ✅ Bottom navigation mobile

---

## 🎨 Estados Visuais de Escrow

### Cores por Estado
| Estado | Cor | Uso |
|--------|-----|-----|
| `pendente` | Amarelo | Aguardando ação do comprador |
| `analise` | Azul claro | Admin a validar |
| `escrow` | Azul escuro | Dinheiro em custódia 🔒 |
| `enviado` | Roxo | Mercadoria a caminho |
| `entregue` | Verde | Comprador confirmou |
| `finalizado` | Verde escuro | Pagamento liberado ✅ |
| `disputa` | Vermelho | Problema a resolver |

### Feedback Visual
```tsx
// Escrow ativo - destaque especial
{status === "escrow" && (
  <div className="bg-escrow-primary/5 border-escrow-primary">
    <Lock className="text-escrow-primary" />
    <p>💰 Dinheiro protegido. Pode enviar a mercadoria.</p>
  </div>
)}
```

---

## 🚀 Performance (Redes 3G)

### 1. Lazy Loading de Imagens
```tsx
<Image 
  src={safra.imagem}
  loading="lazy"
  placeholder="blur"
/>
```

### 2. Skeleton Loading
```tsx
import { Skeleton } from "@/components/ui/skeleton";

{loading ? (
  <Skeleton className="h-24 w-full" />
) : (
  <TransactionCard {...data} />
)}
```

### 3. Compressão (já implementado)
```tsx
import { compressImage } from "@/utils/image-compression";

const compressed = await compressImage(file, {
  maxSizeMB: 0.5,
  maxWidthOrHeight: 1024
});
```

---

## ✅ Próximos Passos

1. **Integrar com API Backend**
   - Mapear estados do backend (`TransactionStatus`) para o frontend
   - Criar hooks SWR para fetching de dados

2. **PWA (Offline-First)**
   - Já tens `next-pwa` instalado
   - Configurar service worker para cache

3. **Testes em Rede 3G**
   - Chrome DevTools > Network > Slow 3G
   - Verificar tempos de carregamento < 3s

4. **Notificações Push**
   - Alertar produtor quando pagamento validado
   - Alertar comprador quando mercadoria enviada

---

## 📚 Estrutura de Ficheiros

```
frontend/
├── TEMPLATE_DESIGN_SYSTEM.md      # Documentação completa
├── EXEMPLO_DASHBOARD.tsx          # Exemplo funcional
├── src/
│   ├── components/
│   │   ├── ui/
│   │   │   └── badge.tsx          # ✅ Novo
│   │   └── dashboard/
│   │       └── transaction-card.tsx  # ✅ Novo
│   └── utils/
│       └── format.ts              # ✅ Novo
```

---

## 🎯 Checklist de Implementação

- [x] Design System documentado
- [x] Badge component (estados de Escrow)
- [x] TransactionCard component
- [x] Utilities de formatação (AOA, datas)
- [x] Exemplo de dashboard completo
- [ ] Integração com API backend
- [ ] PWA configurado
- [ ] Testes em rede 3G
- [ ] Notificações push

---

**Pronto para começar! 🚀**

Qualquer dúvida, consulta `TEMPLATE_DESIGN_SYSTEM.md` ou o exemplo em `EXEMPLO_DASHBOARD.tsx`.
