import { useState, useEffect, createContext, useContext } from 'react';
import { useRouter } from 'next/router';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Verificar sessão ao carregar
  useEffect(() => {
    async function loadUserFromCookies() {
      try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (res.ok && data.ok) {
          setUser(data.user);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error("Erro ao verificar sessão:", error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    loadUserFromCookies();
  }, []);

  const login = async (telemovel, senha) => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ telemovel, senha }),
      });

      const data = await res.json();

      if (res.ok && data.ok) {
        setUser(data.user);
        router.push('/dashboard'); // Redirecionar após login
        return { success: true };
      } else {
        return { success: false, message: data.message || 'Erro ao entrar.' };
      }
    } catch (error) {
      return { success: false, message: 'Erro de conexão.' };
    }
  };

  const register = async (dados) => {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados),
      });

      const data = await res.json();

      if (res.ok && data.ok) {
        setUser(data.user);
        router.push('/completar-perfil'); // Redirecionar após registo
        return { success: true };
      } else {
        return { success: false, message: data.message || 'Erro ao criar conta.' };
      }
    } catch (error) {
      return { success: false, message: 'Erro de conexão.' };
    }
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      setUser(null);
      router.push('/login');
    } catch (error) {
      console.error("Erro ao sair:", error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
