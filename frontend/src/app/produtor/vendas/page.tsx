"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { useRouter } from "next/navigation";

export default function VendasProdutorPage() {
  const router = useRouter();
  const [vendas, setVendas] = useState<any[]>([]);
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
    if (parsedUser.tipo !== "produtor") {
      router.push("/dashboard");
      return;
    }
    setUser(parsedUser);

    fetchVendas();
  }, [router]);

  // 2. Carregar Vendas da API
  const fetchVendas = async () => {
    try {
      const token = localStorage.getItem("token");
      // Aqui usamos o endpoint do dashboard para obter as vendas, mas idealmente teríamos um /api/v1/produtor/vendas com paginação
      // Como o dashboard retorna apenas as últimas 5, vou ajustar para usar o endpoint correcto se existir ou simular com o dashboard por agora
      // NOTA: Vou usar o dashboard_produtor para simplificar, mas num cenário real teríamos uma rota dedicada
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/v1/dashboard/produtor`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setVendas(json.data.ultimas_vendas); // Para MVP serve, mas limita a 5 itens.
      }
    } catch (e) {
      console.error("Erro ao carregar vendas", e);
    } finally {
      setLoading(false);
    }
  };

  // 3. Ações do Produtor (Aceitar, Recusar, Enviar)
  const handleAcao = async (id: number, acao: 'aceitar' | 'recusar' | 'enviar') => {
    if (!confirm(`Tem a certeza que deseja ${acao} este pedido?`)) return;

    try {
      const token = localStorage.getItem("token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/v1/produtor/transacoes/${id}/status`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ acao })
      });

      const json = await res.json();

      if (json.success) {
        alert(json.message);
        fetchVendas(); // Atualiza a lista
      } else {
        alert(json.error || "Erro ao processar ação.");
      }
    } catch (e) {
      console.error("Erro na ação", e);
      alert("Erro de comunicação com o servidor.");
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
              Gestão de Encomendas
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Acompanhe e gira os pedidos recebidos.
            </p>
          </div>
        </div>

        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          {loading ? (
             <div className="p-10 text-center">A carregar vendas...</div>
          ) : vendas.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {vendas.map((venda) => (
                <li key={venda.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-green-600 truncate">
                        {venda.produto}
                      </p>
                      <div className="ml-2 flex-shrink-0 flex">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                          ${venda.status === 'Pendente' ? 'bg-yellow-100 text-yellow-800' :
                            venda.status === 'Pago (Escrow)' ? 'bg-blue-100 text-blue-800' :
                            venda.status === 'Entregue' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'}`}>
                          {venda.status}
                        </span>
                      </div>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between">
                      <div className="sm:flex">
                        <p className="flex items-center text-sm text-gray-500 mr-6">
                          👤 {venda.comprador}
                        </p>
                        <p className="flex items-center text-sm text-gray-500">
                          💰 {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(venda.valor)}
                        </p>
                      </div>
                      <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                        📅 {new Date(venda.data).toLocaleDateString()}
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="mt-4 flex justify-end gap-2 border-t pt-4">
                      {venda.status === 'Pendente' && (
                        <>
                          <button
                            onClick={() => handleAcao(venda.id, 'recusar')}
                            className="inline-flex items-center px-3 py-1.5 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 focus:outline-none"
                          >
                            Recusar
                          </button>
                          <button
                            onClick={() => handleAcao(venda.id, 'aceitar')}
                            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none"
                          >
                            Aceitar Pedido
                          </button>
                        </>
                      )}

                      {venda.status === 'Pago (Escrow)' && (
                        <button
                          onClick={() => handleAcao(venda.id, 'enviar')}
                          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 focus:outline-none"
                        >
                          Confirmar Envio
                        </button>
                      )}

                      {/* Outros estados são informativos */}
                      {['Aguardando Pagamento', 'Em Análise'].includes(venda.status) && (
                         <span className="text-xs text-gray-500 italic">Aguardando ação do comprador/admin...</span>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-10 text-center text-gray-500">
              Não existem vendas recentes para mostrar.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}