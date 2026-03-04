"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sprout, ArrowRight, Lock, Eye, EyeOff } from "lucide-react";
import { http } from "@/services/http";
import toast from "react-hot-toast";

import { redirect } from "next/navigation";

export default function CadastroPasso4() {
  const router = useRouter();
  // Redireciona automaticamente para o passo-3 (fluxo consolidado em 3 passos)
  useEffect(() => {
    router.replace('/auth/cadastro/passo-3');
  }, [router]);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    senha: "",
    confirmar_senha: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.senha.length < 4 || formData.senha.length > 6) {
      toast.error("Use um PIN de 4 a 6 dígitos");
      return;
    }

    if (!/^\d+$/.test(formData.senha)) {
      toast.error("Use apenas números");
      return;
    }

    if (formData.senha !== formData.confirmar_senha) {
      toast.error("As senhas não coincidem");
      return;
    }

    setLoading(true);

    try {
      const res = await http.post("/cadastro/definir-senha", { senha: formData.senha });
      
      if (res.data?.sucesso) {
        toast.success("Senha definida!");
        router.push("/auth/cadastro/passo-5");
      } else {
        toast.error(res.data?.mensagem || "Erro ao definir senha");
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.mensagem || "Erro ao processar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-surface-neutral">
      <header className="border-b bg-white px-4 py-4">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-agro-primary flex items-center justify-center">
              <Sprout className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold">AgroKongo</span>
          </Link>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-agro-primary/10 px-4 py-2 rounded-full mb-4">
            <span className="text-sm font-medium text-agro-primary">Passo 4 de 5</span>
          </div>
          <div className="h-16 w-16 rounded-full bg-escrow-primary/10 flex items-center justify-center mx-auto mb-4">
            <Lock className="h-8 w-8 text-escrow-primary" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Definir Senha</h1>
          <p className="text-slate-600">Crie um PIN de 4 a 6 dígitos</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-2 block">PIN (4-6 dígitos)</label>
              <div className="relative">
                <input
                  required
                  type={showPassword ? "text" : "password"}
                  inputMode="numeric"
                  placeholder="Digite seu PIN"
                  value={formData.senha}
                  onChange={(e) => setFormData({...formData, senha: e.target.value.replace(/\D/g, "")})}
                  maxLength={6}
                  className="w-full h-14 px-4 pr-12 border-2 rounded-xl text-2xl text-center font-bold focus:ring-2 focus:ring-agro-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              <p className="text-xs text-slate-600 mt-2">
                Use números fáceis de memorizar
              </p>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Confirmar PIN</label>
              <input
                required
                type={showPassword ? "text" : "password"}
                inputMode="numeric"
                placeholder="Digite novamente"
                value={formData.confirmar_senha}
                onChange={(e) => setFormData({...formData, confirmar_senha: e.target.value.replace(/\D/g, "")})}
                maxLength={6}
                className="w-full h-14 px-4 border-2 rounded-xl text-2xl text-center font-bold focus:ring-2 focus:ring-agro-primary"
              />
            </div>

            <Button 
              type="submit" 
              variant="primary" 
              className="w-full h-12 text-lg"
              disabled={loading || formData.senha.length < 4}
            >
              {loading ? "A salvar..." : "Continuar"}
              {!loading && <ArrowRight className="h-5 w-5 ml-2" />}
            </Button>
          </form>
        </Card>

        {/* Progresso */}
        <div className="mt-8">
          <div className="flex justify-between text-xs text-slate-600 mb-2">
            <span>Progresso</span>
            <span>80%</span>
          </div>
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div className="h-full bg-agro-primary w-4/5 transition-all"></div>
          </div>
        </div>
      </main>
    </div>
  );
}
