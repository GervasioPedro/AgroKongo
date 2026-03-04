import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import Link from 'next/link';
import Head from 'next/head';

export default function Register() {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    nome: '',
    telemovel: '',
    senha: '',
    tipo: 'produtor', // Valor padrão
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const res = await register(formData);

    if (!res.success) {
      setError(res.message);
      setLoading(false);
    }
    // Se sucesso, o hook redireciona automaticamente
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Head>
        <title>Criar Conta | AgroKongo</title>
      </Head>

      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Crie a sua conta
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Já tem uma conta?{' '}
            <Link href="/login" className="font-medium text-green-600 hover:text-green-500">
              Faça login aqui
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 text-red-700 text-sm" role="alert">
              <p>{error}</p>
            </div>
          )}

          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="nome" className="sr-only">Nome Completo</label>
              <input
                id="nome"
                name="nome"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                placeholder="Nome Completo"
                value={formData.nome}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="telemovel" className="sr-only">Telemóvel</label>
              <input
                id="telemovel"
                name="telemovel"
                type="tel"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                placeholder="Número de Telemóvel (9 dígitos)"
                value={formData.telemovel}
                onChange={handleChange}
              />
            </div>
            <div>
              <label htmlFor="senha" className="sr-only">Senha</label>
              <input
                id="senha"
                name="senha"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                placeholder="Crie uma senha segura"
                value={formData.senha}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="pt-2">
            <label className="text-sm font-medium text-gray-700">Eu sou um:</label>
            <div className="mt-2 flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="tipo"
                  value="produtor"
                  checked={formData.tipo === 'produtor'}
                  onChange={handleChange}
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-900">Produtor</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="tipo"
                  value="comprador"
                  checked={formData.tipo === 'comprador'}
                  onChange={handleChange}
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-900">Comprador</span>
              </label>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${loading ? 'bg-green-400' : 'bg-green-600 hover:bg-green-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors duration-200`}
            >
              {loading ? 'Criando conta...' : 'Criar Conta'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
