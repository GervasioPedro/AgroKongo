"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import toast from "react-hot-toast";
import { mutate } from "swr";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { http } from "@/services/http";

type MePayload = {
  ok: boolean;
  user?: {
    id: number;
    nome: string;
    telemovel: string;
    tipo: string;
    perfil_completo: boolean;
    conta_validada: boolean;
  };
  message?: string;
};

const fetcher = async (url: string) => {
  // Proteção SSRF: validar URL antes de fazer requisição
  const allowedPaths = ['/auth/me', '/auth/logout'];
  if (!allowedPaths.includes(url)) {
    throw new Error('URL não permitida');
  }
  const res = await http.get(url);
  return res.data as MePayload;
};

export default function PerfilPage() {
  const router = useRouter();
  const { data, isLoading } = useSWR<MePayload>("/auth/me", fetcher, {
    revalidateOnFocus: true
  });

  async function logout() {
    try {
      await http.post("/auth/logout");
      // Invalidar cache da sessão imediatamente
      try { await mutate('/auth/me', null, false); } catch {}
      toast.success("Sessao terminada.");
      router.push("/auth/login");
    } catch {
      toast.error("Nao foi possivel terminar sessao.");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8 safe-bottom">
      <header>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Perfil</h1>
        <p className="text-sm text-slate-600">Dados da tua conta</p>
      </header>

      <Card>
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-56" />
          </div>
        ) : data?.ok && data.user ? (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="text-base font-semibold">{data.user.nome}</div>
              <Badge variant={data.user.conta_validada ? "default" : "alert"}>
                {data.user.conta_validada ? "Verificada" : "Em validacao"}
              </Badge>
            </div>
            <div className="text-sm text-slate-600">{data.user.telemovel}</div>
            <div className="text-sm text-slate-600">Tipo: {data.user.tipo}</div>

            {!data.user.perfil_completo ? (
              <Link className="mt-2 text-sm font-semibold text-agro-primary" href="/auth/kyc">
                Completar perfil (KYC)
              </Link>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-slate-700">Nao autenticado.</p>
        )}
      </Card>

      <Card>
        <div className="flex flex-col gap-3">
          <Button variant="outline" asChild>
            <Link href="/dashboard/configuracoes">Configuracoes</Link>
          </Button>
          <Button onClick={logout}>Terminar sessao</Button>
        </div>
      </Card>
    </main>
  );
}
