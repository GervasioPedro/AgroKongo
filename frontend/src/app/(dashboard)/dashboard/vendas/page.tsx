"use client";

import { useState } from "react";
import useSWR from "swr";
import { TransactionCard } from "@/components/dashboard/transaction-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { http } from "@/services/http";

type Transaction = {
  id: number;
  fatura_ref: string;
  status: "pendente" | "analise" | "escrow" | "enviado" | "entregue" | "finalizado" | "disputa" | "cancelado";
  safra: {
    produto: string;
  };
  quantidade_comprada: number;
  valor_total_pago: number;
  data_criacao: string;
  comprador: {
    nome: string;
  };
};

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function VendasPage() {
  const [filter, setFilter] = useState<string>("todas");
  const { data, isLoading } = useSWR<{ transacoes: Transaction[] }>(
    "/produtor/transacoes",
    fetcher
  );

  const transacoes = data?.transacoes || [];
  const filtered = filter === "todas" 
    ? transacoes 
    : transacoes.filter(t => t.status === filter);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8">
      <header>
        <h1 className="text-xl font-bold">Minhas Vendas</h1>
        <p className="text-sm text-slate-600">Histórico de transações</p>
      </header>

      {/* Filtros */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <Button
          size="sm"
          variant={filter === "todas" ? "primary" : "ghost"}
          onClick={() => setFilter("todas")}
        >
          Todas
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
          variant={filter === "pendente" ? "primary" : "ghost"}
          onClick={() => setFilter("pendente")}
        >
          Pendentes
        </Button>
        <Button
          size="sm"
          variant={filter === "finalizado" ? "primary" : "ghost"}
          onClick={() => setFilter("finalizado")}
        >
          Finalizadas
        </Button>
      </div>

      {/* Lista de Transações */}
      <div className="space-y-3">
        {isLoading ? (
          <>
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </>
        ) : filtered.length === 0 ? (
          <div className="rounded-2xl bg-surface-neutral p-8 text-center">
            <p className="text-slate-600">Nenhuma transação encontrada</p>
          </div>
        ) : (
          filtered.map((t) => (
            <TransactionCard
              key={t.id}
              id={t.id}
              faturaRef={t.fatura_ref}
              status={t.status}
              produto={t.safra.produto}
              quantidade={t.quantidade_comprada}
              valorTotal={t.valor_total_pago}
              dataCompra={new Date(t.data_criacao).toLocaleDateString("pt-AO")}
              nomeOutraParte={t.comprador.nome}
              tipoUsuario="produtor"
              onAction={() => window.location.href = `/dashboard/transacao/${t.id}`}
            />
          ))
        )}
      </div>
    </main>
  );
}
