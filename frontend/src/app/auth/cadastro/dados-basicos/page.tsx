"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Sprout, User, MapPin, Sprout as Culture, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";

interface Provincia {
  id: number;
  nome: string;
  municipios: { id: number; nome: string }[];
}

export default function CadastroDadosBasicosPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [provincias, setProvincias] = useState<Provincia[]>([]);
  const [municipios, setMunicipios] = useState<{ id: number; nome: string }[]>([]);
  
  const [formData, setFormData] = useState({
    nome: "",
    provincia_id: "",
    municipio_id: "",
    principal_cultura: ""
  });
  
  const telemovel = searchParams.get("telemovel") || "";

  useEffect(() => {
    if (!telemovel) {
      router.push("/auth/cadastro/passo-1");
      return;
    }

    // Carregar províncias
    carregarProvincias();
  }, [telemovel, router]);

  const carregarProvincias = async () => {
    try {
      const response = await fetch("/api/cadastro/provincias");
      const data = await response.json();
      
      if (data.success) {
        setProvincias(data.data);
      }
    } catch (error) {
      console.error("Erro ao carregar províncias:", error);
    }
  };

  const handleProvinciaChange = (provinciaId: string) => {
    const provincia = provincias.find(p => p.id.toString() === provinciaId);
    if (provincia) {
      setMunicipios(provincia.municipios);
      setFormData(prev => ({
        ...prev,
        provincia_id: provinciaId,
        municipio_id: "" // Reset município quando mudar província
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validações básicas
    if (!formData.nome || formData.nome.length < 3) {
      toast.error("Nome deve ter pelo menos 3 caracteres");
      return;
    }

    if (!formData.provincia_id || !formData.municipio_id) {
      toast.error("Selecione província e município");
      return;
    }

    if (!formData.principal_cultura) {
      toast.error("Informe sua principal cultura");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/cadastro/dados-basicos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome: formData.nome,
          provincia_id: parseInt(formData.provincia_id),
          municipio_id: parseInt(formData.municipio_id),
          principal_cultura: formData.principal_cultura
        }),
      });

      const data = await response.json();

      if (data.success) {
        toast.success("Dados salvos! Agora defina sua senha e IBAN.");
        router.push(`/auth/cadastro/passo-3?telemovel=${encodeURIComponent(telemovel)}`);
      } else {
        toast.error(data.message || "Erro ao salvar dados");
      }
    } catch (error) {
      console.error("Erro ao salvar dados:", error);
      toast.error("Erro ao conectar com servidor");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-agro-primary/5 to-agro-leaf/5 p-4">
      <Card className="w-full max-w-2xl shadow-2xl">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 rounded-2xl bg-agro-primary flex items-center justify-center">
              <Sprout className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl">Dados Pessoais</CardTitle>
          <CardDescription>
            Passo 2 de 3: Preencha suas informações
          </CardDescription>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4">
            <div className="bg-agro-primary h-2.5 rounded-full" style={{ width: "66%" }}></div>
          </div>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Nome Completo */}
            <div className="space-y-2">
              <Label htmlFor="nome">
                <User className="inline h-4 w-4 mr-2" />
                Nome Completo
              </Label>
              <Input
                id="nome"
                type="text"
                placeholder="Ex: João Manuel da Silva"
                value={formData.nome}
                onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                required
                minLength={3}
              />
            </div>

            {/* Localização */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="provincia">
                  <MapPin className="inline h-4 w-4 mr-2" />
                  Província
                </Label>
                <Select 
                  value={formData.provincia_id} 
                  onValueChange={handleProvinciaChange}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {provincias.map((provincia) => (
                      <SelectItem key={provincia.id} value={provincia.id.toString()}>
                        {provincia.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="municipio">
                  Município
                </Label>
                <Select 
                  value={formData.municipio_id} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, municipio_id: value }))}
                  disabled={!formData.provincia_id}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    {municipios.map((municipio) => (
                      <SelectItem key={municipio.id} value={municipio.id.toString()}>
                        {municipio.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Cultura Principal */}
            <div className="space-y-2">
              <Label htmlFor="principal_cultura">
                <Culture className="inline h-4 w-4 mr-2" />
                Cultura Principal
              </Label>
              <Select 
                value={formData.principal_cultura} 
                onValueChange={(value) => setFormData(prev => ({ ...prev, principal_cultura: value }))}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione sua principal cultura" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="milho">Milho</SelectItem>
                  <SelectItem value="feijao">Feijão</SelectItem>
                  <SelectItem value="arroz">Arroz</SelectItem>
                  <SelectItem value="trigo">Trigo</SelectItem>
                  <SelectItem value="cafe">Café</SelectItem>
                  <SelectItem value="algodao">Algodão</SelectItem>
                  <SelectItem value="banana">Banana</SelectItem>
                  <SelectItem value="mandioca">Mandioca</SelectItem>
                  <SelectItem value="batata">Batata</SelectItem>
                  <SelectItem value="tomate">Tomate</SelectItem>
                  <SelectItem value="cebola">Cebola</SelectItem>
                  <SelectItem value="outro">Outro</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Alert>
              <AlertDescription className="text-sm">
                <strong>Importante:</strong> Estas informações serão usadas para seu perfil de produtor e para calcular frete das entregas.
              </AlertDescription>
            </Alert>

            <Button 
              type="submit" 
              className="w-full h-12 text-lg" 
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Salvando...
                </>
              ) : (
                <>
                  Continuar
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </Button>
          </form>

          <div className="text-center mt-4">
            <Link href="/auth/cadastro/passo-1" className="text-sm text-muted-foreground hover:underline">
              ← Voltar
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
