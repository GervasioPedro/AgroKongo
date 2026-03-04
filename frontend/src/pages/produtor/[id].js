import Head from 'next/head';
import { useRouter } from 'next/router';
import Link from 'next/link';
import StatusBadge from '../../components/StatusBadge'; // Usar o componente

export async function getServerSideProps({ params }) {
  // Usar SSR para garantir que os dados estão sempre atualizados
  const res = await fetch(`${process.env.BACKEND_URL || 'http://localhost:5000'}/api/produtor/${params.id}`);
  const data = await res.json();

  if (!data.ok) {
    return { notFound: true };
  }

  return {
    props: {
      data,
    },
  };
}

export default function PerfilProdutor({ data }) {
  const { produtor, safras } = data;

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Perfil de {produtor.nome} | AgroKongo</title>
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header do Perfil */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
          <div className="p-6 md:p-8 text-center">
            <img
              src={produtor.foto_perfil ? `/uploads/public/perfil/${produtor.foto_perfil}` : '/images/default_user.jpg'}
              alt={`Foto de ${produtor.nome}`}
              className="w-32 h-32 rounded-full mx-auto mb-4 object-cover border-4 border-green-500"
            />
            <h1 className="text-3xl font-bold text-gray-900">{produtor.nome}</h1>
            <p className="text-gray-600 mt-1">{produtor.provincia?.nome}, {produtor.municipio?.nome}</p>
            <div className="mt-4">
              <span className="inline-block bg-green-100 text-green-800 text-sm font-semibold mr-2 px-2.5 py-0.5 rounded-full">
                Produtor Validado
              </span>
            </div>
          </div>
        </div>

        {/* Safras do Produtor */}
        <div>
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Safras Disponíveis</h2>
          {safras.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {safras.map((safra) => (
                <div key={safra.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
                  <div className="relative h-48 w-full bg-gray-200">
                    <img
                      src={safra.imagem_url ? `/uploads/public/safras/${safra.imagem_url}` : '/images/placeholder-safra.jpg'}
                      alt={safra.produto?.nome}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-2 right-2">
                      <StatusBadge status={safra.status} />
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">{safra.produto?.nome}</h3>
                    <div className="flex justify-between items-end mt-4">
                      <div>
                        <p className="text-xs text-gray-500">Preço por Kg</p>
                        <p className="text-xl font-bold text-green-600">
                          {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(safra.preco_por_unidade)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Disponível</p>
                        <p className="font-medium text-gray-900">{safra.quantidade_disponivel} kg</p>
                      </div>
                    </div>
                    <Link href={`/safra/${safra.id}`} className="mt-4 block w-full bg-green-600 text-white text-center py-2 rounded-md hover:bg-green-700 transition-colors font-medium">
                      Ver Detalhes
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-10 bg-white rounded-lg shadow">
              <h3 className="text-xl font-medium text-gray-900">Nenhuma safra disponível</h3>
              <p className="mt-1 text-gray-500">Este produtor não tem produtos à venda no momento.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
