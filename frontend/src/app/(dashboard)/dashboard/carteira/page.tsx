"use client";

import Link from "next/link";
import useSWR from "swr";
import { ArrowLeft, Wallet } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatKz } from "@/utils/format";
import { http } from "@/services/http";
import { useWalletStore } from "@/store/wallet";

type WalletResumo = {
  saldoDisponivelKz: number;
  saldoEscrowKz: number;
  pendentes: number;
};

type Movimento = {
  id: string;
  tipo: "credito" | "debito" | "escrow";
  valorKz: number;
  descricao: string;
  createdAtISO: string;
};

type WalletPayload = {
  resumo: WalletResumo;
  movimentos: Movimento[];
};

const fetcher = async (url: string) => {
  // Proteção SSRF: validar URL por prefixo e permitir query params
  if (!url.startsWith('/wallet')) {
    throw new Error('URL não permitida');
  }
  const res = await http.get(url);
  return res.data as WalletPayload;
};

export default function CarteiraPage() {
  const { setResumo, saldoDisponivelKz, saldoEscrowKz, pendentes } = useWalletStore();

  const { data, isLoading, error } = useSWR<WalletPayload>("/wallet", fetcher, {
    revalidateOnFocus: true
  });

  if (data) {
    // sincroniza para estado global
    setResumo(data.resumo);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8 safe-bottom">
      <header className="flex items-center gap-3">
        <Link
          href="/dashboard"
          className="inline-flex h-10 w-10 items-center justify-center rounded-[14px] bg-white shadow-card-soft"
          aria-label="Voltar"
        >
          <ArrowLeft className="h-5 w-5 text-slate-700" />
        </Link>
        <div className="flex flex-col">
          <h1 className="text-xl font-bold tracking-[-0.02em]">Carteira</h1>
          <p className="text-sm text-slate-600">Transparencia do teu dinheiro seguro</p>
        </div>
      </header>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-slate-600">Saldo disponivel</div>
            <div className="mt-1 text-2xl font-semibold">
              {isLoading ? <Skeleton className="h-7 w-40" /> : formatKz(saldoDisponivelKz)}
            </div>
          </div>
          <div className="inline-flex h-10 w-10 items-center justify-center rounded-[14px] bg-escrow-light/15">
            <Wallet className="h-5 w-5 text-escrow-primary" />
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-[14px] bg-surface-neutral p-3">
            <div className="text-xs text-slate-600">Em escrow</div>
            <div className="text-base font-semibold">
              {isLoading ? <Skeleton className="h-5 w-24" /> : formatKz(saldoEscrowKz)}
            </div>
          </div>
          <div className="rounded-[14px] bg-surface-neutral p-3">
            <div className="text-xs text-slate-600">Pendentes</div>
            <div className="text-base font-semibold">
              {isLoading ? <Skeleton className="h-5 w-10" /> : pendentes}
            </div>
          </div>
        </div>

        {error ? (
          <p className="mt-4 text-sm text-alert-critical">
            Nao foi possivel carregar a carteira. Verifica a tua ligacao e tenta novamente.
          </p>
        ) : null}
      </Card>

      <Card>
        <h2 className="text-base font-semibold">Movimentos</h2>
        <p className="mt-1 text-sm text-slate-600">
          Lista clara para evitar duvidas e reduzir suporte.
        </p>

        <div className="mt-4 space-y-3">
          {isLoading ? (
            <>
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </>
          ) : (data?.movimentos ?? []).length === 0 ? (
            <div className="rounded-[14px] bg-surface-neutral p-4 text-sm text-slate-600">
              Ainda nao existem movimentos.
            </div>
          ) : (
            (data?.movimentos ?? []).map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded-[14px] bg-white p-4 shadow-card-soft"
              >
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-slate-900">{m.descricao}</span>
                  <span className="text-xs text-slate-500">{new Date(m.createdAtISO).toLocaleString("pt-AO")}</span>
                </div>
                <div
                  className={
                    "text-sm font-semibold " +
                    (m.tipo === "debito" ? "text-alert-critical" : "text-agro-primary")
                  }
                >
                  {m.tipo === "debito" ? "-" : "+"}
                  {formatKz(m.valorKz)}
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </main>
  );
}
