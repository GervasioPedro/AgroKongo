"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff } from 'lucide-react';

export default function RegistroPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    nome: "",
    email: "",
    telemovel: "",
    senha: "",
    tipo: "comprador",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:5000/api/auth/registro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const json = await res.json();

      if (!res.ok) {
        throw new Error(json.errors ? json.errors[0] : json.error || `Erro HTTP: ${res.status}`);
      }

      if (json.success) {
        localStorage.setItem("token", json.data.access_token);
        localStorage.setItem("user", JSON.stringify(json.data.user));

        if (json.data.next_step) {
          router.push(json.data.next_step);
        } else {
          router.push("/dashboard");
        }
      }
    } catch (err: any) {
      console.error("🔴 FALHA NO FETCH:", err);
      setError(`Erro ao criar conta: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-white">
      {/* Imagem Lateral (Escondida em Mobile) */}
      <div className="hidden lg:block lg:w-1/2 relative bg-gray-900">
        <img
          className="absolute inset-0 h-full w-full object-cover opacity-60"
          src="https://images.unsplash.com/photo-1592982537447-7440770cbfc9?q=80&w=2069&auto=format&fit=crop"
          alt="Agricultor africano a trabalhar"
        />
        <div className="absolute inset-0 bg-green-900 mix-blend-multiply opacity-60"></div>
        <div className="absolute bottom-0 left-0 p-12 text-white">
          <h2 className="text-4xl font-bold mb-4">Comece hoje a sua jornada.</h2>
          <p className="text-lg text-green-100">Junte-se à maior rede de produtores e compradores de Angola.</p>
        </div>
      </div>

      {/* Formulário */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24 overflow-y-auto">
        <div className="mx-auto w-full max-w-sm lg:w-96">
          <div>
            <Link href="/" className="text-2xl font-black text-green-700 tracking-tighter hover:opacity-80 transition">
              AGROKONGO
            </Link>
            <h2 className="mt-8 text-3xl font-extrabold text-gray-900">
              Criar Conta Gratuita
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Já tem conta?{' '}
              <Link href="/auth/login" className="font-medium text-green-600 hover:text-green-500 transition">
                Entrar
              </Link>
            </p>
          </div>

          <div className="mt-8">
            {error && (
              <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4 rounded-r-md">
                <div className="flex">
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">

              <div>
                <label htmlFor="nome" className="block text-sm font-medium text-gray-700">Nome Completo</label>
                <div className="mt-1">
                  <input
                    id="nome"
                    name="nome"
                    type="text"
                    required
                    className="appearance-none block w-full px-3 py-2.5 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                    value={formData.nome}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="telemovel" className="block text-sm font-medium text-gray-700">Telemóvel (9 Digitos)</label>
                <div className="mt-1">
                  <input
                    id="telemovel"
                    name="telemovel"
                    type="tel"
                    required
                    className="appearance-none block w-full px-3 py-2.5 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                    placeholder="9xx xxx xxx"
                    value={formData.telemovel}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email (Opcional)</label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    className="appearance-none block w-full px-3 py-2.5 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="tipo" className="block text-sm font-medium text-gray-700">Quero...</label>
                <div className="mt-1">
                  <select
                    id="tipo"
                    name="tipo"
                    className="block w-full pl-3 pr-10 py-2.5 text-base border-gray-300 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm rounded-lg"
                    value={formData.tipo}
                    onChange={handleChange}
                  >
                    <option value="comprador">Comprar Produtos</option>
                    <option value="produtor">Vender a Minha Produção</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="senha" className="block text-sm font-medium text-gray-700">Senha</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <input
                    id="senha"
                    name="senha"
                    type={showPassword ? "text" : "password"}
                    required
                    className="appearance-none block w-full px-3 py-2.5 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm pr-10"
                    value={formData.senha}
                    onChange={handleChange}
                  />
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer" onClick={() => setShowPassword(!showPassword)}>
                    {showPassword ? <EyeOff className="h-5 w-5 text-gray-400" /> : <Eye className="h-5 w-5 text-gray-400" />}
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-bold text-white ${loading ? 'bg-green-400 cursor-wait' : 'bg-green-600 hover:bg-green-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition duration-150 ease-in-out`}
                >
                  {loading ? "A criar conta..." : "Registar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}