import { useState, useEffect } from 'react';
import Head from 'next/head';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAuth } from '../../hooks/useAuth';
import toast from 'react-hot-toast';
import Link from 'next/link';

function CompradorDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      const res = await fetch('/api/comprador/dashboard');
      const dashboardData = await res.json();
      if (dashboardData.ok) {
        setData(dashboardData);
      } else {
        toast.error('Falha ao carregar dados do dashboard.');
      }
    } catch (err) {
      toast.error('Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Carregando Dashboard...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Não foi possível carregar os dados.</div>;

  const StatusBadge = ({ status }) => {
    const statusStyles = {
      PENDENTE: 'bg-yellow-100 text-yellow-800',
      AGUARDANDO_PAGAMENTO: 'bg-blue-100 text-blue-800',
      ANALISE: 'bg-purple-100 text-purple-800',
      ESCROW: 'bg-green-100 text-green-800',
      ENVIADO: 'bg-cyan-100 text-cyan-800',
      ENTREGUE: 'bg-green-200 text-green-900',
      FINALIZADO: 'bg-gray-200 text-gray-800',
      CANCELADO: 'bg-red-100 text-red-800',
      DISPUTA: 'bg-orange-100 text-orange-800',
    };
    return (
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Dashboard Comprador | AgroKongo</title>
      </Head>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Meu Painel de Comprador</h1>

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Gasto</h3>
            <p className="mt-1 text-3xl font-semibold text-gray-900">
              {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(data.kpis.total_gasto)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Compras Ativas</h3>
            <p className="mt-1 text-3xl font-semibold text-gray-900">{data.kpis.compras_ativas}</p>
          </div>
        </div>

        {/* Lista de Últimas Compras */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">Minhas Últimas Compras</h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">Acompanhe o estado das suas encomendas mais recentes.</p>
            </div>
            <Link href="/comprador/minhas-compras" className="text-sm font-medium text-green-600 hover:text-green-500">
              Ver todas
            </Link>
          </div>
          <div className="border-t border-gray-200">
            <ul role="list" className="divide-y divide-gray-200">
              {data.ultimas_compras.length > 0 ? data.ultimas_compras.map((compra) => (
                <li key={compra.id} className="p-4 sm:p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-green-600">{compra.safra.produto.nome}</p>
                      <p className="text-sm text-gray-500">{compra.quantidade_comprada} kg - {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(compra.valor_total_pago)}</p>
                      <p className="text-xs text-gray-400">Ref: {compra.fatura_ref}</p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <StatusBadge status={compra.status} />
                      <Link href={`/comprador/compra/${compra.id}`} className="text-sm font-medium text-indigo-600 hover:text-indigo-500">
                        Detalhes
                      </Link>
                    </div>
                  </div>
                </li>
              )) : (
                <li className="p-6 text-center text-gray-500">Nenhuma compra realizada ainda.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CompradorDashboard() {
  return (
    <ProtectedRoute>
      <CompradorDashboardPage />
    </ProtectedRoute>
  );
}
