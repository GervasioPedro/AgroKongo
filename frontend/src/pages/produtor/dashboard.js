import { useState, useEffect } from 'react';
import Head from 'next/head';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAuth } from '../../hooks/useAuth';
import toast from 'react-hot-toast';

function ProdutorDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    fetchDashboardData();
  }, [user]);

  const fetchDashboardData = async () => {
    if (!user) return;
    try {
      const res = await fetch('/api/produtor/dashboard');
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

  const handleAction = async (url, successMessage) => {
    if (!confirm('Tem certeza que deseja executar esta ação?')) return;
    try {
      const res = await fetch(url, { method: 'POST' });
      const result = await res.json();
      if (result.ok) {
        toast.success(successMessage);
        fetchDashboardData(); // Recarrega os dados
      } else {
        toast.error(result.message);
      }
    } catch (err) {
      toast.error('Erro de conexão.');
    }
  };

  if (loading) return <div className="p-8 text-center">Carregando Dashboard...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Não foi possível carregar os dados.</div>;

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Dashboard Produtor | AgroKongo</title>
      </Head>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Meu Painel de Produtor</h1>

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* ... (Cards de KPIs como no Admin, mas com dados do produtor) ... */}
        </div>

        {/* Lista de Reservas Pendentes */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Novas Reservas (Aguardando sua Ação)</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Aceite ou recuse os pedidos para os seus produtos.</p>
          </div>
          <div className="border-t border-gray-200">
            <ul role="list" className="divide-y divide-gray-200">
              {data.listas.reservas.length > 0 ? data.listas.reservas.map((reserva) => (
                <li key={reserva.id} className="p-4 sm:p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-green-600">{reserva.produto}</p>
                      <p className="text-sm text-gray-500">{reserva.quantidade} kg por {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(reserva.valor)}</p>
                      <p className="text-xs text-gray-400">Ref: {reserva.fatura_ref}</p>
                    </div>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => handleAction(`/api/produtor/aceitar-reserva/${reserva.id}`, 'Reserva aceite!')}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
                      >
                        Aceitar
                      </button>
                      <button
                        onClick={() => handleAction(`/api/produtor/recusar-reserva/${reserva.id}`, 'Reserva recusada.')}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                      >
                        Recusar
                      </button>
                    </div>
                  </div>
                </li>
              )) : (
                <li className="p-6 text-center text-gray-500">Nenhuma reserva pendente.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Outras listas (Vendas Ativas, Histórico) podem ser adicionadas aqui */}
      </div>
    </div>
  );
}

export default function ProdutorDashboard() {
  return (
    <ProtectedRoute>
      <ProdutorDashboardPage />
    </ProtectedRoute>
  );
}
