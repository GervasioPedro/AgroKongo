"use client";

import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/utils/format";
import { 
  Users, ShoppingBag, DollarSign, AlertCircle, 
  TrendingUp, Package, Shield 
} from "lucide-react";
import { http } from "@/services/http";

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function AdminDashboard() {
  const { data, isLoading } = useSWR("/admin/dashboard", fetcher);

  const stats = data?.stats || {};
  const pendentes = data?.validacoes_pendentes || [];

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b px-4 lg:px-8 py-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold">Dashboard Administrativo</h1>
          <p className="text-slate-600">Visão geral da plataforma</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6 space-y-6">
        {/* KPIs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Total Usuários</p>
                <p className="text-3xl font-bold mt-1">{stats.total_usuarios || 0}</p>
                <p className="text-xs text-green-600 mt-1">+12% este mês</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Transações Ativas</p>
                <p className="text-3xl font-bold mt-1">{stats.transacoes_ativas || 0}</p>
                <p className="text-xs text-slate-600 mt-1">Em processamento</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-purple-100 flex items-center justify-center">
                <ShoppingBag className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Em Custódia</p>
                <p className="text-3xl font-bold mt-1">{formatCurrency(stats.valor_custodia || 0)}</p>
                <p className="text-xs text-escrow-primary mt-1">Protegido</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-escrow-primary/10 flex items-center justify-center">
                <Shield className="h-6 w-6 text-escrow-primary" />
              </div>
            </div>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Pendentes Validação</p>
                <p className="text-3xl font-bold mt-1">{stats.pendentes_validacao || 0}</p>
                <p className="text-xs text-orange-600 mt-1">Requer atenção</p>
              </div>
              <div className="h-12 w-12 rounded-xl bg-orange-100 flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </Card>
        </div>

        {/* Validações Pendentes */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Validações Pendentes</h2>
              <Badge status="analise">{pendentes.length}</Badge>
            </div>
            <div className="space-y-3">
              {pendentes.length === 0 ? (
                <p className="text-center text-slate-600 py-8">Nenhuma validação pendente</p>
              ) : (
                pendentes.slice(0, 5).map((item: any) => (
                  <div key={item.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                    <div>
                      <p className="font-semibold">{item.fatura_ref}</p>
                      <p className="text-sm text-slate-600">{formatCurrency(item.valor)}</p>
                    </div>
                    <Button size="sm" variant="primary">
                      Validar
                    </Button>
                  </div>
                ))
              )}
            </div>
            <Button variant="outline" className="w-full mt-4">
              Ver Todas
            </Button>
          </Card>

          {/* Atividade Recente */}
          <Card>
            <h2 className="text-lg font-semibold mb-4">Atividade Recente</h2>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-start gap-3 pb-3 border-b last:border-0">
                  <div className="h-8 w-8 rounded-full bg-agro-primary/10 flex items-center justify-center flex-shrink-0">
                    <Package className="h-4 w-4 text-agro-primary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Nova transação criada</p>
                    <p className="text-xs text-slate-600">Há 5 minutos</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Gráfico Placeholder */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">Transações por Mês</h2>
          <div className="h-64 bg-slate-50 rounded-xl flex items-center justify-center">
            <p className="text-slate-600">Gráfico de transações (integrar Chart.js)</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
