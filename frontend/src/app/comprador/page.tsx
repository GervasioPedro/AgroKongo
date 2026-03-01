"use client";

import useSWR from "swr";
import { TransactionCard } from "@/components/dashboard/transaction-card";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/utils/format";
import { ShoppingBag, Package, Clock } from "lucide-react";
import { http } from "@/services/http";

type Transaction = {
  id: number;
  fatura_ref: string;
  status: "pendente" | "analise" | "escrow" | "enviado" | "entregue" | "finalizado";
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

export default function CompradorDashboard() {
  const { data, isLoading } = useSWR<{ compras: Transaction[]; stats: any }>(
    "/comprador/dashboard",
    fetcher
  );

  const compras = data?.compras || [];
  const pendentes = compras.filter(c => c.status === "pendente");
  const ativas = compras.filter(c => ["analise", "escrow", "enviado"].includes(c.status));

  return (
    <main className="min-h-screen bg-surface-neutral">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-md mx-auto">
          <h1 className="text-xl font-bold">Dashboard Comprador</h1>
          <p className="text-sm text-slate-600">Minhas compras</p>
        </div>
      </header>

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        <div className="grid grid-cols-3 gap-3">
          <Card className="text-center">
            <ShoppingBag className="h-6 w-6 mx-auto text-agro-primary" />
            <p className="text-2xl font-bold mt-2">{compras.length}</p>
            <p className="text-xs text-slate-600">Total</p>
          </Card>
          <Card className="text-center">
            <Clock className="h-6 w-6 mx-auto text-yellow-600" />
            <p className="text-2xl font-bold mt-2">{pendentes.length}</p>
            <p className="text-xs text-slate-600">Pendentes</p>
          </Card>
          <Card className="text-center">
            <Package className="h-6 w-6 mx-auto text-escrow-primary" />
            <p className="text-2xl font-bold mt-2">{ativas.length}</p>
            <p className="text-xs text-slate-600">Ativas</p>
          </Card>
        </div>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold">Explorar Mercado</h2>
              <p className="text-sm text-slate-600">Ver produtos disponíveis</p>
            </div>
            <Button variant="primary" size="sm" onClick={() => window.location.href = "/mercado"}>
              Ir
            </Button>
          </div>
        </Card>

        <section>
          <h2 className="font-semibold mb-3">Compras Recentes</h2>
          <div className="space-y-3">
            {isLoading ? (
              <>
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-32 w-full" />
              </>
            ) : compras.length === 0 ? (
              <Card className="text-center py-8">
                <p className="text-slate-600">Nenhuma compra ainda</p>
                <Button 
                  variant="primary" 
                  className="mt-4"
                  onClick={() => window.location.href = "/mercado"}
                >
                  Explorar Mercado
                </Button>
              </Card>
            ) : (
              compras.slice(0, 5).map((compra) => (
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
                  onAction={() => window.location.href = `/comprador/transacao/${compra.id}`}
                />
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
