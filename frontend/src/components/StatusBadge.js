const StatusBadge = ({ status }) => {
  const statusStyles = {
    // Cores para Comprador/Produtor
    PENDENTE: 'bg-yellow-100 text-yellow-800',
    AGUARDANDO_PAGAMENTO: 'bg-blue-100 text-blue-800',
    ANALISE: 'bg-purple-100 text-purple-800',
    ESCROW: 'bg-green-100 text-green-800',
    ENVIADO: 'bg-cyan-100 text-cyan-800',
    ENTREGUE: 'bg-green-200 text-green-900',
    FINALIZADO: 'bg-gray-200 text-gray-800',
    CANCELADO: 'bg-red-100 text-red-800',
    DISPUTA: 'bg-orange-100 text-orange-800',

    // Cores para Safras
    disponivel: 'bg-green-100 text-green-800',
    esgotado: 'bg-gray-200 text-gray-800',
    pendente: 'bg-yellow-100 text-yellow-800', // Status de safra pendente, se houver
  };

  const statusText = status ? status.replace(/_/g, ' ') : 'Indefinido';

  return (
    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full capitalize ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
      {statusText}
    </span>
  );
};

export default StatusBadge;
