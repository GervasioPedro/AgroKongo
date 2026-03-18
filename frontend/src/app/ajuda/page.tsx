"use client";

import { useState } from 'react';
import Navbar from "@/components/Navbar";
import { ChevronDown, ChevronUp } from 'lucide-react';

const faqs = [
  {
    question: "Como funciona o pagamento seguro (Escrow)?",
    answer: "Quando um comprador paga por um produto, o dinheiro não vai diretamente para o produtor. Fica retido pela AgroKongo numa conta segura. Apenas após o comprador confirmar que recebeu a mercadoria em boas condições é que o valor é libertado para o produtor. Isto protege ambas as partes contra fraudes."
  },
  {
    question: "Quais são as taxas da plataforma?",
    answer: "A AgroKongo cobra uma comissão de 5% sobre o valor total de cada venda bem-sucedida. Esta taxa ajuda-nos a manter a plataforma segura, a oferecer suporte e a desenvolver novas funcionalidades. Não há custos de inscrição ou mensalidades."
  },
  {
    question: "Como posso vender os meus produtos?",
    answer: "Para vender, precisa de uma conta de 'Produtor'. Após o registo, complete o seu perfil com NIF, IBAN e localização. Assim que a sua conta for validada pela nossa equipa, poderá começar a publicar as suas safras no mercado através do seu Dashboard."
  },
  {
    question: "O que acontece se eu receber um produto que não está em conformidade?",
    answer: "Se o produto recebido não corresponder à descrição, tiver defeitos ou não chegar, não confirme a entrega. Em vez disso, abra uma 'Disputa' na página da sua encomenda. A nossa equipa de suporte irá mediar a situação para encontrar uma solução justa, que pode incluir o reembolso total."
  },
  {
    question: "Quanto tempo demora a entrega?",
    answer: "O tempo de entrega varia dependendo da localização do produtor e do comprador. Após o produtor confirmar o envio, é apresentada uma data de entrega estimada. Pode acompanhar o estado da sua encomenda no seu Dashboard."
  }
];

const FaqItem = ({ faq }: { faq: any }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="border-b border-gray-200 py-6">
      <dt>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex justify-between items-center text-left text-gray-700"
        >
          <span className="text-lg font-medium">{faq.question}</span>
          <span className="ml-6 h-7 flex items-center">
            {isOpen ? <ChevronUp className="h-6 w-6" /> : <ChevronDown className="h-6 w-6" />}
          </span>
        </button>
      </dt>
      {isOpen && (
        <dd className="mt-4 pr-12">
          <p className="text-base text-gray-600 leading-relaxed">{faq.answer}</p>
        </dd>
      )}
    </div>
  );
};

export default function AjudaPage() {
  return (
    <div className="bg-gray-50 min-h-screen">
      <Navbar />

      <div className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
              Centro de Ajuda
            </h1>
            <p className="mt-4 text-xl text-gray-500">
              Encontre respostas para as suas perguntas mais frequentes.
            </p>
          </div>

          <div className="mt-16 bg-white p-8 rounded-2xl shadow-xl">
            <dl className="divide-y divide-gray-200">
              {faqs.map((faq, index) => (
                <FaqItem key={index} faq={faq} />
              ))}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}