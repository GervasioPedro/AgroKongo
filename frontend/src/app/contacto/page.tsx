import Navbar from "@/components/Navbar";
import { Mail, Phone, MapPin } from 'lucide-react';

export default function ContactoPage() {
  return (
    <div className="bg-white min-h-screen">
      <Navbar />

      <div className="bg-green-700 py-16 px-4 sm:px-6 lg:px-8 text-center text-white">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
          Fale Connosco
        </h1>
        <p className="mt-4 text-xl text-green-100 max-w-2xl mx-auto">
          Estamos aqui para ajudar. Se tiver dúvidas, sugestões ou precisar de apoio,
          não hesite em entrar em contacto.
        </p>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white shadow-2xl rounded-2xl overflow-hidden md:flex">

          {/* Informações de Contacto */}
          <div className="md:w-1/3 bg-gray-50 p-8 space-y-8 border-r border-gray-100">
            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span className="bg-green-100 p-2 rounded-lg text-green-600"><Mail size={20} /></span>
                Email
              </h2>
              <p className="text-gray-600">suporte@agrokongo.com</p>
              <p className="text-gray-500 text-sm mt-1">Respondemos em até 24h.</p>
            </div>

            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span className="bg-green-100 p-2 rounded-lg text-green-600"><Phone size={20} /></span>
                Telefone
              </h2>
              <p className="text-gray-600">+244 942 050 656</p>
              <p className="text-gray-500 text-sm mt-1">Seg-Sex, 8h às 17h.</p>
            </div>

            <div>
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span className="bg-green-100 p-2 rounded-lg text-green-600"><MapPin size={20} /></span>
                Sede
              </h2>
              <p className="text-gray-600">
                11 de Novembro,<br />
                Mbanza Kongo, Angola
              </p>
            </div>
          </div>

          {/* Formulário */}
          <div className="md:w-2/3 p-8 lg:p-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Envie uma mensagem</h2>
            <form className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="nome" className="block text-sm font-medium text-gray-700">Nome</label>
                  <input type="text" id="nome" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm p-3 border" placeholder="Seu nome" />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                  <input type="email" id="email" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm p-3 border" placeholder="seu@email.com" />
                </div>
              </div>

              <div>
                <label htmlFor="assunto" className="block text-sm font-medium text-gray-700">Assunto</label>
                <input type="text" id="assunto" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm p-3 border" placeholder="Como podemos ajudar?" />
              </div>

              <div>
                <label htmlFor="mensagem" className="block text-sm font-medium text-gray-700">Mensagem</label>
                <textarea id="mensagem" rows={4} className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-sm p-3 border" placeholder="Escreva a sua mensagem aqui..."></textarea>
              </div>

              <div>
                <button type="submit" className="w-full inline-flex justify-center py-3 px-6 border border-transparent shadow-sm text-base font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors">
                  Enviar Mensagem
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
}