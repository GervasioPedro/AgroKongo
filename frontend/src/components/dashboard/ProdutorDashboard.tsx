import { useEffect, useState } from "react";
import Link from "next/link";

interface Venda {
  id: number;
  produto: string;
  quantidade: number;
  valor_total: number;
  status: string;
  comprador: string;
  data_criacao: string;
}

interface DashboardData {
  kpis: {
    receita_total: number;
    receita_pendente: number;
    receita_a_liquidar: number;
    saldo_disponivel: number;
  };
  listas: {
    reservas: Venda[];
    vendas_ativas: Venda[];
    historico: Venda[];
  };
}

export default function ProdutorDashboard({ user }: { user: any }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem("token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/dashboard/produtor`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      const json = await res.json();
      if (json.success) {
        setData(json.data);
      }
    } catch (e) {
      console.error("Erro ao carregar dashboard", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">A carregar dados...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Erro ao carregar dados.</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Cabeçalho */}
      <div className="md:flex md:items-center md:justify-between mb-8">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Painel do Produtor
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Bem-vindo de volta, {user.nome}.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4 gap-3">
          <Link href="/produtor/safras" className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none">
            Minhas Safras
          </Link>
          <Link href="/produtor/nova-safra" className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none">
            <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Nova Safra
          </Link>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {[
          { label: "Saldo Disponível", value: data.kpis.saldo_disponivel, color: "bg-green-500", icon: "💰" },
          { label: "Em Custódia", value: data.kpis.receita_pendente, color: "bg-blue-500", icon: "⏳" },
          { label: "A Liquidar", value: data.kpis.receita_a_liquidar, color: "bg-yellow-500", icon: "🏦" },
          { label: "Receita Total", value: data.kpis.receita_total, color: "bg-gray-800", icon: "📈" }
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white overflow-hidden shadow rounded-lg border-l-4 border-transparent hover:border-green-500 transition-all">
            <div className="p-5">
              <div className="flex items-center">
                <div className={`flex-shrink-0 rounded-md p-3 ${kpi.color} text-white flex items-center justify-center h-12 w-12 text-xl`}>
                  {kpi.icon}
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dt className="text-sm font-medium text-gray-500 truncate">{kpi.label}</dt>
                  <dd className="text-lg font-bold text-gray-900">
                    {kpi.value.toLocaleString('pt-AO', { style: 'currency', currency: 'AOA' })}
                  </dd>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabelas de Vendas */}
      <div className="space-y-8">

        {/* Novas Reservas */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200 bg-red-50">
            <h3 className="text-lg leading-6 font-bold text-red-800">
              Novas Reservas ({data.listas.reservas.length})
            </h3>
          </div>
          {data.listas.reservas.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {data.listas.reservas.map((venda) => (
                <li key={venda.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{venda.produto} - {venda.quantidade}kg</p>
                      <p className="text-sm text-gray-500">Comprador: {venda.comprador}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm font-bold text-green-600">
                        {venda.valor_total.toLocaleString('pt-AO', { style: 'currency', currency: 'AOA' })}
                      </span>
                      <button className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">Aceitar</button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-8 text-center text-gray-500 text-sm">Sem novas reservas pendentes.</div>
          )}
        </div>

        {/* Vendas Ativas */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Vendas em Curso</h3>
          </div>
          {data.listas.vendas_ativas.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {data.listas.vendas_ativas.map((venda) => (
                <li key={venda.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{venda.produto}</p>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {venda.status}
                      </span>
                    </div>
                    <span className="text-sm text-gray-500">{venda.data_criacao}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-8 text-center text-gray-500 text-sm">Nenhuma venda ativa.</div>
          )}
        </div>

      </div>
    </div>
  );
}