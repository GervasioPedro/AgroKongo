"use client";

import { useAuth } from "@/hooks/useAuth";
import { Sidebar } from "@/components/shared/sidebar";
import { BottomNav } from "@/components/shared/bottom-nav";
import { notFound } from "next/navigation";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, errorType, refresh } = useAuth(true);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-agro-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-600">A carregar...</p>
        </div>
      </div>
    );
  }

  if (errorType === "network") {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <h2 className="text-xl font-semibold mb-2">Falha na ligacao</h2>
          <p className="text-slate-600 mb-4">Nao conseguimos validar a tua sessao. Verifica a internet e tenta novamente.</p>
          <button
            onClick={refresh}
            className="inline-flex items-center justify-center rounded-[12px] bg-agro-primary px-4 py-2 text-white font-medium shadow"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  if (!user) return null;

  // Guarda por papel: este segmento destina-se ao produtor
  if (user.tipo !== "produtor") {
    notFound();
  }

  return (
    <div className="min-h-screen bg-surface-neutral">
      <Sidebar tipo={user.tipo} />
      <div className="lg:pl-64">
        <main className="min-h-screen pb-20 lg:pb-6">
          {children}
        </main>
      </div>
      <div className="lg:hidden">
        <BottomNav tipo={user.tipo} />
      </div>
    </div>
  );
}
