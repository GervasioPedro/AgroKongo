# AgroKongo Frontend (Next.js 15 + TypeScript)

## Stack
- Next.js 15 (App Router)
- TypeScript (strict)
- Tailwind CSS (tokens definidos em `globals.css` e `tailwind.config.ts`)
- Zustand (estado global)
- Lucide React (iconografia)

## Estrutura
A base segue o guia:

- `src/app` (rotas)
- `src/components/ui` (atoms)
- `src/components/dashboard` (organisms/widgets)
- `src/store` (Zustand)
- `src/services` (API)
- `src/utils` (formatters)

## Como correr
1. Instalar dependencias:
   - `npm install`
2. Ambiente dev:
   - `npm run dev`

## Nota
Este frontend esta preparado para evoluir para PWA e cache estrategico (SWR/React Query), e para UX mobile-first com skeleton loaders e indicadores de progresso.
