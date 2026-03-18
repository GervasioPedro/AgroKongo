import { useEffect, useState } from "react";
import Link from "next/link";

interface Compra {
  id: number;
  produto: string;
  quantidade: number;
  valor_total: number;
  status: string;
  vendedor: string;
  data_criacao: string;
  previsao_entrega: string | null;
}

interface DashboardData {
  kpis: {
    total_gasto: number;
    compras_ativas: number;
  };
  listas: {
    pendentes: Compra[];
    em_transito: Compra[];
    historico: Compra[];
  };
}

export default function CompradorDashboard({ user }: { user: any }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/dashboard/comprador`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) setData(json.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-10 text-center text-gray-500">A carregar o seu painel...</div>;
  if (!data) return <div className="p-10 text-center text-red-500">Erro ao carregar dados.</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Cabeçalho */}
      <div className="md:flex md:items-center md:justify-between mb-8">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Painel do Comprador
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Bem-vindo de volta, {user.nome}.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <Link
            href="/mercado"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            Ir para o Mercado
          </Link>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg border-l-4 border-blue-500">
          <div className="p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Compras Ativas</dt>
            <dd className="mt-1 text-3xl font-bold text-gray-900">{data.kpis.compras_ativas}</dd>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg border-l-4 border-gray-800">
          <div className="p-5">
            <dt className="text-sm font-medium text-gray-500 truncate">Total Gasto</dt>
            <dd className="mt-1 text-3xl font-bold text-gray-900">
              {data.kpis.total_gasto.toLocaleString('pt-AO', { style: 'currency', currency: 'AOA' })}
            </dd>
          </div>
        </div>
      </div>

      {/* Listas de Compras */}
      <div className="space-y-8">

        {/* Ações Pendentes */}
        {data.listas.pendentes.length > 0 && (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg border border-yellow-200">
            <div className="px-6 py-5 border-b border-gray-200 bg-yellow-50">
              <h3 className="text-lg leading-6 font-bold text-yellow-800">Ações Necessárias</h3>
            </div>
            <ul className="divide-y divide-gray-200">
              {data.listas.pendentes.map((compra) => (
                <li key={compra.id} className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-gray-900">{compra.produto}</p>
                      <p className="text-xs text-gray-500">Status: {compra.status}</p>
                    </div>
                    <button className="text-sm text-blue-600 font-medium hover:underline">Ver Detalhes</button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Histórico */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Histórico de Compras</h3>
          </div>
          {data.listas.historico.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {data.listas.historico.map((compra) => (
                <li key={compra.id} className="p-6">
                  <div className="flex justify-between">
                    <p className="text-sm font-medium text-gray-900">{compra.produto}</p>
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Concluído
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-12 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">Ainda não fez compras</h3>
              <p className="mt-1 text-sm text-gray-500">Explore o mercado para encontrar produtos frescos.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}