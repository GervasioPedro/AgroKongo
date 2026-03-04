import { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import ProtectedRoute from '../../../components/ProtectedRoute';
import toast from 'react-hot-toast';

function DetalhesCompraPage() {
  const router = useRouter();
  const { id } = router.query;
  const [compra, setCompra] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comprovativo, setComprovativo] = useState(null);

  useEffect(() => {
    if (id) {
      fetchCompra();
    }
  }, [id]);

  const fetchCompra = async () => {
    try {
      const res = await fetch(`/api/comprador/compra/${id}`);
      const data = await res.json();
      if (data.ok) {
        setCompra(data.compra);
      } else {
        toast.error('Não foi possível carregar os detalhes da compra.');
      }
    } catch (err) {
      toast.error('Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmeterComprovativo = async (e) => {
    e.preventDefault();
    if (!comprovativo) {
      toast.error('Por favor, selecione um ficheiro.');
      return;
    }
    const formData = new FormData();
    formData.append('comprovativo', comprovativo);

    try {
      const res = await fetch(`/api/comprador/submeter-comprovativo/${id}`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.ok) {
        toast.success(data.message);
        fetchCompra(); // Recarrega os dados
      } else {
        toast.error(data.message);
      }
    } catch (err) {
      toast.error('Erro ao submeter comprovativo.');
    }
  };

  const handleConfirmarRecebimento = async () => {
    if (!confirm('Confirma que recebeu a mercadoria em boas condições? Esta ação é irreversível.')) return;
    try {
      const res = await fetch(`/api/comprador/confirmar-recebimento/${id}`, { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        toast.success(data.message);
        fetchCompra();
      } else {
        toast.error(data.message);
      }
    } catch (err) {
      toast.error('Erro ao confirmar recebimento.');
    }
  };

  if (loading) return <div className="p-8 text-center">Carregando...</div>;
  if (!compra) return <div className="p-8 text-center text-red-500">Compra não encontrada.</div>;

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Detalhes da Compra {compra.fatura_ref} | AgroKongo</title>
      </Head>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Detalhes da Compra</h1>
        {/* ... (Exibir detalhes da compra) ... */}

        {/* Ações Condicionais */}
        {compra.status === 'AGUARDANDO_PAGAMENTO' && (
          <div className="mt-8 bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Efetuar Pagamento</h2>
            <p className="mb-4">Transfira o valor de <strong>{new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(compra.valor_total_pago)}</strong> para o IBAN da AgroKongo e submeta o comprovativo.</p>
            <form onSubmit={handleSubmeterComprovativo}>
              <input type="file" onChange={(e) => setComprovativo(e.target.files[0])} required className="mb-4" />
              <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
                Submeter Comprovativo
              </button>
            </form>
          </div>
        )}

        {compra.status === 'ENVIADO' && (
          <div className="mt-8 bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Confirmar Recebimento</h2>
            <p className="mb-4">A sua encomenda foi marcada como enviada. Por favor, confirme o recebimento assim que a receber.</p>
            <button onClick={handleConfirmarRecebimento} className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
              Eu Recebi a Mercadoria
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function DetalhesCompra() {
  return (
    <ProtectedRoute>
      <DetalhesCompraPage />
    </ProtectedRoute>
  );
}
