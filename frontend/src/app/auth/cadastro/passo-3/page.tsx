"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sprout, ArrowRight, Lock, CreditCard, Upload, CheckCircle, Eye, EyeOff } from "lucide-react";
import { http } from "@/services/http";
import toast from "react-hot-toast";

export default function CadastroPasso3() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    senha: "",
    confirmar_senha: "",
    iban: "",
    nif: "",
    tipo_entidade: "singular",
  });
  const [biFile, setBiFile] = useState<File | null>(null);
  const [tipoUsuario, setTipoUsuario] = useState<string>("produtor");

  // Detectar tipo de usuário do localStorage
  React.useEffect(() => {
    const dadosCadastro = localStorage.getItem('cadastro_temp');
    if (dadosCadastro) {
      const dados = JSON.parse(dadosCadastro);
      setTipoUsuario(dados.tipo || "produtor");
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.senha.length < 4 || formData.senha.length > 6) {
      toast.error("Use um PIN de 4 a 6 dígitos");
      return;
    }

    if (!/^\d+$/.test(formData.senha)) {
      toast.error("Use apenas números no PIN");
      return;
    }

    if (formData.senha !== formData.confirmar_senha) {
      toast.error("As senhas não coincidem");
      return;
    }

    // Validar NIF obrigatório para produtor ou pessoa coletiva
    if (tipoUsuario === "produtor" || formData.tipo_entidade === "coletiva") {
      if (!formData.nif || formData.nif.length < 9) {
        toast.error("NIF obrigatório para produtores e pessoas coletivas");
        return;
      }
    }

    // Validar IBAN apenas para produtor
    if (tipoUsuario === "produtor") {
      if (!formData.iban.startsWith("AO06") || formData.iban.length !== 27) {
        toast.error("IBAN obrigatório para produtor. Use formato AO06 + 21 dígitos");
        return;
      }
    }

    setLoading(true);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('pin', formData.senha);
      formDataToSend.append('tipo_entidade', formData.tipo_entidade);
      if (formData.nif) formDataToSend.append('nif', formData.nif);
      if (tipoUsuario === "produtor" && formData.iban) {
        formDataToSend.append('iban', formData.iban);
      }
      if (biFile) formDataToSend.append('bi', biFile);

      const res = await http.post("/cadastro/passo-3", formDataToSend, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (res.data?.sucesso) {
        // Salvar usuário no localStorage
        const dadosCadastro = localStorage.getItem('cadastro_temp');
        const userData = {
          id: res.data.usuario_id,
          nome: dadosCadastro ? JSON.parse(dadosCadastro).nome : "Usuário",
          tipo: res.data.tipo || tipoUsuario,
          telemovel: dadosCadastro ? JSON.parse(dadosCadastro).telemovel : "",
          conta_validada: false
        };
        
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.removeItem('cadastro_temp');
        
        toast.success("Conta criada com sucesso!");
        router.push("/dashboard");
      } else {
        toast.error(res.data?.mensagem || "Erro ao criar conta");
      }
    } catch (error: any) {
      console.error('Erro cadastro:', error);
      const msg = error?.response?.data?.mensagem || error?.message || "Erro ao processar";
      toast.error(msg);
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
            <span className="text-sm font-medium text-agro-primary">Passo 3 de 3 - Final</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Segurança e Pagamentos</h1>
          <p className="text-slate-600">Defina sua senha e dados bancários</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <Lock className="h-4 w-4" />
                PIN de Acesso (4-6 dígitos)
              </label>
              <div className="relative">
                <input
                  required
                  type={showPassword ? "text" : "password"}
                  inputMode="numeric"
                  placeholder="Digite seu PIN"
                  value={formData.senha}
                  onChange={(e) => setFormData({...formData, senha: e.target.value.replace(/\D/g, "")})}
                  maxLength={6}
                  className="w-full h-12 px-4 pr-12 border-2 rounded-xl text-center font-bold focus:ring-2 focus:ring-agro-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
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
                className="w-full h-12 px-4 border-2 rounded-xl text-center font-bold focus:ring-2 focus:ring-agro-primary"
              />
            </div>

            <div className="pt-4 border-t">
              <label className="text-sm font-medium mb-2 block">Tipo de Entidade</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormData({...formData, tipo_entidade: "singular"})}
                  className={`h-16 rounded-xl border-2 flex flex-col items-center justify-center transition-all ${
                    formData.tipo_entidade === "singular" 
                      ? "border-agro-primary bg-agro-primary/5 text-agro-primary" 
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <span className="text-sm font-medium">Pessoa Singular</span>
                  <span className="text-xs text-slate-500">Indivíduo</span>
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({...formData, tipo_entidade: "coletiva"})}
                  className={`h-16 rounded-xl border-2 flex flex-col items-center justify-center transition-all ${
                    formData.tipo_entidade === "coletiva" 
                      ? "border-agro-primary bg-agro-primary/5 text-agro-primary" 
                      : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <span className="text-sm font-medium">Pessoa Coletiva</span>
                  <span className="text-xs text-slate-500">Empresa/Cooperativa</span>
                </button>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <CreditCard className="h-4 w-4" />
                NIF {(tipoUsuario === "produtor" || formData.tipo_entidade === "coletiva") && "*"}
              </label>
              <Input
                required={tipoUsuario === "produtor" || formData.tipo_entidade === "coletiva"}
                placeholder="Ex: 501234400001"
                value={formData.nif}
                onChange={(e) => setFormData({...formData, nif: e.target.value.replace(/\D/g, "")})}
                maxLength={14}
                className="h-12"
              />
              <p className="text-xs text-slate-600 mt-1">
                {(tipoUsuario === "produtor" || formData.tipo_entidade === "coletiva") 
                  ? "Obrigatório para produtores e pessoas coletivas" 
                  : "Opcional para pessoas singulares"}
              </p>
            </div>

            {tipoUsuario === "produtor" && (
              <div>
                <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  IBAN (Conta Bancária) *
                </label>
                <Input
                  required
                  placeholder="AO06000000000000000000000"
                  value={formData.iban}
                  onChange={(e) => setFormData({...formData, iban: e.target.value.toUpperCase().replace(/\s/g, "")})}
                  maxLength={27}
                  className="h-12 font-mono"
                />
                <p className="text-xs text-slate-600 mt-1">
                  Formato: AO06 + 21 dígitos (obrigatório para receber pagamentos)
                </p>
              </div>
            )}

            <div>
              <label className="text-sm font-medium mb-2 block">Bilhete de Identidade (Opcional)</label>
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
                      <Upload className="h-10 w-10 text-slate-400 mx-auto mb-2" />
                      <p className="text-agro-primary font-medium mb-1">Escolher arquivo</p>
                      <p className="text-xs text-slate-600">PDF, JPG ou PNG (máx 5MB)</p>
                    </>
                  )}
                </label>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-900">
                <strong>Nota:</strong> Sua conta será revista pela administração. 
                Pode explorar o mercado, mas só poderá publicar após validação.
              </p>
            </div>

            <Button 
              type="submit" 
              variant="primary" 
              className="w-full h-12 text-lg"
              disabled={loading}
            >
              {loading ? "A criar conta..." : "Finalizar Cadastro"}
              {!loading && <ArrowRight className="h-5 w-5 ml-2" />}
            </Button>
          </form>
        </Card>

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
