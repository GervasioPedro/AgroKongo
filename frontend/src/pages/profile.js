import { useState, useEffect } from 'react';
import Head from 'next/head';
import ProtectedRoute from '../components/ProtectedRoute';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast'; // Importar toast

function ProfilePage() {
  const { user, loading: authLoading, isAuthenticated, logout } = useAuth();
  const [profileData, setProfileData] = useState({
    nome: '',
    email: '',
    telemovel: '', // Telemóvel não editável via API de perfil, mas útil para exibir
    nif: '',
    iban: '', // Apenas para produtor
    provincia_id: '',
    municipio_id: '',
    foto_perfil: null,
  });
  const [passwordData, setPasswordData] = useState({
    senha_atual: '',
    nova_senha: '',
    confirmar_senha: '',
  });
  const [loading, setLoading] = useState(false);
  const [provincias, setProvincias] = useState([]);
  const [municipios, setMunicipios] = useState([]);

  useEffect(() => {
    if (isAuthenticated && user) {
      setProfileData({
        nome: user.nome || '',
        email: user.email || '',
        telemovel: user.telemovel || '',
        nif: user.nif || '',
        iban: user.iban || '',
        provincia_id: user.provincia?.id || '',
        municipio_id: user.municipio?.id || '',
        foto_perfil: null, // Não pré-preenche o input de ficheiro
      });
      // Carregar províncias e municípios
      fetchProvincias();
      if (user.provincia?.id) {
        fetchMunicipios(user.provincia.id);
      }
    }
  }, [isAuthenticated, user]);

  const fetchProvincias = async () => {
    try {
      const res = await fetch('/api/localizacao/provincias'); // Assumindo um endpoint de API para localização
      const data = await res.json();
      if (data.ok) setProvincias(data.provincias);
    } catch (err) {
      console.error("Erro ao carregar províncias:", err);
    }
  };

  const fetchMunicipios = async (provinciaId) => {
    try {
      const res = await fetch(`/api/localizacao/municipios?provincia_id=${provinciaId}`); // Assumindo um endpoint de API para localização
      const data = await res.json();
      if (data.ok) setMunicipios(data.municipios);
    } catch (err) {
      console.error("Erro ao carregar municípios:", err);
    }
  };

  const handleProfileChange = (e) => {
    const { name, value, files } = e.target;
    if (name === 'foto_perfil') {
      setProfileData({ ...profileData, foto_perfil: files[0] });
    } else if (name === 'provincia_id') {
      setProfileData({ ...profileData, provincia_id: value, municipio_id: '' }); // Limpa município ao mudar província
      fetchMunicipios(value);
    } else {
      setProfileData({ ...profileData, [name]: value });
    }
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData({ ...passwordData, [name]: value });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const formDataToSend = new FormData();
    for (const key in profileData) {
      if (profileData[key] !== null) { // Não envia null para ficheiros não selecionados
        formDataToSend.append(key, profileData[key]);
      }
    }

    try {
      const res = await fetch('/api/profile', {
        method: 'PUT',
        body: formDataToSend,
      });
      const data = await res.json();
      if (data.ok) {
        toast.success(data.message);
        // Opcional: atualizar o estado do user no useAuth se a API retornar o user atualizado
      } else {
        toast.error(data.message);
      }
    } catch (err) {
      toast.error('Erro de conexão ao atualizar perfil.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    if (passwordData.nova_senha !== passwordData.confirmar_senha) {
      toast.error('A nova palavra-passe e a confirmação não coincidem.');
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('/api/profile/change-password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          senha_atual: passwordData.senha_atual,
          nova_senha: passwordData.nova_senha,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        toast.success(data.message);
        setPasswordData({ senha_atual: '', nova_senha: '', confirmar_senha: '' }); // Limpar formulário
      } else {
        toast.error(data.message);
      }
    } catch (err) {
      toast.error('Erro de conexão ao alterar palavra-passe.');
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Redirecionado pelo ProtectedRoute
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Meu Perfil | AgroKongo</title>
      </Head>

      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Meu Perfil</h1>

        {/* Secção de Dados do Perfil */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Informações Pessoais</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Atualize os seus dados e foto de perfil.</p>
          </div>
          <div className="border-t border-gray-200">
            <form onSubmit={handleProfileSubmit} className="px-4 py-5 sm:p-6">
              <div className="grid grid-cols-6 gap-6">
                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="nome" className="block text-sm font-medium text-gray-700">Nome Completo</label>
                  <input type="text" name="nome" id="nome" value={profileData.nome} onChange={handleProfileChange} className="mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">Endereço de Email</label>
                  <input type="email" name="email" id="email" value={profileData.email} onChange={handleProfileChange} className="mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="telemovel" className="block text-sm font-medium text-gray-700">Telemóvel</label>
                  <input type="text" name="telemovel" id="telemovel" value={profileData.telemovel} disabled className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md bg-gray-50 cursor-not-allowed" />
                </div>

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="nif" className="block text-sm font-medium text-gray-700">NIF</label>
                  <input type="text" name="nif" id="nif" value={profileData.nif} onChange={handleProfileChange} className="mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>

                {user?.tipo === 'produtor' && (
                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="iban" className="block text-sm font-medium text-gray-700">IBAN</label>
                    <input type="text" name="iban" id="iban" value={profileData.iban} onChange={handleProfileChange} className="mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                  </div>
                )}

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="provincia_id" className="block text-sm font-medium text-gray-700">Província</label>
                  <select id="provincia_id" name="provincia_id" value={profileData.provincia_id} onChange={handleProfileChange} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm">
                    <option value="">Selecione uma Província</option>
                    {provincias.map(prov => (
                      <option key={prov.id} value={prov.id}>{prov.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="municipio_id" className="block text-sm font-medium text-gray-700">Município</label>
                  <select id="municipio_id" name="municipio_id" value={profileData.municipio_id} onChange={handleProfileChange} disabled={!profileData.provincia_id} className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm">
                    <option value="">Selecione um Município</option>
                    {municipios.map(mun => (
                      <option key={mun.id} value={mun.id}>{mun.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="col-span-6">
                  <label htmlFor="foto_perfil" className="block text-sm font-medium text-gray-700">Foto de Perfil</label>
                  <div className="mt-1 flex items-center">
                    <span className="inline-block h-12 w-12 rounded-full overflow-hidden bg-gray-100">
                      <img
                        src={user?.foto_perfil ? `/uploads/public/perfil/${user.foto_perfil}` : '/images/default_user.jpg'}
                        alt="Foto de Perfil"
                        className="h-full w-full object-cover"
                      />
                    </span>
                    <input type="file" name="foto_perfil" id="foto_perfil" onChange={handleProfileChange} className="ml-5 bg-white py-2 px-3 border border-gray-300 rounded-md shadow-sm text-sm leading-4 font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500" />
                  </div>
                </div>
              </div>
              <div className="pt-5">
                <button
                  type="submit"
                  disabled={loading}
                  className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${loading ? 'bg-green-400' : 'bg-green-600 hover:bg-green-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500`}
                >
                  {loading ? 'Aguarde...' : 'Atualizar Perfil'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Secção de Alterar Palavra-passe */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Alterar Palavra-passe</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Mantenha a sua conta segura com uma nova palavra-passe.</p>
          </div>
          <div className="border-t border-gray-200">
            <form onSubmit={handlePasswordSubmit} className="px-4 py-5 sm:p-6">
              <div className="grid grid-cols-6 gap-6">
                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="senha_atual" className="block text-sm font-medium text-gray-700">Palavra-passe Atual</label>
                  <input type="password" name="senha_atual" id="senha_atual" value={passwordData.senha_atual} onChange={handlePasswordChange} className="mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>

                <div className="col-span-6 sm:col-span-3"></div> {/* Espaçador */}

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="nova_senha" className="block text-sm font-medium text-gray-700">Nova Palavra-passe</label>
                  <input type="password" name="nova_senha" id="nova_senha" value={passwordData.nova_senha} onChange={handlePasswordChange} className="mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="confirmar_senha" className="block text-sm font-medium text-gray-700">Confirmar Nova Palavra-passe</label>
                  <input type="password" name="confirmar_senha" id="confirmar_senha" value={passwordData.confirmar_senha} onChange={handlePasswordChange} className="mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                </div>
              </div>
              <div className="pt-5">
                <button
                  type="submit"
                  disabled={loading}
                  className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${loading ? 'bg-green-400' : 'bg-green-600 hover:bg-green-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500`}
                >
                  {loading ? 'Aguarde...' : 'Alterar Palavra-passe'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Profile() {
  return (
    <ProtectedRoute>
      <ProfilePage />
    </ProtectedRoute>
  );
}
