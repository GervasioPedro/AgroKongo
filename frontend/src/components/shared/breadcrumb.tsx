"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/utils/cn";

export function Breadcrumb() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const breadcrumbMap: Record<string, string> = {
    dashboard: "Dashboard",
    mercado: "Mercado",
    produtor: "Minhas Safras",
    comprador: "Compras",
    admin: "Administração",
    vendas: "Vendas",
    carteira: "Carteira",
    perfil: "Perfil",
    notificacoes: "Notificações",
    configuracoes: "Configurações",
    transacao: "Transação",
    validacoes: "Validações",
    usuarios: "Usuários",
    transacoes: "Transações",
  };

  if (segments.length === 0) return null;

  return (
    <nav className="flex items-center gap-2 text-sm text-slate-600 mb-4">
      <Link href="/" className="hover:text-agro-primary transition-colors">
        <Home className="h-4 w-4" />
      </Link>
      {segments.map((segment, index) => {
        const href = "/" + segments.slice(0, index + 1).join("/");
        const isLast = index === segments.length - 1;
        const label = breadcrumbMap[segment] || segment;

        return (
          <div key={segment} className="flex items-center gap-2">
            <ChevronRight className="h-4 w-4" />
            {isLast ? (
              <span className="font-medium text-slate-900">{label}</span>
            ) : (
              <Link href={href} className="hover:text-agro-primary transition-colors">
                {label}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
