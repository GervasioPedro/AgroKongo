import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/utils/format";
import { ArrowRight, Lock } from "lucide-react";

type TransactionStatus = 
  | "pendente" 
  | "analise" 
  | "escrow" 
  | "enviado" 
  | "entregue" 
  | "finalizado" 
  | "disputa" 
  | "cancelado";

interface TransactionCardProps {
  id: number;
  faturaRef: string;
  status: TransactionStatus;
  produto: string;
  quantidade: number;
  valorTotal: number;
  dataCompra: string;
  nomeOutraParte: string; // Comprador ou Vendedor
  tipoUsuario: "produtor" | "comprador";
  onAction?: () => void;
}

export function TransactionCard({
  id,
  faturaRef,
  status,
  produto,
  quantidade,
  valorTotal,
  dataCompra,
  nomeOutraParte,
  tipoUsuario,
  onAction,
}: TransactionCardProps) {
  // Determinar borda colorida baseada no status
  const borderClass = {
    pendente: "border-l-4 border-alert-pending",
    analise: "border-l-4 border-blue-500",
    escrow: "border-l-4 border-escrow-primary",
    enviado: "border-l-4 border-purple-500",
    entregue: "border-l-4 border-green-500",
    finalizado: "border-l-4 border-agro-primary",
    disputa: "border-l-4 border-red-500",
    cancelado: "border-l-4 border-gray-400",
  }[status];

  // Determinar ação do botão
  const getActionButton = () => {
    if (status === "pendente" && tipoUsuario === "comprador") {
      return (
        <Button size="sm" variant="primary" onClick={onAction}>
          Enviar Comprovativo
        </Button>
      );
    }
    if (status === "escrow" && tipoUsuario === "produtor") {
      return (
        <Button size="sm" variant="escrow" onClick={onAction}>
          Confirmar Envio
        </Button>
      );
    }
    if (status === "enviado" && tipoUsuario === "comprador") {
      return (
        <Button size="sm" variant="primary" onClick={onAction}>
          Confirmar Receção
        </Button>
      );
    }
    return (
      <Button size="sm" variant="ghost" onClick={onAction}>
        Ver Detalhes <ArrowRight className="h-4 w-4 ml-1" />
      </Button>
    );
  };

  return (
    <Card className={`${borderClass} hover:shadow-md transition-shadow`}>
      <div className="flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs text-slate-500">Ref: {faturaRef}</p>
            <h3 className="font-semibold text-base mt-0.5">{produto}</h3>
            <p className="text-sm text-slate-600">
              {tipoUsuario === "produtor" ? "Comprador" : "Vendedor"}: {nomeOutraParte}
            </p>
          </div>
          <Badge status={status} />
        </div>

        {/* Valores */}
        <div className="flex items-center justify-between py-2 border-t border-slate-100">
          <div>
            <p className="text-xs text-slate-500">Quantidade</p>
            <p className="font-medium">{quantidade} kg</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-500">Valor Total</p>
            <p className="font-bold text-lg">{formatCurrency(valorTotal, "AOA")}</p>
          </div>
        </div>

        {/* Indicador Escrow */}
        {status === "escrow" && (
          <div className="flex items-center gap-2 p-2 bg-escrow-primary/5 rounded-lg">
            <Lock className="h-4 w-4 text-escrow-primary" />
            <p className="text-xs text-escrow-primary font-medium">
              💰 Dinheiro protegido em custódia
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <p className="text-xs text-slate-500">{dataCompra}</p>
          {getActionButton()}
        </div>
      </div>
    </Card>
  );
}
