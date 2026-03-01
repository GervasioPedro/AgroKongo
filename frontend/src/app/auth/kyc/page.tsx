"use client";

import toast from "react-hot-toast";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StepIndicator } from "@/components/dashboard/step-indicator";

export default function KycPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8">
      <Card>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Completar perfil (KYC)</h1>
        <p className="mt-1 text-sm text-slate-600">
          Precisamos destes dados para proteger o teu dinheiro no escrow.
        </p>

        <StepIndicator
          className="mt-4"
          steps={[
            { label: "Dados", state: "active" },
            { label: "Documentos", state: "todo" },
            { label: "Validacao", state: "todo" }
          ]}
        />

        <form
          className="mt-6 flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            toast.success("Dados submetidos. O admin vai validar.");
          }}
        >
          <label className="text-sm font-medium">NIF</label>
          <Input placeholder="Ex: 123456789LA012" />

          <label className="mt-2 text-sm font-medium">Provincia</label>
          <Input placeholder="Ex: Luanda" />

          <label className="mt-2 text-sm font-medium">Municipio</label>
          <Input placeholder="Ex: Viana" />

          <label className="mt-2 text-sm font-medium">IBAN (Produtor)</label>
          <Input placeholder="AO06..." />

          <label className="mt-2 text-sm font-medium">Documento (PDF)</label>
          <input className="text-sm" type="file" accept="application/pdf" />

          <Button className="mt-4" type="submit">
            Submeter para validacao
          </Button>

          <p className="text-xs text-slate-500">
            Se aparecer "O numero do BI parece estar incompleto", confirma o documento.
          </p>
        </form>
      </Card>
    </main>
  );
}
