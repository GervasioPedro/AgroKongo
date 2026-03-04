import { useState, useEffect } from 'react';
import Head from 'next/head';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAuth } from '../../hooks/useAuth';
import StatusBadge from '../../components/StatusBadge';
import Link from 'next/link';

function MinhasVendasPage() {
  const [vendas, setVendas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ativas');
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchVendas();
    }
  }, [user, statusFilter]);

  const fetchVendas = async () => {
    setLoading(true);
    const statusMap = {
      pendentes: 'PENDENTE',
      ativas: 'AGUARDANDO_PAGAMENTO,ANALISE,ESCROW,ENVIADO',
      historico: 'ENTREGUE,FINALIZADO,CANCELADO,DISPUTA'
    };
    try {
      const res = await fetch(`/api/produtor/minhas-vendas?status=${statusMap[statusFilter]}`);
      const data = await res.json();
      if (data.ok) {
        setVendas(data.vendas);
      } else {
        setError('Falha ao carregar vendas.');
      }
    } catch (err) {
      setError('Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Minhas Vendas | AgroKongo</title>
      </Head>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Minhas Vendas</h1>

        <div className="mb-4 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button onClick={() => setStatusFilter('pendentes')} className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${statusFilter === 'pendentes' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
              Reservas
            </button>
            <button onClick={() => setStatusFilter('ativas')} className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${statusFilter === 'ativas' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
              Vendas Ativas
            </button>
            <button onClick={() => setStatusFilter('historico')} className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${statusFilter === 'historico' ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
              Histórico
            </button>
          </nav>
        </div>

        {loading ? (
          <div className="text-center py-10">Carregando...</div>
        ) : error ? (
          <div className="text-center text-red-600 py-10">{error}</div>
        ) : vendas.length === 0 ? (
          <div className="text-center py-10 bg-white rounded-lg shadow">
            <h3 className="text-xl font-medium text-gray-900">Nenhuma venda encontrada</h3>
            <p className="mt-1 text-gray-500">Não há vendas nesta categoria.</p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul role="list" className="divide-y divide-gray-200">
              {vendas.map((venda) => (
                <li key={venda.id}>
                  <Link href={`/produtor/venda/${venda.id}`} className="block hover:bg-gray-50">
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-green-600 truncate">{venda.safra.produto.nome}</p>
                        <div className="ml-2 flex-shrink-0 flex">
                          <StatusBadge status={venda.status} />
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">Ref: {venda.fatura_ref}</p>
                          <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">Comprador: {venda.comprador.nome}</p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>{new Date(venda.data_criacao).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default function MinhasVendas() {
  return (
    <ProtectedRoute>
      <MinhasVendasPage />
    </ProtectedRoute>
  );
}
