"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { http } from "@/services/http";
import toast from "react-hot-toast";

export default function ConfiguracoesPage() {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    senha_atual: "",
    nova_senha: "",
    confirmar_senha: "",
  });

  async function alterarSenha(e: React.FormEvent) {
    e.preventDefault();

    if (!form.senha_atual || !form.nova_senha || !form.confirmar_senha) {
      toast.error("Preencha todos os campos");
      return;
    }
    if (form.nova_senha.length < 6) {
      toast.error("A nova senha deve ter no mínimo 6 caracteres");
      return;
    }
    if (form.nova_senha !== form.confirmar_senha) {
      toast.error("As senhas não coincidem");
      return;
    }

    setLoading(true);
    try {
      const res = await http.put("/profile/change-password", {
        senha_atual: form.senha_atual,
        nova_senha: form.nova_senha,
      });
      if (res.data?.ok) {
        toast.success(res.data?.message || "Senha alterada com sucesso");
        setForm({ senha_atual: "", nova_senha: "", confirmar_senha: "" });
      } else {
        toast.error(res.data?.message || "Não foi possível alterar a senha");
      }
    } catch (err: any) {
      const status = err?.response?.status;
      const apiMsg = err?.response?.data?.message || err?.response?.data?.mensagem;
      if (status === 403) {
        toast.error(apiMsg || "A senha atual está incorreta");
      } else if (status === 400) {
        toast.error(apiMsg || "Dados inválidos");
      } else {
        toast.error(apiMsg || "Erro ao alterar a senha");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-6 py-8 safe-bottom">
      <header>
        <h1 className="text-xl font-bold tracking-[-0.02em]">Configurações</h1>
        <p className="text-sm text-slate-600">Preferências e segurança</p>
      </header>

      <Card>
        <h2 className="text-base font-semibold">Alterar senha</h2>
        <p className="mt-1 text-sm text-slate-600">Mantenha a sua conta protegida atualizando a senha periodicamente.</p>

        <form onSubmit={alterarSenha} className="mt-4 space-y-3">
          <div>
            <label className="text-sm font-medium mb-1 block">Senha atual</label>
            <Input
              type="password"
              value={form.senha_atual}
              onChange={(e) => setForm({ ...form, senha_atual: e.target.value })}
              autoComplete="current-password"
              className="h-11"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Nova senha</label>
            <Input
              type="password"
              value={form.nova_senha}
              onChange={(e) => setForm({ ...form, nova_senha: e.target.value })}
              autoComplete="new-password"
              className="h-11"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Confirmar nova senha</label>
            <Input
              type="password"
              value={form.confirmar_senha}
              onChange={(e) => setForm({ ...form, confirmar_senha: e.target.value })}
              autoComplete="new-password"
              className="h-11"
              required
            />
          </div>

          <div className="pt-2">
            <Button type="submit" disabled={loading} className="h-11">
              {loading ? "A guardar..." : "Guardar alterações"}
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="text-base font-semibold">Notificações</h2>
        <p className="mt-1 text-sm text-slate-600">Preferências de alerta (placeholder). Em breve.</p>
        <div className="mt-3 text-sm text-slate-600">Brevemente poderás configurar alertas de pagamentos e mensagens.</div>
      </Card>
    </main>
  );
}
