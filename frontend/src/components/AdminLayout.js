import Link from 'next/link';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { useAuth } from '../hooks/useAuth'; // Para o logout

const AdminLayout = ({ children, title = "Admin Dashboard" }) => {
  const router = useRouter();
  const { logout } = useAuth();

  const navItems = [
    { name: "Dashboard", href: "/admin/dashboard" },
    { name: "Utilizadores", href: "/admin/usuarios" },
    { name: "Transações", href: "/admin/transacoes" },
    { name: "Pagamentos", href: "/admin/pagamentos" },
    { name: "Disputas", href: "/admin/disputas" },
    { name: "Logs", href: "/admin/logs" },
    // Adicionar mais itens de navegação conforme necessário
  ];

  return (
    <div className="min-h-screen bg-gray-100 flex">
      <Head>
        <title>{title} | AgroKongo Admin</title>
      </Head>

      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white min-h-screen hidden md:block">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-green-400">AgroKongo Admin</h1>
        </div>
        <nav className="mt-6">
          {navItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`block py-2.5 px-4 rounded transition duration-200 ${
                router.pathname === item.href ? 'bg-gray-700 text-white' : 'hover:bg-gray-700 hover:text-white'
              }`}
            >
              {item.name}
            </Link>
          ))}
          <button
            onClick={logout}
            className="block w-full text-left py-2.5 px-4 mt-4 rounded transition duration-200 hover:bg-red-700 hover:text-white text-red-300"
          >
            Sair
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        {children}
      </main>
    </div>
  );
};

export default AdminLayout;
