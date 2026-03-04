import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import AdminLayout from '../../../components/AdminLayout';
import ProtectedRoute from '../../../components/ProtectedRoute';
import toast from 'react-hot-toast';
import StatusBadge from '../../../components/StatusBadge';

function DetalhesUsuarioPage() {
  const router = useRouter();
  const { id } = router.query;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchUserDetails();
    }
  }, [id]);

  const fetchUserDetails = async () => {
    try {
      const res = await fetch(`/api/admin/usuario/${id}`);
      const result = await res.json();
      if (result.ok) {
        setData(result);
      } else {
        toast.error('Falha ao carregar detalhes do utilizador.');
      }
    } catch (err) {
      toast.error('Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <AdminLayout title="Carregando..."><div className="text-center">Carregando...</div></AdminLayout>;
  if (!data) return <AdminLayout title="Erro"><div className="text-center text-red-500">Utilizador não encontrado.</div></AdminLayout>;

  const { usuario, transacoes, logs } = data;

  return (
    <AdminLayout title={`Detalhes de ${usuario.nome}`}>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-3xl font-semibold text-gray-800">{usuario.nome}</h2>
          <p className="text-gray-500">{usuario.email} | {usuario.telemovel}</p>
        </div>
        <StatusBadge status={usuario.conta_validada ? 'Validado' : 'Pendente'} />
      </div>

      {/* ... (Mais detalhes do perfil do utilizador aqui) ... */}

      <div className="mt-8">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Histórico de Transações</h3>
        <div className="bg-white shadow overflow-x-auto sm:rounded-lg">
          {/* Tabela de transações semelhante à da página de transações */}
        </div>
      </div>

      <div className="mt-8">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Logs de Auditoria</h3>
        <div className="bg-white shadow overflow-x-auto sm:rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ação</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detalhes</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(log.data_criacao).toLocaleString('pt-AO')}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.acao}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 max-w-md truncate">{log.detalhes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  );
}

export default function DetalhesUsuario() {
  return (
    <ProtectedRoute>
      <DetalhesUsuarioPage />
    </ProtectedRoute>
  );
}
