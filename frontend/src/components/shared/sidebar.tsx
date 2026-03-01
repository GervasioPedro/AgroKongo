"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/utils/cn";
import { 
  Home, ShoppingBag, Package, Wallet, User, 
  Settings, Bell, LogOut, Sprout, BarChart3,
  Shield, Users
} from "lucide-react";

type NavItem = {
  href: string;
  icon: React.ReactNode;
  label: string;
  badge?: number;
};

const produtorNav: NavItem[] = [
  { href: "/dashboard", icon: <Home className="h-5 w-5" />, label: "Dashboard" },
  { href: "/produtor", icon: <Package className="h-5 w-5" />, label: "Minhas Safras" },
  { href: "/dashboard/vendas", icon: <ShoppingBag className="h-5 w-5" />, label: "Vendas" },
  { href: "/dashboard/carteira", icon: <Wallet className="h-5 w-5" />, label: "Carteira" },
  { href: "/mercado", icon: <Sprout className="h-5 w-5" />, label: "Mercado" },
];

const compradorNav: NavItem[] = [
  { href: "/comprador", icon: <Home className="h-5 w-5" />, label: "Dashboard" },
  { href: "/mercado", icon: <ShoppingBag className="h-5 w-5" />, label: "Explorar Mercado" },
  { href: "/comprador/compras", icon: <Package className="h-5 w-5" />, label: "Minhas Compras" },
  { href: "/dashboard/carteira", icon: <Wallet className="h-5 w-5" />, label: "Carteira" },
];

const adminNav: NavItem[] = [
  { href: "/admin", icon: <BarChart3 className="h-5 w-5" />, label: "Dashboard" },
  { href: "/admin/validacoes", icon: <Shield className="h-5 w-5" />, label: "Validações" },
  { href: "/admin/usuarios", icon: <Users className="h-5 w-5" />, label: "Usuários" },
  { href: "/admin/transacoes", icon: <ShoppingBag className="h-5 w-5" />, label: "Transações" },
];

const bottomNav: NavItem[] = [
  { href: "/dashboard/notificacoes", icon: <Bell className="h-5 w-5" />, label: "Notificações" },
  { href: "/dashboard/perfil", icon: <User className="h-5 w-5" />, label: "Perfil" },
  { href: "/dashboard/configuracoes", icon: <Settings className="h-5 w-5" />, label: "Configurações" },
];

export function Sidebar({ tipo = "produtor" }: { tipo?: "produtor" | "comprador" | "admin" }) {
  const pathname = usePathname();
  
  const mainNav = tipo === "admin" ? adminNav : tipo === "comprador" ? compradorNav : produtorNav;

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white border-r border-slate-200">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-6 border-b">
        <div className="h-10 w-10 rounded-xl bg-agro-primary flex items-center justify-center">
          <Sprout className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg">AgroKongo</h1>
          <p className="text-xs text-slate-500 capitalize">{tipo}</p>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {mainNav.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
                isActive 
                  ? "bg-agro-primary text-white" 
                  : "text-slate-700 hover:bg-slate-100"
              )}
            >
              {item.icon}
              <span>{item.label}</span>
              {item.badge && (
                <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Navigation */}
      <div className="px-3 py-4 border-t space-y-1">
        {bottomNav.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
                isActive 
                  ? "bg-slate-100 text-slate-900" 
                  : "text-slate-600 hover:bg-slate-50"
              )}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          );
        })}
        <button className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 w-full transition-colors">
          <LogOut className="h-5 w-5" />
          <span>Sair</span>
        </button>
      </div>
    </aside>
  );
}
