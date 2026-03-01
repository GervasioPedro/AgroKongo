"use client";

import { TransactionCard } from "@/components/dashboard/transaction-card";
import { KPICard } from "@/components/dashboard/kpi-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/utils/format";
import { Wallet, TrendingUp, Package, AlertCircle } from "lucide-react";

// Mock data - substituir por chamadas API reais
const mockTransactions = [
  {
    id: 1,
    faturaRef: "AK-2024-001",
    status: "escrow" as const,
    produto: "Tomate Fresco",
    quantidade: 500,
    valorTotal: 75000,
    dataCompra: "15 Jan 2024",
    nomeOutraParte: "João Silva",
  },
  {
    id: 2,
    faturaRef: "AK-2024-002",
    status: "pendente" as const,
    produto: "Batata Doce",
    quantidade: 1000,
    valorTotal: 120000,
    dataCompra: "14 Jan 2024",
    nomeOutraParte: "Maria Costa",
  },
  {
    id: 3,
    faturaRef: "AK-2024-003",
    status: "finalizado" as const,
    produto: "Milho",
    quantidade: 2000,
    valorTotal: 350000,
    dataCompra: "10 Jan 2024",
    nomeOutraParte: "Pedro Mendes",
  },
];

export default function DashboardExample() {
  return (
    <main className="min-h-screen bg-surface-neutral">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-4">
        <div className="max-w-md mx-auto">
          <h1 className="text-xl font-bold">Dashboard Produtor</h1>
          <p className="text-sm text-slate-600">Bem-vindo, António Fernandes</p>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-md mx-auto px-4 py-6 pb-24 space-y-6">
        {/* KPIs */}
        <section className="grid grid-cols-2 gap-3">
          <KPICard
            icon={<Wallet className="h-5 w-5 text-agro-primary" />}
            label="Saldo Disponível"
            value={formatCurrency(450000, "AOA")}
            trend="+12%"
          />
          <KPICard
            icon={<TrendingUp className="h-5 w-5 text-escrow-primary" />}
            label="Em Custódia"
            value={formatCurrency(195000, "AOA")}
          />
          <KPICard
            icon={<Package className="h-5 w-5 text-green-600" />}
            label="Vendas Mês"
            value="23"
            trend="+5"
          />
          <KPICard
            icon={<AlertCircle className="h-5 w-5 text-alert-pending" />}
            label="Pendentes"
            value="2"
          />
        </section>

        {/* Ações Rápidas */}
        <section className="bg-white rounded-2xl p-4 shadow-card-soft">
          <h2 className="font-semibold mb-3">Ações Rápidas</h2>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="primary" size="sm" className="w-full">
              Nova Safra
            </Button>
            <Button variant="outline" size="sm" className="w-full">
              Levantar Saldo
            </Button>
          </div>
        </section>

        {/* Transações Recentes */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Transações Recentes</h2>
            <Button variant="ghost" size="sm">
              Ver Todas
            </Button>
          </div>

          <div className="space-y-3">
            {mockTransactions.map((transaction) => (
              <TransactionCard
                key={transaction.id}
                {...transaction}
                tipoUsuario="produtor"
                onAction={() => console.log(`Ação para ${transaction.faturaRef}`)}
              />
            ))}
          </div>
        </section>

        {/* Estados de Escrow - Exemplo Visual */}
        <section className="bg-white rounded-2xl p-4 shadow-card-soft">
          <h2 className="font-semibold mb-3">Estados do Sistema</h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">Aguardando Pagamento</span>
              <Badge status="pendente" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Em Análise</span>
              <Badge status="analise" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Em Custódia (Escrow)</span>
              <Badge status="escrow" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Mercadoria Enviada</span>
              <Badge status="enviado" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Entregue</span>
              <Badge status="entregue" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Finalizado</span>
              <Badge status="finalizado" />
            </div>
          </div>
        </section>
      </div>

      {/* Bottom Navigation (Mobile) */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-4 py-3">
        <div className="max-w-md mx-auto flex items-center justify-around">
          <button className="flex flex-col items-center gap-1 text-agro-primary">
            <Package className="h-5 w-5" />
            <span className="text-xs font-medium">Dashboard</span>
          </button>
          <button className="flex flex-col items-center gap-1 text-slate-400">
            <TrendingUp className="h-5 w-5" />
            <span className="text-xs">Mercado</span>
          </button>
          <button className="flex flex-col items-center gap-1 text-slate-400">
            <Wallet className="h-5 w-5" />
            <span className="text-xs">Carteira</span>
          </button>
        </div>
      </nav>
    </main>
  );
}
