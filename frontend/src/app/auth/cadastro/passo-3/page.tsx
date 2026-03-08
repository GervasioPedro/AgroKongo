"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Sprout, CheckCircle, Loader2, Key, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";

export default function CadastroPasso3Page() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    senha: "",
    confirmar_senha: "",
    iban: ""
  });
  
  const telemovel = searchParams.get("telemovel") || "";

  useEffect(() => {
    if (!telemovel) {
      router.push("/auth/cadastro/passo-1");
    }
  }, [telemovel, router]);

  const handleFinalizarCadastro = async () => {
    // Validar campos
    if (!formData.senha || !/^\d{4,6}$/.test(formData.senha)) {
      toast.error("Senha deve ser um PIN de 4 a 6 dígitos");
      return;
    }

    if (formData.senha !== formData.confirmar_senha) {
      toast.error("Senhas não conferem");
      return;
    }

    if (!formData.iban || !formData.iban.startsWith("AO06") || formData.iban.length !== 27) {
      toast.error("IBAN inválido. Use formato AO06 + 21 dígitos");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/cadastro/finalizar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          telemovel,
          senha: formData.senha,
          iban: formData.iban
        }),
      });

      const data = await response.json();

      if (data.success) {
        toast.success("Cadastro realizado com sucesso! Bem-vindo ao AgroKongo!");
        
        // Aguardar 2 segundos e redirecionar para dashboard
        setTimeout(() => {
          router.push(data.redirect || "/produtor/dashboard");
        }, 2000);
      } else {
        toast.error(data.message || "Erro ao finalizar cadastro");
      }
    } catch (error) {
      console.error("Erro na finalização:", error);
      toast.error("Erro ao conectar com servidor");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-agro-primary/5 to-agro-leaf/5 p-4">
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 rounded-2xl bg-agro-primary flex items-center justify-center">
              <Sprout className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl">Último Passo!</CardTitle>
          <CardDescription>
            Passo 3 de 3: Senha e Pagamento
          </CardDescription>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4">
            <div className="bg-agro-primary h-2.5 rounded-full" style={{ width: "100%" }}></div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="text-center py-2">
            <CheckCircle className="h-16 w-16 text-agro-primary mx-auto mb-3" />
            <h3 className="text-xl font-semibold mb-2">
              Quase Lá!
            </h3>
            <p className="text-muted-foreground">
              Defina sua senha e informe seu IBAN
            </p>
          </div>

          <div className="space-y-4">
            {/* Senha */}
            <div className="space-y-2">
              <Label htmlFor="senha">
                <Key className="inline h-4 w-4 mr-2" />
                Senha (PIN de 4-6 dígitos)
              </Label>
              <Input
                id="senha"
                type="password"
                placeholder="****"
                value={formData.senha}
                onChange={(e) => setFormData(prev => ({ ...prev, senha: e.target.value }))}
                maxLength={6}
                pattern="\d{4,6}"
                required
              />
            </div>

            {/* Confirmar Senha */}
            <div className="space-y-2">
              <Label htmlFor="confirmar_senha">
                Confirmar Senha
              </Label>
              <Input
                id="confirmar_senha"
                type="password"
                placeholder="****"
                value={formData.confirmar_senha}
                onChange={(e) => setFormData(prev => ({ ...prev, confirmar_senha: e.target.value }))}
                required
              />
            </div>

            {/* IBAN */}
            <div className="space-y-2">
              <Label htmlFor="iban">
                <CreditCard className="inline h-4 w-4 mr-2" />
                IBAN para Pagamentos
              </Label>
              <Input
                id="iban"
                type="text"
                placeholder="AO06 XXXXXXXXXXXXXXXXXXXXX"
                value={formData.iban}
                onChange={(e) => setFormData(prev => ({ ...prev, iban: e.target.value.toUpperCase() }))}
                maxLength={27}
                required
                className="uppercase"
              />
              <p className="text-xs text-muted-foreground">
                Formato: AO06 + 21 dígitos
              </p>
            </div>
          </div>

          <Alert>
            <AlertDescription className="text-sm space-y-2">
              <p><strong>O que acontece agora?</strong></p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Ao finalizar, sua conta será criada automaticamente</li>
                <li>Você poderá explorar o marketplace imediatamente</li>
                <li>Sua conta será validada em até 24h para publicar produtos</li>
              </ul>
            </AlertDescription>
          </Alert>

          <div className="space-y-3 pt-4">
            <Button 
              onClick={handleFinalizarCadastro}
              className="w-full h-12 text-lg" 
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Criando Conta...
                </>
              ) : (
                <>
                  <CheckCircle className="h-5 w-5 mr-2" />
                  Finalizar e Criar Conta
                </>
              )}
            </Button>
          </div>

          <div className="text-center pt-4">
            <p className="text-xs text-muted-foreground">
              Ao finalizar, você concorda com nossos{" "}
              <Link href="/termos" className="underline hover:text-agro-primary">
                Termos de Uso
              </Link>{" "}
              e{" "}
              <Link href="/privacidade" className="underline hover:text-agro-primary">
                Política de Privacidade
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
