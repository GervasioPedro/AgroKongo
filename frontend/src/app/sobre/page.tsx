import Navbar from "@/components/Navbar";
import { Users, Target, ShieldCheck } from 'lucide-react';

export default function SobrePage() {
  return (
    <div className="bg-white">
      <Navbar />

      {/* Hero Section */}
      <div className="relative h-96 bg-gray-800">
        <img
          src="https://images.unsplash.com/photo-1572281422795-73853c3c0f08?q=80&w=2070&auto=format&fit=crop"
          alt="Agricultores africanos sorrindo"
          className="w-full h-full object-cover opacity-40"
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white px-4">
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight">
              Sobre a AgroKongo
            </h1>
            <p className="mt-4 text-lg md:text-xl max-w-3xl mx-auto text-green-100">
              A nossa missão é digitalizar e potenciar a agricultura em Angola,
              criando um ecossistema justo e próspero para todos.
            </p>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">

          {/* Nossa História Card */}
          <div className="grid md:grid-cols-2 gap-16 items-center mb-24">
            <div className="rounded-2xl overflow-hidden shadow-2xl">
              <img
                src="https://images.unsplash.com/photo-1617293419839-959c504835f7?q=80&w=1964&auto=format&fit=crop"
                alt="Mãos segurando terra fértil"
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">A Nossa História</h2>
              <p className="text-gray-600 text-lg leading-relaxed">
                A AgroKongo nasceu da observação de uma necessidade fundamental: a falta de uma ponte
                eficiente entre o trabalho árduo dos produtores rurais e as necessidades do mercado.
                Vimos agricultores com produtos de alta qualidade a lutar para escoar a sua produção,
                e compradores a procurar, sem sucesso, fornecedores fiáveis.
              </p>
              <p className="mt-4 text-gray-600 text-lg leading-relaxed">
                Decidimos usar a tecnologia para construir essa ponte. Criámos uma plataforma que não só
                conecta, mas também protege, educa e impulsiona cada membro da nossa comunidade.
              </p>
            </div>
          </div>

          {/* Nossos Valores Cards */}
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900">Os Nossos Valores</h2>
            <p className="mt-2 text-lg text-gray-500">Os pilares que guiam cada decisão.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gray-50 p-8 rounded-2xl shadow-lg text-center hover:shadow-xl transition-shadow">
              <div className="inline-block bg-green-100 text-green-600 p-4 rounded-full mb-4">
                <Users size={32} />
              </div>
              <h3 className="text-xl font-bold mb-2">Comunidade</h3>
              <p className="text-gray-600">
                Acreditamos no poder da colaboração. Juntos, produtores e compradores
                constroem um mercado mais forte e resiliente.
              </p>
            </div>
            <div className="bg-gray-50 p-8 rounded-2xl shadow-lg text-center hover:shadow-xl transition-shadow">
              <div className="inline-block bg-green-100 text-green-600 p-4 rounded-full mb-4">
                <Target size={32} />
              </div>
              <h3 className="text-xl font-bold mb-2">Inovação</h3>
              <p className="text-gray-600">
                Aplicamos a tecnologia para resolver problemas reais, simplificando processos
                e criando novas oportunidades de negócio no setor agrícola.
              </p>
            </div>
            <div className="bg-gray-50 p-8 rounded-2xl shadow-lg text-center hover:shadow-xl transition-shadow">
              <div className="inline-block bg-green-100 text-green-600 p-4 rounded-full mb-4">
                <ShieldCheck size={32} />
              </div>
              <h3 className="text-xl font-bold mb-2">Confiança</h3>
              <p className="text-gray-600">
                A transparência e a segurança são a base do nosso sistema de pagamentos (Escrow),
                garantindo que cada transação seja justa e segura.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}