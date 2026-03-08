"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Sprout, Key, WhatsApp, RefreshCw, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";

export default function CadastroPasso2Page() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [otp, setOtp] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(600); // 10 minutos
  const [canResend, setCanResend] = useState(false);
  
  const telemovel = searchParams.get("telemovel") || "";

  useEffect(() => {
    if (!telemovel) {
      router.push("/auth/cadastro/passo-1");
      return;
    }

    // Timer de expiração
    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // Habilitar reenvio após 60 segundos
    setTimeout(() => setCanResend(true), 60000);

    return () => clearInterval(timer);
  }, [telemovel, router]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleOtpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, "");
    
    if (value.length > 6) {
      value = value.slice(0, 6);
    }
    
    setOtp(value);

    // Auto-submit quando tiver 6 dígitos
    if (value.length === 6) {
      handleSubmit(new Event("submit") as any);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    // Esta página agora é apenas de transição
    // O código OTP é verificado no backend via API
    // Após verificação bem-sucedida, redireciona para passo-3
    
    if (!otp || otp.length !== 6) {
      toast.error("Código deve ter 6 dígitos");
      return;
    }

    if (timeRemaining === 0) {
      toast.error("Código expirado. Solicite um novo código.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/cadastro/verificar-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          telemovel,
          otp 
        }),
      });

      const data = await response.json();

      if (data.success) {
        toast.success("Código verificado! Preencha seus dados.");
        // Redireciona para página de dados básicos
        router.push(`/auth/cadastro/dados-basicos?telemovel=${encodeURIComponent(telemovel)}`);
      } else {
        toast.error(data.message || "Código inválido");
      }
    } catch (error) {
      console.error("Erro na verificação:", error);
      toast.error("Erro ao conectar com servidor");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReenviarCodigo = async () => {
    if (!canResend) return;

    setIsLoading(true);

    try {
      const response = await fetch("/api/cadastro/reenviar-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telemovel }),
      });

      const data = await response.json();

      if (data.success) {
        toast.success("Novo código enviado!");
        setTimeRemaining(600);
        setCanResend(false);
        setTimeout(() => setCanResend(true), 60000);
      } else {
        toast.error(data.message || "Erro ao reenviar código");
      }
    } catch (error) {
      console.error("Erro no reenvio:", error);
      toast.error("Erro ao reenviar código");
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
          <CardTitle className="text-2xl">Verificação de Código</CardTitle>
          <CardDescription>
            Passo 2 de 3: Dados Pessoais
          </CardDescription>
                    
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4">
            <div className="bg-agro-primary h-2.5 rounded-full" style={{ width: "66% }}></div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="text-center mb-6">
            <WhatsApp className="h-12 w-12 text-agro-primary mx-auto mb-3" />
            <h3 className="font-semibold text-lg mb-2">Verifique seu WhatsApp</h3>
            <p className="text-sm text-muted-foreground">
              Enviamos um código de 6 dígitos para seu número
            </p>
            <div className="mt-3 inline-flex items-center px-4 py-2 bg-muted rounded-md">
              <span className="text-sm font-medium">+244 {telemovel.slice(-4)}</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="otp">
                <Key className="inline h-4 w-4 mr-2" />
                Código de Verificação
              </Label>
              <Input
                id="otp"
                type="text"
                placeholder="000000"
                value={otp}
                onChange={handleOtpChange}
                pattern="\d{6}"
                maxLength={6}
                required
                autoFocus
                className="text-center text-2xl tracking-widest"
                disabled={timeRemaining === 0}
              />
              <p className="text-xs text-muted-foreground text-center">
                Digite os 6 dígitos recebidos via WhatsApp
              </p>
            </div>

            {timeRemaining > 0 && (
              <Alert>
                <Clock className="h-4 w-4" />
                <AlertDescription className="text-center font-mono">
                  Código expira em {formatTime(timeRemaining)}
                </AlertDescription>
              </Alert>
            )}

            {timeRemaining === 0 && (
              <Alert variant="destructive">
                <AlertDescription className="text-center font-semibold">
                  Código expirado
                </AlertDescription>
              </Alert>
            )}

            <Button 
              type="submit" 
              className="w-full h-12 text-lg" 
              disabled={isLoading || timeRemaining === 0 || otp.length !== 6}
            >
              {isLoading ? "Verificando..." : "Verificar Código"}
            </Button>
          </form>

          <div className="text-center mt-4 space-y-2">
            <p className="text-sm text-muted-foreground">Não recebeu o código?</p>
            <Button
              variant="outline"
              onClick={handleReenviarCodigo}
              disabled={!canResend || isLoading}
              size="sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reenviar Código
            </Button>
            <p className="text-xs text-muted-foreground">
              Limite: 3 tentativas para evitar custos de SMS
            </p>
          </div>

          <div className="text-center mt-4">
            <Link href="/auth/cadastro/passo-1" className="text-sm text-muted-foreground hover:underline">
              ← Voltar para passo anterior
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
