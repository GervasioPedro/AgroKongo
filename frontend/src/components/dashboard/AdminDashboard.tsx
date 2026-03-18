import { useEffect, useState } from "react";
import Link from "next/link";
import { Users, DollarSign, CheckCircle, AlertTriangle, UserCheck } from 'lucide-react';

const KpiCard = ({ title, value, icon: Icon, color, isCurrency = false }: any) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-5 hover:shadow-md hover:border-gray-200 transition-all">
    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${color}`}>
      <Icon size={24} className="text-white" />
    </div>
    <div>
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold text-gray-800">
        {isCurrency
          ? new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(value || 0)
          : value || 0}
      </p>
    </div>
  </div>
);

export default function AdminDashboard({ user }: { user: any }) {
  const [stats, setStats] = useState<any>(null);
  const [tarefas, setTarefas] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Função para carregar dados
  const fetchAllData = async () => {
    try {
      const token = localStorage.getItem("token");

      const resStats = await fetch("http://localhost:5000/api/v1/dashboard/admin", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const jsonStats = await resStats.json();
      if (jsonStats.success) setStats(jsonStats.data);

      const resTarefas = await fetch("http://localhost:5000/api/v1/admin/tarefas", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const jsonTarefas = await resTarefas.json();
      if (jsonTarefas.success) setTarefas(jsonTarefas.data);

    } catch (error) {
      console.error("Erro ao carregar dashboard admin", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleProcessar = async (id: number, acao: 'validar' | 'rejeitar' | 'liquidar') => {
    let motivo = "";
    if (acao === 'rejeitar') {
      motivo = prompt("Motivo da rejeição:") || "";
      if (!motivo) return; // Cancelou
    }

    if (!confirm(`Tem a certeza que deseja ${acao.toUpperCase()} esta operação?`)) return;

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/v1/admin/transacoes/${id}/processar`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ acao, motivo })
      });

      const json = await res.json();
      if (json.success) {
        alert(json.message);
        fetchAllData(); // Atualiza as listas
      } else {
        alert(json.error || "Erro ao processar.");
      }
    } catch (e) {
      alert("Erro de conexão.");
    }
  };

  if (loading) return <div className="p-10 text-center text-gray-500">A carregar métricas...</div>;

  return (
    <div className="space-y-8">
      {/* KPIs Globais */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Utilizadores" value={stats?.kpis.total_users} icon={Users} color="bg-blue-600" />
        <KpiCard title="Volume de Vendas" value={stats?.kpis.volume_vendas} icon={DollarSign} color="bg-green-600" isCurrency={true} />
        <KpiCard title="Comissões (5%)" value={stats?.kpis.comissoes} icon={CheckCircle} color="bg-purple-600" isCurrency={true} />
        <KpiCard title="Pendências Financeiras" value={(tarefas?.validacoes.length || 0) + (tarefas?.liquidacoes.length || 0)} icon={AlertTriangle} color="bg-yellow-500" />
      </div>

      {/* Cartão de Validação de Contas (NOVO) */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full flex items-center justify-center bg-orange-500">
            <UserCheck size={24} className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-800">Validação de Contas</h3>
            <p className="text-sm text-gray-500">Existem {tarefas?.contas_validar || 0} produtores a aguardar aprovação.</p>
          </div>
        </div>
        <Link href="/admin/validacoes" className="bg-orange-500 text-white px-6 py-2 rounded-lg font-bold hover:bg-orange-600 transition-colors">
          Gerir Contas
        </Link>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">

        {/* COLUNA 1: Validação de Pagamentos */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col h-full">
          <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50 rounded-t-2xl">
            <h3 className="text-lg font-bold text-gray-800">1. Validar Pagamentos (Entrada)</h3>
            <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-2.5 py-1 rounded-full border border-yellow-200">
              {tarefas?.validacoes.length} Pendentes
            </span>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[500px] p-6">
            {tarefas?.validacoes.length > 0 ? (
              <ul className="space-y-4">
                {tarefas.validacoes.map((t: any) => (
                  <li key={t.id} className="bg-white border border-gray-100 rounded-xl p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-0.5 rounded inline-block mb-1">{t.ref}</p>
                        <p className="text-sm font-medium text-gray-900">Comprador: <span className="text-gray-600">{t.comprador}</span></p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-green-700">
                          {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(t.valor)}
                        </p>
                        <p className="text-xs text-gray-400">{new Date(t.data).toLocaleDateString()}</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-4 gap-4">
                      {t.comprovativo ? (
                        <a
                          href={`http://localhost:5000${t.comprovativo}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1 hover:underline"
                        >
                          📎 Ver Comprovativo
                        </a>
                      ) : (
                        <span className="text-red-500 text-xs font-medium bg-red-50 px-2 py-1 rounded">Sem anexo</span>
                      )}

                      <div className="flex gap-2">
                         <button
                          onClick={() => handleProcessar(t.id, 'rejeitar')}
                          className="bg-white border border-red-200 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors"
                        >
                          Rejeitar
                        </button>
                        <button
                          onClick={() => handleProcessar(t.id, 'validar')}
                          className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors shadow-sm"
                        >
                          Aprovar
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
               <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                 <CheckCircle size={48} className="mb-2 text-green-100" />
                 <p>Tudo validado! ✅</p>
               </div>
            )}
          </div>
        </div>

        {/* COLUNA 2: Liquidação ao Produtor */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col h-full">
          <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50 rounded-t-2xl">
            <h3 className="text-lg font-bold text-gray-800">2. Liquidar Produtores (Saída)</h3>
            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-1 rounded-full border border-blue-200">
              {tarefas?.liquidacoes.length} Pendentes
            </span>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[500px] p-6">
            {tarefas?.liquidacoes.length > 0 ? (
              <ul className="space-y-4">
                {tarefas.liquidacoes.map((t: any) => (
                  <li key={t.id} className="bg-white border border-gray-100 rounded-xl p-4 hover:shadow-md transition-shadow relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-2 h-full bg-green-500"></div>

                    <div className="mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <p className="text-sm font-bold text-gray-900">{t.produtor}</p>
                        <p className="text-xs font-mono text-gray-400">{t.ref}</p>
                      </div>

                      <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">IBAN de Destino</p>
                        <p className="font-mono text-gray-800 font-medium tracking-wide">{t.iban || "N/D"}</p>
                      </div>

                      <div className="mt-4 flex justify-between items-end">
                        <div>
                          <p className="text-xs text-gray-500">Comissão Retida (5%)</p>
                          <p className="text-sm font-medium text-purple-600">
                            {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(t.comissao)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-500">Valor a Transferir</p>
                          <p className="text-xl font-bold text-gray-900">
                            {new Intl.NumberFormat('pt-AO', { style: 'currency', currency: 'AOA' }).format(t.valor_liquido)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleProcessar(t.id, 'liquidar')}
                      className="w-full bg-gray-900 text-white px-4 py-3 rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
                    >
                      <CheckCircle size={18} /> Confirmar Transferência
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
               <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                 <DollarSign size={48} className="mb-2 text-blue-100" />
                 <p>Nenhum pagamento pendente! 🎉</p>
               </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}