"use client";

import { Wallet, Bell, User } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StepIndicator } from "@/components/dashboard/step-indicator";
import { Badge } from "@/components/ui/badge";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { formatKz } from "@/utils/format";
import { http } from "@/services/http";

type Kpis = {
  receita_total: number;
  em_custodia: number;
  a_liquidar: number;
  disponivel: number;
};

type Tx = {
  id: number;
  fatura_ref: string | null;
  status: string;
  produto: string | null;
  quantidade: number | null;
  valor: number | null;
  data: string | null;
};

type ProdutorDashboardPayload = {
  kpis: Kpis;
  listas: {
    reservas: Tx[];
    ativas: Tx[];
    historico: Tx[];
  };
  perfil: {
    conta_validada: boolean;
    perfil_completo: boolean;
  };
};

const fetcher = async (url: string) => {
  // Proteção SSRF: validar por prefixo e permitir query params
  if (!url.startsWith('/produtor/dashboard')) {
    throw new Error('URL não permitida');
  }
  const res = await http.get(url);
  return res.data as ProdutorDashboardPayload;
};

export default function DashboardPage() {
  const { data, isLoading } = useSWR<ProdutorDashboardPayload>(
    "/produtor/dashboard",
    fetcher,
    { revalidateOnFocus: true }
  );

  const kpis = data?.kpis;

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8 safe-bottom">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-[-0.02em]">Dashboard</h1>
          <p className="text-sm text-slate-600">Painel do produtor</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/notificacoes"
            className="inline-flex h-10 w-10 items-center justify-center rounded-[14px] bg-white shadow-card-soft"
            aria-label="Abrir notificacoes"
          >
            <Bell className="h-5 w-5 text-escrow-primary" />
          </Link>
          <Link
            href="/dashboard/perfil"
            className="inline-flex h-10 w-10 items-center justify-center rounded-[14px] bg-white shadow-card-soft"
            aria-label="Abrir perfil"
          >
            <User className="h-5 w-5 text-slate-700" />
          </Link>
          <Link
            href="/dashboard/carteira"
            className="inline-flex h-10 w-10 items-center justify-center rounded-[14px] bg-white shadow-card-soft"
            aria-label="Abrir carteira"
          >
            <Wallet className="h-5 w-5 text-agro-primary" />
          </Link>
        </div>
      </header>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold">Estado da conta</h2>
            <p className="mt-1 text-sm text-slate-600">
              {isLoading
                ? "A carregar..."
                : data?.perfil.conta_validada
                  ? "Conta validada. Podes publicar e vender."
                  : "Conta por validar. O admin está a rever os teus documentos."}
            </p>
          </div>
          <Badge variant={data?.perfil.conta_validada ? "default" : "alert"}>
            {isLoading ? "..." : data?.perfil.conta_validada ? "Verificada" : "Em validação"}
          </Badge>
        </div>
      </Card>

      <section className="grid grid-cols-2 gap-3">
        <KpiCard
          title="Disponivel"
          value={isLoading ? "..." : formatKz(kpis?.disponivel ?? 0)}
        />
        <KpiCard
          title="Em custodia"
          tone="escrow"
          value={isLoading ? "..." : formatKz(kpis?.em_custodia ?? 0)}
        />
        <KpiCard
          title="A liquidar"
          tone="alert"
          value={isLoading ? "..." : formatKz(kpis?.a_liquidar ?? 0)}
        />
        <KpiCard
          title="Receita total"
          value={isLoading ? "..." : formatKz(kpis?.receita_total ?? 0)}
        />
      </section>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold">Carteira</h2>
            <p className="mt-1 text-sm text-slate-600">Ver saldo e movimentos</p>
          </div>
          <Link href="/dashboard/carteira" className="text-sm font-semibold text-agro-primary">
            Abrir
          </Link>
        </div>
      </Card>

      <Card>
        <h2 className="text-base font-semibold">Reservas</h2>
        <p className="mt-1 text-sm text-slate-600">Aguardam o teu aceite</p>

        <div className="mt-4 space-y-3">
          {isLoading ? (
            <>
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </>
          ) : (data?.listas.reservas ?? []).length === 0 ? (
            <div className="rounded-[14px] bg-surface-neutral p-4 text-sm text-slate-600">
              Sem reservas no momento.
            </div>
          ) : (
            (data?.listas.reservas ?? []).map((t) => (
              <div key={t.id} className="rounded-[14px] bg-white p-4 shadow-card-soft">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold">{t.produto ?? "Produto"}</div>
                  <Badge variant="alert">Pendente</Badge>
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {t.quantidade ? `${t.quantidade} kg` : ""} {t.valor ? `- ${formatKz(t.valor)}` : ""}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      <Card>
        <h2 className="text-base font-semibold">Validacao de comprovativo</h2>
        <p className="mt-1 text-sm text-slate-600">
          Feedback visual para aumentar confianca enquanto o admin valida.
        </p>
        <StepIndicator
          className="mt-4"
          steps={[
            { label: "Carregado", state: "done" },
            { label: "Em validacao", state: "active" },
            { label: "Aprovado", state: "todo" }
          ]}
        />
      </Card>

      <Card>
        <h2 className="text-base font-semibold">Carregamento (3G)</h2>
        <p className="mt-1 text-sm text-slate-600">
          Skeleton loader evita ecras brancos enquanto os dados chegam.
        </p>
        <div className="mt-4 space-y-2">
          <Skeleton className="h-4 w-3/5" />
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-10 w-full" />
        </div>
      </Card>
    </main>
  );
}
