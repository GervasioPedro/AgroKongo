"use client";

import { useEffect } from "react";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8">
      <Card>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Ocorreu um erro</h1>
        <p className="mt-1 text-sm text-slate-600">
          Tenta novamente. Se a rede falhar, volta ao painel.
        </p>
        <div className="mt-6 flex gap-3">
          <Button onClick={reset}>Tentar novamente</Button>
          <Button variant="outline" asChild>
            <Link href="/dashboard">Ir ao Dashboard</Link>
          </Button>
        </div>
      </Card>
    </main>
  );
}
