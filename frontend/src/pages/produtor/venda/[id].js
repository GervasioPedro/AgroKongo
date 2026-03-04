import { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import ProtectedRoute from '../../../components/ProtectedRoute';
import toast from 'react-hot-toast';
import StatusBadge from '../../../components/StatusBadge';

function DetalhesVendaPage() {
  const router = useRouter();
  const { id } = router.query;
  const [venda, setVenda] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchVenda();
    }
  }, [id]);

  const fetchVenda = async () => {
    try {
      const res = await fetch(`/api/produtor/venda/${id}`);
      const data = await res.json();
      if (data.ok) {
        setVenda(data.venda);
      } else {
        toast.error('Não foi possível carregar os detalhes da venda.');
      }
    } catch (err) {
      toast.error('Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmarEnvio = async () => {
    if (!confirm('Confirma que já enviou a mercadoria para o comprador?')) return;
    try {
      const res = await fetch(`/api/produtor/confirmar-envio/${id}`, { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        toast.success(data.message);
        fetchVenda(); // Recarrega os dados
      } else {
        toast.error(data.message);
      }
    } catch (err) {
      toast.error('Erro ao confirmar o envio.');
    }
  };

  if (loading) return <div className="p-8 text-center">Carregando...</div>;
  if (!venda) return <div className="p-8 text-center text-red-500">Venda não encontrada.</div>;

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Detalhes da Venda {venda.fatura_ref} | AgroKongo</title>
      </Head>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Detalhes da Venda</h1>
            <p className="text-gray-500">Ref: {venda.fatura_ref}</p>
          </div>
          <StatusBadge status={venda.status} />
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-800">Produto</h3>
              <p>{venda.safra.produto.nome}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Comprador</h3>
              <p>{venda.comprador.nome}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Quantidade</h3>
              <p>{venda.quantidade_comprada} kg</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Valor Bruto</h3>
              <p>{new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(venda.valor_total_pago)}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Comissão AgroKongo</h3>
              <p>{new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(venda.comissao_plataforma)}</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">Valor Líquido a Receber</h3>
              <p className="font-bold text-green-600">{new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(venda.valor_liquido_vendedor)}</p>
            </div>
          </div>

          {/* Ação Condicional */}
          {venda.status === 'ESCROW' && (
            <div className="mt-8 border-t pt-6">
              <h2 className="text-xl font-semibold mb-4">Ação Requerida</h2>
              <p className="mb-4 text-gray-600">O pagamento do comprador foi validado e está seguro connosco (Escrow). Por favor, envie a mercadoria e confirme o envio.</p>
              <button
                onClick={handleConfirmarEnvio}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 font-medium"
              >
                Confirmar Envio da Mercadoria
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DetalhesVenda() {
  return (
    <ProtectedRoute>
      <DetalhesVendaPage />
    </ProtectedRoute>
  );
}
