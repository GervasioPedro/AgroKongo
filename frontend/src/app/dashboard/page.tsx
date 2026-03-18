"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import ProdutorDashboard from "@/components/dashboard/ProdutorDashboard";
import CompradorDashboard from "@/components/dashboard/CompradorDashboard";
import AdminDashboard from "@/components/dashboard/AdminDashboard";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/auth/login");
      return;
    }

    try {
      const parsedUser = JSON.parse(storedUser);
      setUser(parsedUser);
    } catch (e) {
      console.error("Erro ao ler dados do utilizador", e);
      localStorage.clear();
      router.push("/auth/login");
    } finally {
      setLoading(false);
    }
  }, [router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">A carregar o seu painel...</p>
        </div>
      </div>
    );
  }

  const getDashboardTitle = () => {
    switch (user.tipo) {
      case 'admin': return 'Painel de Administração';
      case 'produtor': return 'Painel do Produtor';
      case 'comprador': return 'Painel do Comprador';
      default: return 'Visão Geral';
    }
  };

  return (
    <DashboardLayout user={user} title={getDashboardTitle()}>
      {user.tipo === "admin" && <AdminDashboard user={user} />}
      {user.tipo === "produtor" && <ProdutorDashboard user={user} />}
      {user.tipo === "comprador" && <CompradorDashboard user={user} />}
    </DashboardLayout>
  );
}