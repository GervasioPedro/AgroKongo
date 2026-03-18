"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { useRouter } from "next/navigation";

export default function AdminFinanceiroPage() {
  const router = useRouter();
  const [tarefas, setTarefas] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // 1. Validar Sessão
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

    fetchTarefas();
  }, [router]);

  const fetchTarefas = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:5000/api/v1/admin/tarefas", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setTarefas(json.data);
      }
    } catch (e) {
      console.error("Erro ao carregar tarefas", e);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessar = async (id: number, acao: 'validar' | 'rejeitar' | 'liquidar') => {
    let motivo = "";
    if (acao === 'rejeitar') {
      motivo = prompt("Motivo da rejeição:") || "";
      if (!motivo) return; // Cancelar se não der motivo
    } else {
      if (!confirm(`Confirma a ação de ${acao.toUpperCase()}?`)) return;
    }

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/v1/admin/transacoes/${id}/processar`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ acao, motivo })
      });

      const json = await res.json();

      if (json.success) {
        alert(json.message);
        fetchTarefas(); // Atualiza listas
      } else {
        alert(json.error || "Erro ao processar.");
      }
    } catch (e) {
      console.error("Erro na ação", e);
      alert("Erro de comunicação.");
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="md:flex md:items-center md:justify-between mb-8">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Gestão Financeira
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Validação de pagamentos e liquidação de produtores.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="text-center p-10">A carregar dados financeiros...</div>
        ) : (
          <div className="space-y-10">

            {/* Secção 1: Validação de Pagamentos */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 border-b border-gray-200 sm:px-6 flex justify-between items-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  📥 Validar Pagamentos (Comprovativos Recebidos)
                </h3>
                <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                  {tarefas?.validacoes.length || 0} Pendentes
                </span>
              </div>

              {tarefas?.validacoes && tarefas.validacoes.length > 0 ? (
                <ul className="divide-y divide-gray-200">
                  {tarefas.validacoes.map((t: any) => (
                    <li key={t.id} className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-indigo-600 truncate">{t.ref}</p>
                          <p className="text-sm text-gray-500">Comprador: {t.comprador}</p>
                          <p className="text-sm font-bold text-gray-900 mt-1">
                            {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(t.valor)}
                          </p>
                        </div>
                        <div className="flex gap-2">
                           {t.comprovativo && (
                             <a
                               href={`http://localhost:5000${t.comprovativo}`}
                               target="_blank"
                               rel="noopener noreferrer"
                               className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                             >
                               📄 Ver Talão
                             </a>
                           )}
                           <button
                             onClick={() => handleProcessar(t.id, 'rejeitar')}
                             className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200"
                           >
                             Rejeitar
                           </button>
                           <button
                             onClick={() => handleProcessar(t.id, 'validar')}
                             className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                           >
                             Validar
                           </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-6 text-center text-gray-500 text-sm">Nenhum pagamento pendente de validação.</div>
              )}
            </div>

            {/* Secção 2: Liquidações Pendentes */}
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 border-b border-gray-200 sm:px-6 flex justify-between items-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  💸 Liquidações a Produtores (Transferências Bancárias)
                </h3>
                <span className="bg-red-100 text-red-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                  {tarefas?.liquidacoes.length || 0} A Pagar
                </span>
              </div>

              {tarefas?.liquidacoes && tarefas.liquidacoes.length > 0 ? (
                <ul className="divide-y divide-gray-200">
                  {tarefas.liquidacoes.map((t: any) => (
                    <li key={t.id} className="px-4 py-4 sm:px-6">
                      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div>
                          <p className="text-sm font-medium text-indigo-600 truncate">{t.ref}</p>
                          <p className="text-sm text-gray-500">Produtor: <strong>{t.produtor}</strong></p>
                          <p className="text-xs text-gray-400">IBAN: {t.iban || "Não informado"}</p>
                        </div>

                        <div className="text-right">
                          <p className="text-xs text-gray-500">Comissão (5%): {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(t.comissao)}</p>
                          <p className="text-lg font-bold text-green-600">
                            A Transferir: {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(t.valor_liquido)}
                          </p>
                        </div>

                        <div>
                           <button
                             onClick={() => handleProcessar(t.id, 'liquidar')}
                             className="w-full sm:w-auto inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none"
                           >
                             Confirmar Transferência
                           </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-6 text-center text-gray-500 text-sm">Todos os produtores estão pagos.</div>
              )}
            </div>

          </div>
        )}
      </main>
    </div>
  );
}