import { useState, useEffect } from 'react';
import Head from 'next/head';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAuth } from '../../hooks/useAuth';

function MinhasSafrasPage() {
  const [safras, setSafras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingSafra, setEditingSafra] = useState(null);
  const [formData, setFormData] = useState({
    produto_id: '',
    quantidade_disponivel: '',
    preco_por_unidade: '',
    descricao: '',
    imagem: null
  });

  const { user } = useAuth();

  useEffect(() => {
    fetchSafras();
  }, [user]);

  const fetchSafras = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const res = await fetch('/api/produtor/minhas-safras');
      const data = await res.json();
      if (data.ok) setSafras(data.safras);
      else setError('Falha ao carregar safras.');
    } catch (err) {
      setError('Erro de conexão.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, files } = e.target;
    if (name === 'imagem') {
      setFormData({ ...formData, imagem: files[0] });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const form = new FormData();
    for (const key in formData) {
      form.append(key, formData[key]);
    }

    const url = editingSafra
      ? `/api/produtor/minhas-safras/${editingSafra.id}`
      : '/api/produtor/minhas-safras';

    const method = editingSafra ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method: method,
        body: form,
      });
      const data = await res.json();
      if (data.ok) {
        fetchSafras();
        setShowModal(false);
        setEditingSafra(null);
        setFormData({ produto_id: '', quantidade_disponivel: '', preco_por_unidade: '', descricao: '', imagem: null });
      } else {
        alert(data.message);
      }
    } catch (err) {
      alert('Erro ao salvar safra.');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Tem certeza que deseja eliminar esta safra?')) return;
    try {
      const res = await fetch(`/api/produtor/minhas-safras/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.ok) fetchSafras();
      else alert(data.message);
    } catch (err) {
      alert('Erro ao eliminar safra.');
    }
  };

  const openEditModal = (safra) => {
    setEditingSafra(safra);
    setFormData({
      produto_id: safra.produto_id, // Assumindo que o ID do produto vem na safra
      quantidade_disponivel: safra.quantidade_disponivel,
      preco_por_unidade: safra.preco_por_unidade,
      descricao: safra.descricao || '',
      imagem: null
    });
    setShowModal(true);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Minhas Safras | AgroKongo</title>
      </Head>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Minhas Safras</h1>
          <button
            onClick={() => { setEditingSafra(null); setShowModal(true); }}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
          >
            Nova Safra
          </button>
        </div>

        {loading ? (
          <div className="text-center py-10">Carregando...</div>
        ) : error ? (
          <div className="text-center text-red-600 py-10">{error}</div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {safras.map((safra) => (
              <div key={safra.id} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="relative h-48">
                  <img
                    src={safra.imagem_url ? `/uploads/public/safras/${safra.imagem_url}` : '/images/placeholder-safra.jpg'}
                    alt={safra.produto?.nome}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2 bg-white px-2 py-1 rounded text-xs font-bold shadow">
                    {safra.status}
                  </div>
                </div>
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">{safra.produto?.nome}</h3>
                  <div className="mt-2 max-w-xl text-sm text-gray-500">
                    <p>Quantidade: {safra.quantidade_disponivel} kg</p>
                    <p>Preço: {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(safra.preco_por_unidade)}/kg</p>
                  </div>
                  <div className="mt-5 flex justify-end space-x-3">
                    <button
                      onClick={() => openEditModal(safra)}
                      className="text-indigo-600 hover:text-indigo-900 font-medium"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(safra.id)}
                      className="text-red-600 hover:text-red-900 font-medium"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal de Criação/Edição */}
        {showModal && (
          <div className="fixed z-10 inset-0 overflow-y-auto">
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>
              <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
              <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <form onSubmit={handleSubmit} className="p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                    {editingSafra ? 'Editar Safra' : 'Nova Safra'}
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Produto ID</label>
                      <input
                        type="number"
                        name="produto_id"
                        value={formData.produto_id}
                        onChange={handleInputChange}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Quantidade (kg)</label>
                      <input
                        type="number"
                        name="quantidade_disponivel"
                        value={formData.quantidade_disponivel}
                        onChange={handleInputChange}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Preço por Kg (AOA)</label>
                      <input
                        type="number"
                        name="preco_por_unidade"
                        value={formData.preco_por_unidade}
                        onChange={handleInputChange}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Descrição</label>
                      <textarea
                        name="descricao"
                        value={formData.descricao}
                        onChange={handleInputChange}
                        rows="3"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm"
                      ></textarea>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Imagem</label>
                      <input
                        type="file"
                        name="imagem"
                        onChange={handleInputChange}
                        className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
                      />
                    </div>
                  </div>
                  <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                    <button
                      type="submit"
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:col-start-2 sm:text-sm"
                    >
                      Salvar
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowModal(false)}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function MinhasSafras() {
  return (
    <ProtectedRoute>
      <MinhasSafrasPage />
    </ProtectedRoute>
  );
}
