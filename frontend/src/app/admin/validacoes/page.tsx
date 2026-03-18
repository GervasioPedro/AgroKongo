"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { CheckCircle, XCircle, User } from 'lucide-react';

const ValidarContasPage = () => {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [contas, setContas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/auth/login");
      return;
    }
    const parsedUser = JSON.parse(storedUser);
    if (parsedUser.tipo !== "admin") {
      router.push("/dashboard");
      return;
    }
    setUser(parsedUser);

    const fetchContas = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch("http://localhost:5000/api/v1/admin/usuarios/pendentes", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const json = await res.json();
        if (json.success) {
          setContas(json.data);
        } else {
          setError(json.error || "Erro ao carregar contas.");
        }
      } catch (e) {
        console.error("Erro ao carregar contas", e);
        setError("Erro de conexão ao servidor.");
      } finally {
        setLoading(false);
      }
    };

    fetchContas();
  }, [router]);

  const handleValidar = async (id: number) => {
    if (!confirm("Tem a certeza que deseja validar esta conta?")) return;

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/v1/admin/usuarios/${id}/validar`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" }
      });

      const json = await res.json();
      if (json.success) {
        alert(json.message);
        setContas(contas.filter(c => c.id !== id)); // Remove da lista
      } else {
        alert(json.error || "Erro ao validar conta.");
      }
    } catch (e) {
      console.error("Erro ao validar conta", e);
      alert("Erro de conexão ao servidor.");
    }
  };

  if (!user) return null;

  return (
    <DashboardLayout user={user} title="Validar Contas de Produtores">
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900">Contas Pendentes de Validação</h2>
        {loading ? (
          <div className="text-center text-gray-500">A carregar lista de contas...</div>
        ) : error ? (
          <div className="text-red-500">{error}</div>
        ) : contas.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {contas.map((conta) => (
              <li key={conta.id} className="py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                    {conta.foto ? (
                      <img src={`http://localhost:5000${conta.foto}`} alt="Foto de Perfil" className="h-full w-full object-cover rounded-full" />
                    ) : (
                      <User size={20} className="text-gray-500" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{conta.nome}</p>
                    <p className="text-xs text-gray-500">{conta.tipo} - {conta.telemovel || conta.email}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleValidar(conta.id)}
                    className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 transition-colors"
                  >
                    <CheckCircle size={16} className="mr-2 inline-block align-middle" /> Validar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-center text-gray-500">
            Nenhuma conta pendente de validação. 🎉
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ValidarContasPage;