"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/shared/page-header";
import { formatCurrency, formatWeight } from "@/utils/format";
import { MapPin, User, Package, Shield, CheckCircle } from "lucide-react";
import { http } from "@/services/http";

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function SafraDetalhePage() {
  const params = useParams();
  const router = useRouter();
  const [quantidade, setQuantidade] = useState(1);
  const { data, isLoading } = useSWR(`/mercado/safra/${params.id}`, fetcher);

  const safra = data?.safra;
  const total = quantidade * (safra?.preco_por_unidade || 0);

  const handleComprar = async () => {
    try {
      await http.post(`/comprador/comprar/${params.id}`, { quantidade });
      router.push("/comprador");
    } catch (error) {
      alert("Erro ao fazer pedido. Por favor, faça login primeiro.");
      router.push("/auth/login");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-agro-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-600">A carregar...</p>
        </div>
      </div>
    );
  }

  if (!safra) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center p-8">
          <p className="text-slate-600 mb-4">Safra não encontrada</p>
          <Button variant="primary" onClick={() => router.push("/mercado")}>
            Voltar ao Mercado
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-neutral">
      <PageHeader 
        title="Detalhes do Produto"
        backUrl="/mercado"
      />

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Coluna Esquerda - Imagens */}
          <div className="space-y-6">
            <div className="relative h-96 lg:h-[500px] rounded-2xl overflow-hidden shadow-lg">
              <img
                src={safra.imagem || "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=800&q=80"}
                alt={safra.produto.nome}
                className="w-full h-full object-cover"
              />
              <Badge status="finalizado" className="absolute top-4 right-4">
                Disponível
              </Badge>
            </div>
            
            {/* Info do Produtor */}
            <Card>
              <h3 className="font-semibold mb-3">Sobre o Produtor</h3>
              <div className="flex items-center gap-3">
                <div className="h-14 w-14 rounded-full bg-agro-primary/10 flex items-center justify-center">
                  <User className="h-7 w-7 text-agro-primary" />
                </div>
                <div>
                  <p className="font-semibold text-lg">{safra.produtor.nome}</p>
                  <div className="flex items-center gap-1 text-sm text-slate-600">
                    <MapPin className="h-4 w-4" />
                    <span>{safra.produtor.provincia.nome}</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Galeria de Imagens de Agricultura */}
            <div className="grid grid-cols-3 gap-3">
              <div className="aspect-square rounded-xl overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=300&q=80"
                  alt="Agricultura"
                  className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                />
              </div>
              <div className="aspect-square rounded-xl overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=300&q=80"
                  alt="Colheita"
                  className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                />
              </div>
              <div className="aspect-square rounded-xl overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1595278069441-2cf29f8005a4?w=300&q=80"
                  alt="Produtor"
                  className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                />
              </div>
            </div>
          </div>

          {/* Coluna Direita - Detalhes */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl lg:text-4xl font-bold mb-3">{safra.produto.nome}</h1>
              <p className="text-3xl font-bold text-agro-primary">
                {formatCurrency(safra.preco_por_unidade)} 
                <span className="text-base text-slate-600 font-normal"> / kg</span>
              </p>
            </div>

            {/* Quantidade Disponível */}
            <Card className="bg-slate-50">
              <div className="flex items-center gap-3">
                <Package className="h-6 w-6 text-slate-600" />
                <div>
                  <p className="text-sm text-slate-600">Quantidade Disponível</p>
                  <p className="text-2xl font-bold">{formatWeight(safra.quantidade_disponivel)}</p>
                </div>
              </div>
            </Card>

            {/* Descrição */}
            {safra.observacoes && (
              <Card>
                <h3 className="font-semibold mb-2">Descrição</h3>
                <p className="text-slate-700 leading-relaxed">{safra.observacoes}</p>
              </Card>
            )}

            {/* Garantias Escrow */}
            <Card className="bg-escrow-primary/5 border-escrow-primary">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Shield className="h-5 w-5 text-escrow-primary" />
                Protegido por Escrow
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-escrow-primary mt-0.5 flex-shrink-0" />
                  <span>Dinheiro em custódia até entrega confirmada</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-escrow-primary mt-0.5 flex-shrink-0" />
                  <span>Validação administrativa de pagamentos</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-escrow-primary mt-0.5 flex-shrink-0" />
                  <span>Resolução de disputas garantida</span>
                </div>
              </div>
            </Card>

            {/* Formulário de Compra */}
            <Card className="bg-agro-primary/5 border-agro-primary sticky top-24">
              <h3 className="font-semibold mb-4">Fazer Pedido</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-slate-700 mb-2 block">
                    Quantidade (kg)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max={safra.quantidade_disponivel}
                    value={quantidade}
                    onChange={(e) => setQuantidade(Math.max(1, Number(e.target.value)))}
                    className="w-full px-4 py-3 border rounded-xl text-lg font-semibold focus:ring-2 focus:ring-agro-primary"
                  />
                  <p className="text-xs text-slate-600 mt-1">
                    Máximo: {formatWeight(safra.quantidade_disponivel)}
                  </p>
                </div>

                <div className="flex justify-between items-center py-4 border-t border-b">
                  <span className="font-semibold text-lg">Total a Pagar</span>
                  <span className="text-3xl font-bold text-agro-primary">
                    {formatCurrency(total)}
                  </span>
                </div>

                <Button 
                  variant="primary" 
                  className="w-full h-12 text-lg" 
                  onClick={handleComprar}
                >
                  Confirmar Pedido
                </Button>

                <p className="text-xs text-center text-slate-600">
                  Ao confirmar, será redirecionado para enviar o comprovativo de pagamento
                </p>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
