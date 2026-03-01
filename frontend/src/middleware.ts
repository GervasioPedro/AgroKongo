import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('session')?.value;
  const { pathname } = request.nextUrl;

  // Rotas públicas
  const publicRoutes = ['/', '/mercado', '/auth/login', '/auth/registo', '/sobre', '/contacto', '/termos', '/ajuda', '/faq'];
  const isPublicRoute = publicRoutes.some(route => pathname === route || pathname.startsWith('/mercado/')) 
    || pathname.startsWith('/auth/cadastro/'); // Permitir todas as etapas de cadastro

  // Se não tem token e tenta acessar rota protegida
  if (!token && !isPublicRoute) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }

  // Se tem token e tenta acessar login/registo
  if (token && (pathname === '/auth/login' || pathname === '/auth/registo')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
