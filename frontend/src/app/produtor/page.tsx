"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatWeight } from "@/utils/format";
import { Plus, Edit, Trash2 } from "lucide-react";
import { http } from "@/services/http";

type Safra = {
  id: number;
  produto: { nome: string };
  quantidade_disponivel: number;
  preco_por_unidade: number;
  status: string;
  imagem: string;
};

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function MinhasSafrasPage() {
  const { data, isLoading, mutate } = useSWR<{ safras: Safra[] }>(
    "/produtor/safras",
    fetcher
  );

  const safras = data?.safras || [];

  const handleDelete = async (id: number) => {
    if (!confirm("Eliminar esta safra?")) return;
    try {
      await http.delete(`/produtor/safra/${id}`);
      mutate();
    } catch (error) {
      alert("Erro ao eliminar");
    }
  };

  return (
    <main className="min-h-screen bg-surface-neutral">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Minhas Safras</h1>
            <p className="text-sm text-slate-600">{safras.length} publicadas</p>
          </div>
          <Button 
            variant="primary" 
            size="sm"
            onClick={() => window.location.href = "/produtor/nova-safra"}
          >
            <Plus className="h-4 w-4 mr-1" />
            Nova
          </Button>
        </div>
      </header>

      <div className="max-w-md mx-auto px-4 py-6 space-y-3">
        {isLoading ? (
          <>
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </>
        ) : safras.length === 0 ? (
          <Card className="text-center py-12">
            <Package className="h-12 w-12 mx-auto text-slate-400" />
            <p className="text-slate-600 mt-4">Nenhuma safra publicada</p>
            <Button 
              variant="primary" 
              className="mt-4"
              onClick={() => window.location.href = "/produtor/nova-safra"}
            >
              Publicar Primeira Safra
            </Button>
          </Card>
        ) : (
          safras.map((safra) => (
            <Card key={safra.id}>
              <div className="flex gap-4">
                <img
                  src={safra.imagem || "/placeholder.jpg"}
                  alt={safra.produto.nome}
                  className="w-20 h-20 rounded-xl object-cover"
                />
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{safra.produto.nome}</h3>
                      <Badge status={safra.status === "disponivel" ? "finalizado" : "cancelado"}>
                        {safra.status}
                      </Badge>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => window.location.href = `/produtor/safra/${safra.id}/editar`}
                        className="p-2 hover:bg-slate-100 rounded-lg"
                      >
                        <Edit className="h-4 w-4 text-slate-600" />
                      </button>
                      <button
                        onClick={() => handleDelete(safra.id)}
                        className="p-2 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </button>
                    </div>
                  </div>
                  <div className="flex justify-between mt-2">
                    <div>
                      <p className="text-xs text-slate-500">Disponível</p>
                      <p className="font-medium">{formatWeight(safra.quantidade_disponivel)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Preço/kg</p>
                      <p className="font-bold text-agro-primary">
                        {formatCurrency(safra.preco_por_unidade)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </main>
  );
}
