"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sprout, ArrowRight, Shield } from "lucide-react";
import { http } from "@/services/http";
import toast from "react-hot-toast";

export default function CadastroPasso2() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) return;
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const codigo = otp.join("");

    if (codigo.length !== 6) {
      toast.error("Digite o código completo");
      return;
    }

    setLoading(true);

    try {
      const res = await http.post("/cadastro/passo-2", { codigo });
      
      if (res.data?.sucesso) {
        toast.success("Telefone validado!");
        router.push("/auth/cadastro/passo-3");
      } else {
        toast.error(res.data?.mensagem || "Código inválido");
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.mensagem || "Código inválido");
    } finally {
      setLoading(false);
    }
  };

  const handleReenviar = async () => {
    try {
      await http.post("/cadastro/reenviar-otp");
      toast.success("Novo código enviado via SMS!");
    } catch (error) {
      toast.error("Erro ao reenviar código");
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
            <span className="text-sm font-medium text-agro-primary">Passo 2 de 3</span>
          </div>
          <div className="h-16 w-16 rounded-full bg-escrow-primary/10 flex items-center justify-center mx-auto mb-4">
            <Shield className="h-8 w-8 text-escrow-primary" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Validar Telemóvel</h1>
          <p className="text-slate-600">Digite o código enviado via SMS</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex gap-2 justify-center">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  id={`otp-${index}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  className="w-12 h-14 text-center text-2xl font-bold border-2 rounded-xl focus:border-agro-primary focus:ring-2 focus:ring-agro-primary/20"
                />
              ))}
            </div>

            <Button 
              type="submit" 
              variant="primary" 
              className="w-full h-12 text-lg"
              disabled={loading || otp.join("").length !== 6}
            >
              {loading ? "A validar..." : "Validar Código"}
              {!loading && <ArrowRight className="h-5 w-5 ml-2" />}
            </Button>

            <div className="text-center">
              <p className="text-sm text-slate-600 mb-2">Não recebeu o código?</p>
              <Button 
                type="button" 
                variant="ghost" 
                size="sm"
                onClick={handleReenviar}
              >
                Reenviar via SMS
              </Button>
            </div>
          </form>
        </Card>

        <div className="mt-8">
          <div className="flex justify-between text-xs text-slate-600 mb-2">
            <span>Progresso</span>
            <span>66%</span>
          </div>
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div className="h-full bg-agro-primary w-2/3 transition-all"></div>
          </div>
        </div>
      </main>
    </div>
  );
}
