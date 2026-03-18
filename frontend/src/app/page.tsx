import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 font-inter">
      <Navbar />

      {/* Hero Section */}
      <div className="relative bg-gray-900 overflow-hidden">
        <div className="absolute inset-0">
          <img
            className="w-full h-full object-cover object-center opacity-40"
            src="https://images.unsplash.com/photo-1500937386664-56d1dfef3854?q=80&w=1470&auto=format&fit=crop"
            alt="Campo agrícola vasto em Angola"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-gray-900 via-gray-900/80 to-transparent"></div>
        </div>

        <div className="relative max-w-7xl mx-auto py-24 px-4 sm:py-32 sm:px-6 lg:px-8 flex flex-col justify-center h-full">
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-7xl mb-6">
            O Futuro da <br />
            <span className="text-green-400">Agricultura Angolana</span>
          </h1>
          <p className="mt-2 text-xl text-gray-300 max-w-2xl leading-relaxed">
            A plataforma digital que conecta produtores e compradores de forma direta.
            Sem intermediários desnecessários, com segurança garantida e preços justos para todos.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row gap-4">
            <Link
              href="/auth/registro"
              className="bg-green-600 text-white px-8 py-4 rounded-full font-bold text-lg hover:bg-green-700 transition transform hover:scale-105 shadow-lg flex items-center justify-center"
            >
              Começar a Vender
            </Link>
            <Link
              href="/mercado"
              className="bg-white/10 backdrop-blur-md text-white border border-white/30 px-8 py-4 rounded-full font-bold text-lg hover:bg-white/20 transition flex items-center justify-center"
            >
              Explorar Mercado
            </Link>
          </div>
        </div>
      </div>

      {/* Features / Como Funciona */}
      <div className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-green-600 font-bold tracking-wide uppercase text-sm mb-2">Simples e Eficiente</h2>
            <p className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
              Como funciona o AgroKongo?
            </p>
            <p className="mt-4 text-lg text-gray-500">
              Criámos um ecossistema seguro onde o seu negócio pode crescer sem barreiras.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {/* Card 1 */}
            <div className="group relative p-8 bg-gray-50 rounded-3xl hover:bg-white hover:shadow-xl transition-all duration-300 border border-transparent hover:border-gray-100">
              <div className="absolute top-0 left-0 -mt-6 ml-6 w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg transform group-hover:-translate-y-2 transition duration-300">
                1
              </div>
              <h3 className="mt-4 text-xl font-bold text-gray-900 mb-3">Registo Gratuito</h3>
              <p className="text-gray-600 leading-relaxed">
                Crie a sua conta em minutos. Seja produtor ou comprador, o processo é simples e validado para garantir a confiança da rede.
              </p>
            </div>

            {/* Card 2 */}
            <div className="group relative p-8 bg-gray-50 rounded-3xl hover:bg-white hover:shadow-xl transition-all duration-300 border border-transparent hover:border-gray-100">
              <div className="absolute top-0 left-0 -mt-6 ml-6 w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg transform group-hover:-translate-y-2 transition duration-300">
                2
              </div>
              <h3 className="mt-4 text-xl font-bold text-gray-900 mb-3">Negociação Direta</h3>
              <p className="text-gray-600 leading-relaxed">
                Produtores publicam as suas safras com fotos reais. Compradores reservam stock e garantem o melhor preço do mercado.
              </p>
            </div>

            {/* Card 3 */}
            <div className="group relative p-8 bg-gray-50 rounded-3xl hover:bg-white hover:shadow-xl transition-all duration-300 border border-transparent hover:border-gray-100">
              <div className="absolute top-0 left-0 -mt-6 ml-6 w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg transform group-hover:-translate-y-2 transition duration-300">
                3
              </div>
              <h3 className="mt-4 text-xl font-bold text-gray-900 mb-3">Pagamento Seguro (Escrow)</h3>
              <p className="text-gray-600 leading-relaxed">
                O seu dinheiro fica protegido connosco. O pagamento só é libertado ao produtor após a confirmação da entrega da mercadoria.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Final */}
      <div className="bg-green-700">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8 lg:flex lg:items-center lg:justify-between">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            <span className="block">Pronto para começar?</span>
            <span className="block text-green-200">Junte-se a milhares de agricultores hoje.</span>
          </h2>
          <div className="mt-8 flex lg:mt-0 lg:flex-shrink-0">
            <div className="inline-flex rounded-full shadow">
              <Link
                href="/auth/registro"
                className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-bold rounded-full text-green-700 bg-white hover:bg-gray-50 transition"
              >
                Criar Conta Grátis
              </Link>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}