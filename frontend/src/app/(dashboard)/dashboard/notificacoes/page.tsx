"use client";

import useSWR from "swr";
import { http } from "@/services/http";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import toast from "react-hot-toast";

 type Notificacao = {
  id: number;
  titulo: string;
  mensagem: string;
  lida: boolean;
  criada_em: string; // ISO
};

type NotificacoesPayload = {
  ok: boolean;
  items: Notificacao[];
};

const fetcher = async (url: string) => {
  if (!url.startsWith('/notificacoes')) throw new Error('URL não permitida');
  const res = await http.get(url);
  return res.data as NotificacoesPayload;
};

export default function NotificacoesPage() {
  const { data, isLoading, error, mutate } = useSWR<NotificacoesPayload>("/notificacoes", fetcher, {
    revalidateOnFocus: true
  });

  const marcarComoLida = async (id: number) => {
    try {
      await http.post(`/notificacoes/${id}/lida`);
      toast.success("Marcada como lida");
      mutate();
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.response?.data?.mensagem;
      toast.error(msg || "Não foi possível marcar como lida");
    }
  };

  const items = data?.items ?? [];

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8 safe-bottom">
      <header>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Alertas</h1>
        <p className="text-sm text-slate-600">Mensagens claras em portugues</p>
      </header>

      <Card>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : error ? (
          <div className="text-sm text-alert-critical">
            Não foi possível carregar notificações. Tenta novamente mais tarde.
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-700">
            Ainda nao tens notificacoes.
          </p>
        ) : (
          <div className="space-y-3">
            {items.map((n) => (
              <div key={n.id} className="flex items-start justify-between rounded-[14px] bg-white p-4 shadow-card-soft">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900">{n.titulo}</span>
                    {!n.lida && <span className="inline-flex h-2 w-2 rounded-full bg-escrow-primary" />}
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{n.mensagem}</p>
                  <p className="text-[11px] text-slate-400 mt-1">{new Date(n.criada_em).toLocaleString('pt-AO')}</p>
                </div>
                {!n.lida && (
                  <Button size="sm" variant="outline" onClick={() => marcarComoLida(n.id)}>
                    Marcar como lida
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </main>
  );
}
