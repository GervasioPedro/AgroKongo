"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { useRouter } from "next/navigation";
import { UploadCloud, Sprout, DollarSign, Scale, FileText, Image as ImageIcon, X } from 'lucide-react';

export default function NovaSafraPage() {
  const router = useRouter();
  const [produtos, setProdutos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState<any>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    produto_id: "",
    quantidade_kg: "",
    preco_kg: "",
    descricao: "",
    imagem_safra: null as File | null
  });

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/auth/login");
      return;
    }
    const parsedUser = JSON.parse(storedUser);
    setUser(parsedUser);

    fetch("http://localhost:5000/api/v1/produtos")
      .then(res => res.json())
      .then(json => {
        if (json.success) setProdutos(json.data);
      })
      .catch(err => console.error("Erro ao carregar produtos", err));
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFormData({ ...formData, imagem_safra: file });
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const removeImage = () => {
    setFormData({ ...formData, imagem_safra: null });
    setPreviewUrl(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (!formData.produto_id || !formData.quantidade_kg || !formData.preco_kg) {
      setError("Por favor, preencha todos os campos obrigatórios.");
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const data = new FormData();
      data.append("produto_id", formData.produto_id);
      data.append("quantidade_kg", formData.quantidade_kg);
      data.append("preco_kg", formData.preco_kg);
      data.append("descricao", formData.descricao);
      if (formData.imagem_safra) {
        data.append("imagem_safra", formData.imagem_safra);
      }

      const res = await fetch("http://localhost:5000/api/v1/produtor/nova-safra", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: data
      });

      const json = await res.json();

      if (json.success) {
        router.push("/produtor/safras");
      } else {
        throw new Error(json.error || "Erro ao criar safra.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <DashboardLayout user={user} title="Nova Safra">
      <div className="max-w-3xl mx-auto">

        {/* Cabeçalho */}
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight sm:text-4xl">
            O que vamos colher hoje? 🚜
          </h2>
          <p className="mt-2 text-lg text-gray-600">
            Preencha os detalhes abaixo para colocar o seu produto no mercado.
          </p>
        </div>

        <div className="bg-white shadow-xl rounded-2xl overflow-hidden border border-gray-100">
          <div className="p-8 sm:p-10">

            {error && (
              <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg animate-fade-in">
                <div className="flex">
                  <div className="ml-3">
                    <p className="text-sm text-red-700 font-medium">{error}</p>
                  </div>
                </div>
              </div>
            )}

            <form className="space-y-8" onSubmit={handleSubmit}>

              {/* Seleção do Produto */}
              <div className="group">
                <label htmlFor="produto_id" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                  <Sprout className="text-green-600" size={18} /> Produto
                </label>
                <div className="relative">
                  <select
                    id="produto_id"
                    name="produto_id"
                    required
                    className="block w-full pl-4 pr-10 py-3 text-base border-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 sm:text-sm rounded-xl transition-shadow shadow-sm hover:shadow-md cursor-pointer bg-white appearance-none"
                    value={formData.produto_id}
                    onChange={handleChange}
                  >
                    <option value="">Selecione da lista...</option>
                    {produtos.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.nome} ({p.categoria})
                      </option>
                    ))}
                  </select>
                  {/* Custom Arrow */}
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500">
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Grid: Quantidade e Preço */}
              <div className="grid grid-cols-1 gap-y-6 gap-x-6 sm:grid-cols-2">

                {/* Quantidade */}
                <div className="group">
                  <label htmlFor="quantidade_kg" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                    <Scale className="text-green-600" size={18} /> Quantidade (Kg)
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <input
                      type="number"
                      name="quantidade_kg"
                      id="quantidade_kg"
                      required
                      min="0.1"
                      step="0.1"
                      className="block w-full pl-4 pr-12 py-3 border-gray-300 rounded-xl focus:ring-green-500 focus:border-green-500 sm:text-sm transition-shadow hover:shadow-md"
                      placeholder="0.00"
                      value={formData.quantidade_kg}
                      onChange={handleChange}
                    />
                    <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                      <span className="text-gray-500 sm:text-sm font-medium bg-gray-100 px-2 py-1 rounded">Kg</span>
                    </div>
                  </div>
                </div>

                {/* Preço */}
                <div className="group">
                  <label htmlFor="preco_kg" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                    <DollarSign className="text-green-600" size={18} /> Preço por Kg
                  </label>
                  <div className="relative rounded-xl shadow-sm">
                    <input
                      type="number"
                      name="preco_kg"
                      id="preco_kg"
                      required
                      min="1"
                      className="block w-full pl-4 pr-12 py-3 border-gray-300 rounded-xl focus:ring-green-500 focus:border-green-500 sm:text-sm transition-shadow hover:shadow-md"
                      placeholder="0"
                      value={formData.preco_kg}
                      onChange={handleChange}
                    />
                    <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                      <span className="text-gray-500 sm:text-sm font-medium bg-gray-100 px-2 py-1 rounded">Kz</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Descrição */}
              <div className="group">
                <label htmlFor="descricao" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                  <FileText className="text-green-600" size={18} /> Detalhes (Opcional)
                </label>
                <div className="mt-1">
                  <textarea
                    id="descricao"
                    name="descricao"
                    rows={3}
                    className="shadow-sm focus:ring-green-500 focus:border-green-500 block w-full sm:text-sm border-gray-300 rounded-xl p-4 transition-shadow hover:shadow-md resize-none"
                    placeholder="Descreva a qualidade, tempo de colheita, etc..."
                    value={formData.descricao}
                    onChange={handleChange}
                  />
                </div>
              </div>

              {/* Upload de Imagem Moderno */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                  <ImageIcon className="text-green-600" size={18} /> Foto do Produto
                </label>

                {!previewUrl ? (
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-xl hover:border-green-500 hover:bg-green-50 transition-all cursor-pointer group relative">
                    <div className="space-y-2 text-center">
                      <div className="mx-auto h-16 w-16 text-gray-400 group-hover:text-green-500 transition-colors flex items-center justify-center bg-gray-50 rounded-full group-hover:bg-white">
                        <UploadCloud size={32} />
                      </div>
                      <div className="flex text-sm text-gray-600 justify-center">
                        <label
                          htmlFor="imagem_safra"
                          className="relative cursor-pointer bg-transparent rounded-md font-medium text-green-600 hover:text-green-500 focus-within:outline-none"
                        >
                          <span>Clique para carregar</span>
                          <input id="imagem_safra" name="imagem_safra" type="file" className="sr-only" onChange={handleFileChange} accept="image/*" />
                        </label>
                        <p className="pl-1">ou arraste para aqui</p>
                      </div>
                      <p className="text-xs text-gray-500">PNG, JPG até 10MB</p>
                    </div>
                  </div>
                ) : (
                  <div className="relative mt-2 rounded-xl overflow-hidden shadow-lg group">
                    <img src={previewUrl} alt="Preview" className="w-full h-64 object-cover" />
                    <div className="absolute inset-0 bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <button
                        type="button"
                        onClick={removeImage}
                        className="bg-white text-red-600 p-2 rounded-full hover:bg-red-50 transition-transform hover:scale-110"
                      >
                        <X size={24} />
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Botões de Ação */}
              <div className="flex items-center justify-end gap-4 pt-6 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-6 py-3 border border-gray-300 rounded-xl shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className={`inline-flex items-center justify-center px-8 py-3 border border-transparent text-sm font-bold rounded-xl shadow-lg text-white
                    ${loading
                      ? 'bg-green-400 cursor-wait'
                      : 'bg-green-600 hover:bg-green-700 hover:shadow-green-500/30 transform hover:-translate-y-0.5'}
                    transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500`}
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      A processar...
                    </>
                  ) : (
                    "Publicar no Mercado"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}