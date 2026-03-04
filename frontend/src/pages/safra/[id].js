import Head from 'next/head';
import { useRouter } from 'next/router';
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth'; // Importar o hook de autenticação

// ... (getStaticPaths e getStaticProps permanecem os mesmos) ...
export async function getStaticPaths() {
  const res = await fetch(`${process.env.BACKEND_URL || 'http://localhost:5000'}/api/mercado/produtos?per_page=10`);
  const data = await res.json();
  const paths = data.ok ? data.produtos.map((safra) => ({ params: { id: safra.id.toString() } })) : [];
  return { paths, fallback: 'blocking' };
}
export async function getStaticProps({ params }) {
  const res = await fetch(`${process.env.BACKEND_URL || 'http://localhost:5000'}/api/mercado/produto/${params.id}`);
  const data = await res.json();
  if (!data.ok) return { notFound: true };
  return { props: { safra: data.produto }, revalidate: 60 };
}


export default function SafraDetalhes({ safra }) {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth(); // Usar o estado de autenticação
  const [quantidade, setQuantidade] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  if (router.isFallback) {
    return <div>Carregando...</div>;
  }

  const handleCompra = async () => {
    if (!isAuthenticated) {
      router.push('/login?redirect=/safra/' + safra.id);
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const res = await fetch(`/api/mercado/encomendar/${safra.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantidade }),
      });

      const data = await res.json();

      if (res.ok && data.ok) {
        setSuccess(data.message);
        // Redirecionar para a página de minhas compras após um tempo
        setTimeout(() => router.push('/comprador/minhas-compras'), 2000);
      } else {
        setError(data.message || 'Ocorreu um erro.');
      }
    } catch (err) {
      setError('Erro de conexão. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>{safra.produto.nome} | AgroKongo</title>
      </Head>

      <div className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2">
            {/* Coluna da Imagem */}
            <div className="relative h-64 md:h-full bg-gray-200">
              <img
                src={safra.imagem_url ? `/uploads/public/safras/${safra.imagem_url}` : 'https://via.placeholder.com/600x400?text=Sem+Imagem'}
                alt={safra.produto.nome}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Coluna de Detalhes e Compra */}
            <div className="p-6 md:p-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{safra.produto.nome}</h1>
              <p className="text-gray-600 mb-4">{safra.produto.categoria}</p>

              <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-2">Sobre o Produto</h2>
                <p className="text-gray-700">{safra.descricao || 'Nenhuma descrição fornecida.'}</p>
              </div>

              <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-2">Produtor</h2>
                <div className="flex items-center">
                  <img src={safra.produtor.foto_perfil ? `/uploads/public/perfil/${safra.produtor.foto_perfil}` : '/images/default_user.jpg'} alt={safra.produtor.nome} className="h-12 w-12 rounded-full object-cover mr-4" />
                  <div>
                    <p className="font-bold text-gray-900">{safra.produtor.nome}</p>
                    <p className="text-sm text-gray-600">{safra.produtor.provincia?.nome}, {safra.produtor.municipio?.nome}</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-gray-600">Preço por Kg:</span>
                  <span className="text-3xl font-bold text-green-600">
                    {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(safra.preco_por_unidade)}
                  </span>
                </div>
                <div className="flex justify-between items-center mb-4">
                  <span className="text-gray-600">Disponível:</span>
                  <span className="font-bold text-gray-900">{safra.quantidade_disponivel} kg</span>
                </div>

                <div className="flex items-center space-x-4 mb-4">
                  <label htmlFor="quantidade" className="font-medium">Quantidade (kg):</label>
                  <input
                    type="number"
                    id="quantidade"
                    name="quantidade"
                    min="1"
                    max={safra.quantidade_disponivel}
                    value={quantidade}
                    onChange={(e) => setQuantidade(e.target.value)}
                    className="w-24 p-2 border border-gray-300 rounded-md text-center"
                  />
                </div>

                {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
                {success && <p className="text-green-600 text-sm mb-4">{success}</p>}

                <button
                  onClick={handleCompra}
                  disabled={loading || safra.status !== 'disponivel'}
                  className={`w-full py-3 px-4 border border-transparent text-lg font-medium rounded-md text-white transition-colors duration-200 ${
                    safra.status !== 'disponivel'
                      ? 'bg-gray-400 cursor-not-allowed'
                      : loading
                      ? 'bg-green-400'
                      : 'bg-green-600 hover:bg-green-700'
                  } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500`}
                >
                  {safra.status !== 'disponivel' ? 'Esgotado' : loading ? 'Processando...' : isAuthenticated ? 'Comprar Agora' : 'Faça Login para Comprar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
