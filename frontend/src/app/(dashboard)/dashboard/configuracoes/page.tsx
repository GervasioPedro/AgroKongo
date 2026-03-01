import { Card } from "@/components/ui/card";

export default function ConfiguracoesPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8 safe-bottom">
      <header>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Configuracoes</h1>
        <p className="text-sm text-slate-600">Preferencias e seguranca</p>
      </header>

      <Card>
        <div className="space-y-2 text-sm text-slate-700">
          <div>
            <div className="font-semibold">Notificacoes</div>
            <div className="text-slate-600">Em breve: push e alertas por pagamento.</div>
          </div>
          <div>
            <div className="font-semibold">Seguranca</div>
            <div className="text-slate-600">Em breve: alterar senha e dispositivos.</div>
          </div>
        </div>
      </Card>
    </main>
  );
}
