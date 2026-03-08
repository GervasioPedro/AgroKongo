"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Sprout, Smartphone, ArrowRight, Info, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";

export default function CadastroPasso1Page() {
  const router = useRouter();
  const [telemovel, setTelemovel] = useState("");
  const [termosAceites, setTermosAceites] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleTelemovelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, "");
    
    if (value.length > 9) {
      value = value.slice(0, 9);
    }
    
    setTelemovel(value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!termosAceites) {
      toast.error("Precisa aceitar os termos de uso");
      return;
    }

    if (!telemovel || telemovel.length !== 9 || !telemovel.startsWith("9")) {
      toast.error("Número de telemóvel inválido. Deve começar com 9 e ter 9 dígitos");
      return;
    }

    setIsLoading(true);

    try {
      // Chamar API de cadastro
      const response = await fetch("/api/cadastro/iniciar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telemovel }),
      });

      const data = await response.json();

      if (data.success) {
        toast.success("Código enviado! Verifique seu WhatsApp");
        // Já inclui telemóvel na URL para próximo passo
        router.push(`/auth/cadastro/passo-2?telemovel=${encodeURIComponent(telemovel)}`);
      } else {
        toast.error(data.message || "Erro ao enviar código");
      }
    } catch (error) {
      console.error("Erro no cadastro:", error);
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
          <CardTitle className="text-2xl">Criar Conta como Produtor</CardTitle>
          <CardDescription>
            Passo 1 de 3: Contato e Validação
          </CardDescription>
                    
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4">
            <div className="bg-agro-primary h-2.5 rounded-full" style={{ width: "33% }}></div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="text-center mb-6">
            <Smartphone className="h-12 w-12 text-agro-primary mx-auto mb-3" />
            <h3 className="font-semibold text-lg mb-2">Validação de Contato</h3>
            <p className="text-sm text-muted-foreground">
              Insira seu número de telemóvel para receber o código de verificação via WhatsApp
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="telemovel">
                <Smartphone className="inline h-4 w-4 mr-2" />
                Número de Telemóvel
              </Label>
              <div className="flex">
                <div className="bg-muted px-3 py-2 rounded-l-md border border-r-0 text-sm font-medium">
                  +244
                </div>
                <Input
                  id="telemovel"
                  type="tel"
                  placeholder="9 1234 5678"
                  value={telemovel}
                  onChange={handleTelemovelChange}
                  pattern="9\d{8}"
                  maxLength={9}
                  required
                  className="rounded-l-none"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                RN01: Número deve começar com 9 e ter exatamente 9 dígitos
              </p>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <strong>Importante:</strong>
                <ul className="mt-2 text-sm space-y-1">
                  <li>• Vamos enviar um código de 6 dígitos via WhatsApp</li>
                  <li>• O código tem validade de 10 minutos</li>
                  <li>• Você tem 3 tentativas para acertar o código</li>
                </ul>
              </AlertDescription>
            </Alert>

            <div className="flex items-start space-x-2">
              <Checkbox 
                id="termos" 
                checked={termosAceites}
                onCheckedChange={(checked) => setTermosAceites(checked as boolean)}
                required
              />
              <label
                htmlFor="termos"
                className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Li e aceito os{" "}
                <Link href="/termos" className="text-agro-primary hover:underline">
                  Termos de Uso
                </Link>{" "}
                e{" "}
                <Link href="/privacidade" className="text-agro-primary hover:underline">
                  Política de Privacidade
                </Link>{" "}
                da AgroKongo
              </label>
            </div>

            <Button 
              type="submit" 
              className="w-full h-12 text-lg" 
              disabled={isLoading || !termosAceites}
            >
              {isLoading ? (
                "Enviando..."
              ) : (
                <>
                  Continuar
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </Button>
          </form>

          <div className="text-center mt-4">
            <p className="text-sm text-muted-foreground">
              Já tem conta?{" "}
              <Link href="/auth/login" className="text-agro-primary hover:underline font-medium">
                Faça login
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
