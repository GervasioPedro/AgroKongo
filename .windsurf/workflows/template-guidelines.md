# AgroKongo Template Guidelines

**Guidelines específicas para desenvolvimento de templates do marketplace agrícola AgroKongo**

<!--

System Guidelines

Use este arquivo como referência para manter consistência visual e funcional em todos os templates do AgroKongo.

-->

# General guidelines

* **Sempre usar Bootstrap 5** como framework CSS base
* **Jinja2** como template engine com blocos bem definidos
* **Font Awesome 6.4.0** para ícones (prefixos `fas`, `fab`, `far`)
* **Mobile-first**: Design responsivo priorizando dispositivos móveis
* **Componentização**: Reutilizar componentes em `app/templates/components/`
* **Performance**: Minimizar CSS inline, usar classes Bootstrap
* **Acessibilidade**: Sempre incluir atributos `aria-label`, `alt`, e semântica HTML5 correta
* **Segurança**: Nunca confiar em input do usuário, sempre sanitizar com `|safe` apenas quando necessário

--------------

# Design system guidelines

## Identidade Visual AgroKongo

### Cores Primárias
* **Verde Principal**: `#1b4332` (gradiente escuro hero/footer)
* **Verde Secundário**: `#081c15` (gradiente base)
* **Verde Vivo**: `#2ecc71` (ênfase e acentos)
* **Verde Bootstrap**: `success` (buttons, badges)

### Cores Neutras
* **Branco**: `#ffffff` (navbars, cards)
* **Cinza Claro**: `#f8f9fa` (backgrounds)
* **Texto Principal**: `#212529` (text-dark)
* **Texto Secundário**: `#6c757d` (text-muted)

### Tipografia
* **Font-weight 900** para títulos e CTAs principais (`fw-900`)
* **Font-weight Bold** para subtítulos (`fw-bold`)
* **Base font-size**: 14px (Bootstrap default)
* **Hero titles**: `display-4` com `line-height: 1.06`

### Espaçamento
* **Containers**: `container-fluid` para layouts full-width
* **Margens**: Usar escala Bootstrap (`mt-3`, `mb-5`, etc.)
* **Cards**: `shadow-sm` e `rounded-4` para consistência
* **Buttons**: `rounded-pill` ou `rounded-0.9rem` para CTAs

## Componentes Específicos

### Navbar
* **Estilo**: `navbar-light bg-white border-bottom shadow-sm`
* **Brand**: Ícone `fa-seedling` + texto "AgroKongo"
* **Links**: `nav-link` sem underline
* **Perfil**: Imagem circular 30x30px com `border-radius: 50%`

### Cards de Safras
* **Estrutura**: `card h-100 shadow-sm rounded-4 border-0 overflow-hidden`
* **Imagem**: 200px height com `object-fit: cover`
* **Status**: Badges posicionados `position-absolute top-0 end-0 m-3`
* **Preços**: `fw-900 text-success` para valores
* **Produtor**: Avatar 30x30px + rating com estrelas

### Botões
* **Primário**: `btn btn-success fw-900` (verde AgroKongo)
* **Secundário**: `btn btn-outline-success fw-900`
* **Terciário**: `btn btn-link fw-900` (sem bordas)
* **Tamanhos**: `btn-sm` para formulários, default para CTAs

### Formulários
* **Campos**: Usar componente `form_field.html`
* **Validação**: Classes `is-invalid` para erros
* **Labels**: Sempre associados com `for` attribute
* **Placeholders**: Descritivos e em português

### Footer
* **Gradiente**: `linear-gradient(135deg, #081c15 0%, #1b4332 100%)`
* **Texto**: `text-light` com `text-white-50` para secundários
* **Links**: `link-light text-decoration-none`
* **Social**: Ícones com `hover-opacity` transition

## Padrões de Layout

### Hero Sections
* **Gradiente**: `radial-gradient(120% 120% at 0% 0%, #1b4332 0%, #081c15 100%)`
* **Texto**: `text-white` e `text-white-75`
* **Badges**: `badge-uf` com background `rgba(255,255,255,.12)`
* **CTAs**: `big-cta` com padding generoso

### Grid System
* **12-column** Bootstrap grid
* **Gutters**: `g-2`, `g-4` para espaçamento consistente
* **Cards**: `col-12 col-md-6 col-lg-4` para responsividade

### Alertas
* **Flash messages**: `alert alert-dismissible fade show`
* **Cores**: `alert-success`, `alert-danger`, `alert-warning`
* **Posição**: Topo da página com `container-fluid mt-3`

## Animações e Interações

### Transições
* **Hover**: `hover-opacity` para social links
* **Fade-in**: `animation: fadeIn .4s ease both`
* **Cards**: `shadow-sm` com hover `shadow-lg`

### Micro-interactions
* **Buttons**: Transform sutil no hover
* **Cards**: Elevação com shadow increase
* **Links**: Subtle underline no hover

## Breakpoints e Responsividade

* **Mobile**: `< 768px` - Stack vertical, full-width cards
* **Tablet**: `768px - 992px` - 2 columns grid
* **Desktop**: `> 992px` - 3-4 columns grid

### Hidden/Visible Classes
* **Mobile only**: `d-block d-md-none`
* **Desktop only**: `d-none d-md-block`

## Validação de Dados Angolanos

### Formatos Específicos
* **Telemóvel**: Pattern `^9[1-9]\d{7}$` (9 dígitos, começa com 9)
* **NIF**: 10 dígitos com checksum
* **IBAN**: `AO06` + 21 dígitos

## Componentes Reutilizáveis

### Macros Disponíveis
* `card_safra()` - Cards de produtos no marketplace
* `button_primary()` - Botões padronizados
* `form_field()` - Campos de formulário universais

### Includes Recomendados
* `layout/footer.html` - Rodapé global
* `components/alert.html` - Alertas consistentes
* `components/pagination_custom.html` - Paginação estilizada

## Performance e Otimização

* **CDN**: Bootstrap e Font Awesome via CDN
* **Imagens**: Sempre com `object-fit: cover` e alt text
* **CSS**: Mínimo inline, preferir classes
* **JavaScript**: Bootstrap bundle + custom scripts no final

## Convenções de Nomenclatura

* **Classes**: kebab-case (`card-safra`, `hero-wave`)
* **IDs**: camelCase (`userMenu`, `notifBadge`)
* **Templates**: snake_case (`detalhes_safra.html`)
* **Blocos**: `{% block content %}`, `{% block extra_css %}`

## Boas Práticas Específicas

* **Sempre** extender `base.html` como template base
* **Usar** `{% with %}` para passar variáveis a includes
* **Manter** lógica complexa nos routes, não nos templates
* **Comentar** código complexo com `{# #}`
* **Validar** presença de variáveis com `is defined`
* **Usar** filtros Jinja2 para formatação (`formatar_moeda_kz`)

## Internacionalização

* **Idioma**: Português de Angola (`pt-PT`)
* **Moeda**: Kwanza (Kz) com formatação própria
* **Datas**: Formato `DD/MM/YYYY` localizado
* **Números**: Separador decimal vírgula, milhar ponto
