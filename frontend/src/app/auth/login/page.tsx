"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sprout, ArrowRight, Eye, EyeOff } from "lucide-react";
import { http } from "@/services/http";
import { mutate } from "swr";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    telemovel: "",
    senha: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.telemovel || !formData.senha) {
      toast.error("Preencha todos os campos");
      return;
    }
    
    setLoading(true);

    try {
      const res = await http.post("/auth/login", {
        telemovel: formData.telemovel,
        senha: formData.senha,
      });

      const data = res.data as { ok: boolean; user?: { nome: string; tipo: string } ; message?: string };

      if (!data?.ok || !data?.user) {
        toast.error(data?.message || "Credenciais inválidas");
        setLoading(false);
        return;
      }

      toast.success(`Bem-vindo, ${data.user.nome}!`);
      setLoading(false);

      // Sincronizar sessão imediatamente no SWR
      try { await mutate('/auth/me'); } catch {}

      if (data.user.tipo === "admin") {
        router.push("/admin");
      } else if (data.user.tipo === "comprador") {
        router.push("/comprador");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      const apiMsg = err?.response?.data?.message || err?.response?.data?.mensagem;
      toast.error(apiMsg || "Não foi possível iniciar sessão");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-surface-neutral">
      {/* Header */}
      <header className="border-b bg-white px-4 py-4">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-agro-primary flex items-center justify-center">
              <Sprout className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold">AgroKongo</span>
          </Link>
          <Link href="/auth/cadastro/passo-1">
            <Button variant="outline" size="sm">Criar Conta</Button>
          </Link>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Bem-vindo de volta</h1>
          <p className="text-slate-600">Entre para continuar</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Telemóvel */}
            <div>
              <label className="text-sm font-medium mb-2 block">Telemóvel</label>
              <Input
                required
                placeholder="912345678"
                inputMode="numeric"
                value={formData.telemovel}
                onChange={(e) => setFormData({...formData, telemovel: e.target.value})}
                autoComplete="tel"
                className="h-12"
              />
            </div>

            {/* Senha */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Senha</label>
                <Link href="/auth/recuperar" className="text-xs text-agro-primary hover:underline">
                  Esqueceu a senha?
                </Link>
              </div>
              <div className="relative">
                <Input
                  required
                  type={showPassword ? "text" : "password"}
                  placeholder="Digite sua senha"
                  value={formData.senha}
                  onChange={(e) => setFormData({...formData, senha: e.target.value})}
                  autoComplete="current-password"
                  className="h-12 pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            {/* Botão */}
            <Button 
              type="submit" 
              variant="primary" 
              className="w-full h-12 text-lg mt-6"
              disabled={loading}
            >
              {loading ? "A entrar..." : "Entrar"}
              {!loading && <ArrowRight className="h-5 w-5 ml-2" />}
            </Button>

            {/* Link Registo */}
            <div className="text-center pt-4 border-t">
              <p className="text-sm text-slate-700">
                Não tens conta?{" "}
                <Link href="/auth/cadastro/passo-1" className="font-semibold text-agro-primary hover:underline">
                  Criar conta grátis
                </Link>
              </p>
            </div>
          </form>
        </Card>

      </main>
    </div>
  );
}
