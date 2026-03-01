"use client";

import { useAuth } from "@/hooks/useAuth";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/shared/page-header";
import { formatCurrency, formatDateTime } from "@/utils/format";
import { CheckCircle, XCircle, Eye, Download } from "lucide-react";
import { http } from "@/services/http";

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function ValidacoesPage() {
  const { user } = useAuth();
  const { data, isLoading, mutate } = useSWR("/admin/validacoes", fetcher);

  const pendentes = data?.pendentes || [];

  const handleValidar = async (id: number) => {
    try {
      await http.post(`/admin/validar/${id}`);
      mutate();
    } catch (error) {
      alert("Erro ao validar");
    }
  };

  const handleRejeitar = async (id: number) => {
    const motivo = prompt("Motivo da rejeição:");
    if (!motivo) return;
    try {
      await http.post(`/admin/rejeitar/${id}`, { motivo });
      mutate();
    } catch (error) {
      alert("Erro ao rejeitar");
    }
  };

  if (user?.tipo !== "admin") {
    return <div className="p-6">Acesso negado</div>;
  }

  return (
    <div className="min-h-screen">
      <PageHeader 
        title="Validações Pendentes"
        subtitle={`${pendentes.length} pagamentos aguardando validação`}
        showBack={false}
      />

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6">
        {isLoading ? (
          <div className="text-center py-12">A carregar...</div>
        ) : pendentes.length === 0 ? (
          <Card className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <p className="text-lg font-semibold mb-2">Tudo validado!</p>
            <p className="text-slate-600">Nenhum pagamento pendente de validação</p>
          </Card>
        ) : (
          <div className="space-y-4">
            {pendentes.map((item: any) => (
              <Card key={item.id} className="hover:shadow-lg transition-shadow">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge status="analise">Em Análise</Badge>
                      <span className="font-mono text-sm text-slate-600">{item.fatura_ref}</span>
                    </div>
                    <h3 className="font-semibold text-lg mb-1">{item.produto}</h3>
                    <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                      <span>Comprador: {item.comprador}</span>
                      <span>Vendedor: {item.vendedor}</span>
                      <span>{formatDateTime(item.data_criacao)}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-600">Valor</p>
                    <p className="text-2xl font-bold text-agro-primary">
                      {formatCurrency(item.valor)}
                    </p>
                  </div>
                  <div className="flex flex-col gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => window.open(item.comprovativo_url, '_blank')}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      Ver Comprovativo
                    </Button>
                    <Button 
                      variant="primary" 
                      size="sm"
                      onClick={() => handleValidar(item.id)}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Validar
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => handleRejeitar(item.id)}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Rejeitar
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
