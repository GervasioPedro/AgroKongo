"use client";

import { useAuth } from "@/hooks/useAuth";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/shared/page-header";
import { formatCurrency, formatDate } from "@/utils/format";
import { Search, Filter } from "lucide-react";
import { http } from "@/services/http";
import { useState } from "react";
import Link from "next/link";

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function TransacoesAdminPage() {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("todas");
  const { data, isLoading } = useSWR("/admin/transacoes", fetcher);

  const transacoes = data?.transacoes || [];
  const filtered = transacoes.filter((t: any) => {
    const matchSearch = t.fatura_ref.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "todas" || t.status === statusFilter;
    return matchSearch && matchStatus;
  });

  if (user?.tipo !== "admin") {
    return <div className="p-6">Acesso negado</div>;
  }

  return (
    <div className="min-h-screen">
      <PageHeader 
        title="Todas as Transações"
        subtitle={`${transacoes.length} transações no sistema`}
        showBack={false}
      />

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6">
        {/* Filtros */}
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Procurar por referência..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-agro-primary"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto">
            {["todas", "pendente", "analise", "escrow", "enviado", "finalizado"].map((status) => (
              <Button
                key={status}
                size="sm"
                variant={statusFilter === status ? "primary" : "ghost"}
                onClick={() => setStatusFilter(status)}
                className="whitespace-nowrap"
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </Button>
            ))}
          </div>
        </div>

        {/* Tabela */}
        {isLoading ? (
          <div className="text-center py-12">A carregar...</div>
        ) : (
          <Card className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b">
                <tr className="text-left">
                  <th className="p-4 font-semibold">Referência</th>
                  <th className="p-4 font-semibold">Produto</th>
                  <th className="p-4 font-semibold">Comprador</th>
                  <th className="p-4 font-semibold">Vendedor</th>
                  <th className="p-4 font-semibold">Valor</th>
                  <th className="p-4 font-semibold">Status</th>
                  <th className="p-4 font-semibold">Data</th>
                  <th className="p-4 font-semibold">Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t: any) => (
                  <tr key={t.id} className="border-b hover:bg-slate-50">
                    <td className="p-4 font-mono text-sm">{t.fatura_ref}</td>
                    <td className="p-4">{t.produto}</td>
                    <td className="p-4 text-sm">{t.comprador}</td>
                    <td className="p-4 text-sm">{t.vendedor}</td>
                    <td className="p-4 font-semibold">{formatCurrency(t.valor)}</td>
                    <td className="p-4">
                      <Badge status={t.status}>{t.status}</Badge>
                    </td>
                    <td className="p-4 text-sm text-slate-600">{formatDate(t.data)}</td>
                    <td className="p-4">
                      <Link href={`/transacao/${t.id}`}>
                        <Button variant="outline" size="sm">Ver</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>
    </div>
  );
}
