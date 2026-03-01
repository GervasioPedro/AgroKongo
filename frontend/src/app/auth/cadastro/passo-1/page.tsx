"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sprout, ArrowRight, User, Phone, MapPin } from "lucide-react";
import { http } from "@/services/http";
import toast from "react-hot-toast";

export default function CadastroPasso1() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    nome: "",
    telemovel: "",
    provincia_id: "",
    municipio_id: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.telemovel.startsWith("9") || formData.telemovel.length !== 9) {
      toast.error("Número inválido. Use 9 dígitos começando com 9");
      return;
    }

    if (formData.nome.length < 3) {
      toast.error("Nome deve ter pelo menos 3 caracteres");
      return;
    }

    setLoading(true);

    try {
      const res = await http.post("/cadastro/passo-1", formData);
      
      if (res.data?.sucesso) {
        toast.success("Código OTP enviado via WhatsApp!");
        router.push("/auth/cadastro/passo-2");
      } else {
        toast.error(res.data?.mensagem || "Erro ao processar");
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
          <Link href="/auth/login">
            <Button variant="ghost" size="sm">Entrar</Button>
          </Link>
        </div>
      </header>

      <main className="max-w-md mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-agro-primary/10 px-4 py-2 rounded-full mb-4">
            <span className="text-sm font-medium text-agro-primary">Passo 1 de 3</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Criar Conta Produtor</h1>
          <p className="text-slate-600">Preencha seus dados básicos</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <User className="h-4 w-4" />
                Nome Completo
              </label>
              <Input
                required
                placeholder="Ex: António Fernandes"
                value={formData.nome}
                onChange={(e) => setFormData({...formData, nome: e.target.value})}
                className="h-12"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Número de Telemóvel
              </label>
              <Input
                required
                placeholder="912345678"
                inputMode="numeric"
                value={formData.telemovel}
                onChange={(e) => setFormData({...formData, telemovel: e.target.value.replace(/\D/g, "")})}
                maxLength={9}
                className="h-12"
              />
              <p className="text-xs text-slate-600 mt-1">
                Enviaremos código de verificação via WhatsApp
              </p>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Província
              </label>
              <select
                required
                value={formData.provincia_id}
                onChange={(e) => setFormData({...formData, provincia_id: e.target.value})}
                className="w-full h-12 px-4 border rounded-xl focus:ring-2 focus:ring-agro-primary"
              >
                <option value="">Selecione a província</option>
                <option value="1">Luanda</option>
                <option value="2">Bengo</option>
                <option value="3">Benguela</option>
                <option value="4">Bié</option>
                <option value="5">Cabinda</option>
                <option value="6">Cuando Cubango</option>
                <option value="7">Cuanza Norte</option>
                <option value="8">Cuanza Sul</option>
                <option value="9">Cunene</option>
                <option value="10">Huámbo</option>
                <option value="11">Huíla</option>
                <option value="12">Lunda Norte</option>
                <option value="13">Lunda Sul</option>
                <option value="14">Malanje</option>
                <option value="15">Moxico</option>
                <option value="16">Namibe</option>
                <option value="17">Uíge</option>
                <option value="18">Zaire</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Município</label>
              <select
                required
                value={formData.municipio_id}
                onChange={(e) => setFormData({...formData, municipio_id: e.target.value})}
                className="w-full h-12 px-4 border rounded-xl focus:ring-2 focus:ring-agro-primary"
              >
                <option value="">Selecione o município</option>
                <option value="1">Luanda</option>
                <option value="2">Viana</option>
                <option value="3">Cacuaco</option>
              </select>
            </div>

            <Button 
              type="submit" 
              variant="primary" 
              className="w-full h-12 text-lg mt-6"
              disabled={loading}
            >
              {loading ? "A enviar código..." : "Continuar"}
              {!loading && <ArrowRight className="h-5 w-5 ml-2" />}
            </Button>

            <div className="text-center pt-4 border-t">
              <p className="text-sm text-slate-700">
                Já tens conta?{" "}
                <Link href="/auth/login" className="font-semibold text-agro-primary hover:underline">
                  Entrar
                </Link>
              </p>
            </div>
          </form>
        </Card>

        {/* Progresso */}
        <div className="mt-8">
          <div className="flex justify-between text-xs text-slate-600 mb-2">
            <span>Progresso</span>
            <span>33%</span>
          </div>
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div className="h-full bg-agro-primary w-1/3 transition-all"></div>
          </div>
        </div>
      </main>
    </div>
  );
}
