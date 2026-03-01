import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/utils/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-800 border border-slate-200",
        alert: "bg-yellow-100 text-yellow-800 border border-yellow-200",
      },
      status: {
        pendente: "bg-yellow-100 text-yellow-800 border border-yellow-200",
        analise: "bg-blue-100 text-blue-800 border border-blue-200",
        escrow: "bg-escrow-primary/10 text-escrow-primary border border-escrow-primary/20",
        enviado: "bg-purple-100 text-purple-800 border border-purple-200",
        entregue: "bg-green-100 text-green-800 border border-green-200",
        finalizado: "bg-agro-primary/10 text-agro-primary border border-agro-primary/20",
        disputa: "bg-red-100 text-red-800 border border-red-200",
        cancelado: "bg-gray-100 text-gray-600 border border-gray-200",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

const statusIcons: Record<string, string> = {
  pendente: "⏳",
  analise: "🔍",
  escrow: "🔒",
  enviado: "📦",
  entregue: "✅",
  finalizado: "🎉",
  disputa: "⚠️",
  cancelado: "❌",
};

const statusLabels: Record<string, string> = {
  pendente: "Aguardando Pagamento",
  analise: "Em Análise",
  escrow: "Em Custódia",
  enviado: "Mercadoria Enviada",
  entregue: "Entregue",
  finalizado: "Finalizado",
  disputa: "Em Disputa",
  cancelado: "Cancelado",
};

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  showIcon?: boolean;
  customLabel?: string;
}

export function Badge({
  className,
  variant,
  status,
  showIcon = true,
  customLabel,
  children,
  ...props
}: BadgeProps) {
  const statusKey = status || "default";
  
  return (
    <div className={cn(badgeVariants({ variant, status }), className)} {...props}>
      {showIcon && statusIcons[statusKey] && <span>{statusIcons[statusKey]}</span>}
      <span>{customLabel || children || statusLabels[statusKey] || ""}</span>
    </div>
  );
}
