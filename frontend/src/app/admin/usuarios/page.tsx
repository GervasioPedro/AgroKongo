"use client";

import { useAuth } from "@/hooks/useAuth";
import useSWR from "swr";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/shared/page-header";
import { User, CheckCircle, XCircle, Search } from "lucide-react";
import { http } from "@/services/http";
import { useState } from "react";

const fetcher = async (url: string) => {
  const res = await http.get(url);
  return res.data;
};

export default function UsuariosPage() {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const { data, isLoading, mutate } = useSWR("/admin/usuarios", fetcher);

  const usuarios = data?.usuarios || [];
  const filtered = usuarios.filter((u: any) => 
    u.nome.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  const handleValidar = async (id: number) => {
    try {
      await http.post(`/admin/validar-usuario/${id}`);
      mutate();
    } catch (error) {
      alert("Erro ao validar usuário");
    }
  };

  const handleBloquear = async (id: number) => {
    if (!confirm("Bloquear este usuário?")) return;
    try {
      await http.post(`/admin/bloquear-usuario/${id}`);
      mutate();
    } catch (error) {
      alert("Erro ao bloquear usuário");
    }
  };

  if (user?.tipo !== "admin") {
    return <div className="p-6">Acesso negado</div>;
  }

  return (
    <div className="min-h-screen">
      <PageHeader 
        title="Gestão de Usuários"
        subtitle={`${usuarios.length} usuários registados`}
        showBack={false}
      />

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-6">
        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Procurar por nome ou email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-agro-primary"
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <p className="text-sm text-slate-600">Total Usuários</p>
            <p className="text-3xl font-bold">{usuarios.length}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-600">Produtores</p>
            <p className="text-3xl font-bold text-agro-primary">
              {usuarios.filter((u: any) => u.tipo === "produtor").length}
            </p>
          </Card>
          <Card>
            <p className="text-sm text-slate-600">Compradores</p>
            <p className="text-3xl font-bold text-blue-600">
              {usuarios.filter((u: any) => u.tipo === "comprador").length}
            </p>
          </Card>
        </div>

        {/* Lista */}
        {isLoading ? (
          <div className="text-center py-12">A carregar...</div>
        ) : (
          <div className="space-y-3">
            {filtered.map((usuario: any) => (
              <Card key={usuario.id} className="hover:shadow-lg transition-shadow">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-full bg-agro-primary/10 flex items-center justify-center">
                    <User className="h-6 w-6 text-agro-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold">{usuario.nome}</h3>
                      <Badge variant={usuario.conta_validada ? "default" : "alert"}>
                        {usuario.tipo}
                      </Badge>
                      {usuario.conta_validada && (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      )}
                    </div>
                    <p className="text-sm text-slate-600">{usuario.email}</p>
                    <p className="text-xs text-slate-500">{usuario.provincia}</p>
                  </div>
                  <div className="flex gap-2">
                    {!usuario.conta_validada && (
                      <Button 
                        variant="primary" 
                        size="sm"
                        onClick={() => handleValidar(usuario.id)}
                      >
                        Validar
                      </Button>
                    )}
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="text-red-600"
                      onClick={() => handleBloquear(usuario.id)}
                    >
                      Bloquear
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
