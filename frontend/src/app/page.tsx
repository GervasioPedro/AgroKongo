import Link from "next/link";
import { ArrowRight, ShoppingBag, Sprout, Shield, Lock, CheckCircle, Users, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-surface-neutral">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-10 w-10 rounded-xl bg-agro-primary flex items-center justify-center">
              <Sprout className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold">AgroKongo</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="#como-funciona" className="text-slate-600 hover:text-agro-primary transition-colors">
              Como Funciona
            </Link>
            <Link href="#vantagens" className="text-slate-600 hover:text-agro-primary transition-colors">
              Vantagens
            </Link>
            <Link href="/mercado" className="text-slate-600 hover:text-agro-primary transition-colors">
              Mercado
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/auth/login">
              <Button variant="ghost" size="sm">Entrar</Button>
            </Link>
            <Link href="/auth/cadastro/passo-1">
              <Button variant="primary" size="sm">Criar Conta</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section com Imagem Real */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-agro-primary/10 px-4 py-2 rounded-full mb-6">
              <Shield className="h-4 w-4 text-agro-primary" />
              <span className="text-sm font-medium text-agro-primary">Sistema de Escrow Seguro</span>
            </div>
            <h1 className="text-4xl lg:text-6xl font-bold mb-6 leading-tight">
              Conectando a Terra ao Mercado com <span className="text-agro-primary">Segurança</span>
            </h1>
            <p className="text-xl text-slate-600 mb-8">
              Marketplace agrícola angolano com sistema de custódia financeira. 
              Dinheiro protegido até a mercadoria chegar.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/auth/cadastro/passo-1">
                <Button variant="primary" className="h-12 px-8 text-lg w-full sm:w-auto">
                  Começar Agora
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Button>
              </Link>
              <Link href="/mercado">
                <Button variant="outline" className="h-12 px-8 text-lg w-full sm:w-auto">
                  Explorar Mercado
                </Button>
              </Link>
            </div>
          </div>
          
          {/* Imagem de Agricultor Angolano */}
          <div className="relative">
            <div className="aspect-square rounded-3xl overflow-hidden shadow-2xl">
              <img
                src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=800&q=80"
                alt="Agricultor angolano no campo"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-agro-primary/80 to-transparent flex items-end p-8">
                <div className="text-white">
                  <p className="text-2xl font-bold mb-2">500+ Produtores</p>
                  <p className="text-white/90">Confiam no AgroKongo</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-white py-12 border-y">
        <div className="max-w-7xl mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <p className="text-4xl font-bold text-agro-primary">500+</p>
              <p className="text-slate-600 mt-2">Produtores</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-agro-primary">2.5M+</p>
              <p className="text-slate-600 mt-2">Kz Transacionados</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-agro-primary">1.200+</p>
              <p className="text-slate-600 mt-2">Transações</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-agro-primary">21</p>
              <p className="text-slate-600 mt-2">Províncias</p>
            </div>
          </div>
        </div>
      </section>

      {/* Imagens de Agricultura */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="relative h-64 rounded-2xl overflow-hidden group">
            <img
              src="https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=600&q=80"
              alt="Colheita de tomates"
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-6">
              <p className="text-white font-semibold text-lg">Hortaliças Frescas</p>
            </div>
          </div>
          <div className="relative h-64 rounded-2xl overflow-hidden group">
            <img
              src="https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=600&q=80"
              alt="Plantação de milho"
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-6">
              <p className="text-white font-semibold text-lg">Cereais</p>
            </div>
          </div>
          <div className="relative h-64 rounded-2xl overflow-hidden group">
            <img
              src="https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=600&q=80"
              alt="Frutas frescas em mercado"
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-6">
              <p className="text-white font-semibold text-lg">Frutas Frescas</p>
            </div>
          </div>
        </div>
      </section>

      {/* Como Funciona */}
      <section id="como-funciona" className="max-w-7xl mx-auto px-4 lg:px-8 py-16 lg:py-24">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold mb-4">Como Funciona o Escrow</h2>
          <p className="text-xl text-slate-600">Segurança em cada etapa da transação</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { num: "1", title: "Pedido", desc: "Comprador escolhe produto e faz pedido", icon: ShoppingBag },
            { num: "2", title: "Custódia", desc: "Pagamento validado e guardado em escrow", icon: Lock },
            { num: "3", title: "Envio", desc: "Produtor envia mercadoria com segurança", icon: Sprout },
            { num: "4", title: "Liberação", desc: "Pagamento liberado após confirmação", icon: CheckCircle },
          ].map((step) => (
            <Card key={step.num} className="text-center hover:shadow-xl transition-shadow">
              <div className="h-16 w-16 rounded-2xl bg-agro-primary/10 flex items-center justify-center mx-auto mb-4">
                <step.icon className="h-8 w-8 text-agro-primary" />
              </div>
              <div className="text-3xl font-bold text-agro-primary mb-2">{step.num}</div>
              <h3 className="font-bold text-lg mb-2">{step.title}</h3>
              <p className="text-sm text-slate-600">{step.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Vantagens com Imagem */}
      <section id="vantagens" className="bg-white py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <h2 className="text-3xl lg:text-4xl font-bold mb-6">Por que escolher AgroKongo?</h2>
              <div className="space-y-4">
                {[
                  { icon: Shield, title: "Pagamento Protegido", desc: "Dinheiro em custódia até entrega confirmada" },
                  { icon: Users, title: "Validação Humana", desc: "Administradores verificam cada pagamento" },
                  { icon: TrendingUp, title: "Sem Intermediários", desc: "Produtor recebe mais, comprador paga menos" },
                  { icon: CheckCircle, title: "Resolução de Disputas", desc: "Mediação profissional em caso de problemas" },
                ].map((item) => (
                  <div key={item.title} className="flex gap-4">
                    <div className="h-12 w-12 rounded-xl bg-agro-primary/10 flex items-center justify-center flex-shrink-0">
                      <item.icon className="h-6 w-6 text-agro-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{item.title}</h3>
                      <p className="text-slate-600">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="order-1 lg:order-2 relative h-96 lg:h-full rounded-3xl overflow-hidden shadow-2xl">
              <img
                src="https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=800&q=80"
                alt="Frutas frescas em mercado angolano"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="max-w-7xl mx-auto px-4 lg:px-8 py-16">
        <Card className="bg-gradient-to-br from-agro-primary to-agro-leaf text-white p-8 lg:p-12 text-center">
          <h3 className="text-3xl lg:text-4xl font-bold mb-4">Pronto para começar?</h3>
          <p className="text-xl mb-8 text-white/90 max-w-2xl mx-auto">
            Junte-se a centenas de produtores e compradores que já confiam no AgroKongo.
          </p>
          <Link href="/auth/cadastro/passo-1">
            <Button className="bg-white text-agro-primary hover:bg-white/90 h-14 px-10 text-lg">
              Criar Conta Grátis
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </Link>
        </Card>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <Link href="/" className="flex items-center gap-2 mb-4">
                <div className="h-8 w-8 rounded-lg bg-agro-primary flex items-center justify-center">
                  <Sprout className="h-5 w-5 text-white" />
                </div>
                <span className="font-bold">AgroKongo</span>
              </Link>
              <p className="text-slate-400 text-sm">
                Conectando a terra ao mercado com segurança.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-3">Produto</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link href="/mercado" className="hover:text-white transition-colors">Mercado</Link></li>
                <li><Link href="#como-funciona" className="hover:text-white transition-colors">Como Funciona</Link></li>
                <li><Link href="#vantagens" className="hover:text-white transition-colors">Vantagens</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3">Empresa</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link href="/sobre" className="hover:text-white transition-colors">Sobre Nós</Link></li>
                <li><Link href="/contacto" className="hover:text-white transition-colors">Contacto</Link></li>
                <li><Link href="/termos" className="hover:text-white transition-colors">Termos</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3">Suporte</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><Link href="/ajuda" className="hover:text-white transition-colors">Central de Ajuda</Link></li>
                <li><Link href="/faq" className="hover:text-white transition-colors">FAQ</Link></li>
                <li className="text-slate-400">suporte@agrokongo.ao</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 mt-8 pt-8 text-center text-sm text-slate-400">
            <p>&copy; 2026 AgroKongo. Todos os direitos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
