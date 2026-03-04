import { useState, useEffect } from 'react';
import Head from 'next/head';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAuth } from '../../hooks/useAuth';

function MinhasComprasPage() {
  const [compras, setCompras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ativas'); // 'ativas' ou 'historico'

  const { user } = useAuth();

  useEffect(() => {
    async function fetchCompras() {
      if (!user) return;
      setLoading(true);

      const statusMap = {
        ativas: 'PENDENTE,AGUARDANDO_PAGAMENTO,ANALISE,ESCROW,ENVIADO,DISPUTA',
        historico: 'ENTREGUE,FINALIZADO,CANCELADO'
      };

      try {
        const res = await fetch(`/api/comprador/minhas-compras?status=${statusMap[statusFilter]}`);
        const data = await res.json();

        if (data.ok) {
          setCompras(data.compras);
        } else {
          setError('Falha ao carregar compras.');
        }
      } catch (err) {
        setError('Erro de conexão.');
      } finally {
        setLoading(false);
      }
    }

    fetchCompras();
  }, [user, statusFilter]);

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
        <title>Minhas Compras | AgroKongo</title>
      </Head>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Minhas Compras</h1>

        <div className="mb-4 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setStatusFilter('ativas')}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${statusFilter === 'ativas' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
            >
              Compras Ativas
            </button>
            <button
              onClick={() => setStatusFilter('historico')}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${statusFilter === 'historico' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
            >
              Histórico
            </button>
          </nav>
        </div>

        {loading ? (
          <div className="text-center py-10">Carregando...</div>
        ) : error ? (
          <div className="text-center text-red-600 py-10">{error}</div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul role="list" className="divide-y divide-gray-200">
              {compras.map((compra) => (
                <li key={compra.id}>
                  <a href="#" className="block hover:bg-gray-50">
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-green-600 truncate">
                          {compra.safra.produto.nome}
                        </p>
                        <div className="ml-2 flex-shrink-0 flex">
                          <StatusBadge status={compra.status} />
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">
                            Ref: {compra.fatura_ref}
                          </p>
                          <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                            Vendedor: {compra.vendedor.nome}
                          </p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>
                            {new Date(compra.data_criacao).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default function MinhasCompras() {
  return (
    <ProtectedRoute>
      <MinhasComprasPage />
    </ProtectedRoute>
  );
}
