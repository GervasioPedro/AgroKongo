"use client";

import { useAuth } from "@/hooks/useAuth";
import { Sidebar } from "@/components/shared/sidebar";
import { BottomNav } from "@/components/shared/bottom-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth(true);

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

  if (!user) return null;

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
