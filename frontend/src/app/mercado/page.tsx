"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Link from "next/link";

interface Safra {
  id: number;
  produto: string;
  categoria: string;
  quantidade: number;
  preco: number;
  imagem_url: string | null;
  produtor: {
    nome: string;
    localizacao: string;
    rating: number;
  };
}

export default function MercadoPage() {
  const [safras, setSafras] = useState<Safra[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSafras();
  }, []);

  const fetchSafras = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/market/safras`);
      const json = await res.json();

      if (json.success) {
        setSafras(json.data);
      } else {
        setError("Falha ao carregar produtos.");
      }
    } catch (err) {
      console.error(err);
      setError("Erro de conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Mercado</h1>
          {/* Aqui podem entrar filtros no futuro */}
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="w-12 h-12 border-4 border-green-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : error ? (
          <div className="text-center py-20 text-red-600">{error}</div>
        ) : safras.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            Nenhum produto disponível no momento.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {safras.map((safra) => (
              <div key={safra.id} className="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                <div className="h-48 bg-gray-200 relative">
                  <img
                    src={safra.imagem_url || `https://dummyimage.com/600x400/e2e8f0/16a34a&text=${safra.produto}`}
                    alt={safra.produto}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2 bg-white px-2 py-1 rounded-full text-xs font-bold text-gray-800 shadow">
                    {safra.preco.toLocaleString('pt-AO')} Kz/kg
                  </div>
                </div>

                <div className="p-5">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="text-xs text-green-600 font-bold uppercase tracking-wide">{safra.categoria}</p>
                      <h3 className="text-lg font-bold text-gray-900 mt-1">{safra.produto}</h3>
                    </div>
                  </div>

                  <div className="flex items-center text-sm text-gray-500 mb-4">
                    <svg className="w-4 h-4 mr-1 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                    </svg>
                    {safra.produtor.localizacao}
                  </div>

                  <div className="flex items-center justify-between border-t pt-4">
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-600">
                        {safra.produtor.nome.charAt(0)}
                      </div>
                      <div className="ml-2 text-sm">
                        <p className="font-medium text-gray-900">{safra.produtor.nome.split(' ')[0]}</p>
                        <p className="text-xs text-gray-500">Stock: {safra.quantidade} kg</p>
                      </div>
                    </div>

                    <Link
                      href={`/mercado/${safra.id}`}
                      className="bg-gray-900 text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-gray-800 transition"
                    >
                      Ver Detalhes
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}