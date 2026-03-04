import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-neutral px-6">
      <div className="max-w-lg w-full text-center">
        <div className="text-[6rem] leading-none font-extrabold text-slate-300">404</div>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Página Não Encontrada</h1>
        <p className="mt-2 text-slate-600">
          Lamentamos, mas a página que procuras não existe, foi removida ou está temporariamente indisponível.
        </p>
        <div className="mt-6">
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-[12px] bg-agro-primary px-5 py-3 text-white font-semibold shadow hover:opacity-95"
          >
            Voltar à Página Inicial
          </Link>
        </div>
      </div>
    </div>
  );
}
