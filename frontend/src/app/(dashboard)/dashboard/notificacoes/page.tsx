import { Card } from "@/components/ui/card";

export default function NotificacoesPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8 safe-bottom">
      <header>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Alertas</h1>
        <p className="text-sm text-slate-600">Mensagens claras em portugues</p>
      </header>

      <Card>
        <p className="text-sm text-slate-700">
          Ainda nao tens notificacoes. Quando houver um pagamento pendente, vais ver o estado aqui.
        </p>
      </Card>
    </main>
  );
}
