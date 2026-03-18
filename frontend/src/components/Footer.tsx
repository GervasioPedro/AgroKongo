import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-gray-800 text-gray-300 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <Link href="/" className="text-2xl font-bold text-green-500 hover:text-green-400 transition">
              Agro<span className="text-white">Kongo</span>
            </Link>
            <p className="mt-4 text-sm">
              Conectando produtores e compradores em Angola de forma direta, segura e transparente.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Links Rápidos</h3>
            <ul className="space-y-2">
              <li><Link href="/mercado" className="hover:text-white transition">Mercado</Link></li>
              <li><Link href="/auth/registro" className="hover:text-white transition">Registar</Link></li>
              <li><Link href="/auth/login" className="hover:text-white transition">Login</Link></li>
              <li><Link href="/dashboard" className="hover:text-white transition">Dashboard</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Contacto</h3>
            <p className="text-sm">Email: info@agrokongo.com</p>
            <p className="text-sm">Telefone: +244 9XX XXX XXX</p>
            <div className="flex space-x-4 mt-4">
              {/* Social Media Icons */}
              <a href="#" className="hover:text-white transition"><i className="fab fa-facebook-f"></i></a>
              <a href="#" className="hover:text-white transition"><i className="fab fa-instagram"></i></a>
              <a href="#" className="hover:text-white transition"><i className="fab fa-twitter"></i></a>
            </div>
          </div>
        </div>
        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-sm">
          &copy; {new Date().getFullYear()} AgroKongo. Todos os direitos reservados.
        </div>
      </div>
    </footer>
  );
}