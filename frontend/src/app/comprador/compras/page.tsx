"use client";

import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import useSWR from "swr";
import { TransactionCard } from "@/components/dashboard/transaction-card";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { http } from "@/services/http";

type Transaction = {
  id: number;
  fatura_ref: string;
  status: "pendente" | "analise" | "escrow" | "enviado" | "entregue" | "finalizado" | "disputa" | "cancelado";
  safra: { produto: string };
  quantidade_comprada: number;
  valor_total_pago: number;
  data_criacao: string;
  vendedor: { nome: string };
};

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function ComprasPage() {
  const { user } = useAuth();
  const [filter, setFilter] = useState("todas");
  const { data, isLoading } = useSWR<{ compras: Transaction[] }>("/comprador/compras", fetcher);

  const compras = data?.compras || [];
  const filtered = filter === "todas" 
    ? compras 
    : compras.filter(c => c.status === filter);

  if (user?.tipo !== "comprador") {
    return <div className="p-6">Acesso negado</div>;
  }

  return (
    <div className="min-h-screen">
      <PageHeader 
        title="Minhas Compras"
        subtitle={`${compras.length} compras realizadas`}
        showBack={false}
      />

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6">
        {/* Filtros */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          <Button
            size="sm"
            variant={filter === "todas" ? "primary" : "ghost"}
            onClick={() => setFilter("todas")}
          >
            Todas
          </Button>
          <Button
            size="sm"
            variant={filter === "pendente" ? "primary" : "ghost"}
            onClick={() => setFilter("pendente")}
          >
            Pendentes
          </Button>
          <Button
            size="sm"
            variant={filter === "escrow" ? "escrow" : "ghost"}
            onClick={() => setFilter("escrow")}
          >
            Em Custódia
          </Button>
          <Button
            size="sm"
            variant={filter === "enviado" ? "primary" : "ghost"}
            onClick={() => setFilter("enviado")}
          >
            Enviadas
          </Button>
          <Button
            size="sm"
            variant={filter === "finalizado" ? "primary" : "ghost"}
            onClick={() => setFilter("finalizado")}
          >
            Finalizadas
          </Button>
        </div>

        {/* Lista */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {isLoading ? (
            <>
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-48 w-full" />
            </>
          ) : filtered.length === 0 ? (
            <Card className="col-span-full text-center py-12">
              <p className="text-slate-600 mb-4">Nenhuma compra encontrada</p>
              <Button variant="primary" onClick={() => window.location.href = "/mercado"}>
                Explorar Mercado
              </Button>
            </Card>
          ) : (
            filtered.map((compra) => (
              <TransactionCard
                key={compra.id}
                id={compra.id}
                faturaRef={compra.fatura_ref}
                status={compra.status}
                produto={compra.safra.produto}
                quantidade={compra.quantidade_comprada}
                valorTotal={compra.valor_total_pago}
                dataCompra={new Date(compra.data_criacao).toLocaleDateString("pt-AO")}
                nomeOutraParte={compra.vendedor.nome}
                tipoUsuario="comprador"
                onAction={() => window.location.href = `/transacao/${compra.id}`}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
