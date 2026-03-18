"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";

interface SafraDetalhe {
  id: number;
  produto: string;
  categoria: string;
  quantidade: number;
  preco: number;
  imagem_url: string | null;
  observacoes: string | null;
  produtor: {
    id: number;
    nome: string;
    rating: number;
    localizacao: string;
  };
}

export default function DetalheSafraPage() {
  const params = useParams();
  const router = useRouter();
  const [safra, setSafra] = useState<SafraDetalhe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [quantidade, setQuantidade] = useState(1);
  const [user, setUser] = useState<any>(null);
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) setUser(JSON.parse(storedUser));

    if (params.id) {
      fetchSafra(params.id as string);
    }
  }, [params.id]);

  const fetchSafra = async (id: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/market/safras/${id}`);
      const json = await res.json();

      if (json.success) {
        setSafra(json.data);
      } else {
        setError(json.errors ? json.errors[0] : "Erro ao carregar");
      }
    } catch (err) {
      setError("Erro de conexão.");
    } finally {
      setLoading(false);
    }
  };

  const handleComprar = async () => {
    if (!user) {
      router.push("/auth/login");
      return;
    }

    // Validação básica
    if (!safra || quantidade > safra.quantidade || quantidade <= 0) {
      alert("Quantidade inválida.");
      return;
    }

    setBuying(true);
    const token = localStorage.getItem("token");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/market/buy`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          safra_id: safra.id,
          quantidade: quantidade
        }),
      });

      const json = await res.json();

      if (json.success) {
        alert("Reserva efetuada com sucesso! Redirecionando para o painel...");
        router.push("/dashboard");
      } else {
        alert("Erro: " + (json.errors ? json.errors[0] : "Falha na compra"));
      }
    } catch (err) {
      console.error(err);
      alert("Erro de conexão ao processar compra.");
    } finally {
      setBuying(false);
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center">Carregando...</div>;
  if (error || !safra) return <div className="min-h-screen flex items-center justify-center text-red-600">{error || "Produto não encontrado"}</div>;

  const total = quantidade * safra.preco;
  const taxa = total * 0.05;
  const totalFinal = total + taxa;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="lg:grid lg:grid-cols-2 lg:gap-x-8">
          {/* Imagem */}
          <div className="aspect-w-4 aspect-h-3 rounded-lg overflow-hidden bg-gray-100">
            <img
              src={safra.imagem_url || `https://dummyimage.com/800x600/e2e8f0/16a34a&text=${safra.produto}`}
              alt={safra.produto}
              className="w-full h-full object-center object-cover"
            />
          </div>

          {/* Info */}
          <div className="mt-10 px-4 sm:px-0 sm:mt-16 lg:mt-0">
            <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">{safra.produto}</h1>

            <div className="mt-3">
              <h2 className="sr-only">Informação do Produtor</h2>
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-green-100 rounded-full p-2">
                  <span className="text-green-800 font-bold">{safra.produtor.nome.charAt(0)}</span>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">{safra.produtor.nome}</p>
                  <div className="flex items-center text-sm text-gray-500">
                    <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                    </svg>
                    {safra.produtor.localizacao}
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="sr-only">Descrição</h3>
              <div className="text-base text-gray-700 space-y-6" dangerouslySetInnerHTML={{ __html: safra.observacoes || "Sem descrição detalhada." }} />
            </div>

            {/* Caixa de Compra */}
            <div className="mt-10 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <span className="text-lg font-medium text-gray-900">Preço por Kg</span>
                <span className="text-2xl font-bold text-gray-900">{safra.preco.toLocaleString('pt-AO')} Kz</span>
              </div>

              <div className="mb-6">
                <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-2">
                  Quantidade (Disponível: {safra.quantidade} kg)
                </label>
                <input
                  type="number"
                  id="quantity"
                  min="1"
                  max={safra.quantidade}
                  value={quantidade}
                  onChange={(e) => setQuantidade(Number(e.target.value))}
                  className="shadow-sm focus:ring-green-500 focus:border-green-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
                />
              </div>

              <div className="border-t border-gray-200 pt-4 mb-6 space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Subtotal</span>
                  <span>{total.toLocaleString('pt-AO')} Kz</span>
                </div>
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Taxa de Serviço (5%)</span>
                  <span>{taxa.toLocaleString('pt-AO')} Kz</span>
                </div>
                <div className="flex justify-between text-base font-bold text-gray-900 pt-2">
                  <span>Total</span>
                  <span>{totalFinal.toLocaleString('pt-AO')} Kz</span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleComprar}
                disabled={buying}
                className={`w-full border border-transparent rounded-md py-3 px-8 flex items-center justify-center text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 ${buying ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'}`}
              >
                {buying ? "Processando..." : "Reservar Agora"}
              </button>
              <p className="mt-4 text-center text-xs text-gray-500">
                Pagamento seguro via Escrow. O valor só é libertado após a entrega.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}