import Head from 'next/head';
import StatusBadge from '../../components/StatusBadge';

export async function getServerSideProps({ params }) {
  const res = await fetch(`${process.env.BACKEND_URL || 'http://localhost:5000'}/api/validar-fatura/${params.code}`);
  const data = await res.json();
  return { props: { data } };
}

export default function ValidarFatura({ data }) {
  const { ok, message, fatura, acesso_completo } = data;

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <Head>
        <title>Validação de Fatura | AgroKongo</title>
      </Head>

      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg text-center">
        {!ok ? (
          <>
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="mt-5 text-2xl font-bold text-gray-900">Fatura Inválida</h2>
            <p className="mt-2 text-gray-600">{message}</p>
          </>
        ) : (
          <>
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mt-5 text-2xl font-bold text-gray-900">Fatura Válida</h2>
            <div className="mt-4 space-y-2 text-left border-t pt-4">
              <p><strong>Ref. Fatura:</strong> {fatura.fatura_ref}</p>
              <p><strong>Data de Emissão:</strong> {new Date(fatura.data_criacao).toLocaleString('pt-AO')}</p>
              <p className="flex items-center"><strong>Status:</strong> <span className="ml-2"><StatusBadge status={fatura.status} /></span></p>

              {acesso_completo && (
                <>
                  <hr className="my-2"/>
                  <p><strong>Produto:</strong> {fatura.safra.produto.nome}</p>
                  <p><strong>Quantidade:</strong> {fatura.quantidade_comprada} kg</p>
                  <p><strong>Valor Total:</strong> {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(fatura.valor_total_pago)}</p>
                  <p><strong>Vendedor:</strong> {fatura.vendedor.nome}</p>
                  <p><strong>Comprador:</strong> {fatura.comprador.nome}</p>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
