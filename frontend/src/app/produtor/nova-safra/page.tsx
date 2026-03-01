"use client";

import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shared/page-header";
import { Upload, AlertCircle } from "lucide-react";
import { http } from "@/services/http";

export default function NovaSafraPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    produto_id: "",
    quantidade_kg: "",
    preco_kg: "",
    descricao: "",
  });
  const [imagem, setImagem] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const data = new FormData();
      data.append("produto_id", formData.produto_id);
      data.append("quantidade_kg", formData.quantidade_kg);
      data.append("preco_kg", formData.preco_kg);
      data.append("descricao", formData.descricao);
      if (imagem) data.append("imagem_safra", imagem);

      await http.post("/produtor/nova-safra", data);
      router.push("/produtor");
    } catch (error) {
      alert("Erro ao criar safra");
    } finally {
      setLoading(false);
    }
  };

  if (user?.tipo !== "produtor") {
    return <div className="p-6">Acesso negado</div>;
  }

  if (!user.conta_validada) {
    return (
      <div className="min-h-screen">
        <PageHeader title="Nova Safra" backUrl="/produtor" />
        <div className="max-w-2xl mx-auto px-4 py-12">
          <Card className="text-center py-12">
            <AlertCircle className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Conta Não Validada</h2>
            <p className="text-slate-600 mb-6">
              A sua conta precisa ser validada pela administração antes de publicar safras.
            </p>
            <Button variant="primary" onClick={() => router.push("/dashboard")}>
              Voltar ao Dashboard
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <PageHeader title="Publicar Nova Safra" backUrl="/produtor" />

      <div className="max-w-2xl mx-auto px-4 lg:px-8 py-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <h3 className="font-semibold mb-4">Informações do Produto</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Produto</label>
                <select
                  required
                  value={formData.produto_id}
                  onChange={(e) => setFormData({...formData, produto_id: e.target.value})}
                  className="w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-agro-primary"
                >
                  <option value="">Selecione o produto</option>
                  <option value="1">Tomate</option>
                  <option value="2">Batata Doce</option>
                  <option value="3">Milho</option>
                  <option value="4">Feijão</option>
                  <option value="5">Mandioca</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Quantidade (kg)</label>
                  <input
                    type="number"
                    required
                    min="1"
                    step="0.01"
                    value={formData.quantidade_kg}
                    onChange={(e) => setFormData({...formData, quantidade_kg: e.target.value})}
                    className="w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-agro-primary"
                    placeholder="Ex: 500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Preço por kg (Kz)</label>
                  <input
                    type="number"
                    required
                    min="1"
                    step="0.01"
                    value={formData.preco_kg}
                    onChange={(e) => setFormData({...formData, preco_kg: e.target.value})}
                    className="w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-agro-primary"
                    placeholder="Ex: 150"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Descrição</label>
                <textarea
                  rows={4}
                  value={formData.descricao}
                  onChange={(e) => setFormData({...formData, descricao: e.target.value})}
                  className="w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-agro-primary"
                  placeholder="Descreva a qualidade, origem, etc..."
                />
              </div>
            </div>
          </Card>

          <Card>
            <h3 className="font-semibold mb-4">Imagem do Produto</h3>
            <div className="border-2 border-dashed rounded-xl p-8 text-center">
              <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setImagem(e.target.files?.[0] || null)}
                className="hidden"
                id="imagem"
              />
              <label htmlFor="imagem" className="cursor-pointer">
                <span className="text-agro-primary font-medium">Escolher imagem</span>
                <p className="text-sm text-slate-600 mt-1">PNG, JPG até 5MB</p>
              </label>
              {imagem && (
                <p className="text-sm text-green-600 mt-2">✓ {imagem.name}</p>
              )}
            </div>
          </Card>

          <div className="flex gap-3">
            <Button 
              type="button" 
              variant="outline" 
              className="flex-1"
              onClick={() => router.push("/produtor")}
            >
              Cancelar
            </Button>
            <Button 
              type="submit" 
              variant="primary" 
              className="flex-1"
              disabled={loading}
            >
              {loading ? "A publicar..." : "Publicar Safra"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
