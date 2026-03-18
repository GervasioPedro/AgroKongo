"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ShoppingBag,
  Sprout,
  Settings,
  LogOut,
  Menu,
  X,
  Bell,
  Search,
  User,
  FileText,
  ShieldCheck,
  HelpCircle
} from 'lucide-react';

interface DashboardLayoutProps {
  children: React.ReactNode;
  user: any;
  title: string;
}

export default function DashboardLayout({ children, user, title }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/auth/login");
  };

  // Menu corrigido com rotas existentes ou planeadas
  const menuItems = [
    { icon: LayoutDashboard, label: "Visão Geral", href: "/dashboard", roles: ['all'] },
    // { icon: Sprout, label: "Minhas Safras", href: "/produtor/safras", roles: ['produtor'] }, // TODO: Criar página
    { icon: Sprout, label: "Nova Safra", href: "/produtor/nova-safra", roles: ['produtor'] }, // Atalho útil
    { icon: ShoppingBag, label: "Encomendas", href: "/produtor/vendas", roles: ['produtor'] },
    { icon: ShoppingBag, label: "Minhas Compras", href: "/comprador/minhas-compras", roles: ['comprador'] },
    { icon: Search, label: "Ir ao Mercado", href: "/mercado", roles: ['comprador', 'produtor', 'admin'] },
    // Admin centralizado no Dashboard por enquanto
  ];

  // Filtra itens pelo papel do usuário
  const filteredMenu = menuItems.filter(item =>
    item.roles.includes('all') || item.roles.includes(user.tipo)
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-900/50 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-72 bg-white border-r border-gray-100 transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="h-full flex flex-col">
          {/* Logo Area */}
          <div className="h-20 flex items-center px-8 border-b border-gray-50">
            <Link href="/" className="flex items-center gap-2">
              <div className="bg-green-600 p-1.5 rounded-lg">
                <span className="text-white font-bold text-lg">AK</span>
              </div>
              <span className="font-bold text-xl tracking-tight text-gray-900">
                AGRO<span className="text-green-600">KONGO</span>
              </span>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            <p className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
              Menu Principal
            </p>
            {filteredMenu.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200
                    ${isActive
                      ? 'bg-green-50 text-green-700 shadow-sm'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
                  `}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon size={20} className={isActive ? 'text-green-600' : 'text-gray-400'} />
                  {item.label}
                </Link>
              );
            })}

            <p className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mt-8 mb-4">
              Conta
            </p>
            {/* Link temporariamente desativado ou a apontar para dashboard até a página existir */}
            {/*
            <Link
              href="/perfil"
              className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-600 rounded-xl hover:bg-gray-50 hover:text-gray-900"
            >
              <User size={20} className="text-gray-400" />
              Meu Perfil
            </Link>
            */}
            <Link
              href="/ajuda"
              className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-600 rounded-xl hover:bg-gray-50 hover:text-gray-900"
              onClick={() => setSidebarOpen(false)}
            >
              <HelpCircle size={20} className="text-gray-400" />
              Ajuda & Suporte
            </Link>
          </nav>

          {/* User Profile Snippet (Bottom) */}
          <div className="p-4 border-t border-gray-50">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 border border-gray-100">
              <div className="h-10 w-10 rounded-full bg-white flex items-center justify-center text-green-700 font-bold border border-gray-200 shadow-sm overflow-hidden">
                 {user.foto_perfil && user.foto_perfil !== 'default_user.jpg' ? (
                    <img src={`http://localhost:5000${user.foto_perfil}`} alt="Perfil" className="h-full w-full object-cover" />
                  ) : (
                    user.nome.charAt(0)
                  )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.nome}</p>
                <p className="text-xs text-gray-500 truncate capitalize">{user.tipo}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-red-500 transition-colors"
                title="Sair"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-gray-100 h-20 flex items-center justify-between px-4 sm:px-6 lg:px-8 sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-gray-500 hover:text-gray-700"
            >
              <Menu size={24} />
            </button>
            <h1 className="text-xl font-bold text-gray-800">{title}</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center text-green-700 font-bold text-sm">
              {user.nome.charAt(0)}
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}