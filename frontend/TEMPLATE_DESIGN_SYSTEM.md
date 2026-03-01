# 🎨 AgroKongo Design System - Angola

## 🎯 Princípios Core

### 1. Mobile-First (Redes 3G)
- Componentes < 50KB
- Lazy loading de imagens
- Estados de loading claros
- Offline-first quando possível

### 2. Feedback Visual Imediato
- Estados de Escrow com cores distintas
- Animações < 200ms
- Toasts para ações críticas

### 3. Acessibilidade Rural
- Contraste mínimo 4.5:1
- Touch targets ≥ 44px
- Texto legível sob sol (16px+)

---

## 🎨 Paleta de Cores

### Primárias (Agricultura)
```css
--agro-primary: #1B5E20    /* Verde Floresta - CTAs principais */
--agro-leaf: #8BC34A       /* Verde Folha - Sucesso */
--agro-moss: #415A3F       /* Verde Musgo - Texto secundário */
```

### Escrow (Estados Financeiros)
```css
--escrow-primary: #0D47A1  /* Azul Oceano - Dinheiro em custódia */
--escrow-light: #03A9F4    /* Azul Claro - Hover states */
```

### Alertas
```css
--alert-pending: #FBC02D   /* Amarelo - Aguardando ação */
--alert-critical: #F57C00  /* Laranja - Atenção urgente */
--alert-danger: #D32F2F    /* Vermelho - Erro/Disputa */
```

### Neutros
```css
--surface-neutral: #F0F4F0 /* Background suave */
--text-primary: #1A1A1A    /* Texto principal */
--text-secondary: #64748B  /* Texto secundário */
```

---

## 📦 Componentes Base

### Button
```tsx
// Variantes
<Button variant="primary">Comprar Safra</Button>      // Verde
<Button variant="escrow">Validar Pagamento</Button>   // Azul
<Button variant="outline">Cancelar</Button>           // Outline
<Button variant="ghost">Ver Detalhes</Button>         // Texto

// Estados
<Button loading>Processando...</Button>
<Button disabled>Indisponível</Button>
```

### Card (Transações/Safras)
```tsx
<Card variant="default">      // Branco com sombra suave
<Card variant="escrow">       // Azul claro (dinheiro em custódia)
<Card variant="success">      // Verde claro (finalizado)
<Card variant="warning">      // Amarelo (ação pendente)
```

### Badge (Status)
```tsx
<Badge status="pendente">Aguardando Pagamento</Badge>     // Amarelo
<Badge status="analise">Em Análise</Badge>                // Azul
<Badge status="escrow">Em Custódia</Badge>                // Azul escuro
<Badge status="enviado">Mercadoria Enviada</Badge>        // Roxo
<Badge status="entregue">Entregue</Badge>                 // Verde
<Badge status="finalizado">Finalizado</Badge>             // Verde escuro
<Badge status="disputa">Em Disputa</Badge>                // Vermelho
```

---

## 🔄 Estados de Escrow (Visual)

### 1. Aguardando Pagamento
```tsx
<Card className="border-l-4 border-alert-pending">
  <Badge status="pendente" />
  <p>Envie o comprovativo bancário</p>
  <Button variant="primary">Enviar Comprovativo</Button>
</Card>
```

### 2. Em Análise (Admin)
```tsx
<Card className="border-l-4 border-escrow-light">
  <Badge status="analise" />
  <Spinner size="sm" />
  <p>Administrador a validar...</p>
</Card>
```

### 3. Em Custódia (Escrow)
```tsx
<Card className="bg-escrow-primary/5 border-escrow-primary">
  <Badge status="escrow" />
  <LockIcon className="text-escrow-primary" />
  <p>💰 Dinheiro protegido. Pode enviar a mercadoria.</p>
  <Button variant="escrow">Confirmar Envio</Button>
</Card>
```

### 4. Finalizado
```tsx
<Card className="bg-agro-leaf/10 border-agro-leaf">
  <Badge status="finalizado" />
  <CheckCircle className="text-agro-leaf" />
  <p>✅ Transação concluída com sucesso!</p>
</Card>
```

---

## 📱 Layouts Mobile

### Dashboard (Produtor/Comprador)
```tsx
<main className="max-w-md mx-auto px-4 pb-20"> {/* pb-20 para bottom nav */}
  <Header />
  <KPICards />
  <TransactionList />
  <BottomNav />
</main>
```

### Formulários
```tsx
<form className="space-y-4">
  <Input 
    label="Quantidade (kg)"
    type="number"
    inputMode="decimal"  // Teclado numérico no mobile
  />
  <Button type="submit" className="w-full">
    Confirmar Compra
  </Button>
</form>
```

---

## 🚀 Performance

### Imagens
```tsx
// Usar compressão automática (já implementado)
import { compressImage } from '@/utils/image-compression';

// Lazy loading
<Image 
  src={safra.imagem} 
  loading="lazy"
  placeholder="blur"
/>
```

### Skeleton Loading
```tsx
<Skeleton className="h-24 w-full" />  // Cards
<Skeleton className="h-4 w-3/4" />    // Texto
```

---

## 🎯 Componentes Específicos Angola

### Comprovativo Upload
```tsx
<FileUpload
  accept="image/*,application/pdf"
  maxSize={5 * 1024 * 1024}  // 5MB
  compress={true}
  label="Talão Bancário (Multicaixa/BAI)"
/>
```

### Moeda (Kwanzas)
```tsx
import { formatCurrency } from '@/utils/format';

<p>{formatCurrency(15000, 'AOA')}</p>  // 15.000,00 Kz
```

### Notificações Offline
```tsx
<Toast variant="warning">
  📡 Sem conexão. Dados salvos localmente.
</Toast>
```

---

## ✅ Checklist de Implementação

- [x] Paleta de cores definida
- [x] Componentes base (Button, Card, Badge)
- [ ] Estados de Escrow visuais
- [ ] Skeleton loaders
- [ ] Compressão de imagens
- [ ] PWA (offline-first)
- [ ] Testes em rede 3G

---

## 📚 Referências

- Tailwind Config: `tailwind.config.ts`
- Componentes UI: `src/components/ui/`
- Utils: `src/utils/format.ts`
