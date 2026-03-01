"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Home, ShoppingBag, Package, Wallet, User } from "lucide-react";
import { cn } from "@/utils/cn";

type NavItem = {
  href: string;
  icon: React.ReactNode;
  label: string;
};

const produtorNav: NavItem[] = [
  { href: "/dashboard", icon: <Home className="h-5 w-5" />, label: "Início" },
  { href: "/produtor", icon: <Package className="h-5 w-5" />, label: "Safras" },
  { href: "/dashboard/vendas", icon: <ShoppingBag className="h-5 w-5" />, label: "Vendas" },
  { href: "/dashboard/carteira", icon: <Wallet className="h-5 w-5" />, label: "Carteira" },
  { href: "/dashboard/perfil", icon: <User className="h-5 w-5" />, label: "Perfil" },
];

const compradorNav: NavItem[] = [
  { href: "/comprador", icon: <Home className="h-5 w-5" />, label: "Início" },
  { href: "/mercado", icon: <ShoppingBag className="h-5 w-5" />, label: "Mercado" },
  { href: "/comprador/compras", icon: <Package className="h-5 w-5" />, label: "Compras" },
  { href: "/dashboard/perfil", icon: <User className="h-5 w-5" />, label: "Perfil" },
];

export function BottomNav({ tipo = "produtor" }: { tipo?: "produtor" | "comprador" }) {
  const pathname = usePathname();
  const navItems = tipo === "produtor" ? produtorNav : compradorNav;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-4 py-3 safe-bottom z-50">
      <div className="max-w-md mx-auto flex items-center justify-around">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 transition-colors",
                isActive ? "text-agro-primary" : "text-slate-400 hover:text-slate-600"
              )}
            >
              {item.icon}
              <span className="text-xs font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
