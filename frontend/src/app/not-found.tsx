import Link from "next/link";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8">
      <Card>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Pagina nao encontrada</h1>
        <p className="mt-1 text-sm text-slate-600">
          Pode ter sido uma falha de ligacao. Tenta voltar ao painel.
        </p>
        <div className="mt-6">
          <Button asChild>
            <Link href="/dashboard">Voltar ao Dashboard</Link>
          </Button>
        </div>
      </Card>
    </main>
  );
}
