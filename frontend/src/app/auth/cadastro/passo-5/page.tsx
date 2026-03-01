"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sprout, ArrowRight, CreditCard, Upload, CheckCircle } from "lucide-react";
import { http } from "@/services/http";
import toast from "react-hot-toast";

export default function CadastroPasso5() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [iban, setIban] = useState("");
  const [biFile, setBiFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!iban.startsWith("AO06") || iban.length !== 27) {
      toast.error("IBAN inválido. Use formato AO06 + 21 dígitos");
      return;
    }

    if (!biFile) {
      toast.error("Upload do BI é obrigatório");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("iban", iban);
      formData.append("bi_file", biFile);

      const res = await http.post("/cadastro/dados-financeiros", formData);
      
      if (res.data?.sucesso) {
        toast.success("Conta criada com sucesso!");
        router.push("/dashboard");
      } else {
        toast.error(res.data?.mensagem || "Erro ao finalizar cadastro");
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
            <span className="text-sm font-medium text-agro-primary">Passo 5 de 5 - Final</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Dados Financeiros</h1>
          <p className="text-slate-600">Para receber pagamentos com segurança</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* IBAN */}
            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <CreditCard className="h-4 w-4" />
                IBAN (Conta Bancária)
              </label>
              <Input
                required
                placeholder="AO06000000000000000000000"
                value={iban}
                onChange={(e) => setIban(e.target.value.toUpperCase().replace(/\s/g, ""))}
                maxLength={27}
                className="h-12 font-mono"
              />
              <p className="text-xs text-slate-600 mt-2">
                Formato: AO06 + 21 dígitos (ex: AO06000123456789012345678)
              </p>
            </div>

            {/* Upload BI */}
            <div>
              <label className="text-sm font-medium mb-2 block">Bilhete de Identidade</label>
              <div className="border-2 border-dashed rounded-xl p-6 text-center hover:border-agro-primary transition-colors">
                <input
                  type="file"
                  accept="image/*,application/pdf"
                  onChange={(e) => setBiFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="bi-upload"
                />
                <label htmlFor="bi-upload" className="cursor-pointer">
                  {biFile ? (
                    <div className="flex items-center justify-center gap-2 text-green-600">
                      <CheckCircle className="h-6 w-6" />
                      <span className="font-medium">{biFile.name}</span>
                    </div>
                  ) : (
                    <>
                      <Upload className="h-12 w-12 text-slate-400 mx-auto mb-3" />
                      <p className="text-agro-primary font-medium mb-1">Escolher arquivo</p>
                      <p className="text-xs text-slate-600">PDF, JPG ou PNG (máx 5MB)</p>
                    </>
                  )}
                </label>
              </div>
              <p className="text-xs text-slate-600 mt-2">
                Necessário para validação da conta pela administração
              </p>
            </div>

            {/* Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-900">
                <strong>Nota:</strong> A sua conta será revista pela administração. 
                Pode explorar o mercado, mas só poderá publicar produtos após validação.
              </p>
            </div>

            <Button 
              type="submit" 
              variant="primary" 
              className="w-full h-12 text-lg"
              disabled={loading || !biFile || iban.length !== 27}
            >
              {loading ? "A finalizar..." : "Finalizar Cadastro"}
              {!loading && <ArrowRight className="h-5 w-5 ml-2" />}
            </Button>
          </form>
        </Card>

        {/* Progresso */}
        <div className="mt-8">
          <div className="flex justify-between text-xs text-slate-600 mb-2">
            <span>Progresso</span>
            <span>100%</span>
          </div>
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div className="h-full bg-agro-primary w-full transition-all"></div>
          </div>
        </div>
      </main>
    </div>
  );
}
