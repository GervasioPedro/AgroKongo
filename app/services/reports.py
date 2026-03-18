from sqlalchemy import func
from app.models import db, Transacao, TransactionStatus
from datetime import datetime, timezone, timedelta
from decimal import Decimal


def obter_relatorio_financeiro():
    """
    Gera indicadores financeiros precisos para o Dashboard Administrativo.
    Focado em integridade de dados e performance de índices.
    """
    # 1. Definição de Janela Temporal Otimizada (Evita 'extract')
    agora = datetime.now(timezone.utc)
    primeiro_dia_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 2. Volume Total Bruto (GMV)
    # Ignora apenas transações canceladas ou pendentes iniciais
    volume_total = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
        Transacao.status.notin_([
            TransactionStatus.CANCELADO,
            TransactionStatus.PENDENTE
        ])
    ).scalar() or Decimal('0.00')

    # 3. Receita Realizada (Comissões em posse da plataforma)
    # Apenas o que já foi pago pelo comprador (Escrow em diante)
    receita_total = db.session.query(func.sum(Transacao.comissao_plataforma)).filter(
        Transacao.status.in_([
            TransactionStatus.ESCROW,
            TransactionStatus.ENVIADO,
            TransactionStatus.ENTREGUE,
            TransactionStatus.FINALIZADO
        ])
    ).scalar() or Decimal('0.00')

    # 4. Volume Mensal (Query indexada por intervalo)
    volume_mes = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
        Transacao.data_criacao >= primeiro_dia_mes,
        Transacao.status != TransactionStatus.CANCELADO
    ).scalar() or Decimal('0.00')

    # 5. Projeção de Lucro (Exemplo de regra de negócio)
    custos_operacionais = Decimal('0.20')  # 20%
    lucro_estimado = receita_total * (Decimal('1.00') - custos_operacionais)

    return {
        "volume_total": volume_total,
        "receita_total": receita_total,
        "volume_mes": volume_mes,
        "lucro_estimado": lucro_estimado.quantize(Decimal('0.01'))
    }