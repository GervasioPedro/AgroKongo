"use client";

import { useState } from "react";
import Link from "next/link";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/shared/page-header";
import { formatCurrency, formatWeight } from "@/utils/format";
import { Search, MapPin, SlidersHorizontal } from "lucide-react";
import { http } from "@/services/http";

type Safra = {
  id: number;
  produto: { nome: string };
  quantidade_disponivel: number;
  preco_por_unidade: number;
  produtor: { nome: string; provincia: { nome: string } };
  imagem: string;
  status: string;
};

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function MercadoPage() {
  const [search, setSearch] = useState("");
  const [categoria, setCategoria] = useState("todas");
  const { data, isLoading } = useSWR<{ safras: Safra[] }>("/mercado/safras", fetcher);

  const safras = data?.safras || [];
  const filtered = safras.filter(s => 
    s.produto.nome.toLowerCase().includes(search.toLowerCase())
  );

  const categorias = ["Todas", "Hortaliças", "Frutas", "Cereais", "Tubérculos"];

  return (
    <div className="min-h-screen bg-surface-neutral">
      <PageHeader 
        title="Explorar Mercado"
        subtitle={`${filtered.length} produtos disponíveis`}
        showBack={false}
        action={
          <Link href="/dashboard">
            <Button variant="outline" size="sm">
              Ir para Dashboard
            </Button>
          </Link>
        }
      />

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6">
        {/* Filtros */}
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Procurar produtos..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-agro-primary focus:border-transparent"
            />
          </div>
          <Button variant="outline" className="hidden lg:flex">
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            Filtros Avançados
          </Button>
        </div>

        {/* Categorias */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {categorias.map((cat) => (
            <Button
              key={cat}
              size="sm"
              variant={categoria === cat.toLowerCase() ? "primary" : "ghost"}
              onClick={() => setCategoria(cat.toLowerCase())}
              className="whitespace-nowrap"
            >
              {cat}
            </Button>
          ))}
        </div>

        {/* Grid de Produtos */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <Skeleton key={i} className="h-96 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <Card className="text-center py-16">
            <p className="text-slate-600 text-lg mb-4">Nenhuma safra disponível</p>
            <Link href="/produtor">
              <Button variant="primary">Publicar Primeira Safra</Button>
            </Link>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map((safra) => (
              <Link key={safra.id} href={`/mercado/${safra.id}`}>
                <Card className="hover:shadow-xl transition-all cursor-pointer group overflow-hidden h-full">
                  {/* Imagem */}
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={safra.imagem || "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=400&q=80"}
                      alt={safra.produto.nome}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                    />
                    <Badge 
                      status="finalizado" 
                      className="absolute top-3 right-3"
                    >
                      Disponível
                    </Badge>
                  </div>

                  {/* Conteúdo */}
                  <div className="p-4">
                    <h3 className="font-bold text-lg mb-2 line-clamp-1">{safra.produto.nome}</h3>
                    
                    <div className="flex items-center gap-1 text-xs text-slate-600 mb-3">
                      <MapPin className="h-3 w-3 flex-shrink-0" />
                      <span className="truncate">{safra.produtor.provincia.nome}</span>
                      <span className="mx-1">•</span>
                      <span className="truncate">{safra.produtor.nome}</span>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t">
                      <div>
                        <p className="text-xs text-slate-500">Disponível</p>
                        <p className="font-semibold">{formatWeight(safra.quantidade_disponivel)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-slate-500">Preço/kg</p>
                        <p className="font-bold text-lg text-agro-primary">
                          {formatCurrency(safra.preco_por_unidade)}
                        </p>
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
