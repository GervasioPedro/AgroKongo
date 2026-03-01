"use client";

import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/shared/page-header";
import { formatCurrency, formatWeight, formatDateTime } from "@/utils/format";
import { 
  User, Package, MapPin, Calendar, 
  Upload, CheckCircle, Truck, AlertCircle 
} from "lucide-react";
import { http } from "@/services/http";

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function TransacaoDetalhePage() {
  const params = useParams();
  const router = useRouter();
  const { data, isLoading } = useSWR(`/transacao/${params.id}`, fetcher);

  const transacao = data?.transacao;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-agro-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-600">A carregar...</p>
        </div>
      </div>
    );
  }

  if (!transacao) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center p-8">
          <AlertCircle className="h-16 w-16 text-slate-400 mx-auto mb-4" />
          <p className="text-slate-600 mb-4">Transação não encontrada</p>
          <Button variant="primary" onClick={() => router.push("/dashboard")}>
            Voltar ao Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-neutral">
      <PageHeader 
        title="Detalhes da Transação"
        subtitle={transacao.fatura_ref}
        backUrl="/dashboard/vendas"
      />

      <div className="max-w-5xl mx-auto px-4 lg:px-8 py-6 space-y-6">
        {/* Status Card */}
        <Card className="bg-gradient-to-r from-agro-primary/5 to-escrow-primary/5">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <Badge status={transacao.status} className="mb-2" />
              <h2 className="text-2xl font-bold">{transacao.safra.produto}</h2>
              <p className="text-slate-600">Ref: {transacao.fatura_ref}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-600">Valor Total</p>
              <p className="text-3xl font-bold text-agro-primary">
                {formatCurrency(transacao.valor_total_pago)}
              </p>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Detalhes do Pedido */}
          <Card>
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Package className="h-5 w-5" />
              Detalhes do Pedido
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-600">Produto</span>
                <span className="font-semibold">{transacao.safra.produto}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Quantidade</span>
                <span className="font-semibold">{formatWeight(transacao.quantidade_comprada)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Preço/kg</span>
                <span className="font-semibold">
                  {formatCurrency(transacao.valor_total_pago / transacao.quantidade_comprada)}
                </span>
              </div>
              <div className="flex justify-between pt-3 border-t">
                <span className="text-slate-600 font-medium">Total</span>
                <span className="font-bold text-lg">{formatCurrency(transacao.valor_total_pago)}</span>
              </div>
            </div>
          </Card>

          {/* Partes Envolvidas */}
          <Card>
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <User className="h-5 w-5" />
              Partes Envolvidas
            </h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-600 mb-2">Vendedor</p>
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-full bg-agro-primary/10 flex items-center justify-center">
                    <User className="h-6 w-6 text-agro-primary" />
                  </div>
                  <div>
                    <p className="font-semibold">{transacao.vendedor.nome}</p>
                    <div className="flex items-center gap-1 text-xs text-slate-600">
                      <MapPin className="h-3 w-3" />
                      <span>{transacao.vendedor.provincia}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-600 mb-2">Comprador</p>
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-semibold">{transacao.comprador.nome}</p>
                    <div className="flex items-center gap-1 text-xs text-slate-600">
                      <MapPin className="h-3 w-3" />
                      <span>{transacao.comprador.provincia}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Timeline */}
        <Card>
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Histórico da Transação
          </h3>
          <div className="space-y-4">
            {transacao.historico?.map((evento: any, index: number) => (
              <div key={index} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="h-10 w-10 rounded-full bg-agro-primary/10 flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 text-agro-primary" />
                  </div>
                  {index < transacao.historico.length - 1 && (
                    <div className="w-0.5 flex-1 bg-slate-200 mt-2" />
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <p className="font-semibold">{evento.status}</p>
                  <p className="text-sm text-slate-600">{evento.observacoes}</p>
                  <p className="text-xs text-slate-500 mt-1">{formatDateTime(evento.data)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Ações Contextuais */}
        {transacao.status === "pendente" && (
          <Card className="bg-yellow-50 border-yellow-200">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div>
                <h3 className="font-semibold mb-1 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                  Ação Necessária
                </h3>
                <p className="text-sm text-slate-600">Envie o comprovativo de pagamento para prosseguir</p>
              </div>
              <Button variant="primary">
                <Upload className="h-4 w-4 mr-2" />
                Enviar Comprovativo
              </Button>
            </div>
          </Card>
        )}

        {transacao.status === "escrow" && (
          <Card className="bg-escrow-primary/5 border-escrow-primary">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div>
                <h3 className="font-semibold mb-1 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-escrow-primary" />
                  Dinheiro em Custódia
                </h3>
                <p className="text-sm text-slate-600">Pode enviar a mercadoria com segurança</p>
              </div>
              <Button variant="escrow">
                <Truck className="h-4 w-4 mr-2" />
                Confirmar Envio
              </Button>
            </div>
          </Card>
        )}

        {/* Botões de Navegação */}
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => router.push("/dashboard/vendas")} className="flex-1">
            Ver Todas as Vendas
          </Button>
          <Button variant="outline" onClick={() => router.push("/dashboard")} className="flex-1">
            Ir para Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
