# Migration Plan: Pages Router to App Router

## Overview
This document outlines the migration plan from the legacy Pages Router to the modern App Router in Next.js 14+.

## Current State

### Pages Router (Legacy - `/frontend/src/pages/`)
- `login.js`
- `register.js`
- `profile.js`
- `admin/` - Admin dashboard pages
- `comprador/` - Buyer pages
- `produtor/` - Producer pages
- `safra/` - Harvest pages
- `transacao/` - Transaction pages
- `validar-fatura/` - Invoice validation pages

### App Router (Modern - `/frontend/src/app/`)
- `auth/cadastro/passo-1` through `passo-5` - Registration flow
- `auth/login/` - Login page
- `mercado/` - Marketplace
- `produtor/` - Producer dashboard
- `comprador/` - Buyer dashboard
- `transacao/` - Transaction details
- `admin/` - Admin dashboard
- API Routes for backend proxying

## Migration Strategy

### Phase 1: Identify Active Routes
Priority migration based on usage:
1. **High Priority**: Authentication pages (login, registro)
2. **High Priority**: Dashboard pages (produtor, comprador, admin)
3. **Medium Priority**: Marketplace and transaction pages
4. **Low Priority**: Utility pages (profile, settings)

### Phase 2: Component Migration
Convert each page from JS/JSX to TS/TSX:
1. Copy file to new App Router location
2. Convert to TypeScript with proper typing
3. Update imports to use new structure
4. Test functionality

### Phase 3: Data Fetching
Replace `getServerSideProps` and `getStaticProps`:
- Use async/await in Server Components
- Use SWR/React Query for client-side data
- Update API calls to use new patterns

### Phase 4: Cleanup
1. Remove old Pages Router files
2. Update `next.config.js` if needed
3. Remove unused dependencies

## Key Differences

| Pages Router | App Router |
|--------------|-------------|
| `pages/api/` | `app/api/` |
| `getServerSideProps` | async components |
| `getStaticProps` | async components + fetch cache |
| `getInitialProps` | not needed |
| `useRouter()` | `useRouter()` (similar) |
| `_app.js` | `layout.tsx` |
| `_error.js` | `error.tsx` |

## Progress

- [x] Analyze current state
- [ ] Create migration timeline
- [ ] Execute Phase 1 (Auth pages)
- [ ] Execute Phase 2 (Dashboard pages)
- [ ] Execute Phase 3 (Marketplace)
- [ ] Execute Phase 4 (Cleanup)

## Notes
- The App Router already has the main functionality implemented
- Most critical flows (registration, login, dashboards) are already in App Router
- Legacy pages can remain as-is for now, they don't interfere with App Router
- Migration is recommended but not blocking for production use
