"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface Municipio {
  id: number;
  nome: string;
}

interface Provincia {
  id: number;
  nome: string;
  municipios: Municipio[];
}

export default function CompletarPerfilPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);

  // Estados do Formulário
  const [nif, setNif] = useState("");
  const [iban, setIban] = useState("");
  const [provinciaId, setProvinciaId] = useState("");
  const [municipioId, setMunicipioId] = useState("");
  const [fotoPerfil, setFotoPerfil] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [provincias, setProvincias] = useState<Provincia[]>([]);
  const [municipiosFiltrados, setMunicipiosFiltrados] = useState<Municipio[]>([]);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const storedToken = localStorage.getItem("token");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";

    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
      setToken(storedToken);
      fetch(`${apiUrl}/v1/provincias`)
        .then(res => res.json())
        .then(data => {
          if(data.success) setProvincias(data.data);
        })
        .catch(console.error);
    } else {
      router.push("/auth/login");
    }
  }, [router]);

  const handleProvinciaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setProvinciaId(id);
    const provincia = provincias.find((p) => p.id === parseInt(id));
    setMunicipiosFiltrados(provincia ? provincia.municipios : []);
    setMunicipioId("");
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFotoPerfil(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (!token) return;

    try {
      const formData = new FormData();
      formData.append("nif", nif);
      formData.append("iban", iban);
      formData.append("provincia_id", provinciaId);
      formData.append("municipio_id", municipioId);
      if (fotoPerfil) {
        formData.append("foto_perfil", fotoPerfil);
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000/api";
      const res = await fetch(`${apiUrl}/auth/completar-perfil`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData // Não definir Content-Type, o browser define automaticamente com boundary
      });

      const json = await res.json();

      if (!json.success) {
        throw new Error(json.errors ? json.errors[0] : json.error || "Erro ao completar perfil");
      }

      // Atualizar user no localStorage
      localStorage.setItem("user", JSON.stringify(json.data.user));
      router.push("/dashboard");

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return <div className="p-10 text-center">Carregando...</div>;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Complete o seu Perfil
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Adicione uma foto e a sua localização.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>

            {/* Foto de Perfil */}
            <div>
              <label className="block text-sm font-medium text-gray-700">Foto de Perfil</label>
              <div className="mt-2 flex items-center">
                <span className="inline-block h-12 w-12 rounded-full overflow-hidden bg-gray-100">
                  {fotoPerfil ? (
                    <img src={URL.createObjectURL(fotoPerfil)} alt="Preview" className="h-full w-full object-cover" />
                  ) : (
                    <svg className="h-full w-full text-gray-300" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M24 20.993V24H0v-2.996A14.977 14.977 0 0112.004 15c4.904 0 9.26 2.354 11.996 5.993zM16.002 8.999a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  )}
                </span>
                <label
                  htmlFor="foto_perfil"
                  className="ml-5 bg-white py-2 px-3 border border-gray-300 rounded-md shadow-sm text-sm leading-4 font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 cursor-pointer"
                >
                  Carregar
                  <input id="foto_perfil" name="foto_perfil" type="file" className="sr-only" onChange={handleFileChange} accept="image/*" />
                </label>
              </div>
            </div>

            {/* NIF */}
            <div>
              <label htmlFor="nif" className="block text-sm font-medium text-gray-700">
                NIF *
              </label>
              <div className="mt-1">
                <input
                  id="nif"
                  type="text"
                  required
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                  placeholder="000000000LA000"
                  value={nif}
                  onChange={(e) => setNif(e.target.value)}
                />
              </div>
            </div>

            {/* IBAN */}
            <div>
              <label htmlFor="iban" className="block text-sm font-medium text-gray-700">
                IBAN {user.tipo === 'produtor' ? '*' : '(Opcional)'}
              </label>
              <div className="mt-1">
                <input
                  id="iban"
                  type="text"
                  required={user.tipo === 'produtor'}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                  placeholder="AO06..."
                  value={iban}
                  onChange={(e) => setIban(e.target.value)}
                />
              </div>
            </div>

            {/* Província */}
            <div>
              <label htmlFor="provincia" className="block text-sm font-medium text-gray-700">
                Província *
              </label>
              <select
                id="provincia"
                required
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm rounded-md"
                value={provinciaId}
                onChange={handleProvinciaChange}
              >
                <option value="">Selecione...</option>
                {provincias.map((prov) => (
                  <option key={prov.id} value={prov.id}>{prov.nome}</option>
                ))}
              </select>
            </div>

            {/* Município */}
            <div>
              <label htmlFor="municipio" className="block text-sm font-medium text-gray-700">
                Município *
              </label>
              <select
                id="municipio"
                required
                disabled={!provinciaId}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm rounded-md disabled:bg-gray-100"
                value={municipioId}
                onChange={(e) => setMunicipioId(e.target.value)}
              >
                <option value="">Selecione...</option>
                {municipiosFiltrados.map((mun) => (
                  <option key={mun.id} value={mun.id}>{mun.nome}</option>
                ))}
              </select>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${loading ? 'bg-green-400' : 'bg-green-600 hover:bg-green-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500`}
              >
                {loading ? "A guardar..." : "Concluir Cadastro"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}