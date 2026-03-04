import { useState, useEffect } from 'react';
import ProtectedRoute from '../../components/ProtectedRoute';
import AdminLayout from '../../components/AdminLayout'; // Importar o novo layout
import toast from 'react-hot-toast';

function AdminDashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch('/api/admin/dashboard-stats');
        const data = await res.json();
        if (data.ok) setStats(data.stats);
        else toast.error("Falha ao carregar estatísticas.");
      } catch (err) {
        toast.error("Erro de conexão.");
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading) return <div className="p-8 text-center">Carregando...</div>;

  return (
    <AdminLayout title="Dashboard">
      <h2 className="text-3xl font-semibold text-gray-800 mb-6">Visão Geral</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Card 1 */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <p className="text-sm font-medium text-gray-500">Volume Total de Vendas</p>
          <p className="text-2xl font-semibold text-gray-700 mt-1">
            {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(stats?.total_vendas || 0)}
          </p>
        </div>

        {/* Card 2 */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <p className="text-sm font-medium text-gray-500">Utilizadores Ativos</p>
          <p className="text-2xl font-semibold text-gray-700 mt-1">{stats?.total_utilizadores || 0}</p>
        </div>

        {/* Card 3 */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <p className="text-sm font-medium text-gray-500">Pagamentos a Validar</p>
          <p className="text-2xl font-semibold text-gray-700 mt-1">{stats?.pagamentos_a_validar || 0}</p>
        </div>

        {/* Card 4 */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <p className="text-sm font-medium text-gray-500">Comissão Acumulada</p>
          <p className="text-2xl font-semibold text-gray-700 mt-1">
            {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(stats?.comissao_total || 0)}
          </p>
        </div>
      </div>

      {/* Aqui entrariam as tabelas de transações recentes, etc. */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Ações Rápidas</h3>
        <p className="text-gray-500">Selecione uma opção no menu lateral para gerir o sistema.</p>
      </div>
    </AdminLayout>
  );
}

export default function AdminDashboard() {
  return (
    <ProtectedRoute>
      <AdminDashboardPage />
    </ProtectedRoute>
  );
}
